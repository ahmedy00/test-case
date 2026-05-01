"""Raw SQL for retrieval. Kept as text() rather than ORM expressions because
pgvector's `<=>` operator and Postgres `ts_rank` / `websearch_to_tsquery` don't
have clean SQLAlchemy ORM equivalents.

The vector parameter is bound as a string formatted like '[0.123,0.456,...]'
and CAST to `vector` server-side. This avoids depending on the pgvector
psycopg adapter being registered on each async connection — every shape of
SQLAlchemy/psycopg setup parses that literal correctly.

FTS connector choice: `websearch_to_tsquery` sanitizes user input but ANDs
unquoted terms (Google-style), which makes chatty natural-language queries
("What laptops do you offer under $1500?") return zero rows on a small
catalog where no single product matches every stem. We work around this by
running websearch_to_tsquery for sanitization, serializing the result to text,
swapping the `&` connectives for `|`, and re-parsing with `to_tsquery`. That
preserves negation (`!'foo'`) and phrase (`'foo' <-> 'bar'`) operators while
relaxing the AND-of-everything default. Stopword-only inputs round-trip to the
empty tsquery, which yields zero rows — also fine.
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

# Products: FTS fallback. The CTE produces a single OR-connected tsquery
# (see module docstring) so chatty queries don't get filtered out by AND
# semantics on a small catalog.
PRODUCTS_FTS_SQL = """
WITH q AS (
    SELECT to_tsquery(
        'english',
        replace(websearch_to_tsquery('english', :query)::text, ' & ', ' | ')
    ) AS tsq
)
SELECT
    p.id, p.sku, p.name, p.description, p.category, p.price, p.currency, p.stock,
    ts_rank(p.search_tsv, q.tsq) AS score
FROM products p, q
WHERE p.search_tsv @@ q.tsq
  AND (:exclude_out_of_stock = false OR p.stock > 0)
  AND (CAST(:max_price AS NUMERIC) IS NULL OR p.price <= CAST(:max_price AS NUMERIC))
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
WITH q AS (
    SELECT to_tsquery(
        'english',
        replace(websearch_to_tsquery('english', :query)::text, ' & ', ' | ')
    ) AS tsq
)
SELECT
    k.id, k.title, k.content, k.category,
    ts_rank(k.search_tsv, q.tsq) AS score
FROM knowledge_entries k, q
WHERE k.search_tsv @@ q.tsq
ORDER BY score DESC
LIMIT :top_k
"""


def format_vector(embedding: list[float]) -> str:
    """Format a Python float list as a pgvector literal: '[v1,v2,...]'."""
    return "[" + ",".join(format(float(x), "g") for x in embedding) + "]"
