from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class QuoteItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    product_sku: str
    product_name: str
    quantity: int
    unit_price_snapshot: Decimal
    line_total: Decimal


class QuoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: UUID
    status: str
    items: list[QuoteItemRead]
    subtotal: Decimal
    item_count: int
    created_at: datetime
    updated_at: datetime
