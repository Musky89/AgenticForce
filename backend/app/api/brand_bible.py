from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import BrandBible, Client
from app.schemas.schemas import BrandBibleCreate, BrandBibleUpdate, BrandBibleOut

router = APIRouter(prefix="/brand-bibles", tags=["brand-bible"])


@router.post("", response_model=BrandBibleOut, status_code=201)
async def create_brand_bible(payload: BrandBibleCreate, db: AsyncSession = Depends(get_db)):
    client = await db.get(Client, payload.client_id)
    if not client:
        raise HTTPException(404, "Client not found")

    existing = await db.execute(select(BrandBible).where(BrandBible.client_id == payload.client_id))
    if existing.scalar_one_or_none():
        raise HTTPException(409, "Brand Bible already exists for this client. Use PATCH to update.")

    bible = BrandBible(**payload.model_dump())
    db.add(bible)
    await db.flush()
    await db.refresh(bible)
    return bible


@router.get("/client/{client_id}", response_model=BrandBibleOut)
async def get_by_client(client_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BrandBible).where(BrandBible.client_id == client_id))
    bible = result.scalar_one_or_none()
    if not bible:
        raise HTTPException(404, "No Brand Bible found for this client")
    return bible


@router.patch("/{bible_id}", response_model=BrandBibleOut)
async def update_brand_bible(bible_id: str, payload: BrandBibleUpdate, db: AsyncSession = Depends(get_db)):
    bible = await db.get(BrandBible, bible_id)
    if not bible:
        raise HTTPException(404, "Brand Bible not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        if k != "client_id":
            setattr(bible, k, v)
    bible.version += 1
    await db.flush()
    await db.refresh(bible)
    return bible
