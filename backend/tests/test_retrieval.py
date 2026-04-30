from decimal import Decimal

from app.retrieval import retrieve_knowledge, retrieve_products


async def test_fts_returns_grounded_products(db_session) -> None:
    results, method = await retrieve_products(db_session, "laptop for engineers", top_k=5)
    assert method == "fts"
    assert len(results) >= 1
    assert all(r.kind == "product" for r in results)
    assert any(r.payload["category"] == "laptop" for r in results)


async def test_fts_excludes_out_of_stock_by_default(db_session) -> None:
    results, _ = await retrieve_products(db_session, "elitebook", top_k=10)
    assert all(r.payload["stock"] > 0 for r in results)
    assert not any(r.payload["sku"] == "LAP-004" for r in results)


async def test_fts_includes_out_of_stock_when_disabled(db_session) -> None:
    results, _ = await retrieve_products(
        db_session, "elitebook", top_k=10, exclude_out_of_stock=False
    )
    assert any(r.payload["sku"] == "LAP-004" for r in results)


async def test_fts_respects_price_limit(db_session) -> None:
    results, _ = await retrieve_products(
        db_session, "laptop", top_k=10, max_price=Decimal("1000")
    )
    assert len(results) >= 1
    assert all(r.payload["price"] <= Decimal("1000") for r in results)


async def test_fts_returns_grounded_knowledge(db_session) -> None:
    results, method = await retrieve_knowledge(
        db_session, "how do I return a damaged item", top_k=3
    )
    assert method == "fts"
    assert len(results) >= 1
    assert all(r.kind == "knowledge" for r in results)


async def test_search_endpoint_returns_bundle(async_client) -> None:
    response = await async_client.post(
        "/search",
        json={
            "query": "warranty for monitors",
            "top_k_products": 3,
            "top_k_knowledge": 2,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert "products" in body
    assert "knowledge" in body
    assert body["method_used"] in {"vector", "fts", "mixed"}
