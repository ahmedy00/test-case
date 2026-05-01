"""Knowledge list/create endpoint tests."""
import uuid

import httpx
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_entry import KnowledgeEntry


async def test_list_knowledge_returns_seeded_rows(
    async_client: httpx.AsyncClient,
) -> None:
    response = await async_client.get("/knowledge")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) >= 8
    sample = body[0]
    for key in ("id", "title", "content", "category"):
        assert key in sample


async def test_create_knowledge_appears_in_list(
    async_client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    suffix = uuid.uuid4().hex[:8]
    title = f"Pytest entry {suffix}"
    payload = {
        "title": title,
        "content": "This is a temporary entry created by the test suite.",
        "category": "test",
    }

    try:
        create_resp = await async_client.post("/knowledge", json=payload)
        assert create_resp.status_code == 201, create_resp.text
        created = create_resp.json()
        assert created["title"] == title
        assert created["category"] == "test"

        list_resp = await async_client.get("/knowledge")
        assert list_resp.status_code == 200
        titles = {row["title"] for row in list_resp.json()}
        assert title in titles
    finally:
        await db_session.execute(
            delete(KnowledgeEntry).where(KnowledgeEntry.title == title)
        )
        await db_session.commit()
