from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat.orchestrator import stream_chat
from app.chat.schemas import ChatRequest
from app.db import get_db

router = APIRouter()


@router.post("/chat/stream")
async def chat_stream(
    req: ChatRequest, db: AsyncSession = Depends(get_db)
) -> StreamingResponse:
    return StreamingResponse(
        stream_chat(db, req.session_id, req.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
