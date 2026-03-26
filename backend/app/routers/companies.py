import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

COMPANIES_DIR = Path(os.environ.get("COMPANIES_DIR", "/app/companies"))

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


# ── Steering file endpoints ──

@router.get("/{company_id}/steering", response_model=dict)
async def get_steering(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Read STEERING.md for a company."""
    company = await _get_owned_company(company_id, current_user, db)

    steering_path = COMPANIES_DIR / company.slug / "STEERING.md"
    content = ""
    if steering_path.exists():
        content = steering_path.read_text()

    return {
        "data": {"content": content},
        "error": None,
        "meta": None,
    }


@router.put("/{company_id}/steering", response_model=dict)
async def update_steering(
    company_id: uuid.UUID,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Write STEERING.md for a company."""
    company = await _get_owned_company(company_id, current_user, db)

    content = body.get("content", "")
    steering_path = COMPANIES_DIR / company.slug / "STEERING.md"
    steering_path.parent.mkdir(parents=True, exist_ok=True)
    steering_path.write_text(content)

    return {
        "data": {"content": content},
        "error": None,
        "meta": {"message": "STEERING.md updated"},
    }


@router.delete("/{company_id}", response_model=dict)
async def delete(
    company_id: uuid.UUID,
    hard: bool = Query(False, description="Full teardown: delete GitHub repo, Vercel project, Stripe account"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a company.
    - Soft delete (default): archives in DB, stops scheduled tasks.
    - Hard delete (?hard=true): also deletes GitHub repo, Vercel project, and Stripe account.
    """
    company = await _get_owned_company(company_id, current_user, db)

    # Always: unschedule Celery Beat tasks
    teardown_results: dict = {"scheduler": "unscheduled"}
    try:
        from app.services.agent_scheduler import unschedule_company_cycles
        unschedule_company_cycles(str(company.id), slug=company.slug)
    except Exception as e:
        teardown_results["scheduler"] = f"error: {e}"

    if hard:
        # Read the company .env for stored IDs
        env_file = COMPANIES_DIR / company.slug / ".env"
        env_data: dict = {}
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    env_data[k.strip()] = v.strip()

        # Delete GitHub repo
        from app.config import settings as app_settings
        if app_settings.GITHUB_PAT:
            github_repo = env_data.get("GITHUB_REPO")
            if github_repo:
                try:
                    import httpx
                    async with httpx.AsyncClient() as client:
                        resp = await client.delete(
                            f"https://api.github.com/repos/{github_repo}",
                            headers={
                                "Authorization": f"Bearer {app_settings.GITHUB_PAT}",
                                "Accept": "application/vnd.github+json",
                            },
                            timeout=10.0,
                        )
                    teardown_results["github"] = "deleted" if resp.status_code == 204 else f"error: {resp.status_code}"
                except Exception as e:
                    teardown_results["github"] = f"error: {e}"
            else:
                teardown_results["github"] = "no_repo_configured"

        # Delete Vercel project
        if app_settings.VERCEL_TOKEN:
            vercel_project_id = env_data.get("VERCEL_PROJECT_ID")
            if vercel_project_id:
                try:
                    import httpx
                    async with httpx.AsyncClient() as client:
                        resp = await client.delete(
                            f"https://api.vercel.com/v9/projects/{vercel_project_id}",
                            headers={"Authorization": f"Bearer {app_settings.VERCEL_TOKEN}"},
                            timeout=10.0,
                        )
                    teardown_results["vercel"] = "deleted" if resp.status_code == 204 else f"error: {resp.status_code}"
                except Exception as e:
                    teardown_results["vercel"] = f"error: {e}"
            else:
                teardown_results["vercel"] = "no_project_configured"

        # Soft-delete Stripe Connect account (can't fully delete, just reject)
        stripe_account_id = env_data.get("STRIPE_CONNECT_ACCOUNT_ID")
        if stripe_account_id and app_settings.STRIPE_SECRET_KEY:
            try:
                import httpx
                async with httpx.AsyncClient() as client:
                    resp = await client.delete(
                        f"https://api.stripe.com/v1/accounts/{stripe_account_id}",
                        auth=(app_settings.STRIPE_SECRET_KEY, ""),
                        timeout=10.0,
                    )
                teardown_results["stripe"] = "deleted" if resp.status_code == 200 else f"error: {resp.status_code}"
            except Exception as e:
                teardown_results["stripe"] = f"error: {e}"

    # Archive in DB
    company = await archive_company(db, company)
    await db.commit()

    return {
        "data": {
            "id": str(company.id),
            "status": company.status.value,
            "hard": hard,
            "teardown": teardown_results,
        },
        "error": None,
        "meta": {"message": "Company archived" if not hard else "Company fully deleted"},
    }
