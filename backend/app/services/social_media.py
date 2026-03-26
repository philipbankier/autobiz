"""
Social media integration service.
Supports Twitter/X (API v2) and LinkedIn posting.
Uses OAuth 1.0a for Twitter user-context endpoints (manual HMAC-SHA1 signing).
"""
import hashlib
import hmac
import json
import logging
import time
import urllib.parse
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

import os as _os
COMPANIES_DIR = Path(_os.environ.get("COMPANIES_DIR", "/app/companies"))

# Twitter API v2 endpoints
TWITTER_TWEET_URL = "https://api.twitter.com/2/tweets"
TWITTER_TIMELINE_URL = "https://api.twitter.com/2/users/{user_id}/tweets"
TWITTER_ME_URL = "https://api.twitter.com/2/users/me"

# LinkedIn API
LINKEDIN_UGC_URL = "https://api.linkedin.com/v2/ugcPosts"

# In-memory rate limiting: {company_slug: {"tweets": [(timestamp, count)], ...}}
_rate_limits: dict[str, dict[str, list]] = {}

MAX_TWEETS_PER_DAY = 50
MAX_LINKEDIN_PER_DAY = 30


def _read_company_env(slug: str) -> dict[str, str]:
    """Read key=value pairs from companies/{slug}/.env."""
    env_file = COMPANIES_DIR / slug / ".env"
    env = {}
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip()
    return env


def _get_twitter_creds(slug: str) -> dict[str, str] | None:
    """Get Twitter API credentials from company .env."""
    env = _read_company_env(slug)
    required = ["TWITTER_API_KEY", "TWITTER_API_SECRET", "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_SECRET"]
    if all(env.get(k) for k in required):
        return {k: env[k] for k in required}
    return None


def _get_linkedin_creds(slug: str) -> dict[str, str] | None:
    """Get LinkedIn credentials from company .env."""
    env = _read_company_env(slug)
    if env.get("LINKEDIN_ACCESS_TOKEN") and env.get("LINKEDIN_PERSON_ID"):
        return {
            "access_token": env["LINKEDIN_ACCESS_TOKEN"],
            "person_id": env["LINKEDIN_PERSON_ID"],
        }
    return None


def _check_rate_limit(slug: str, platform: str, max_per_day: int) -> bool:
    """Check if company is within daily rate limit for a platform."""
    now = time.time()
    day_ago = now - 86400

    if slug not in _rate_limits:
        _rate_limits[slug] = {}
    if platform not in _rate_limits[slug]:
        _rate_limits[slug][platform] = []

    # Prune old entries
    _rate_limits[slug][platform] = [
        ts for ts in _rate_limits[slug][platform] if ts > day_ago
    ]

    return len(_rate_limits[slug][platform]) < max_per_day


def _record_rate_limit(slug: str, platform: str):
    """Record a rate limit event."""
    if slug not in _rate_limits:
        _rate_limits[slug] = {}
    if platform not in _rate_limits[slug]:
        _rate_limits[slug][platform] = []
    _rate_limits[slug][platform].append(time.time())


# ── OAuth 1.0a signing (manual, no external deps) ──

def _percent_encode(s: str) -> str:
    """RFC 5849 percent-encoding."""
    return urllib.parse.quote(str(s), safe="")


def _generate_oauth_signature(
    method: str,
    url: str,
    params: dict[str, str],
    consumer_secret: str,
    token_secret: str,
) -> str:
    """Generate OAuth 1.0a HMAC-SHA1 signature."""
    # Sort and encode parameters
    sorted_params = "&".join(
        f"{_percent_encode(k)}={_percent_encode(v)}"
        for k, v in sorted(params.items())
    )

    # Build signature base string
    base_string = f"{method.upper()}&{_percent_encode(url)}&{_percent_encode(sorted_params)}"

    # Build signing key
    signing_key = f"{_percent_encode(consumer_secret)}&{_percent_encode(token_secret)}"

    # HMAC-SHA1
    signature = hmac.new(
        signing_key.encode("utf-8"),
        base_string.encode("utf-8"),
        hashlib.sha1,
    ).digest()

    import base64
    return base64.b64encode(signature).decode("utf-8")


def _build_oauth_header(
    method: str,
    url: str,
    creds: dict[str, str],
    body_params: dict | None = None,
) -> str:
    """Build OAuth 1.0a Authorization header for Twitter API."""
    oauth_params = {
        "oauth_consumer_key": creds["TWITTER_API_KEY"],
        "oauth_nonce": uuid.uuid4().hex,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": creds["TWITTER_ACCESS_TOKEN"],
        "oauth_version": "1.0",
    }

    # Combine oauth params with any body params for signing
    all_params = {**oauth_params}
    if body_params:
        all_params.update(body_params)

    signature = _generate_oauth_signature(
        method=method,
        url=url,
        params=all_params,
        consumer_secret=creds["TWITTER_API_SECRET"],
        token_secret=creds["TWITTER_ACCESS_SECRET"],
    )
    oauth_params["oauth_signature"] = signature

    # Build header string
    header_parts = ", ".join(
        f'{_percent_encode(k)}="{_percent_encode(v)}"'
        for k, v in sorted(oauth_params.items())
    )
    return f"OAuth {header_parts}"


# ── Twitter/X API v2 ──

async def post_tweet(
    company_slug: str,
    text: str,
    media_urls: list[str] | None = None,
) -> dict:
    """Post a tweet from the company's Twitter account."""
    creds = _get_twitter_creds(company_slug)
    if not creds:
        return {
            "status": "error",
            "message": (
                "Twitter not configured. Add TWITTER_API_KEY, TWITTER_API_SECRET, "
                "TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET to companies/{slug}/.env"
            ),
        }

    if not _check_rate_limit(company_slug, "twitter", MAX_TWEETS_PER_DAY):
        return {
            "status": "error",
            "message": f"Rate limit reached: max {MAX_TWEETS_PER_DAY} tweets per day",
        }

    if len(text) > 280:
        return {"status": "error", "message": f"Tweet too long: {len(text)} chars (max 280)"}

    payload = {"text": text}

    # For Twitter API v2 with JSON body, OAuth signing uses only oauth_* params
    auth_header = _build_oauth_header("POST", TWITTER_TWEET_URL, creds)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                TWITTER_TWEET_URL,
                headers={
                    "Authorization": auth_header,
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=30.0,
            )

            if response.status_code in (200, 201):
                data = response.json()
                _record_rate_limit(company_slug, "twitter")
                logger.info(f"[{company_slug}] Tweet posted: {data.get('data', {}).get('id')}")
                return {
                    "status": "ok",
                    "tweet_id": data.get("data", {}).get("id"),
                    "text": text,
                }
            else:
                error_body = response.text
                logger.error(f"[{company_slug}] Twitter API error {response.status_code}: {error_body}")
                return {
                    "status": "error",
                    "message": f"Twitter API {response.status_code}: {error_body}",
                }

    except Exception as e:
        logger.error(f"[{company_slug}] Twitter post failed: {e}")
        return {"status": "error", "message": str(e)}


async def get_recent_tweets(company_slug: str, limit: int = 10) -> list:
    """Get recent tweets from the company's Twitter account."""
    creds = _get_twitter_creds(company_slug)
    if not creds:
        return []

    # First get the authenticated user's ID
    auth_header = _build_oauth_header("GET", TWITTER_ME_URL, creds)

    try:
        async with httpx.AsyncClient() as client:
            me_resp = await client.get(
                TWITTER_ME_URL,
                headers={"Authorization": auth_header},
                timeout=15.0,
            )
            if me_resp.status_code != 200:
                logger.error(f"[{company_slug}] Twitter /users/me failed: {me_resp.status_code}")
                return []

            user_id = me_resp.json().get("data", {}).get("id")
            if not user_id:
                return []

            # Get timeline
            timeline_url = TWITTER_TIMELINE_URL.format(user_id=user_id)
            params = {"max_results": min(limit, 100), "tweet.fields": "created_at,public_metrics"}
            auth_header2 = _build_oauth_header("GET", timeline_url, creds, body_params=params)

            timeline_resp = await client.get(
                timeline_url,
                params=params,
                headers={"Authorization": auth_header2},
                timeout=15.0,
            )

            if timeline_resp.status_code != 200:
                logger.error(f"[{company_slug}] Twitter timeline failed: {timeline_resp.status_code}")
                return []

            return timeline_resp.json().get("data", [])

    except Exception as e:
        logger.error(f"[{company_slug}] Twitter fetch failed: {e}")
        return []


async def schedule_tweet(
    company_slug: str,
    text: str,
    publish_at: datetime,
) -> dict:
    """
    Schedule a tweet for future posting.
    Writes to content/scheduled_tweets.json for the scheduler to pick up.
    """
    if len(text) > 280:
        return {"status": "error", "message": f"Tweet too long: {len(text)} chars (max 280)"}

    scheduled_file = COMPANIES_DIR / company_slug / "content" / "scheduled_tweets.json"
    scheduled_file.parent.mkdir(parents=True, exist_ok=True)

    # Read existing
    entries = []
    if scheduled_file.exists():
        try:
            entries = json.loads(scheduled_file.read_text())
        except json.JSONDecodeError:
            entries = []

    entry = {
        "id": uuid.uuid4().hex[:12],
        "text": text,
        "publish_at": publish_at.isoformat(),
        "status": "scheduled",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    entries.append(entry)
    scheduled_file.write_text(json.dumps(entries, indent=2))

    logger.info(f"[{company_slug}] Tweet scheduled for {publish_at.isoformat()}")
    return {"status": "ok", "scheduled": entry}


# ── LinkedIn API ──

async def post_linkedin(
    company_slug: str,
    text: str,
    media_urls: list[str] | None = None,
) -> dict:
    """Post to LinkedIn from the company's account."""
    creds = _get_linkedin_creds(company_slug)
    if not creds:
        return {
            "status": "error",
            "message": (
                "LinkedIn not configured. Add LINKEDIN_ACCESS_TOKEN and "
                "LINKEDIN_PERSON_ID to companies/{slug}/.env"
            ),
        }

    if not _check_rate_limit(company_slug, "linkedin", MAX_LINKEDIN_PER_DAY):
        return {
            "status": "error",
            "message": f"Rate limit reached: max {MAX_LINKEDIN_PER_DAY} LinkedIn posts per day",
        }

    payload = {
        "author": f"urn:li:person:{creds['person_id']}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        },
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                LINKEDIN_UGC_URL,
                headers={
                    "Authorization": f"Bearer {creds['access_token']}",
                    "Content-Type": "application/json",
                    "X-Restli-Protocol-Version": "2.0.0",
                },
                json=payload,
                timeout=30.0,
            )

            if response.status_code in (200, 201):
                data = response.json()
                _record_rate_limit(company_slug, "linkedin")
                post_id = data.get("id", "")
                logger.info(f"[{company_slug}] LinkedIn post created: {post_id}")
                return {
                    "status": "ok",
                    "post_id": post_id,
                    "text": text,
                }
            else:
                error_body = response.text
                logger.error(f"[{company_slug}] LinkedIn API error {response.status_code}: {error_body}")
                return {
                    "status": "error",
                    "message": f"LinkedIn API {response.status_code}: {error_body}",
                }

    except Exception as e:
        logger.error(f"[{company_slug}] LinkedIn post failed: {e}")
        return {"status": "error", "message": str(e)}


# ── Integration status ──

def get_social_media_status(company_slug: str) -> dict:
    """Check which social media integrations are configured for a company."""
    return {
        "twitter": _get_twitter_creds(company_slug) is not None,
        "linkedin": _get_linkedin_creds(company_slug) is not None,
    }
