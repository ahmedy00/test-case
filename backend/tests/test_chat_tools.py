"""Tool-handler tests. They exercise the real DB; each test consumes a
`fresh_session_id` fixture which cleans up via CASCADE on teardown."""
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat.tools import (
    add_to_quote_handler,
    replace_with_alternative_handler,
    update_quote_item_handler,
)
from app.models.product import Product
from app.models.quote import Quote, QuoteItem


async def _pick_product(db_session: AsyncSession, sku: str) -> Product:
    res = await db_session.execute(select(Product).where(Product.sku == sku))
    return res.scalar_one()


async def _quote_for_session(db_session: AsyncSession, session_id: UUID) -> Quote | None:
    res = await db_session.execute(
        select(Quote).where(Quote.session_id == session_id, Quote.status == "draft")
    )
    return res.scalar_one_or_none()


async def _items_for_quote(db_session: AsyncSession, quote_id: int) -> list[QuoteItem]:
    res = await db_session.execute(select(QuoteItem).where(QuoteItem.quote_id == quote_id))
    return list(res.scalars().all())


async def test_add_to_quote_creates_quote_and_item(
    db_session: AsyncSession, fresh_session_id: UUID
) -> None:
    product = await _pick_product(db_session, "LAP-001")

    result = await add_to_quote_handler(
        db_session, fresh_session_id, {"product_id": product.id, "quantity": 1}
    )

    assert result.status == "success"
    quote = await _quote_for_session(db_session, fresh_session_id)
    assert quote is not None
    items = await _items_for_quote(db_session, quote.id)
    assert len(items) == 1
    assert items[0].product_id == product.id
    assert items[0].quantity == 1
    assert items[0].unit_price_snapshot == product.price


async def test_add_to_quote_duplicate_increments_quantity(
    db_session: AsyncSession, fresh_session_id: UUID
) -> None:
    product = await _pick_product(db_session, "MON-001")

    await add_to_quote_handler(
        db_session, fresh_session_id, {"product_id": product.id, "quantity": 1}
    )
    await add_to_quote_handler(
        db_session, fresh_session_id, {"product_id": product.id, "quantity": 1}
    )

    quote = await _quote_for_session(db_session, fresh_session_id)
    assert quote is not None
    items = await _items_for_quote(db_session, quote.id)
    assert len(items) == 1
    assert items[0].quantity == 2


async def test_add_to_quote_increments_with_explicit_quantity(
    db_session: AsyncSession, fresh_session_id: UUID
) -> None:
    product = await _pick_product(db_session, "KB-001")

    await add_to_quote_handler(
        db_session, fresh_session_id, {"product_id": product.id, "quantity": 2}
    )
    result = await add_to_quote_handler(
        db_session, fresh_session_id, {"product_id": product.id, "quantity": 3}
    )

    assert result.status == "success"
    assert result.result["quantity"] == 5
    quote = await _quote_for_session(db_session, fresh_session_id)
    assert quote is not None
    items = await _items_for_quote(db_session, quote.id)
    assert len(items) == 1
    assert items[0].quantity == 5


async def test_update_quote_item_changes_quantity(
    db_session: AsyncSession, fresh_session_id: UUID
) -> None:
    product = await _pick_product(db_session, "MS-001")
    add_result = await add_to_quote_handler(
        db_session, fresh_session_id, {"product_id": product.id, "quantity": 1}
    )
    quote_item_id = add_result.result["quote_item_id"]

    update_result = await update_quote_item_handler(
        db_session,
        fresh_session_id,
        {"quote_item_id": quote_item_id, "quantity": 5},
    )

    assert update_result.status == "success"
    res = await db_session.execute(select(QuoteItem).where(QuoteItem.id == quote_item_id))
    item = res.scalar_one()
    await db_session.refresh(item)
    assert item.quantity == 5


async def test_update_quote_item_rejects_unknown_id(
    db_session: AsyncSession, fresh_session_id: UUID
) -> None:
    result = await update_quote_item_handler(
        db_session, fresh_session_id, {"quote_item_id": 999_999, "quantity": 2}
    )
    assert result.status == "error"


async def test_replace_with_alternative_swaps_product(
    db_session: AsyncSession, fresh_session_id: UUID
) -> None:
    product_a = await _pick_product(db_session, "MON-001")
    product_b = await _pick_product(db_session, "MON-002")
    add_result = await add_to_quote_handler(
        db_session, fresh_session_id, {"product_id": product_a.id, "quantity": 2}
    )
    item_id = add_result.result["quote_item_id"]

    result = await replace_with_alternative_handler(
        db_session,
        fresh_session_id,
        {"quote_item_id": item_id, "new_product_id": product_b.id},
    )

    assert result.status == "success"
    quote = await _quote_for_session(db_session, fresh_session_id)
    assert quote is not None
    items = await _items_for_quote(db_session, quote.id)
    assert len(items) == 1
    assert items[0].product_id == product_b.id
    assert items[0].quantity == 2
    assert items[0].unit_price_snapshot == product_b.price


async def test_add_to_quote_unknown_product_returns_error(
    db_session: AsyncSession, fresh_session_id: UUID
) -> None:
    result = await add_to_quote_handler(
        db_session, fresh_session_id, {"product_id": 999_999, "quantity": 1}
    )
    assert result.status == "error"


async def test_add_to_quote_out_of_stock_warns_but_succeeds(
    db_session: AsyncSession, fresh_session_id: UUID
) -> None:
    # LAP-004 (HP EliteBook) is seeded with stock=0 specifically for this case.
    product = await _pick_product(db_session, "LAP-004")
    assert product.stock == 0

    result = await add_to_quote_handler(
        db_session, fresh_session_id, {"product_id": product.id, "quantity": 1}
    )
    assert result.status == "success"
    assert "out of stock" in result.message.lower()
    quote = await _quote_for_session(db_session, fresh_session_id)
    assert quote is not None
    items = await _items_for_quote(db_session, quote.id)
    assert len(items) == 1
    assert items[0].unit_price_snapshot == Decimal("1599.00")
