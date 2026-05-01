from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.quotes import QuoteRead, get_active_quote_with_items

router = APIRouter()


@router.get("/quotes/active", response_model=QuoteRead | None)
async def get_active_quote(
    session_id: UUID, db: AsyncSession = Depends(get_db)
) -> QuoteRead | None:
    return await get_active_quote_with_items(db, session_id)
