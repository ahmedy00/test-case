from decimal import Decimal
from typing import Any, Literal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.retrieval.embedding import embed_text
from app.retrieval.queries import (
    KNOWLEDGE_FTS_SQL,
    KNOWLEDGE_VECTOR_SQL,
    PRODUCTS_FTS_SQL,
    PRODUCTS_VECTOR_SQL,
    format_vector,
)
from app.retrieval.schemas import RetrievalBundle, RetrievalResult

_SNIPPET_LEN = 200


def _snippet(content: str) -> str:
    return content.strip()[:_SNIPPET_LEN]


def _product_result(row: Any, method: Literal["vector", "fts"]) -> RetrievalResult:
    payload: dict[str, Any] = {
        "sku": row.sku,
        "name": row.name,
        "category": row.category,
        "price": row.price,
        "currency": row.currency,
        "stock": row.stock,
        "description": row.description,
    }
    return RetrievalResult(
        kind="product",
        id=row.id,
        title=row.name,
        snippet=_snippet(row.description),
        score=float(row.score),
        method=method,
        payload=payload,
    )


def _knowledge_result(row: Any, method: Literal["vector", "fts"]) -> RetrievalResult:
    payload: dict[str, Any] = {
        "title": row.title,
        "category": row.category,
        "content": row.content,
    }
    return RetrievalResult(
        kind="knowledge",
        id=row.id,
        title=row.title,
        snippet=_snippet(row.content),
        score=float(row.score),
        method=method,
        payload=payload,
    )


async def retrieve_products(
    session: AsyncSession,
    query: str,
    top_k: int = 5,
    max_price: Decimal | None = None,
    exclude_out_of_stock: bool = True,
) -> tuple[list[RetrievalResult], Literal["vector", "fts"]]:
    embedding = await embed_text(query)

    if embedding is not None:
        result = await session.execute(
            text(PRODUCTS_VECTOR_SQL),
            {
                "embedding": format_vector(embedding),
                "top_k": top_k,
                "max_price": max_price,
                "exclude_out_of_stock": exclude_out_of_stock,
            },
        )
        rows = result.all()
        if rows:
            return [_product_result(r, "vector") for r in rows], "vector"

    result = await session.execute(
        text(PRODUCTS_FTS_SQL),
        {
            "query": query,
            "top_k": top_k,
            "max_price": max_price,
            "exclude_out_of_stock": exclude_out_of_stock,
        },
    )
    rows = result.all()
    return [_product_result(r, "fts") for r in rows], "fts"


async def retrieve_knowledge(
    session: AsyncSession,
    query: str,
    top_k: int = 3,
) -> tuple[list[RetrievalResult], Literal["vector", "fts"]]:
    embedding = await embed_text(query)

    if embedding is not None:
        result = await session.execute(
            text(KNOWLEDGE_VECTOR_SQL),
            {"embedding": format_vector(embedding), "top_k": top_k},
        )
        rows = result.all()
        if rows:
            return [_knowledge_result(r, "vector") for r in rows], "vector"

    result = await session.execute(
        text(KNOWLEDGE_FTS_SQL),
        {"query": query, "top_k": top_k},
    )
    rows = result.all()
    return [_knowledge_result(r, "fts") for r in rows], "fts"


async def retrieve_bundle(
    session: AsyncSession,
    query: str,
    top_k_products: int = 5,
    top_k_knowledge: int = 3,
    max_price: Decimal | None = None,
    exclude_out_of_stock: bool = True,
) -> RetrievalBundle:
    products, products_method = await retrieve_products(
        session=session,
        query=query,
        top_k=top_k_products,
        max_price=max_price,
        exclude_out_of_stock=exclude_out_of_stock,
    )
    knowledge, knowledge_method = await retrieve_knowledge(
        session=session,
        query=query,
        top_k=top_k_knowledge,
    )

    if products_method == knowledge_method:
        method_used: Literal["vector", "fts", "mixed"] = products_method
    else:
        method_used = "mixed"

    return RetrievalBundle(
        products=products,
        knowledge=knowledge,
        method_used=method_used,
    )
