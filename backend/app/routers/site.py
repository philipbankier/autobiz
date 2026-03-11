import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.company import Company
from app.models.user import User
from app.services.site_deploy import deploy_site, get_site_status, get_site_url

router = APIRouter(prefix="/api/companies/{company_id}/site", tags=["site"])


async def _verify_ownership(company_id: uuid.UUID, user: User, db: AsyncSession) -> Company:
    company = await db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    if company.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your company")
    return company


@router.get("", response_model=dict)
async def site_status(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = await _verify_ownership(company_id, current_user, db)
    site = get_site_status(company.slug)
    return {"data": site, "error": None, "meta": None}


@router.post("/deploy", response_model=dict)
async def deploy(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = await _verify_ownership(company_id, current_user, db)
    result = deploy_site(company.slug)
    return {"data": result, "error": None, "meta": None}


@router.get("/url", response_model=dict)
async def site_url(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = await _verify_ownership(company_id, current_user, db)
    return {
        "data": {"url": get_site_url(company.slug), "slug": company.slug},
        "error": None,
        "meta": None,
    }
