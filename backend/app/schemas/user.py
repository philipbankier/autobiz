import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    name: str = Field(..., max_length=255)


class UserLogin(BaseModel):
    email: str
    password: str


class UserRead(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    credits_balance: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
