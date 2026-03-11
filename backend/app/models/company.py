import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Enum, JSON, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CompanyStatus(str, enum.Enum):
    planning = "planning"
    building = "building"
    running = "running"
    paused = "paused"
    archived = "archived"


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    mission: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    status: Mapped[CompanyStatus] = mapped_column(Enum(CompanyStatus), nullable=False, default=CompanyStatus.planning)
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="companies", lazy="selectin")  # noqa: F821
    departments: Mapped[list["Department"]] = relationship("Department", back_populates="company", lazy="selectin")  # noqa: F821
    agent_runs: Mapped[list["AgentRun"]] = relationship("AgentRun", back_populates="company", lazy="noload")  # noqa: F821
    tasks: Mapped[list["AgentTask"]] = relationship("AgentTask", back_populates="company", lazy="noload")  # noqa: F821
    messages: Mapped[list["AgentMessage"]] = relationship("AgentMessage", back_populates="company", lazy="noload")  # noqa: F821
    cost_events: Mapped[list["CostEvent"]] = relationship("CostEvent", back_populates="company", lazy="noload")  # noqa: F821
