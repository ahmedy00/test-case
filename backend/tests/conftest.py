"""Test fixtures.

Tests run against the seeded development database. They are read-only against
shared tables (products, knowledge_entries) and create their own rows in
mutable tables (chat_sessions, quotes) with cleanup. Acceptable for a 2-day
take-home; not production-grade isolation.
"""
from collections.abc import AsyncIterator

import httpx
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionLocal
from app.main import app


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def async_client() -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
