from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    name: str
    description: str
    category: str
    price: Decimal
    currency: str
    stock: int
    created_at: datetime
    updated_at: datetime


class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    category: str = Field(min_length=1, max_length=64)
    price: Decimal = Field(ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    stock: int = Field(default=0, ge=0)
