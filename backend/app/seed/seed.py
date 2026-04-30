"""Idempotent seed: upsert products + knowledge entries, then optionally embed.

Run as: `python -m app.seed.seed` (typically inside the backend container).

Idempotency: ON CONFLICT (sku) / (title) DO UPDATE — re-running the script
overwrites changeable columns and leaves embeddings untouched (so we don't
silently wipe them when re-seeding without an API key).
"""
import asyncio
import logging
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import SessionLocal
from app.logging_config import configure_logging
from app.models import KnowledgeEntry, Product
from app.seed.data import KNOWLEDGE_ENTRIES, PRODUCTS

logger = logging.getLogger("seed")


async def _upsert_products(session: AsyncSession) -> int:
    rows = [dict(p) for p in PRODUCTS]
    stmt = pg_insert(Product).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=[Product.sku],
        set_={
            "name": stmt.excluded.name,
            "description": stmt.excluded.description,
            "category": stmt.excluded.category,
            "price": stmt.excluded.price,
            "stock": stmt.excluded.stock,
        },
    )
    await session.execute(stmt)
    return len(rows)


async def _upsert_knowledge(session: AsyncSession) -> int:
    rows = [dict(k) for k in KNOWLEDGE_ENTRIES]
    stmt = pg_insert(KnowledgeEntry).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=[KnowledgeEntry.title],
        set_={
            "content": stmt.excluded.content,
            "category": stmt.excluded.category,
        },
    )
    await session.execute(stmt)
    return len(rows)


async def _embed_batch(client: Any, model: str, texts: list[str]) -> list[list[float]]:
    response = await asyncio.to_thread(
        client.embeddings.create,
        model=model,
        input=texts,
    )
    return [item.embedding for item in response.data]


async def _embed_products(session: AsyncSession, client: Any, model: str) -> int:
    result = await session.execute(select(Product.id, Product.name, Product.description))
    rows = result.all()
    if not rows:
        return 0
    texts = [f"{r.name}\n{r.description}" for r in rows]
    embeddings = await _embed_batch(client, model, texts)
    for row, emb in zip(rows, embeddings):
        await session.execute(update(Product).where(Product.id == row.id).values(embedding=emb))
    return len(rows)


async def _embed_knowledge(session: AsyncSession, client: Any, model: str) -> int:
    result = await session.execute(
        select(KnowledgeEntry.id, KnowledgeEntry.title, KnowledgeEntry.content)
    )
    rows = result.all()
    if not rows:
        return 0
    texts = [f"{r.title}\n{r.content}" for r in rows]
    embeddings = await _embed_batch(client, model, texts)
    for row, emb in zip(rows, embeddings):
        await session.execute(
            update(KnowledgeEntry).where(KnowledgeEntry.id == row.id).values(embedding=emb)
        )
    return len(rows)


async def main() -> None:
    configure_logging()
    settings = get_settings()

    async with SessionLocal() as session:
        n_products = await _upsert_products(session)
        n_knowledge = await _upsert_knowledge(session)
        await session.commit()

        embeddings_done = False
        if settings.openai_api_key:
            try:
                # Imported lazily so a missing key path doesn't pull in the SDK at all.
                from openai import OpenAI

                client = OpenAI(api_key=settings.openai_api_key)
                model = settings.openai_embedding_model
                logger.info("Generating embeddings with model %s", model)
                await _embed_products(session, client, model)
                await _embed_knowledge(session, client, model)
                await session.commit()
                embeddings_done = True
            except Exception:
                await session.rollback()
                logger.warning(
                    "Embedding generation failed; rows are seeded but embeddings remain NULL.",
                    exc_info=True,
                )
        else:
            logger.warning(
                "OPENAI_API_KEY not set; seeded data will have NULL embeddings (FTS-only retrieval)"
            )

    print(
        f"Seeded {n_products} products, {n_knowledge} knowledge entries "
        f"(embeddings: {'yes' if embeddings_done else 'no'})"
    )


if __name__ == "__main__":
    asyncio.run(main())
