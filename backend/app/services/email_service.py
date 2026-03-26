"""
Email service using Resend API.
Supports transactional and marketing emails with rate limiting.
"""
import json
import logging
import time
from pathlib import Path

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

import os as _os_; COMPANIES_DIR = Path(_os_.environ.get("COMPANIES_DIR", "/app/companies"))

RESEND_API_URL = "https://api.resend.com"
MAX_EMAILS_PER_DAY = 100
MAX_BULK_PER_CALL = 10

# In-memory rate limiting: {company_slug: [timestamps]}
_email_rate_limits: dict[str, list[float]] = {}


def _get_resend_key(slug: str) -> str | None:
    """Get Resend API key — company .env first, then global settings."""
    # Check company .env
    env_file = COMPANIES_DIR / slug / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line.startswith("RESEND_API_KEY="):
                val = line.partition("=")[2].strip()
                if val:
                    return val
    # Fall back to global
    return settings.RESEND_API_KEY or None


def _check_email_rate_limit(slug: str, count: int = 1) -> bool:
    """Check if company is within daily email rate limit."""
    now = time.time()
    day_ago = now - 86400

    if slug not in _email_rate_limits:
        _email_rate_limits[slug] = []

    # Prune old entries
    _email_rate_limits[slug] = [ts for ts in _email_rate_limits[slug] if ts > day_ago]

    return (len(_email_rate_limits[slug]) + count) <= MAX_EMAILS_PER_DAY


def _record_email_sends(slug: str, count: int = 1):
    """Record email sends for rate limiting."""
    now = time.time()
    if slug not in _email_rate_limits:
        _email_rate_limits[slug] = []
    _email_rate_limits[slug].extend([now] * count)


async def send_email(
    company_slug: str,
    to: str | list[str],
    subject: str,
    html_body: str,
    text_body: str | None = None,
) -> dict:
    """Send a single email via Resend API."""
    api_key = _get_resend_key(company_slug)
    if not api_key:
        return {
            "status": "error",
            "message": "Resend API key not configured. Set RESEND_API_KEY in .env or company .env",
        }

    if not _check_email_rate_limit(company_slug):
        return {
            "status": "error",
            "message": f"Rate limit reached: max {MAX_EMAILS_PER_DAY} emails per day",
        }

    to_list = [to] if isinstance(to, str) else to
    from_addr = f"{company_slug}@{settings.SITE_BASE_DOMAIN}"

    payload = {
        "from": from_addr,
        "to": to_list,
        "subject": subject,
        "html": html_body,
    }
    if text_body:
        payload["text"] = text_body

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{RESEND_API_URL}/emails",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=30.0,
            )

            if response.status_code in (200, 201):
                data = response.json()
                _record_email_sends(company_slug)
                email_id = data.get("id", "")
                logger.info(f"[{company_slug}] Email sent to {to_list}: {email_id}")
                return {
                    "status": "ok",
                    "email_id": email_id,
                    "to": to_list,
                    "subject": subject,
                }
            else:
                error_body = response.text
                logger.error(f"[{company_slug}] Resend API error {response.status_code}: {error_body}")
                return {
                    "status": "error",
                    "message": f"Resend API {response.status_code}: {error_body}",
                }

    except Exception as e:
        logger.error(f"[{company_slug}] Email send failed: {e}")
        return {"status": "error", "message": str(e)}


async def send_bulk_emails(
    company_slug: str,
    recipients: list[dict],
    subject: str,
    html_body: str,
) -> dict:
    """
    Send emails to multiple recipients.
    Each recipient dict: {"email": "...", "name": "..."} (name optional).
    Max 10 per call.
    """
    api_key = _get_resend_key(company_slug)
    if not api_key:
        return {
            "status": "error",
            "message": "Resend API key not configured",
        }

    if len(recipients) > MAX_BULK_PER_CALL:
        return {
            "status": "error",
            "message": f"Max {MAX_BULK_PER_CALL} recipients per call (got {len(recipients)})",
        }

    if not _check_email_rate_limit(company_slug, len(recipients)):
        return {
            "status": "error",
            "message": f"Rate limit: sending {len(recipients)} would exceed {MAX_EMAILS_PER_DAY}/day limit",
        }

    from_addr = f"{company_slug}@{settings.SITE_BASE_DOMAIN}"
    results = []
    errors = []

    async with httpx.AsyncClient() as client:
        for recipient in recipients:
            email = recipient.get("email")
            if not email:
                errors.append({"recipient": recipient, "error": "Missing email"})
                continue

            name = recipient.get("name", "")
            to_addr = f"{name} <{email}>" if name else email

            payload = {
                "from": from_addr,
                "to": [to_addr],
                "subject": subject,
                "html": html_body,
            }

            try:
                response = await client.post(
                    f"{RESEND_API_URL}/emails",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=30.0,
                )

                if response.status_code in (200, 201):
                    data = response.json()
                    _record_email_sends(company_slug)
                    results.append({"email": email, "id": data.get("id"), "status": "sent"})
                else:
                    errors.append({"email": email, "error": response.text})

            except Exception as e:
                errors.append({"email": email, "error": str(e)})

    sent_count = len(results)
    logger.info(f"[{company_slug}] Bulk email: {sent_count} sent, {len(errors)} failed")

    return {
        "status": "ok" if sent_count > 0 else "error",
        "sent": sent_count,
        "failed": len(errors),
        "results": results,
        "errors": errors,
    }


async def get_send_history(company_slug: str, limit: int = 20) -> list:
    """Get recent email send history from Resend API."""
    api_key = _get_resend_key(company_slug)
    if not api_key:
        return []

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{RESEND_API_URL}/emails",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=15.0,
            )

            if response.status_code == 200:
                data = response.json()
                emails = data.get("data", [])
                return emails[:limit]
            else:
                logger.error(f"[{company_slug}] Resend history failed: {response.status_code}")
                return []

    except Exception as e:
        logger.error(f"[{company_slug}] Resend history error: {e}")
        return []


def get_email_status(company_slug: str) -> dict:
    """Check if email is configured for a company."""
    return {
        "configured": _get_resend_key(company_slug) is not None,
        "from_address": f"{company_slug}@{settings.SITE_BASE_DOMAIN}",
    }
