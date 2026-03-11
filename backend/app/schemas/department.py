import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.department import DepartmentType, AutonomyLevel, DepartmentStatus


class DepartmentRead(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    type: DepartmentType
    autonomy_level: AutonomyLevel
    budget_cap_daily: Decimal | None
    status: DepartmentStatus
    agent_session_id: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DepartmentUpdate(BaseModel):
    autonomy_level: AutonomyLevel | None = None
    budget_cap_daily: Decimal | None = None
