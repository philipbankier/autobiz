"""
Agent scheduling service.
Delegates to the hybrid scheduler (scheduler.py) for cron registration,
condition-checked dispatch, and smart triggering.
"""
import asyncio
import logging

from app.services.scheduler import (
    register_company_cron_jobs,
    unregister_company_cron_jobs,
    smart_dispatch,
)

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run async code from sync context (e.g. Celery tasks)."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _get_company_slug(company_id: str) -> str | None:
    """Look up company slug from ID."""
    import uuid
    from sqlalchemy import select
    from app.database import async_session
    from app.models.company import Company

    async with async_session() as db:
        company = await db.get(Company, uuid.UUID(company_id))
        return company.slug if company else None


def schedule_company_cycles(company_id: str, slug: str | None = None):
    """Register cron jobs for all departments of a company."""
    if not slug:
        slug = _run_async(_get_company_slug(company_id))
    if not slug:
        logger.error(f"Cannot schedule cycles: company {company_id} not found")
        return {}
    result = _run_async(register_company_cron_jobs(company_id, slug))
    logger.info(f"Scheduled cycles for company {company_id} ({slug}): {result}")
    return result


def unschedule_company_cycles(company_id: str, slug: str | None = None):
    """Remove all cron jobs for a company."""
    if not slug:
        slug = _run_async(_get_company_slug(company_id))
    if not slug:
        logger.error(f"Cannot unschedule cycles: company {company_id} not found")
        return {}
    result = _run_async(unregister_company_cron_jobs(slug))
    logger.info(f"Unscheduled cycles for company {company_id} ({slug}): {result}")
    return result


def trigger_department_cycle(company_id: str, department_type: str, force: bool = False):
    """Trigger a department cycle through smart_dispatch (with condition checks)."""
    slug = _run_async(_get_company_slug(company_id))
    if not slug:
        logger.error(f"Cannot trigger cycle: company {company_id} not found")
        return None
    result = _run_async(smart_dispatch(
        company_id=company_id,
        slug=slug,
        department_type=department_type,
        force=force,
    ))
    logger.info(f"Triggered {department_type} for {company_id}: {result}")
    return result.get("task_id")


def trigger_ceo_planning(company_id: str, force: bool = False):
    """Trigger CEO planning cycle through smart_dispatch."""
    slug = _run_async(_get_company_slug(company_id))
    if not slug:
        logger.error(f"Cannot trigger CEO planning: company {company_id} not found")
        return None
    result = _run_async(smart_dispatch(
        company_id=company_id,
        slug=slug,
        department_type="ceo",
        force=force,
    ))
    logger.info(f"Triggered CEO planning for {company_id}: {result}")
    return result.get("task_id")
