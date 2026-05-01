"""Pydantic models for chat I/O and SSE event payloads.

The SSE event payload models live next to ChatRequest because they form the
public contract that the web/mobile clients will parse — keeping them in one
place keeps that contract reviewable.
"""
from __future__ import annotations

import json
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.retrieval.schemas import RetrievalBundle


class ChatRequest(BaseModel):
    session_id: UUID | None = None
    message: str = Field(min_length=1, max_length=2000)


class SessionEvent(BaseModel):
    session_id: UUID


class SourcesEvent(BaseModel):
    products: list[dict[str, Any]]
    knowledge: list[dict[str, Any]]
    method_used: Literal["vector", "fts", "mixed"]

    @classmethod
    def from_bundle(cls, bundle: RetrievalBundle) -> "SourcesEvent":
        return cls(
            products=[r.model_dump(mode="json") for r in bundle.products],
            knowledge=[r.model_dump(mode="json") for r in bundle.knowledge],
            method_used=bundle.method_used,
        )


class ChunkEvent(BaseModel):
    delta: str


class ActionEvent(BaseModel):
    tool: str
    args: dict[str, Any]
    result: dict[str, Any]
    status: Literal["success", "error"]
    message: str


class DoneEvent(BaseModel):
    message_id: int


class ErrorEvent(BaseModel):
    code: str
    message: str


class ToolResult(BaseModel):
    tool: str
    args: dict[str, Any]
    result: dict[str, Any]
    status: Literal["success", "error"]
    message: str


def format_sse(event_name: str, payload: BaseModel | dict[str, Any]) -> str:
    """Produce `event: <name>\\ndata: <json>\\n\\n` framing for SSE."""
    if isinstance(payload, BaseModel):
        body = payload.model_dump_json()
    else:
        body = json.dumps(payload, default=str)
    return f"event: {event_name}\ndata: {body}\n\n"
