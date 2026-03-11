from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.services.billing import get_balance, get_usage

router = APIRouter(prefix="/api/billing", tags=["billing"])


@router.get("/balance", response_model=dict)
async def balance(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    credits = await get_balance(db, current_user.id)
    return {
        "data": {"credits_balance": str(credits)},
        "error": None,
        "meta": None,
    }


@router.get("/usage", response_model=dict)
async def usage(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    usage_data = await get_usage(db, current_user.id, days=days)
    return {
        "data": {
            "items": [
                {
                    "type": item["type"].value if hasattr(item["type"], "value") else item["type"],
                    "total_amount": str(item["total_amount"]),
                    "event_count": item["event_count"],
                }
                for item in usage_data["items"]
            ],
            "total_spent": str(usage_data["total_spent"]),
            "period_start": usage_data["period_start"].isoformat(),
            "period_end": usage_data["period_end"].isoformat(),
        },
        "error": None,
        "meta": None,
    }
