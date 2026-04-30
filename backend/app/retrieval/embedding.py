import logging

from app.config import get_settings

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 10.0


async def embed_text(text: str) -> list[float] | None:
    """Embed `text` via OpenAI. Returns None if the key is missing or the call
    fails for any reason — callers fall back to FTS in that case."""
    settings = get_settings()
    if not settings.openai_api_key:
        return None

    try:
        # Lazy import so the SDK isn't loaded when we never reach it.
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=_TIMEOUT_SECONDS)
        response = await client.embeddings.create(
            model=settings.openai_embedding_model,
            input=text,
        )
        return list(response.data[0].embedding)
    except Exception:
        logger.warning("Embedding call failed; falling back to FTS", exc_info=True)
        return None
