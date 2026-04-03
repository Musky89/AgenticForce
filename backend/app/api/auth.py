from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import User
from app.services.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class SetupRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: str
    email: str
    is_active: bool

    model_config = {"from_attributes": True}


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account deactivated")

    token = create_access_token(data={"sub": user.id})
    return TokenResponse(access_token=token)


@router.post("/setup", response_model=TokenResponse, status_code=201)
async def setup(payload: SetupRequest, db: AsyncSession = Depends(get_db)):
    count_result = await db.execute(select(func.count()).select_from(User))
    if count_result.scalar() > 0:
        raise HTTPException(status_code=400, detail="Setup already completed. Use /api/auth/login.")

    user = User(email=payload.email, hashed_password=hash_password(payload.password))
    db.add(user)
    await db.flush()
    await db.refresh(user)

    token = create_access_token(data={"sub": user.id})
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
