"""
Integration endpoints for social media and email services.
"""
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.services.company import get_company


router = APIRouter(prefix="/api/companies/{company_id}/integrations", tags=["integrations"])


# ── Request schemas ──

class TweetRequest(BaseModel):
    text: str
    media_urls: list[str] | None = None


class LinkedInPostRequest(BaseModel):
    text: str
    media_urls: list[str] | None = None


class EmailRequest(BaseModel):
    to: str | list[str]
    subject: str
    html_body: str
    text_body: str | None = None


# ── Helpers ──

async def _get_owned_company(company_id: uuid.UUID, user: User, db: AsyncSession):
    company = await get_company(db, company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    if company.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your company")
    return company


# ── Twitter ──

@router.post("/twitter/post", response_model=dict)
async def twitter_post(
    company_id: uuid.UUID,
    body: TweetRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Post a tweet from the company's Twitter account."""
    company = await _get_owned_company(company_id, current_user, db)

    from app.services.social_media import post_tweet
    result = await post_tweet(company.slug, body.text, body.media_urls)

    if result["status"] == "error":
        return {"data": None, "error": result["message"], "meta": None}

    return {"data": result, "error": None, "meta": None}


@router.get("/twitter/recent", response_model=dict)
async def twitter_recent(
    company_id: uuid.UUID,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get recent tweets from the company's Twitter account."""
    company = await _get_owned_company(company_id, current_user, db)

    from app.services.social_media import get_recent_tweets
    tweets = await get_recent_tweets(company.slug, limit)

    return {"data": tweets, "error": None, "meta": {"count": len(tweets)}}


# ── LinkedIn ──

@router.post("/linkedin/post", response_model=dict)
async def linkedin_post(
    company_id: uuid.UUID,
    body: LinkedInPostRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Post to LinkedIn from the company's account."""
    company = await _get_owned_company(company_id, current_user, db)

    from app.services.social_media import post_linkedin
    result = await post_linkedin(company.slug, body.text, body.media_urls)

    if result["status"] == "error":
        return {"data": None, "error": result["message"], "meta": None}

    return {"data": result, "error": None, "meta": None}


# ── Email ──

@router.post("/email/send", response_model=dict)
async def email_send(
    company_id: uuid.UUID,
    body: EmailRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send an email via Resend."""
    company = await _get_owned_company(company_id, current_user, db)

    from app.services.email_service import send_email
    result = await send_email(
        company.slug, body.to, body.subject, body.html_body, body.text_body,
    )

    if result["status"] == "error":
        return {"data": None, "error": result["message"], "meta": None}

    return {"data": result, "error": None, "meta": None}


# ── Integration status ──

@router.get("/status", response_model=dict)
async def integration_status(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check which integrations are configured for this company."""
    company = await _get_owned_company(company_id, current_user, db)

    from app.services.social_media import get_social_media_status
    from app.services.email_service import get_email_status

    social = get_social_media_status(company.slug)
    email = get_email_status(company.slug)

    return {
        "data": {
            "twitter": {"configured": social["twitter"]},
            "linkedin": {"configured": social["linkedin"]},
            "email": {
                "configured": email["configured"],
                "from_address": email["from_address"],
            },
        },
        "error": None,
        "meta": None,
    }
