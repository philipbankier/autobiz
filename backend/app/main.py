from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

import asyncio
import logging

from app.routers import auth, companies, departments, activity, chat, tasks, billing, dashboard, knowledge, site, webhooks, integrations

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AutoBiz API",
    description="AI-powered business automation platform",
    version="0.1.0",
)

# Rate limiting
from slowapi import Limiter
from slowapi.util import get_remote_address
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — allow frontend origins (wildcards require allow_credentials=False for most browsers,
# but EventSource doesn't send credentials anyway; JWT is passed as a query param).
# We use explicit origins so allow_credentials=True works correctly with fetch() calls.
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "https://autobiz-app.vercel.app",
    "https://oneidea.app",
    "https://www.oneidea.app",
    "http://127.0.0.1:3002",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.(autobiz\.app|vercel\.app|oneidea\.app)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(companies.router)
app.include_router(departments.router)
app.include_router(activity.router)
app.include_router(chat.router)
app.include_router(tasks.router)
app.include_router(billing.router)
app.include_router(dashboard.router)
app.include_router(knowledge.router)
app.include_router(site.router)
app.include_router(webhooks.router)
app.include_router(integrations.router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "data": None,
            "error": str(exc),
            "meta": None,
        },
    )


@app.on_event("startup")
async def startup():
    """Start the fallback scheduler loop and event bus on app startup."""
    from app.services.scheduler import scheduler_loop
    from app.services.event_bus import set_event_loop

    # Capture event loop for sync→async event publishing bridge
    set_event_loop(asyncio.get_running_loop())

    # Run scheduler every 30 minutes as a backup to OpenClaw cron
    asyncio.create_task(scheduler_loop(interval_seconds=1800))
    logger.info("Fallback scheduler loop started (30 min interval)")


@app.get("/api/health")
async def health():
    return {"data": {"status": "ok"}, "error": None, "meta": None}
