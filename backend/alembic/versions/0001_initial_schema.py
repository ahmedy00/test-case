"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-30
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_PRODUCT_TSV_EXPR = (
    "to_tsvector('english', coalesce(name,'') || ' ' || coalesce(description,''))"
)
_KNOWLEDGE_TSV_EXPR = (
    "to_tsvector('english', coalesce(title,'') || ' ' || coalesce(content,''))"
)


def upgrade() -> None:
    # Extensions must come before any column that depends on them.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    # PG 16 has gen_random_uuid() built in, but enable pgcrypto explicitly so
    # the migration is portable to PG 13/14/15 hosts as well.
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("sku", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("stock", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column(
            "search_tsv",
            postgresql.TSVECTOR(),
            sa.Computed(_PRODUCT_TSV_EXPR, persisted=True),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("sku", name="uq_products_sku"),
    )
    op.create_index("ix_products_sku", "products", ["sku"], unique=True)
    op.create_index("ix_products_category", "products", ["category"])

    op.create_table(
        "knowledge_entries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column(
            "search_tsv",
            postgresql.TSVECTOR(),
            sa.Computed(_KNOWLEDGE_TSV_EXPR, persisted=True),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("title", name="uq_knowledge_entries_title"),
    )
    op.create_index("ix_knowledge_entries_category", "knowledge_entries", ["category"])

    op.create_table(
        "chat_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("chat_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sources", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("tool_calls", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "role IN ('user', 'assistant', 'system', 'tool')",
            name="ck_chat_messages_role",
        ),
    )
    op.create_index("ix_chat_messages_session_id", "chat_messages", ["session_id"])

    op.create_table(
        "quotes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("chat_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(16), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('draft', 'finalized', 'cancelled')",
            name="ck_quotes_status",
        ),
    )
    op.create_index("ix_quotes_session_id", "quotes", ["session_id"])

    op.create_table(
        "quote_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "quote_id",
            sa.Integer(),
            sa.ForeignKey("quotes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            sa.Integer(),
            sa.ForeignKey("products.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("unit_price_snapshot", sa.Numeric(10, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("quantity > 0", name="ck_quote_items_quantity_positive"),
        sa.UniqueConstraint("quote_id", "product_id", name="uq_quote_items_quote_product"),
    )
    op.create_index("ix_quote_items_quote_id", "quote_items", ["quote_id"])

    # Full-text and vector indexes. Raw SQL for HNSW and partial unique because
    # SQLAlchemy/Alembic don't have first-class support for those operators.
    op.execute(
        "CREATE INDEX ix_products_search_tsv ON products USING GIN (search_tsv)"
    )
    op.execute(
        "CREATE INDEX ix_knowledge_entries_search_tsv "
        "ON knowledge_entries USING GIN (search_tsv)"
    )
    op.execute(
        "CREATE INDEX ix_products_embedding "
        "ON products USING hnsw (embedding vector_cosine_ops)"
    )
    op.execute(
        "CREATE INDEX ix_knowledge_entries_embedding "
        "ON knowledge_entries USING hnsw (embedding vector_cosine_ops)"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_quotes_one_draft_per_session "
        "ON quotes (session_id) WHERE status = 'draft'"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_quotes_one_draft_per_session")
    op.execute("DROP INDEX IF EXISTS ix_knowledge_entries_embedding")
    op.execute("DROP INDEX IF EXISTS ix_products_embedding")
    op.execute("DROP INDEX IF EXISTS ix_knowledge_entries_search_tsv")
    op.execute("DROP INDEX IF EXISTS ix_products_search_tsv")

    op.drop_table("quote_items")
    op.drop_table("quotes")
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")
    op.drop_table("knowledge_entries")
    op.drop_table("products")

    # Leave extensions installed — other apps in the same DB may depend on them.
