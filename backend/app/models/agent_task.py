import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Enum, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.department import DepartmentType


class TaskStatus(str, enum.Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"
    blocked = "blocked"


class TaskPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class TaskCreator(str, enum.Enum):
    human = "human"
    agent = "agent"


class AgentTask(Base):
    __tablename__ = "agent_tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    department_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), nullable=False, default=TaskStatus.todo)
    priority: Mapped[TaskPriority] = mapped_column(Enum(TaskPriority), nullable=False, default=TaskPriority.medium)
    created_by: Mapped[TaskCreator] = mapped_column(Enum(TaskCreator), nullable=False, default=TaskCreator.human)
    assigned_department: Mapped[DepartmentType | None] = mapped_column(Enum(DepartmentType), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    company: Mapped["Company"] = relationship("Company", back_populates="tasks", lazy="selectin")  # noqa: F821
    department: Mapped["Department | None"] = relationship("Department", back_populates="tasks", lazy="selectin")  # noqa: F821
