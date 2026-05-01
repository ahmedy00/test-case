from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.product import Product
from app.products import ProductCreate, ProductRead

router = APIRouter()


@router.get("/products", response_model=list[ProductRead])
async def list_products(db: AsyncSession = Depends(get_db)) -> list[Product]:
    result = await db.execute(select(Product).order_by(Product.id))
    return list(result.scalars().all())


@router.post(
    "/products",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_product(
    payload: ProductCreate, db: AsyncSession = Depends(get_db)
) -> Product:
    product = Product(
        sku=payload.sku,
        name=payload.name,
        description=payload.description,
        category=payload.category,
        price=payload.price,
        currency=payload.currency,
        stock=payload.stock,
    )
    db.add(product)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Product with sku '{payload.sku}' already exists.",
        ) from exc
    await db.refresh(product)
    return product
