import asyncio
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func as sqlfunc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.agent_run import AgentRun
from app.models.company import Company
from app.models.user import User
from app.schemas.agent import AgentRunRead
from app.services.auth import verify_token
from app.services.event_bus import subscribe, get_recent_events

router = APIRouter(prefix="/api/companies/{company_id}/activity", tags=["activity"])


async def _get_owned_company(company_id: uuid.UUID, user: User, db: AsyncSession) -> Company:
    company = await db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    if company.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your company")
    return company


@router.get("", response_model=dict)
async def get_activity(
    company_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_owned_company(company_id, current_user, db)

    # Count total
    count_result = await db.execute(
        select(sqlfunc.count(AgentRun.id)).where(AgentRun.company_id == company_id)
    )
    total = count_result.scalar() or 0

    # Fetch page
    offset = (page - 1) * page_size
    result = await db.execute(
        select(AgentRun)
        .where(AgentRun.company_id == company_id)
        .order_by(AgentRun.started_at.desc().nullslast())
        .offset(offset)
        .limit(page_size)
    )
    runs = list(result.scalars().all())

    return {
        "data": [AgentRunRead.model_validate(r).model_dump(mode="json") for r in runs],
        "error": None,
        "meta": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size if total > 0 else 0,
        },
    }


@router.get("/events", response_model=dict)
async def get_event_history(
    company_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get recent events from the in-memory ring buffer."""
    await _get_owned_company(company_id, current_user, db)
    events = get_recent_events(str(company_id), limit=limit)
    return {"data": events, "error": None, "meta": {"count": len(events)}}


@router.get("/stream")
async def activity_stream(
    company_id: uuid.UUID,
    token: str = Query(..., description="JWT auth token"),
    db: AsyncSession = Depends(get_db),
):
    """SSE endpoint for real-time activity events.

    Auth via query param because SSE (EventSource) can't set headers.
    """
    from sse_starlette.sse import EventSourceResponse

    # Verify token
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # Verify company ownership
    company = await db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    try:
        owner_id = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if company.user_id != owner_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your company")

    cid = str(company_id)

    async def event_generator():
        async for event in subscribe(cid):
            # Use unnamed events so EventSource.onmessage fires for all events.
            # The event type is included in the JSON data payload.
            yield {
                "id": str(event["id"]),
                "data": json.dumps(event),
            }

    return EventSourceResponse(
        event_generator(),
        ping=30,  # heartbeat every 30s
    )
