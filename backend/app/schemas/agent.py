import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.agent_run import RunTrigger, RunStatus
from app.models.agent_task import TaskStatus, TaskPriority, TaskCreator
from app.models.agent_message import MessageRole
from app.models.department import DepartmentType


class AgentRunRead(BaseModel):
    id: uuid.UUID
    department_id: uuid.UUID
    company_id: uuid.UUID
    trigger: RunTrigger
    status: RunStatus
    started_at: datetime | None
    completed_at: datetime | None
    tokens_used: int
    cost: Decimal
    summary: str | None

    model_config = {"from_attributes": True}


class AgentMessageCreate(BaseModel):
    department_type: DepartmentType
    content: str = Field(..., max_length=10000)


class AgentMessageRead(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    department_id: uuid.UUID
    role: MessageRole
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentTaskCreate(BaseModel):
    title: str = Field(..., max_length=500)
    description: str | None = None
    priority: TaskPriority = TaskPriority.medium
    assigned_department: DepartmentType | None = None


class AgentTaskRead(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    department_id: uuid.UUID | None
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    created_by: TaskCreator
    assigned_department: DepartmentType | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}
