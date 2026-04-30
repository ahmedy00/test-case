from decimal import Decimal
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.chat import ChatSession
from app.models.product import Product


class Quote(TimestampMixin, Base):
    __tablename__ = "quotes"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'finalized', 'cancelled')",
            name="ck_quotes_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="draft",
        server_default="draft",
    )

    session: Mapped[ChatSession] = relationship(back_populates="quotes")
    items: Mapped[list["QuoteItem"]] = relationship(
        back_populates="quote",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class QuoteItem(TimestampMixin, Base):
    __tablename__ = "quote_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_quote_items_quantity_positive"),
        UniqueConstraint("quote_id", "product_id", name="uq_quote_items_quote_product"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    quote_id: Mapped[int] = mapped_column(
        ForeignKey("quotes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(nullable=False, default=1, server_default="1")
    unit_price_snapshot: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    quote: Mapped[Quote] = relationship(back_populates="items")
    product: Mapped[Product] = relationship()
