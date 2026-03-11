import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select, func as sqlfunc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cost_event import CostEvent, CostType
from app.models.user import User


async def get_balance(db: AsyncSession, user_id: uuid.UUID) -> Decimal:
    user = await db.get(User, user_id)
    if user is None:
        return Decimal("0")
    return user.credits_balance


async def get_usage(
    db: AsyncSession,
    user_id: uuid.UUID,
    company_id: uuid.UUID | None = None,
    days: int = 30,
) -> dict:
    period_end = datetime.now(timezone.utc)
    period_start = period_end - timedelta(days=days)

    query = (
        select(
            CostEvent.type,
            sqlfunc.sum(CostEvent.amount).label("total_amount"),
            sqlfunc.count(CostEvent.id).label("event_count"),
        )
        .where(CostEvent.created_at >= period_start)
        .group_by(CostEvent.type)
    )

    if company_id:
        query = query.where(CostEvent.company_id == company_id)

    result = await db.execute(query)
    rows = result.all()

    items = []
    total_spent = Decimal("0")
    for row in rows:
        items.append({
            "type": row.type,
            "total_amount": row.total_amount or Decimal("0"),
            "event_count": row.event_count,
        })
        total_spent += row.total_amount or Decimal("0")

    return {
        "items": items,
        "total_spent": total_spent,
        "period_start": period_start,
        "period_end": period_end,
    }


async def deduct_credits(db: AsyncSession, user_id: uuid.UUID, amount: Decimal) -> Decimal:
    user = await db.get(User, user_id)
    if user is None:
        raise ValueError("User not found")
    if user.credits_balance < amount:
        raise ValueError("Insufficient credits")
    user.credits_balance -= amount
    await db.flush()
    return user.credits_balance
