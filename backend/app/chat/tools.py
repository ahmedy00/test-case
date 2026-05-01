"""Tool handlers + OpenAI function-calling specs.

Each handler:
- Operates on the active draft quote for a session (creating it if needed).
- Performs an atomic upsert / mutation in Postgres.
- Returns a `ToolResult` with a structured `result` dict and a human-readable
  `message` (used directly as the `action` SSE payload by the orchestrator).

Handlers commit their own transaction so each tool call is durable independent
of the surrounding stream — if the SSE response disconnects mid-stream, the
quote state still reflects what the user saw happen.
"""
from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat.schemas import ToolResult
from app.models.product import Product
from app.models.quote import Quote, QuoteItem
from app.quotes.service import get_or_create_active_quote

TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "add_to_quote",
            "description": (
                "Add a product to the active draft quote for this session. Use when the user "
                "agrees to include a product in their quote, or when they explicitly ask to "
                "add one. The same product added twice increments the existing line's quantity."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "integer",
                        "description": "The id of the product to add.",
                    },
                    "quantity": {"type": "integer", "minimum": 1, "default": 1},
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_quote_item",
            "description": "Change the quantity of an existing line item in the active draft quote.",
            "parameters": {
                "type": "object",
                "properties": {
                    "quote_item_id": {"type": "integer"},
                    "quantity": {"type": "integer", "minimum": 1},
                },
                "required": ["quote_item_id", "quantity"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "replace_with_alternative",
            "description": "Replace an existing line item with a different product (same quantity).",
            "parameters": {
                "type": "object",
                "properties": {
                    "quote_item_id": {"type": "integer"},
                    "new_product_id": {"type": "integer"},
                },
                "required": ["quote_item_id", "new_product_id"],
            },
        },
    },
]


def _product_summary(product: Product) -> dict[str, Any]:
    return {
        "id": product.id,
        "sku": product.sku,
        "name": product.name,
        "price": str(product.price),
        "currency": product.currency,
        "stock": product.stock,
    }


async def _upsert_item(
    session: AsyncSession,
    quote_id: int,
    product: Product,
    quantity: int,
) -> tuple[int, int]:
    """Insert or merge a line item. Returns (quote_item_id, final_quantity)."""
    result = await session.execute(
        text(
            """
            INSERT INTO quote_items (quote_id, product_id, quantity, unit_price_snapshot)
            VALUES (:quote_id, :product_id, :quantity, :unit_price)
            ON CONFLICT ON CONSTRAINT uq_quote_items_quote_product
            DO UPDATE SET
                quantity = quote_items.quantity + EXCLUDED.quantity,
                updated_at = now()
            RETURNING id, quantity
            """
        ),
        {
            "quote_id": quote_id,
            "product_id": product.id,
            "quantity": quantity,
            "unit_price": product.price,
        },
    )
    row = result.one()
    return int(row.id), int(row.quantity)


async def add_to_quote_handler(
    session: AsyncSession, session_id: UUID, args: dict[str, Any]
) -> ToolResult:
    product_id = args.get("product_id")
    quantity = args.get("quantity", 1)
    if not isinstance(product_id, int) or not isinstance(quantity, int) or quantity < 1:
        return ToolResult(
            tool="add_to_quote",
            args=args,
            result={},
            status="error",
            message="Invalid arguments: product_id and quantity must be positive integers.",
        )

    product = (
        await session.execute(select(Product).where(Product.id == product_id))
    ).scalar_one_or_none()
    if product is None:
        return ToolResult(
            tool="add_to_quote",
            args=args,
            result={},
            status="error",
            message=f"Product with id {product_id} not found.",
        )

    quote = await get_or_create_active_quote(session, session_id)
    quote_item_id, final_qty = await _upsert_item(session, quote.id, product, quantity)
    await session.commit()

    out_of_stock = product.stock <= 0
    if out_of_stock:
        msg = (
            f"Added {quantity}× {product.name} [{product.sku}] to your quote, but "
            f"this product is currently out of stock."
        )
    else:
        msg = (
            f"Added {quantity}× {product.name} [{product.sku}] to your quote "
            f"(now {final_qty} in cart)."
        )

    return ToolResult(
        tool="add_to_quote",
        args=args,
        result={
            "quote_id": quote.id,
            "quote_item_id": quote_item_id,
            "quantity": final_qty,
            "product": _product_summary(product),
        },
        status="success",
        message=msg,
    )


async def update_quote_item_handler(
    session: AsyncSession, session_id: UUID, args: dict[str, Any]
) -> ToolResult:
    quote_item_id = args.get("quote_item_id")
    quantity = args.get("quantity")
    if (
        not isinstance(quote_item_id, int)
        or not isinstance(quantity, int)
        or quantity < 1
    ):
        return ToolResult(
            tool="update_quote_item",
            args=args,
            result={},
            status="error",
            message="Invalid arguments: quote_item_id and quantity must be positive integers.",
        )

    item = (
        await session.execute(
            select(QuoteItem)
            .join(Quote, QuoteItem.quote_id == Quote.id)
            .where(QuoteItem.id == quote_item_id, Quote.session_id == session_id)
        )
    ).scalar_one_or_none()

    if item is None:
        return ToolResult(
            tool="update_quote_item",
            args=args,
            result={},
            status="error",
            message=f"Quote item {quote_item_id} not found in this session.",
        )

    item.quantity = quantity
    await session.commit()

    return ToolResult(
        tool="update_quote_item",
        args=args,
        result={
            "quote_item_id": item.id,
            "quote_id": item.quote_id,
            "product_id": item.product_id,
            "quantity": item.quantity,
        },
        status="success",
        message=f"Updated line {item.id} to quantity {item.quantity}.",
    )


async def replace_with_alternative_handler(
    session: AsyncSession, session_id: UUID, args: dict[str, Any]
) -> ToolResult:
    quote_item_id = args.get("quote_item_id")
    new_product_id = args.get("new_product_id")
    if not isinstance(quote_item_id, int) or not isinstance(new_product_id, int):
        return ToolResult(
            tool="replace_with_alternative",
            args=args,
            result={},
            status="error",
            message="Invalid arguments: quote_item_id and new_product_id must be integers.",
        )

    item = (
        await session.execute(
            select(QuoteItem)
            .join(Quote, QuoteItem.quote_id == Quote.id)
            .where(QuoteItem.id == quote_item_id, Quote.session_id == session_id)
        )
    ).scalar_one_or_none()
    if item is None:
        return ToolResult(
            tool="replace_with_alternative",
            args=args,
            result={},
            status="error",
            message=f"Quote item {quote_item_id} not found in this session.",
        )

    new_product = (
        await session.execute(select(Product).where(Product.id == new_product_id))
    ).scalar_one_or_none()
    if new_product is None:
        return ToolResult(
            tool="replace_with_alternative",
            args=args,
            result={},
            status="error",
            message=f"Replacement product with id {new_product_id} not found.",
        )

    quote_id = item.quote_id
    quantity = item.quantity
    old_item_id = item.id

    await session.delete(item)
    await session.flush()

    new_item_id, final_qty = await _upsert_item(session, quote_id, new_product, quantity)
    await session.commit()

    return ToolResult(
        tool="replace_with_alternative",
        args=args,
        result={
            "quote_id": quote_id,
            "removed_quote_item_id": old_item_id,
            "quote_item_id": new_item_id,
            "quantity": final_qty,
            "product": _product_summary(new_product),
        },
        status="success",
        message=(
            f"Replaced line {old_item_id} with {new_product.name} [{new_product.sku}] "
            f"({final_qty}×)."
        ),
    )


TOOL_HANDLERS: dict[
    str,
    Callable[[AsyncSession, UUID, dict[str, Any]], Awaitable[ToolResult]],
] = {
    "add_to_quote": add_to_quote_handler,
    "update_quote_item": update_quote_item_handler,
    "replace_with_alternative": replace_with_alternative_handler,
}
