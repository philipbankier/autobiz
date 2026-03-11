import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Enum, Numeric, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DepartmentType(str, enum.Enum):
    ceo = "ceo"
    developer = "developer"
    marketing = "marketing"
    sales = "sales"
    finance = "finance"
    support = "support"


class AutonomyLevel(str, enum.Enum):
    full_auto = "full_auto"
    notify = "notify"
    approve = "approve"
    manual = "manual"


class DepartmentStatus(str, enum.Enum):
    idle = "idle"
    running = "running"
    waiting = "waiting"


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    type: Mapped[DepartmentType] = mapped_column(Enum(DepartmentType), nullable=False)
    autonomy_level: Mapped[AutonomyLevel] = mapped_column(Enum(AutonomyLevel), nullable=False, default=AutonomyLevel.notify)
    budget_cap_daily: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    status: Mapped[DepartmentStatus] = mapped_column(Enum(DepartmentStatus), nullable=False, default=DepartmentStatus.idle)
    agent_session_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    company: Mapped["Company"] = relationship("Company", back_populates="departments", lazy="selectin")  # noqa: F821
    agent_runs: Mapped[list["AgentRun"]] = relationship("AgentRun", back_populates="department", lazy="noload")  # noqa: F821
    tasks: Mapped[list["AgentTask"]] = relationship("AgentTask", back_populates="department", lazy="noload")  # noqa: F821
    messages: Mapped[list["AgentMessage"]] = relationship("AgentMessage", back_populates="department", lazy="noload")  # noqa: F821
    cost_events: Mapped[list["CostEvent"]] = relationship("CostEvent", back_populates="department", lazy="noload")  # noqa: F821
