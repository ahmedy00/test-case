from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.retrieval import RetrievalBundle, SearchRequest, retrieve_bundle

router = APIRouter()


@router.post("/search", response_model=RetrievalBundle)
async def search(req: SearchRequest, db: AsyncSession = Depends(get_db)) -> RetrievalBundle:
    return await retrieve_bundle(
        session=db,
        query=req.query,
        top_k_products=req.top_k_products,
        top_k_knowledge=req.top_k_knowledge,
        max_price=req.max_price,
        exclude_out_of_stock=req.exclude_out_of_stock,
    )
