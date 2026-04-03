from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import LoRAModel, Client
from app.schemas.schemas import LoRAModelCreate, LoRAModelOut

router = APIRouter(prefix="/lora", tags=["lora"])


@router.get("/client/{client_id}", response_model=list[LoRAModelOut])
async def list_client_loras(client_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(LoRAModel).where(LoRAModel.client_id == client_id).order_by(LoRAModel.version.desc())
    )
    return result.scalars().all()


@router.post("", response_model=LoRAModelOut, status_code=201)
async def create_lora(payload: LoRAModelCreate, db: AsyncSession = Depends(get_db)):
    client = await db.get(Client, payload.client_id)
    if not client:
        raise HTTPException(404, "Client not found")

    lora = LoRAModel(**payload.model_dump())
    db.add(lora)
    await db.flush()
    await db.refresh(lora)
    return lora


@router.get("/{lora_id}", response_model=LoRAModelOut)
async def get_lora(lora_id: str, db: AsyncSession = Depends(get_db)):
    lora = await db.get(LoRAModel, lora_id)
    if not lora:
        raise HTTPException(404, "LoRA model not found")
    return lora


@router.patch("/{lora_id}", response_model=LoRAModelOut)
async def update_lora(lora_id: str, data: dict, db: AsyncSession = Depends(get_db)):
    lora = await db.get(LoRAModel, lora_id)
    if not lora:
        raise HTTPException(404, "LoRA model not found")
    for k, v in data.items():
        if hasattr(lora, k):
            setattr(lora, k, v)
    await db.flush()
    await db.refresh(lora)
    return lora
