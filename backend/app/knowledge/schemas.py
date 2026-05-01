from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    category: str
    created_at: datetime
    updated_at: datetime


class KnowledgeCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    category: str = Field(min_length=1, max_length=64)
