"""SSE-streaming chat orchestrator.

Algorithm overview:

    session bootstrap → persist user msg → retrieve → emit `sources` →
        if OPENAI_API_KEY: LLM tool-loop, emitting `chunk` and `action`
        else: fallback streamer, emitting `chunk` only
    persist assistant msg → emit `done`

LLM tool-loop interleaves text deltas and tool-call deltas in a single stream.
Tool-call deltas arrive incrementally per index (id, function.name, and
function.arguments — the last one is a JSON string assembled chunk-by-chunk).
We accumulate them into a list keyed by index, execute on `finish_reason ==
"tool_calls"`, append assistant + tool messages to the history, and re-stream.
A 3-round cap prevents runaway tool loops.

Errors are caught at the generator boundary and emitted as a terminal `error`
SSE event — never re-raised, because SSE clients can't recover from it.
"""
from __future__ import annotations

import json
import logging
from collections.abc import AsyncGenerator
from typing import Any
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat.fallback import stream_fallback_response
from app.chat.prompts import SYSTEM_PROMPT, build_context_message
from app.chat.schemas import (
    ActionEvent,
    ChunkEvent,
    DoneEvent,
    ErrorEvent,
    SessionEvent,
    SourcesEvent,
    format_sse,
)
from app.chat.tools import TOOL_HANDLERS, TOOLS
from app.config import get_settings
from app.models.chat import ChatMessage, ChatSession
from app.retrieval import retrieve_bundle
from app.retrieval.schemas import RetrievalBundle

logger = logging.getLogger(__name__)

_HISTORY_LIMIT = 10
_TOOL_LOOP_CAP = 3


async def _create_session(session: AsyncSession) -> UUID:
    row = ChatSession()
    session.add(row)
    await session.flush()
    await session.commit()
    await session.refresh(row)
    return row.id


async def _persist_message(
    session: AsyncSession,
    session_id: UUID,
    role: str,
    content: str,
    sources: Any | None = None,
    tool_calls: Any | None = None,
) -> int:
    msg = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        sources=sources,
        tool_calls=tool_calls,
    )
    session.add(msg)
    await session.flush()
    await session.commit()
    return msg.id


async def _load_history(
    session: AsyncSession, session_id: UUID
) -> list[dict[str, Any]]:
    """Return the last N messages, oldest-first, in OpenAI message format.

    `tool` and `tool_calls` rows from prior turns are intentionally NOT
    replayed — keeping history to bare user/assistant text avoids the
    invalid-history class of OpenAI errors and is enough for short
    conversational continuity.
    """
    result = await session.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(desc(ChatMessage.id))
        .limit(_HISTORY_LIMIT)
    )
    rows = list(result.scalars().all())
    rows.reverse()
    history: list[dict[str, Any]] = []
    for r in rows:
        if r.role in ("user", "assistant") and r.content:
            history.append({"role": r.role, "content": r.content})
    return history


def _accumulate_tool_call_delta(
    accumulator: list[dict[str, Any]], delta_tool_calls: list[Any]
) -> None:
    for tcd in delta_tool_calls:
        idx = tcd.index
        while len(accumulator) <= idx:
            accumulator.append({"id": None, "name": None, "arguments": ""})
        slot = accumulator[idx]
        if getattr(tcd, "id", None):
            slot["id"] = tcd.id
        fn = getattr(tcd, "function", None)
        if fn is not None:
            if getattr(fn, "name", None):
                slot["name"] = fn.name
            if getattr(fn, "arguments", None):
                slot["arguments"] += fn.arguments


async def _execute_tool_call(
    db: AsyncSession,
    session_id: UUID,
    tool_call: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    """Run one accumulated tool call. Returns (sse_string, action_payload_dict)."""
    name = tool_call["name"] or ""
    raw_args = tool_call["arguments"] or "{}"
    try:
        parsed_args = json.loads(raw_args)
        if not isinstance(parsed_args, dict):
            raise ValueError("tool arguments must be a JSON object")
    except (json.JSONDecodeError, ValueError) as exc:
        action = ActionEvent(
            tool=name,
            args={"_raw": raw_args},
            result={},
            status="error",
            message=f"Could not parse tool arguments: {exc}",
        )
        return format_sse("action", action), action.model_dump()

    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        action = ActionEvent(
            tool=name,
            args=parsed_args,
            result={},
            status="error",
            message=f"Unknown tool: {name}",
        )
        return format_sse("action", action), action.model_dump()

    result = await handler(db, session_id, parsed_args)
    action = ActionEvent(
        tool=result.tool,
        args=result.args,
        result=result.result,
        status=result.status,
        message=result.message,
    )
    return format_sse("action", action), action.model_dump()


async def _stream_llm_path(
    db: AsyncSession,
    session_id: UUID,
    user_message: str,
    bundle: RetrievalBundle,
    sources_payload: dict[str, Any],
) -> AsyncGenerator[str, None]:
    from openai import AsyncOpenAI

    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    history = await _load_history(db, session_id)
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": build_context_message(bundle)},
        *history,
    ]

    assistant_text_total = ""
    executed_actions: list[dict[str, Any]] = []
    tool_call_record: list[dict[str, Any]] = []
    tool_rounds = 0

    while True:
        stream = await client.chat.completions.create(
            model=settings.openai_chat_model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            stream=True,
        )

        round_text = ""
        tool_calls_acc: list[dict[str, Any]] = []
        finish_reason: str | None = None

        async for chunk in stream:
            if not chunk.choices:
                continue
            choice = chunk.choices[0]
            delta = choice.delta

            if delta and getattr(delta, "content", None):
                round_text += delta.content
                yield format_sse("chunk", ChunkEvent(delta=delta.content))

            if delta and getattr(delta, "tool_calls", None):
                _accumulate_tool_call_delta(tool_calls_acc, delta.tool_calls)

            if choice.finish_reason:
                finish_reason = choice.finish_reason

        assistant_text_total += round_text

        if finish_reason != "tool_calls" or not tool_calls_acc:
            break

        if tool_rounds >= _TOOL_LOOP_CAP:
            yield format_sse(
                "error",
                ErrorEvent(
                    code="tool_loop_exceeded",
                    message=f"Tool-call loop exceeded {_TOOL_LOOP_CAP} rounds.",
                ),
            )
            return

        assistant_msg: dict[str, Any] = {
            "role": "assistant",
            "content": round_text or None,
            "tool_calls": [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"] or "",
                        "arguments": tc["arguments"] or "{}",
                    },
                }
                for tc in tool_calls_acc
            ],
        }
        messages.append(assistant_msg)
        tool_call_record.extend(assistant_msg["tool_calls"])

        for tc in tool_calls_acc:
            sse_str, action_payload = await _execute_tool_call(db, session_id, tc)
            yield sse_str
            executed_actions.append(action_payload)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc["id"] or "",
                    "content": json.dumps(action_payload["result"], default=str),
                }
            )

        tool_rounds += 1

    final_text = assistant_text_total or "(no response)"
    persisted_tool_calls = (
        {"calls": tool_call_record, "actions": executed_actions}
        if tool_call_record
        else None
    )
    msg_id = await _persist_message(
        db,
        session_id,
        role="assistant",
        content=final_text,
        sources=sources_payload,
        tool_calls=persisted_tool_calls,
    )
    yield format_sse("done", DoneEvent(message_id=msg_id))


async def stream_chat(
    session: AsyncSession,
    session_id: UUID | None,
    user_message: str,
) -> AsyncGenerator[str, None]:
    settings = get_settings()
    sources_payload: dict[str, Any] = {}

    try:
        if session_id is None:
            session_id = await _create_session(session)
            yield format_sse("session", SessionEvent(session_id=session_id))

        await _persist_message(session, session_id, role="user", content=user_message)

        try:
            bundle = await retrieve_bundle(session, user_message)
        except Exception:
            logger.exception("Retrieval failed; using empty bundle")
            bundle = RetrievalBundle(products=[], knowledge=[], method_used="fts")

        sources_event = SourcesEvent.from_bundle(bundle)
        sources_payload = sources_event.model_dump()
        yield format_sse("sources", sources_event)

        if settings.openai_api_key:
            try:
                async for sse in _stream_llm_path(
                    session, session_id, user_message, bundle, sources_payload
                ):
                    yield sse
                return
            except Exception:
                # If the LLM client itself raises before producing any output,
                # silently pivot to the fallback. The user gets a templated
                # answer instead of a broken stream.
                logger.exception("LLM path failed; serving fallback response")

        text_acc = ""
        async for piece in stream_fallback_response(bundle, user_message):
            text_acc += piece
            yield format_sse("chunk", ChunkEvent(delta=piece))

        msg_id = await _persist_message(
            session,
            session_id,
            role="assistant",
            content=text_acc,
            sources=sources_payload,
            tool_calls=None,
        )
        yield format_sse("done", DoneEvent(message_id=msg_id))

    except Exception as exc:
        logger.exception("stream_chat top-level failure")
        yield format_sse(
            "error",
            ErrorEvent(
                code=type(exc).__name__,
                message="An unexpected error occurred while generating the response.",
            ),
        )
