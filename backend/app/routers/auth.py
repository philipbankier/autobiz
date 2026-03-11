from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserRead, TokenResponse
from app.services.auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        name=data.name,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return {
        "data": {
            "user": UserRead.model_validate(user).model_dump(mode="json"),
            "access_token": token,
            "token_type": "bearer",
        },
        "error": None,
        "meta": None,
    }


@router.post("/login", response_model=dict)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token({"sub": str(user.id)})
    return {
        "data": {
            "user": UserRead.model_validate(user).model_dump(mode="json"),
            "access_token": token,
            "token_type": "bearer",
        },
        "error": None,
        "meta": None,
    }


@router.get("/me", response_model=dict)
async def me(current_user: User = Depends(get_current_user)):
    return {
        "data": UserRead.model_validate(current_user).model_dump(mode="json"),
        "error": None,
        "meta": None,
    }
