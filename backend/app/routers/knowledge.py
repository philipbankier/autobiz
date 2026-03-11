import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.company import Company
from app.models.user import User
from app.services.knowledge_graph import get_entities, get_stats, get_context_summary

router = APIRouter(prefix="/api/companies/{company_id}/knowledge", tags=["knowledge"])


async def _verify_ownership(company_id: uuid.UUID, user: User, db: AsyncSession) -> Company:
    company = await db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    if company.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your company")
    return company


@router.get("/stats", response_model=dict)
async def knowledge_stats(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = await _verify_ownership(company_id, current_user, db)
    stats = get_stats(company.slug)
    return {"data": stats, "error": None, "meta": None}


@router.get("/entities", response_model=dict)
async def knowledge_entities(
    company_id: uuid.UUID,
    entity_type: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = await _verify_ownership(company_id, current_user, db)
    entities = get_entities(company.slug, entity_type=entity_type, limit=limit)
    return {"data": entities, "error": None, "meta": {"count": len(entities)}}


@router.get("/context", response_model=dict)
async def knowledge_context(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = await _verify_ownership(company_id, current_user, db)
    context = get_context_summary(company.slug)
    return {"data": {"context": context}, "error": None, "meta": None}
