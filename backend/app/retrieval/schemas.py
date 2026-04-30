from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field


class RetrievalResult(BaseModel):
    kind: Literal["product", "knowledge"]
    id: int
    title: str
    snippet: str
    score: float
    method: Literal["vector", "fts"]
    payload: dict[str, Any]


class RetrievalBundle(BaseModel):
    products: list[RetrievalResult]
    knowledge: list[RetrievalResult]
    method_used: Literal["vector", "fts", "mixed"]


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    top_k_products: int = Field(default=5, ge=1, le=20)
    top_k_knowledge: int = Field(default=3, ge=1, le=20)
    max_price: Decimal | None = None
    exclude_out_of_stock: bool = True
