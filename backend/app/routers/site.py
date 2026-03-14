import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.company import Company
from app.models.user import User
from app.services.site_deploy import (
    deploy_site,
    deploy_to_vercel,
    check_deploy_status,
    get_site_status,
    get_site_url,
)
from app.services.git_service import git_commit, git_push, git_status

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
    """Deploy site: copy files locally + push to GitHub for Vercel auto-deploy."""
    company = await _verify_ownership(company_id, current_user, db)
    # Local deploy (nginx/caddy)
    local_result = deploy_site(company.slug)
    # Vercel deploy (git push)
    vercel_result = await deploy_to_vercel(company.slug)
    return {
        "data": {
            "local": local_result,
            "vercel": vercel_result,
        },
        "error": None,
        "meta": None,
    }


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


@router.get("/deploys", response_model=dict)
async def list_deploys(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List recent Vercel deployments."""
    company = await _verify_ownership(company_id, current_user, db)
    result = await check_deploy_status(company.slug)
    return {"data": result, "error": None, "meta": None}


@router.post("/git/commit", response_model=dict)
async def manual_commit(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manual git commit trigger."""
    company = await _verify_ownership(company_id, current_user, db)
    result = await git_commit(company.slug, "manual commit via API")
    return {"data": result, "error": None, "meta": None}


@router.post("/git/push", response_model=dict)
async def manual_push(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manual git push trigger."""
    company = await _verify_ownership(company_id, current_user, db)
    result = await git_push(company.slug)
    return {"data": result, "error": None, "meta": None}


@router.get("/git/status", response_model=dict)
async def show_git_status(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Show git status for company code repo."""
    company = await _verify_ownership(company_id, current_user, db)
    result = await git_status(company.slug)
    return {"data": result, "error": None, "meta": None}
