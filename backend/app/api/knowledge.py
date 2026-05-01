from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.knowledge import KnowledgeCreate, KnowledgeRead
from app.models.knowledge_entry import KnowledgeEntry

router = APIRouter()


@router.get("/knowledge", response_model=list[KnowledgeRead])
async def list_knowledge(db: AsyncSession = Depends(get_db)) -> list[KnowledgeEntry]:
    result = await db.execute(select(KnowledgeEntry).order_by(KnowledgeEntry.id))
    return list(result.scalars().all())


@router.post(
    "/knowledge",
    response_model=KnowledgeRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_knowledge(
    payload: KnowledgeCreate, db: AsyncSession = Depends(get_db)
) -> KnowledgeEntry:
    entry = KnowledgeEntry(
        title=payload.title,
        content=payload.content,
        category=payload.category,
    )
    db.add(entry)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Knowledge entry with title '{payload.title}' already exists.",
        ) from exc
    await db.refresh(entry)
    return entry
