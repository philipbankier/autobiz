"""
Webhook endpoints for event-driven agent triggers.
These are called by external services (Stripe, Vercel, GitHub)
and route events to the appropriate department agent.
"""
import hashlib
import hmac
import json
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models.company import Company
from app.config import settings
from app.services.scheduler import (
    handle_stripe_webhook,
    handle_deploy_webhook,
    handle_github_webhook,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


async def _find_company_by_slug(slug: str) -> Optional[Company]:
    """Find company by slug using async session."""
    async with async_session() as db:
        result = await db.execute(select(Company).where(Company.slug == slug))
        return result.scalar_one_or_none()


async def _find_company_by_stripe_account(account_id: str) -> Optional[dict]:
    """Find company by Stripe Connect account ID from .env file."""
    from pathlib import Path
    import os as _osx; companies_dir = Path(_osx.environ.get("COMPANIES_DIR", "/app/companies"))
    
    for company_dir in companies_dir.iterdir():
        if not company_dir.is_dir():
            continue
        env_file = company_dir / ".env"
        if env_file.exists():
            content = env_file.read_text()
            if account_id in content:
                return {"slug": company_dir.name}
    return None


@router.post("/stripe")
async def stripe_webhook(request: Request):
    """
    Stripe webhook — handles payment events for company Stripe Connect accounts.
    Route: POST /webhooks/stripe
    """
    body = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    # Verify webhook signature if secret is configured
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET
    if webhook_secret and sig_header:
        try:
            import stripe
            event = stripe.Webhook.construct_event(body, sig_header, webhook_secret)
        except Exception as e:
            logger.warning(f"Stripe webhook signature verification failed: {e}")
            raise HTTPException(status_code=400, detail="Invalid signature")
    else:
        try:
            event = json.loads(body)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON")

    event_type = event.get("type", "")
    account = event.get("account", "")  # Connect account ID
    data = event.get("data", {}).get("object", {})

    logger.info(f"Stripe webhook: {event_type} for account {account}")

    # Find company by Stripe account
    company_info = await _find_company_by_stripe_account(account) if account else None

    if not company_info:
        # Log but don't fail — might be a platform-level event
        logger.info(f"Stripe event {event_type} — no matching company for account {account}")
        return {"status": "ok", "matched": False}

    # Resolve slug to actual company record for the ID
    company = await _find_company_by_slug(company_info["slug"])
    if not company:
        logger.info(f"Stripe event {event_type} — slug '{company_info['slug']}' not in DB")
        return {"status": "ok", "matched": False}

    # Only trigger agents for meaningful events
    actionable_events = {
        "payment_intent.succeeded",
        "invoice.paid",
        "customer.subscription.created",
        "customer.subscription.deleted",
        "charge.succeeded",
        "charge.refunded",
    }

    if event_type in actionable_events:
        result = await handle_stripe_webhook(
            company_id=str(company.id),
            event_type=event_type,
            event_data={"amount": data.get("amount"), "currency": data.get("currency"), "customer": data.get("customer")},
        )
        return {"status": "ok", "triggered": True, **result}

    return {"status": "ok", "triggered": False, "event_type": event_type}


@router.post("/vercel")
async def vercel_webhook(request: Request):
    """
    Vercel deploy webhook — triggers developer agent on deploy events.
    Route: POST /webhooks/vercel
    """
    body = await request.json()

    # Vercel sends deployment events
    deploy_type = body.get("type", "")
    payload = body.get("payload", {})
    project_name = payload.get("name", "")
    
    # Extract company slug from project name (autobiz-{slug})
    slug = ""
    if project_name.startswith("autobiz-"):
        slug = project_name[len("autobiz-"):]

    if not slug:
        return {"status": "ok", "matched": False}

    logger.info(f"Vercel webhook: {deploy_type} for {project_name}")

    # Look up company by slug
    company = await _find_company_by_slug(slug)
    if not company:
        logger.info(f"Vercel webhook: no company found for slug '{slug}'")
        return {"status": "ok", "matched": False}

    # Only trigger on deployment ready/error
    if deploy_type in ("deployment.created", "deployment.ready", "deployment.error"):
        deploy_data = {
            "status": "ready" if deploy_type == "deployment.ready" else "error" if deploy_type == "deployment.error" else "building",
            "url": payload.get("url", ""),
            "project": project_name,
        }
        result = await handle_deploy_webhook(
            company_id=str(company.id),
            deploy_data=deploy_data,
        )
        return {"status": "ok", "triggered": True, **result}

    return {"status": "ok", "triggered": False}


@router.post("/github")
async def github_webhook(
    request: Request,
    x_github_event: Optional[str] = Header(None),
):
    """
    GitHub webhook — triggers developer agent on PR/push/issue events.
    Route: POST /webhooks/github
    """
    body = await request.json()
    event_type = x_github_event or body.get("action", "unknown")

    # Extract repo name
    repo = body.get("repository", {}).get("name", "")
    
    # Extract company slug from repo name (autobiz-{slug})
    slug = ""
    if repo.startswith("autobiz-"):
        slug = repo[len("autobiz-"):]

    if not slug:
        return {"status": "ok", "matched": False}

    # Look up company by slug
    company = await _find_company_by_slug(slug)
    if not company:
        logger.info(f"GitHub webhook: no company found for slug '{slug}'")
        return {"status": "ok", "matched": False}

    logger.info(f"GitHub webhook: {event_type} for {repo}")

    # Only trigger for actionable events
    actionable_events = {"push", "pull_request", "issues"}
    if event_type in actionable_events:
        event_data = {
            "ref": body.get("ref", ""),
            "commits": len(body.get("commits", [])),
            "sender": body.get("sender", {}).get("login", ""),
        }
        result = await handle_github_webhook(
            company_id=str(company.id),
            event_type=event_type,
            event_data=event_data,
        )
        return {"status": "ok", "triggered": True, **result}

    return {"status": "ok", "triggered": False}
