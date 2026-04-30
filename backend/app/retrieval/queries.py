"""Raw SQL for retrieval. Kept as text() rather than ORM expressions because
pgvector's `<=>` operator and Postgres `ts_rank` / `plainto_tsquery` don't have
clean SQLAlchemy ORM equivalents.

The vector parameter is bound as a string formatted like '[0.123,0.456,...]'
and CAST to `vector` server-side. This avoids depending on the pgvector
psycopg adapter being registered on each async connection — every shape of
SQLAlchemy/psycopg setup parses that literal correctly.
"""

# Products: vector path. cosine distance is `<=>`, similarity = 1 - distance.
PRODUCTS_VECTOR_SQL = """
SELECT
    id, sku, name, description, category, price, currency, stock,
    1 - (embedding <=> CAST(:embedding AS vector)) AS score
FROM products
WHERE embedding IS NOT NULL
  AND (:exclude_out_of_stock = false OR stock > 0)
  AND (CAST(:max_price AS NUMERIC) IS NULL OR price <= CAST(:max_price AS NUMERIC))
ORDER BY embedding <=> CAST(:embedding AS vector)
LIMIT :top_k
"""

# Products: FTS fallback. plainto_tsquery sanitizes user input and is safe on
# punctuation; do NOT swap to to_tsquery without quoting.
PRODUCTS_FTS_SQL = """
SELECT
    id, sku, name, description, category, price, currency, stock,
    ts_rank(search_tsv, plainto_tsquery('english', :query)) AS score
FROM products
WHERE search_tsv @@ plainto_tsquery('english', :query)
  AND (:exclude_out_of_stock = false OR stock > 0)
  AND (CAST(:max_price AS NUMERIC) IS NULL OR price <= CAST(:max_price AS NUMERIC))
ORDER BY score DESC
LIMIT :top_k
"""

KNOWLEDGE_VECTOR_SQL = """
SELECT
    id, title, content, category,
    1 - (embedding <=> CAST(:embedding AS vector)) AS score
FROM knowledge_entries
WHERE embedding IS NOT NULL
ORDER BY embedding <=> CAST(:embedding AS vector)
LIMIT :top_k
"""

KNOWLEDGE_FTS_SQL = """
SELECT
    id, title, content, category,
    ts_rank(search_tsv, plainto_tsquery('english', :query)) AS score
FROM knowledge_entries
WHERE search_tsv @@ plainto_tsquery('english', :query)
ORDER BY score DESC
LIMIT :top_k
"""


def format_vector(embedding: list[float]) -> str:
    """Format a Python float list as a pgvector literal: '[v1,v2,...]'."""
    return "[" + ",".join(format(float(x), "g") for x in embedding) + "]"
