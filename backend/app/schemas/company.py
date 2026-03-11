import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.company import CompanyStatus


class CompanyCreate(BaseModel):
    name: str = Field(..., max_length=255)
    mission: str | None = Field(None, max_length=1000)
    slug: str = Field(..., max_length=100, pattern=r"^[a-z0-9][a-z0-9-]*[a-z0-9]$")


class CompanyUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    mission: str | None = Field(None, max_length=1000)
    status: CompanyStatus | None = None
    config: dict[str, Any] | None = None


class CompanyRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    mission: str | None
    slug: str
    status: CompanyStatus
    config: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
