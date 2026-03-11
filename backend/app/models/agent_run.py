import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Enum, Integer, Numeric, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RunTrigger(str, enum.Enum):
    scheduled = "scheduled"
    manual = "manual"
    chat = "chat"


class RunStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    department_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False, index=True)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    trigger: Mapped[RunTrigger] = mapped_column(Enum(RunTrigger), nullable=False)
    status: Mapped[RunStatus] = mapped_column(Enum(RunStatus), nullable=False, default=RunStatus.pending)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost: Mapped[Decimal] = mapped_column(Numeric(12, 6), nullable=False, default=Decimal("0"))
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    department: Mapped["Department"] = relationship("Department", back_populates="agent_runs", lazy="selectin")  # noqa: F821
    company: Mapped["Company"] = relationship("Company", back_populates="agent_runs", lazy="selectin")  # noqa: F821
