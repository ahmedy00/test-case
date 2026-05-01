"""Fallback-path tests. Force `openai_api_key=None` so the orchestrator
takes the templated path. The stream still runs through the real FastAPI
app and a real DB."""
import json
from collections.abc import AsyncIterator

import httpx
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import SessionLocal
from app.main import app
from app.models.chat import ChatMessage, ChatSession


@pytest_asyncio.fixture
async def fallback_client(monkeypatch) -> AsyncIterator[httpx.AsyncClient]:
    """Patch the cached settings so the chat path treats the env as keyless."""
    settings = get_settings()
    monkeypatch.setattr(settings, "openai_api_key", None)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


def parse_sse_events(raw: str) -> list[dict]:
    """Parse a complete SSE response body into a list of {event, data} dicts."""
    events: list[dict] = []
    for block in raw.split("\n\n"):
        if not block.strip():
            continue
        event_name: str | None = None
        data_lines: list[str] = []
        for line in block.split("\n"):
            if line.startswith("event:"):
                event_name = line[len("event:") :].strip()
            elif line.startswith("data:"):
                data_lines.append(line[len("data:") :].strip())
        if event_name is None:
            continue
        try:
            data = json.loads("\n".join(data_lines)) if data_lines else None
        except json.JSONDecodeError:
            data = "\n".join(data_lines)
        events.append({"event": event_name, "data": data})
    return events


async def _post_and_read(
    client: httpx.AsyncClient, body: dict
) -> tuple[list[dict], str]:
    raw_chunks: list[str] = []
    async with client.stream("POST", "/chat/stream", json=body) as resp:
        assert resp.status_code == 200
        async for chunk in resp.aiter_text():
            raw_chunks.append(chunk)
    raw = "".join(raw_chunks)
    return parse_sse_events(raw), raw


async def _delete_session(session_id) -> None:
    async with SessionLocal() as session:
        row = await session.get(ChatSession, session_id)
        if row is not None:
            await session.delete(row)
            await session.commit()


async def test_fallback_stream_emits_sources_and_chunks(
    fallback_client: httpx.AsyncClient,
) -> None:
    # Single-token query reliably hits the seeded product whose description
    # contains "laptop" — keeps this assertion robust regardless of which
    # tsquery flavor the FTS path uses.
    events, _ = await _post_and_read(
        fallback_client,
        {"session_id": None, "message": "laptop"},
    )

    by_name = [e["event"] for e in events]
    assert by_name[0] == "session"  # new session created → fires first
    assert "sources" in by_name
    assert by_name.count("sources") == 1
    assert "chunk" in by_name
    assert by_name[-1] == "done"
    assert "action" not in by_name
    assert "error" not in by_name

    # Sources event must contain at least one product for this query.
    sources_event = next(e for e in events if e["event"] == "sources")
    assert isinstance(sources_event["data"]["products"], list)
    assert len(sources_event["data"]["products"]) >= 1
    assert sources_event["data"]["method_used"] in {"vector", "fts", "mixed"}

    session_event = next(e for e in events if e["event"] == "session")
    sid = session_event["data"]["session_id"]
    try:
        # `done` carries a real persisted message_id.
        done_event = next(e for e in events if e["event"] == "done")
        assert isinstance(done_event["data"]["message_id"], int)
    finally:
        await _delete_session(sid)


async def test_fallback_persists_messages(
    fallback_client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    events, _ = await _post_and_read(
        fallback_client,
        {"session_id": None, "message": "Tell me about your return policy"},
    )

    session_event = next(e for e in events if e["event"] == "session")
    sid = session_event["data"]["session_id"]

    try:
        result = await db_session.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == sid)
            .order_by(ChatMessage.id)
        )
        rows = list(result.scalars().all())
        assert len(rows) == 2
        assert rows[0].role == "user"
        assert rows[1].role == "assistant"
        assert rows[1].sources is not None
        assert "products" in rows[1].sources
        assert "knowledge" in rows[1].sources
        # Fallback path emits no tool calls.
        assert rows[1].tool_calls is None
    finally:
        await _delete_session(sid)


async def test_fallback_with_existing_session_no_session_event(
    fallback_client: httpx.AsyncClient, fresh_session_id
) -> None:
    events, _ = await _post_and_read(
        fallback_client,
        {"session_id": str(fresh_session_id), "message": "show me a 4K monitor"},
    )

    by_name = [e["event"] for e in events]
    # When session_id is provided, no `session` event is emitted.
    assert "session" not in by_name
    assert by_name[0] == "sources"
    assert by_name[-1] == "done"
    assert "chunk" in by_name


async def test_fallback_handles_empty_retrieval_gracefully(
    fallback_client: httpx.AsyncClient, fresh_session_id
) -> None:
    # Gibberish query should produce empty (or near-empty) retrieval; either
    # way the fallback must complete without crashing.
    events, _ = await _post_and_read(
        fallback_client,
        {
            "session_id": str(fresh_session_id),
            "message": "qwxzpfg nonexistent gobbledygook xyzzyplugh",
        },
    )
    by_name = [e["event"] for e in events]
    assert by_name[-1] == "done"
    assert "error" not in by_name
