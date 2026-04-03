from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import Deliverable
from app.schemas.schemas import DeliverableCreate, DeliverableUpdate, DeliverableOut

router = APIRouter(prefix="/deliverables", tags=["deliverables"])


@router.get("", response_model=list[DeliverableOut])
async def list_deliverables(
    project_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Deliverable).order_by(Deliverable.created_at.desc())
    if project_id:
        query = query.where(Deliverable.project_id == project_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=DeliverableOut, status_code=201)
async def create_deliverable(payload: DeliverableCreate, db: AsyncSession = Depends(get_db)):
    deliverable = Deliverable(**payload.model_dump())
    db.add(deliverable)
    await db.flush()
    await db.refresh(deliverable)
    return deliverable


@router.get("/{deliverable_id}", response_model=DeliverableOut)
async def get_deliverable(deliverable_id: str, db: AsyncSession = Depends(get_db)):
    deliverable = await db.get(Deliverable, deliverable_id)
    if not deliverable:
        raise HTTPException(404, "Deliverable not found")
    return deliverable


@router.patch("/{deliverable_id}", response_model=DeliverableOut)
async def update_deliverable(
    deliverable_id: str,
    payload: DeliverableUpdate,
    db: AsyncSession = Depends(get_db),
):
    deliverable = await db.get(Deliverable, deliverable_id)
    if not deliverable:
        raise HTTPException(404, "Deliverable not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(deliverable, k, v)
    await db.flush()
    await db.refresh(deliverable)
    return deliverable


@router.delete("/{deliverable_id}", status_code=204)
async def delete_deliverable(deliverable_id: str, db: AsyncSession = Depends(get_db)):
    deliverable = await db.get(Deliverable, deliverable_id)
    if not deliverable:
        raise HTTPException(404, "Deliverable not found")
    await db.delete(deliverable)
    await db.flush()
