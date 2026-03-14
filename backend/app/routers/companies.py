import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyRead
from app.schemas.department import DepartmentRead
from app.services.company import (
    create_company,
    list_companies,
    get_company,
    update_company,
    archive_company,
)

router = APIRouter(prefix="/api/companies", tags=["companies"])


async def _get_owned_company(company_id: uuid.UUID, user: User, db: AsyncSession):
    company = await get_company(db, company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    if company.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your company")
    return company


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create(
    data: CompanyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = await create_company(db, current_user.id, data)
    await db.commit()

    # Provision real infrastructure (async, best-effort)
    from app.services.provisioning import provision_company
    provision_result = await provision_company(
        company_id=str(company.id),
        slug=company.slug,
        name=company.name,
        mission=company.mission or "",
    )

    company_data = CompanyRead.model_validate(company).model_dump(mode="json")
    return {
        "data": company_data,
        "error": None,
        "meta": {"provisioning": provision_result},
    }


@router.get("", response_model=dict)
async def list_all(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    companies = await list_companies(db, current_user.id)
    return {
        "data": [CompanyRead.model_validate(c).model_dump(mode="json") for c in companies],
        "error": None,
        "meta": {"count": len(companies)},
    }


@router.get("/{company_id}", response_model=dict)
async def get_one(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = await _get_owned_company(company_id, current_user, db)
    company_data = CompanyRead.model_validate(company).model_dump(mode="json")
    company_data["departments"] = [
        DepartmentRead.model_validate(d).model_dump(mode="json") for d in company.departments
    ]
    return {
        "data": company_data,
        "error": None,
        "meta": None,
    }


@router.put("/{company_id}", response_model=dict)
async def update(
    company_id: uuid.UUID,
    data: CompanyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = await _get_owned_company(company_id, current_user, db)
    company = await update_company(db, company, data)
    return {
        "data": CompanyRead.model_validate(company).model_dump(mode="json"),
        "error": None,
        "meta": None,
    }


@router.post("/{company_id}/onboard", response_model=dict)
async def onboard(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger CEO onboarding — takes the company mission and has the CEO agent
    ralph-loop it into a full business plan with department tasks.
    """
    company = await _get_owned_company(company_id, current_user, db)

    from app.tasks.agent_cycles import run_onboarding
    task = run_onboarding.delay(str(company.id), company.mission or company.name)

    return {
        "data": {
            "task_id": task.id,
            "company_id": str(company.id),
            "status": "onboarding_started",
        },
        "error": None,
        "meta": {"message": "CEO agent is creating your business plan. This may take a few minutes."},
    }


@router.post("/{company_id}/run/{department_type}", response_model=dict)
async def run_department(
    company_id: uuid.UUID,
    department_type: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger a single department execution cycle."""
    company = await _get_owned_company(company_id, current_user, db)

    from app.tasks.agent_cycles import run_department_execution_cycle
    task = run_department_execution_cycle.delay(str(company.id), department_type)

    return {
        "data": {
            "task_id": task.id,
            "department": department_type,
            "status": "triggered",
        },
        "error": None,
        "meta": None,
    }


# ── Scheduler management endpoints ──

@router.post("/{company_id}/scheduler/start", response_model=dict)
async def scheduler_start(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Register cron jobs for all departments of a company."""
    company = await _get_owned_company(company_id, current_user, db)

    from app.services.scheduler import register_company_cron_jobs
    result = await register_company_cron_jobs(str(company.id), company.slug)

    return {
        "data": {"company_id": str(company.id), "slug": company.slug, "jobs": result},
        "error": None,
        "meta": None,
    }


@router.post("/{company_id}/scheduler/stop", response_model=dict)
async def scheduler_stop(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Unregister all cron jobs for a company."""
    company = await _get_owned_company(company_id, current_user, db)

    from app.services.scheduler import unregister_company_cron_jobs
    result = await unregister_company_cron_jobs(company.slug)

    return {
        "data": {"company_id": str(company.id), "slug": company.slug, "jobs": result},
        "error": None,
        "meta": None,
    }


@router.get("/{company_id}/scheduler/status", response_model=dict)
async def scheduler_status(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List active cron jobs for a company."""
    company = await _get_owned_company(company_id, current_user, db)

    from app.services.scheduler import list_company_cron_jobs
    jobs = await list_company_cron_jobs(company.slug)

    return {
        "data": {"company_id": str(company.id), "slug": company.slug, "jobs": jobs},
        "error": None,
        "meta": {"count": len(jobs)},
    }


@router.post("/{company_id}/scheduler/trigger/{dept}", response_model=dict)
async def scheduler_trigger(
    company_id: uuid.UUID,
    dept: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually trigger a department cycle with condition checks via smart_dispatch."""
    company = await _get_owned_company(company_id, current_user, db)

    from app.services.scheduler import smart_dispatch
    result = await smart_dispatch(
        company_id=str(company.id),
        slug=company.slug,
        department_type=dept,
        force=False,
    )

    return {
        "data": result,
        "error": None,
        "meta": None,
    }


@router.delete("/{company_id}", response_model=dict)
async def delete(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = await _get_owned_company(company_id, current_user, db)
    company = await archive_company(db, company)
    return {
        "data": {"id": str(company.id), "status": company.status.value},
        "error": None,
        "meta": None,
    }
