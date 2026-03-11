import uuid

from fastapi import APIRouter, Depends, Query, Request, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.services.billing import get_balance, get_usage
from app.services.stripe_service import create_checkout_session, add_credits

router = APIRouter(prefix="/api/billing", tags=["billing"])


class PurchaseCreditsRequest(BaseModel):
    amount: float  # Dollar amount


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


@router.post("/purchase", response_model=dict)
async def purchase_credits(
    data: PurchaseCreditsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Purchase credits. In dev mode, adds credits directly."""
    if data.amount < 1 or data.amount > 500:
        raise HTTPException(status_code=400, detail="Amount must be between $1 and $500")

    result = await create_checkout_session(current_user, data.amount)

    if result.get("mode") == "dev":
        # Dev mode: add credits directly
        new_balance = await add_credits(db, str(current_user.id), data.amount, source="dev_purchase")
        await db.commit()
        return {
            "data": {
                "mode": "dev",
                "credits_added": data.amount,
                "new_balance": str(new_balance),
            },
            "error": None,
            "meta": None,
        }

    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])

    return {
        "data": {
            "checkout_url": result["checkout_url"],
            "session_id": result["session_id"],
        },
        "error": None,
        "meta": None,
    }


@router.post("/webhook", response_model=dict)
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle Stripe webhook events (payment completed, etc.)."""
    import stripe
    from app.config import settings

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if settings.STRIPE_WEBHOOK_SECRET and sig_header:
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        # Dev mode: parse raw JSON
        import json
        event = json.loads(payload)

    event_type = event.get("type", "")

    if event_type == "checkout.session.completed":
        session = event.get("data", {}).get("object", {})
        metadata = session.get("metadata", {})
        user_id = metadata.get("user_id")
        credits_amount = float(metadata.get("credits_amount", 0))

        if user_id and credits_amount > 0:
            await add_credits(db, user_id, credits_amount, source="stripe_checkout")
            await db.commit()

    return {"data": {"received": True}, "error": None, "meta": None}
