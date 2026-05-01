"""Active-quote endpoint tests."""
from decimal import Decimal
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat.tools import add_to_quote_handler
from app.models.product import Product


async def test_active_quote_returns_null_when_empty(
    async_client: httpx.AsyncClient, fresh_session_id: UUID
) -> None:
    response = await async_client.get(
        "/quotes/active", params={"session_id": str(fresh_session_id)}
    )
    assert response.status_code == 200
    assert response.json() is None


async def test_active_quote_returns_items_after_add(
    async_client: httpx.AsyncClient,
    db_session: AsyncSession,
    fresh_session_id: UUID,
) -> None:
    product = (
        await db_session.execute(select(Product).where(Product.sku == "LAP-001"))
    ).scalar_one()

    await add_to_quote_handler(
        db_session, fresh_session_id, {"product_id": product.id, "quantity": 2}
    )

    response = await async_client.get(
        "/quotes/active", params={"session_id": str(fresh_session_id)}
    )
    assert response.status_code == 200
    body = response.json()
    assert body is not None
    assert body["session_id"] == str(fresh_session_id)
    assert body["status"] == "draft"
    assert body["item_count"] == 2
    assert len(body["items"]) == 1

    item = body["items"][0]
    assert item["product_sku"] == "LAP-001"
    assert item["quantity"] == 2
    assert Decimal(item["unit_price_snapshot"]) == product.price
    assert Decimal(item["line_total"]) == product.price * 2
    assert Decimal(body["subtotal"]) == product.price * 2


async def test_active_quote_invalid_uuid_returns_422(
    async_client: httpx.AsyncClient,
) -> None:
    response = await async_client.get(
        "/quotes/active", params={"session_id": "not-a-uuid"}
    )
    assert response.status_code == 422
