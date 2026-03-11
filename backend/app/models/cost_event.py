import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Enum, Numeric, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CostType(str, enum.Enum):
    llm_tokens = "llm_tokens"
    api_call = "api_call"
    deployment = "deployment"


class CostEvent(Base):
    __tablename__ = "cost_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    department_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True, index=True)
    type: Mapped[CostType] = mapped_column(Enum(CostType), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 6), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    company: Mapped["Company"] = relationship("Company", back_populates="cost_events", lazy="selectin")  # noqa: F821
    department: Mapped["Department | None"] = relationship("Department", back_populates="cost_events", lazy="selectin")  # noqa: F821
