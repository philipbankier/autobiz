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

router = APIRouter(prefix="/api/companies/{company_id}/activity", tags=["activity"])


@router.get("", response_model=dict)
async def get_activity(
    company_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = await db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    if company.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your company")

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
