"""Products list/create endpoint tests."""
import uuid
from decimal import Decimal

import httpx
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product


async def test_list_products_returns_seeded_rows(
    async_client: httpx.AsyncClient,
) -> None:
    response = await async_client.get("/products")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) >= 15
    sample = body[0]
    for key in ("id", "sku", "name", "description", "category", "price", "currency", "stock"):
        assert key in sample


async def test_create_product_appears_in_list(
    async_client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    suffix = uuid.uuid4().hex[:8]
    sku = f"TEST-{suffix}"
    payload = {
        "sku": sku,
        "name": f"Test Widget {suffix}",
        "description": "Pytest-created product.",
        "category": "test",
        "price": "12.34",
        "stock": 7,
    }

    try:
        create_resp = await async_client.post("/products", json=payload)
        assert create_resp.status_code == 201, create_resp.text
        created = create_resp.json()
        assert created["sku"] == sku
        assert Decimal(created["price"]) == Decimal("12.34")
        assert created["currency"] == "USD"
        assert created["stock"] == 7

        list_resp = await async_client.get("/products")
        assert list_resp.status_code == 200
        skus = {row["sku"] for row in list_resp.json()}
        assert sku in skus
    finally:
        await db_session.execute(delete(Product).where(Product.sku == sku))
        await db_session.commit()
