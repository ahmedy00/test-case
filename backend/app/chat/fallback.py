"""Templated, no-LLM streaming response. Used when OPENAI_API_KEY is missing
or the LLM call raises. Retrieval still ran — sources have already been
emitted by the orchestrator. This module owns only the assistant text."""
from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator

from app.retrieval.schemas import RetrievalBundle

_CHUNK_SIZE = 40
_CHUNK_DELAY = 0.02
_KNOWLEDGE_SNIPPET = 250


def _build_response(bundle: RetrievalBundle, user_message: str) -> str:
    has_products = bool(bundle.products)
    has_knowledge = bool(bundle.knowledge)

    if not has_products and not has_knowledge:
        return (
            "I couldn't find anything relevant in our catalog or knowledge base "
            "for your question. Could you rephrase or share more detail about what "
            "you're looking for?"
        )

    if has_products:
        top = bundle.products[:3]
        bullets = []
        for r in top:
            p = r.payload
            bullets.append(
                f"- {p['name']} [{p['sku']}] — ${p['price']} {p.get('currency', 'USD')}"
            )
        intro = (
            "Here are some products from our catalog that match your query:\n"
            + "\n".join(bullets)
            + "\n\nLet me know if you'd like to add any of these to your quote."
        )
        if has_knowledge:
            k = bundle.knowledge[0].payload
            snippet = k["content"].strip()[:_KNOWLEDGE_SNIPPET]
            intro += f"\n\nRelated policy ({k['title']}): {snippet}"
        return intro

    # Knowledge-only path.
    k = bundle.knowledge[0].payload
    snippet = k["content"].strip()[:_KNOWLEDGE_SNIPPET]
    return f"Based on our policies: {snippet} (Source: {k['title']})."


async def stream_fallback_response(
    bundle: RetrievalBundle,
    user_message: str,
) -> AsyncGenerator[str, None]:
    """Yields chunks of a templated response. The orchestrator wraps each
    chunk in an SSE `chunk` event.
    """
    text = _build_response(bundle, user_message)
    for i in range(0, len(text), _CHUNK_SIZE):
        yield text[i : i + _CHUNK_SIZE]
        await asyncio.sleep(_CHUNK_DELAY)
