"""
Cost control service.
Enforces per-department budget caps, tracks spending, and provides circuit breakers.
"""
import logging
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cost_event import CostEvent, CostType
from app.models.department import Department

logger = logging.getLogger(__name__)

# Model pricing (per 1M tokens, as of March 2026)
MODEL_PRICING = {
    "claude-opus-4-6": {"input": 15.0, "output": 75.0},
    "anthropic/claude-opus-4-6": {"input": 15.0, "output": 75.0},
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0},
    "anthropic/claude-sonnet-4-6": {"input": 3.0, "output": 15.0},
    "claude-haiku-3.5": {"input": 0.25, "output": 1.25},
    "anthropic/claude-haiku-3.5": {"input": 0.25, "output": 1.25},
}

# Default daily budget per department type (in USD)
DEFAULT_BUDGETS = {
    "ceo": Decimal("5.00"),       # Opus — expensive but strategic
    "developer": Decimal("10.00"),  # Sonnet — lots of code generation
    "marketing": Decimal("5.00"),   # Sonnet — content creation
    "sales": Decimal("3.00"),
    "finance": Decimal("2.00"),     # Sonnet — analysis
    "support": Decimal("2.00"),
}

# Model tier per department
DEPARTMENT_MODELS = {
    "ceo": "anthropic/claude-opus-4-6",
    "developer": "anthropic/claude-sonnet-4-6",
    "marketing": "anthropic/claude-sonnet-4-6",
    "sales": "anthropic/claude-sonnet-4-6",
    "finance": "anthropic/claude-sonnet-4-6",
    "support": "anthropic/claude-sonnet-4-6",
}

# Cheap model for validation/judging
JUDGE_MODEL = "anthropic/claude-haiku-3.5"


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> Decimal:
    """Estimate cost for a model run."""
    pricing = MODEL_PRICING.get(model, MODEL_PRICING.get("claude-sonnet-4-6"))
    input_cost = Decimal(str(input_tokens)) * Decimal(str(pricing["input"])) / Decimal("1000000")
    output_cost = Decimal(str(output_tokens)) * Decimal(str(pricing["output"])) / Decimal("1000000")
    return input_cost + output_cost


def get_model_for_department(department_type: str) -> str:
    """Get the appropriate model tier for a department."""
    return DEPARTMENT_MODELS.get(department_type, "anthropic/claude-sonnet-4-6")


async def get_daily_spend(
    db: AsyncSession,
    department_id: uuid.UUID,
    date: datetime | None = None,
) -> Decimal:
    """Get total spend for a department today."""
    if date is None:
        date = datetime.now(timezone.utc)

    start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    result = await db.execute(
        select(func.coalesce(func.sum(CostEvent.amount), 0))
        .where(
            CostEvent.department_id == department_id,
            CostEvent.created_at >= start_of_day,
            CostEvent.created_at < end_of_day,
        )
    )
    return Decimal(str(result.scalar()))


async def check_budget(
    db: AsyncSession,
    department: Department,
) -> dict:
    """
    Check if a department has budget remaining.
    Returns {allowed: bool, spend: Decimal, budget: Decimal, pct: float, warning: str|None}
    """
    budget = department.budget_cap_daily or DEFAULT_BUDGETS.get(
        department.type.value, Decimal("5.00")
    )
    spend = await get_daily_spend(db, department.id)
    pct = float(spend / budget * 100) if budget > 0 else 0

    warning = None
    if pct >= 100:
        warning = f"BUDGET EXCEEDED: ${spend:.2f}/${budget:.2f} ({pct:.0f}%)"
        logger.warning(f"[{department.type.value}] {warning}")
        return {"allowed": False, "spend": spend, "budget": budget, "pct": pct, "warning": warning}

    if pct >= 80:
        warning = f"Budget warning: ${spend:.2f}/${budget:.2f} ({pct:.0f}%)"
        logger.info(f"[{department.type.value}] {warning}")

    return {"allowed": True, "spend": spend, "budget": budget, "pct": pct, "warning": warning}


async def record_cost(
    db: AsyncSession,
    company_id: uuid.UUID,
    department_id: uuid.UUID,
    cost_type: CostType,
    amount: Decimal,
    description: str = "",
) -> CostEvent:
    """Record a cost event."""
    event = CostEvent(
        company_id=company_id,
        department_id=department_id,
        type=cost_type,
        amount=amount,
        description=description,
    )
    db.add(event)
    await db.flush()
    return event


async def get_company_daily_spend(
    db: AsyncSession,
    company_id: uuid.UUID,
    date: datetime | None = None,
) -> dict:
    """Get spend breakdown by department for a company today."""
    if date is None:
        date = datetime.now(timezone.utc)

    start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    result = await db.execute(
        select(
            CostEvent.department_id,
            func.sum(CostEvent.amount).label("total"),
        )
        .where(
            CostEvent.company_id == company_id,
            CostEvent.created_at >= start_of_day,
            CostEvent.created_at < end_of_day,
        )
        .group_by(CostEvent.department_id)
    )

    breakdown = {}
    total = Decimal("0")
    for row in result:
        dept_id = str(row.department_id) if row.department_id else "platform"
        breakdown[dept_id] = Decimal(str(row.total))
        total += Decimal(str(row.total))

    return {"total": total, "breakdown": breakdown, "date": start_of_day.isoformat()}
