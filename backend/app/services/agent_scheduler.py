"""
Agent scheduling service using Celery Beat.
Registers periodic tasks directly in Celery Beat's schedule so everything
runs inside Docker without needing access to the OpenClaw gateway.
"""
import asyncio
import logging
from celery.schedules import crontab

logger = logging.getLogger(__name__)

# Department cron schedules (same timing as the old OpenClaw cron approach)
DEPT_SCHEDULES = {
    "ceo":       {"minute": "0", "hour": "6",    "day_of_week": "*", "description": "Daily strategic planning"},
    "developer": {"minute": "0", "hour": "*/2",  "day_of_week": "*", "description": "Every 2 hours"},
    "marketing": {"minute": "0", "hour": "*/3",  "day_of_week": "*", "description": "Every 3 hours"},
    "sales":     {"minute": "0", "hour": "*/4",  "day_of_week": "*", "description": "Every 4 hours"},
    "finance":   {"minute": "0", "hour": "22",   "day_of_week": "*", "description": "Daily at 10 PM"},
    "support":   {"minute": "0", "hour": "*/6",  "day_of_week": "*", "description": "Every 6 hours"},
}


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
    from app.database import async_session
    from app.models.company import Company

    async with async_session() as db:
        company = await db.get(Company, uuid.UUID(company_id))
        return company.slug if company else None


def schedule_company_cycles(company_id: str, slug: str | None = None) -> dict:
    """
    Register Celery Beat periodic tasks for all departments of a company.
    These run entirely inside Docker — no gateway access needed.
    """
    from app.worker import celery_app

    if not slug:
        slug = _run_async(_get_company_slug(company_id))
    if not slug:
        logger.error(f"Cannot schedule cycles: company {company_id} not found")
        return {}

    results = {}
    beat_schedule = celery_app.conf.beat_schedule or {}

    for dept_type, sched in DEPT_SCHEDULES.items():
        task_name = f"autobiz-{slug}-{dept_type}"
        beat_schedule[task_name] = {
            "task": "run_department_execution_cycle",
            "schedule": crontab(
                minute=sched["minute"],
                hour=sched["hour"],
                day_of_week=sched["day_of_week"],
            ),
            "args": (company_id, dept_type),
            "kwargs": {},
        }
        results[dept_type] = {
            "status": "registered",
            "task_name": task_name,
            "description": sched["description"],
        }
        logger.info(f"[{slug}] Registered Beat schedule: {task_name}")

    celery_app.conf.beat_schedule = beat_schedule
    return results


def unschedule_company_cycles(company_id: str, slug: str | None = None) -> dict:
    """Remove all Celery Beat periodic tasks for a company."""
    from app.worker import celery_app

    if not slug:
        slug = _run_async(_get_company_slug(company_id))
    if not slug:
        logger.error(f"Cannot unschedule cycles: company {company_id} not found")
        return {}

    beat_schedule = celery_app.conf.beat_schedule or {}
    prefix = f"autobiz-{slug}-"
    removed = {}

    for key in list(beat_schedule.keys()):
        if key.startswith(prefix):
            del beat_schedule[key]
            dept = key.replace(prefix, "")
            removed[dept] = "removed"
            logger.info(f"[{slug}] Removed Beat schedule: {key}")

    celery_app.conf.beat_schedule = beat_schedule

    for dept in DEPT_SCHEDULES:
        if dept not in removed:
            removed[dept] = "not_found"

    return removed


def trigger_department_cycle(company_id: str, department_type: str, force: bool = False):
    """Trigger a department cycle immediately via Celery."""
    from app.tasks.agent_cycles import run_department_execution_cycle
    task = run_department_execution_cycle.delay(company_id, department_type)
    logger.info(f"Triggered {department_type} for {company_id}: {task.id}")
    return task.id


def trigger_ceo_planning(company_id: str, force: bool = False):
    """Trigger CEO planning cycle immediately via Celery."""
    from app.tasks.agent_cycles import run_ceo_planning_cycle
    task = run_ceo_planning_cycle.delay(company_id)
    logger.info(f"Triggered CEO planning for {company_id}: {task.id}")
    return task.id
