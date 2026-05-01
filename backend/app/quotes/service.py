"""Quote read/write services.

`get_or_create_active_quote` relies on the partial unique index
`uq_quotes_one_draft_per_session` (created in migration 0001). The flow is:

  1. SELECT the draft.
  2. If absent, INSERT ... ON CONFLICT DO NOTHING RETURNING id.
  3. If the insert lost a race (returned nothing), SELECT again and return.

This is simpler than SELECT FOR UPDATE and correct under concurrency because
the partial unique index forbids two drafts per session at the DB level.
"""
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.quote import Quote, QuoteItem
from app.quotes.schemas import QuoteItemRead, QuoteRead


async def get_or_create_active_quote(session: AsyncSession, session_id: UUID) -> Quote:
    existing = await session.execute(
        select(Quote).where(Quote.session_id == session_id, Quote.status == "draft")
    )
    quote = existing.scalar_one_or_none()
    if quote is not None:
        return quote

    # The partial unique index `uq_quotes_one_draft_per_session` is a unique
    # *index* (not a named constraint), so we must use the index-inference
    # form of ON CONFLICT and repeat the partial predicate.
    insert_result = await session.execute(
        text(
            """
            INSERT INTO quotes (session_id, status)
            VALUES (:session_id, 'draft')
            ON CONFLICT (session_id) WHERE status = 'draft' DO NOTHING
            RETURNING id
            """
        ),
        {"session_id": session_id},
    )
    inserted_id = insert_result.scalar_one_or_none()
    await session.commit()

    if inserted_id is not None:
        re_fetch = await session.execute(select(Quote).where(Quote.id == inserted_id))
        return re_fetch.scalar_one()

    re_fetch = await session.execute(
        select(Quote).where(Quote.session_id == session_id, Quote.status == "draft")
    )
    return re_fetch.scalar_one()


async def get_active_quote_with_items(
    session: AsyncSession, session_id: UUID
) -> QuoteRead | None:
    result = await session.execute(
        select(Quote)
        .where(Quote.session_id == session_id, Quote.status == "draft")
        .options(selectinload(Quote.items).selectinload(QuoteItem.product))
    )
    quote = result.scalar_one_or_none()
    if quote is None:
        return None

    items: list[QuoteItemRead] = []
    subtotal = Decimal("0.00")
    for item in quote.items:
        line_total = (item.unit_price_snapshot * item.quantity).quantize(Decimal("0.01"))
        subtotal += line_total
        items.append(
            QuoteItemRead(
                id=item.id,
                product_id=item.product_id,
                product_sku=item.product.sku,
                product_name=item.product.name,
                quantity=item.quantity,
                unit_price_snapshot=item.unit_price_snapshot,
                line_total=line_total,
            )
        )

    items.sort(key=lambda it: it.id)

    return QuoteRead(
        id=quote.id,
        session_id=quote.session_id,
        status=quote.status,
        items=items,
        subtotal=subtotal.quantize(Decimal("0.01")),
        item_count=sum(it.quantity for it in items),
        created_at=quote.created_at,
        updated_at=quote.updated_at,
    )
