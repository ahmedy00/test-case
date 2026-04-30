"""Test fixtures.

Tests run against the seeded development database. They are read-only against
shared tables (products, knowledge_entries) and create their own rows in
mutable tables (chat_sessions, quotes) with cleanup. Acceptable for a 2-day
take-home; not production-grade isolation.
"""
from collections.abc import AsyncIterator
from uuid import UUID

import httpx
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionLocal
from app.main import app
from app.models.chat import ChatSession


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def async_client() -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def fresh_session_id() -> AsyncIterator[UUID]:
    """Yield a freshly-created chat_session UUID; cascade-delete on teardown.

    The CASCADE on chat_messages, quotes, and quote_items takes the dependent
    rows with it, so individual tests don't have to clean those tables.
    """
    async with SessionLocal() as session:
        cs = ChatSession()
        session.add(cs)
        await session.flush()
        await session.commit()
        sid = cs.id

    try:
        yield sid
    finally:
        async with SessionLocal() as session:
            row = await session.get(ChatSession, sid)
            if row is not None:
                await session.delete(row)
                await session.commit()
