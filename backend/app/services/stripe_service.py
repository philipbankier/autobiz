"""
Stripe integration service.
Handles both AutoBiz platform billing (credit purchases) and
generated business payments (Stripe Connect for company products).
"""
import logging
from decimal import Decimal
from typing import Optional
from uuid import uuid4

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User
from app.models.company import Company
from app.models.cost_event import CostEvent, CostType

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY if hasattr(settings, 'STRIPE_SECRET_KEY') else None


# ============================================================
# AutoBiz Platform Billing (credit purchases)
# ============================================================

async def create_checkout_session(
    user: User,
    amount_dollars: float,
    success_url: str = "http://localhost:3000/dashboard?credits=success",
    cancel_url: str = "http://localhost:3000/dashboard?credits=cancel",
) -> dict:
    """Create a Stripe checkout session for credit purchase."""
    if not stripe.api_key:
        # Dev mode: just add credits directly
        return {
            "mode": "dev",
            "message": f"Dev mode: would charge ${amount_dollars} for credits",
            "credits_to_add": amount_dollars,
        }

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"AutoBiz Credits (${amount_dollars})",
                        "description": f"Add ${amount_dollars} in credits to your AutoBiz account",
                    },
                    "unit_amount": int(amount_dollars * 100),
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "user_id": str(user.id),
                "credits_amount": str(amount_dollars),
            },
        )
        return {
            "checkout_url": session.url,
            "session_id": session.id,
        }
    except Exception as e:
        logger.error(f"Stripe checkout error: {e}")
        return {"error": str(e)}


async def add_credits(db: AsyncSession, user_id: str, amount: float, source: str = "purchase") -> Decimal:
    """Add credits to a user account."""
    user = await db.get(User, user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")

    credit_amount = Decimal(str(amount))
    user.credits_balance += credit_amount

    await db.flush()
    logger.info(f"Added ${amount} credits to user {user_id}. New balance: ${user.credits_balance}")
    return user.credits_balance


async def deduct_credits(db: AsyncSession, user_id: str, amount: float, description: str = "") -> Decimal:
    """Deduct credits from a user account."""
    user = await db.get(User, user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")

    deduct_amount = Decimal(str(amount))
    user.credits_balance = max(Decimal("0"), user.credits_balance - deduct_amount)

    await db.flush()
    return user.credits_balance


# ============================================================
# Generated Business Payments (Stripe Connect)
# ============================================================

async def create_payment_link(
    company: Company,
    product_name: str,
    price_cents: int,
    description: str = "",
) -> dict:
    """Create a Stripe payment link for a generated business product."""
    if not stripe.api_key:
        # Dev mode: return a mock payment link
        return {
            "mode": "dev",
            "url": f"https://buy.stripe.com/mock_{company.slug}_{price_cents}",
            "product_name": product_name,
            "price": price_cents / 100,
        }

    try:
        product = stripe.Product.create(
            name=product_name,
            description=description,
            metadata={"company_id": str(company.id), "company_slug": company.slug},
        )

        price = stripe.Price.create(
            product=product.id,
            unit_amount=price_cents,
            currency="usd",
            recurring={"interval": "month"} if price_cents > 0 else None,
        )

        link = stripe.PaymentLink.create(
            line_items=[{"price": price.id, "quantity": 1}],
            metadata={"company_id": str(company.id)},
        )

        return {
            "url": link.url,
            "product_id": product.id,
            "price_id": price.id,
            "link_id": link.id,
        }
    except Exception as e:
        logger.error(f"Stripe payment link error: {e}")
        return {"error": str(e)}


# ============================================================
# Revenue Tracking
# ============================================================

async def get_revenue_summary(db: AsyncSession, company_id: str) -> dict:
    """Get revenue summary for a company. Phase 3: from cost_events table."""
    # For now, aggregate from cost_events (revenue events stored as negative costs)
    from sqlalchemy import func

    # Total costs
    result = await db.execute(
        select(func.coalesce(func.sum(CostEvent.amount), 0)).where(
            CostEvent.company_id == company_id,
            CostEvent.type == CostType.llm_tokens,
        )
    )
    total_agent_cost = float(result.scalar())

    result = await db.execute(
        select(func.coalesce(func.sum(CostEvent.amount), 0)).where(
            CostEvent.company_id == company_id,
            CostEvent.type == CostType.api_call,
        )
    )
    total_api_cost = float(result.scalar())

    return {
        "total_revenue": 0.0,  # TODO: connect Stripe webhooks
        "total_agent_cost": total_agent_cost,
        "total_api_cost": total_api_cost,
        "total_cost": total_agent_cost + total_api_cost,
        "profit": 0.0 - total_agent_cost - total_api_cost,
        "mrr": 0.0,
        "customers": 0,
    }
