"""The single most important test for the rubric: prove the fallback
response (no LLM) actually mentions retrieved products. A generic apology
that ignores `bundle.products` would still pass `test_chat_fallback`'s
event-flow assertions, so this fills that gap explicitly."""
from collections.abc import AsyncIterator

import httpx
import pytest_asyncio

from app.config import get_settings
from app.db import SessionLocal
from app.main import app
from app.models.chat import ChatSession

from .test_chat_fallback import parse_sse_events


@pytest_asyncio.fixture
async def fallback_client(monkeypatch) -> AsyncIterator[httpx.AsyncClient]:
    settings = get_settings()
    monkeypatch.setattr(settings, "openai_api_key", None)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def _delete_session(session_id) -> None:
    async with SessionLocal() as session:
        row = await session.get(ChatSession, session_id)
        if row is not None:
            await session.delete(row)
            await session.commit()


async def test_fallback_response_is_grounded_in_retrieval(
    fallback_client: httpx.AsyncClient,
) -> None:
    raw_chunks: list[str] = []
    async with fallback_client.stream(
        "POST", "/chat/stream", json={"session_id": None, "message": "monitors"}
    ) as resp:
        assert resp.status_code == 200
        async for chunk in resp.aiter_text():
            raw_chunks.append(chunk)
    events = parse_sse_events("".join(raw_chunks))

    sources_event = next(e for e in events if e["event"] == "sources")
    products = sources_event["data"]["products"]
    assert len(products) >= 1, "query must surface at least one monitor"

    # Build the set of identifying tokens we expect to find verbatim in the
    # assistant's chunked text — the fallback template inserts both `name`
    # and `[sku]` for each top-3 product.
    candidate_tokens: set[str] = set()
    for p in products[:3]:
        candidate_tokens.add(p["payload"]["sku"])
        candidate_tokens.add(p["payload"]["name"])

    text = "".join(
        e["data"]["delta"] for e in events if e["event"] == "chunk"
    )
    assert text.strip(), "fallback must produce non-empty chunked text"

    matches = [tok for tok in candidate_tokens if tok in text]
    assert matches, (
        "fallback response did not mention any retrieved product. "
        f"sources={sorted(candidate_tokens)} chunked_text={text!r}"
    )

    session_event = next(e for e in events if e["event"] == "session")
    sid = session_event["data"]["session_id"]
    await _delete_session(sid)
