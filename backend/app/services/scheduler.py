"""
Hybrid scheduler service.
Three trigger layers, all feeding into the same Celery tasks:

1. CRON — OpenClaw cron jobs for scheduled autonomy
2. EVENT — webhook endpoints for real-time reactions  
3. CONDITION — pre-run filters to skip unnecessary agent runs

The agent logic doesn't care how it was triggered.
"""
import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session
from app.models.company import Company
from app.models.department import Department, DepartmentType, DepartmentStatus

logger = logging.getLogger(__name__)

GATEWAY_URL = "http://127.0.0.1:18789"
COMPANIES_DIR = Path("/home/philip/TinkerLab/autobiz/companies")

# Schedule config: how often each department type should run
DEFAULT_SCHEDULES = {
    "ceo": {
        "cron": "0 6 * * *",        # Daily at 6 AM
        "description": "Daily strategic planning",
    },
    "developer": {
        "cron": "0 */2 * * *",      # Every 2 hours
        "description": "Execute next development task",
    },
    "marketing": {
        "cron": "0 */3 * * *",      # Every 3 hours
        "description": "Execute next marketing task",
    },
    "sales": {
        "cron": "0 */4 * * *",      # Every 4 hours
        "description": "Execute next sales task",
    },
    "finance": {
        "cron": "0 22 * * *",       # Daily at 10 PM
        "description": "Daily financial reporting",
    },
    "support": {
        "cron": "0 */6 * * *",      # Every 6 hours
        "description": "Check for support tasks",
    },
}


def _get_gateway_token() -> str:
    config_path = Path.home() / ".openclaw" / "openclaw.json"
    try:
        with open(config_path) as f:
            config = json.load(f)
        return config["gateway"]["auth"]["token"]
    except (FileNotFoundError, KeyError):
        return ""


# ──────────────────────────────────────────────
# LAYER 1: CRON — OpenClaw cron jobs
# ──────────────────────────────────────────────

async def register_company_cron_jobs(company_id: str, slug: str) -> dict:
    """
    Register OpenClaw cron jobs for a company's department cycles.
    Uses isolated sessions so each run gets fresh context.
    """
    token = _get_gateway_token()
    if not token:
        return {"status": "error", "message": "No gateway token"}

    results = {}
    workspace = str(COMPANIES_DIR / slug)

    for dept_type, schedule in DEFAULT_SCHEDULES.items():
        job_id = f"autobiz-{slug}-{dept_type}"
        
        # Build the cron job task message
        task_message = (
            f"You are the {dept_type.upper()} department of company '{slug}'. "
            f"Your workspace is {workspace}. "
            f"Read {workspace}/STEERING.md for human overrides. "
            f"Read {workspace}/departments/{dept_type}/PLAN.md for your tasks. "
            f"Execute the next unchecked task (- [ ]). "
            f"Mark it done (- [x]) when complete. "
            f"Update {workspace}/departments/{dept_type}/MEMORY.md with learnings."
        )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{GATEWAY_URL}/tools/invoke",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "tool": "cron.add",
                        "args": {
                            "jobId": job_id,
                            "name": f"{slug} {dept_type} cycle",
                            "schedule": {
                                "kind": "cron",
                                "expr": schedule["cron"],
                                "tz": "America/New_York",
                            },
                            "sessionTarget": "isolated",
                            "payload": {
                                "kind": "agentTurn",
                                "message": task_message,
                                "timeoutSeconds": 300,
                            },
                            "delivery": {
                                "mode": "none",  # Silent — don't spam channels
                            },
                        },
                    },
                    timeout=10.0,
                )
                result = response.json()
                if result.get("ok"):
                    results[dept_type] = {"status": "registered", "job_id": job_id, "expr": schedule["cron"]}
                    logger.info(f"Registered cron job: {job_id} ({schedule['cron']})")
                else:
                    results[dept_type] = {"status": "error", "message": str(result.get("error", ""))}
                    logger.warning(f"Failed to register cron job {job_id}: {result}")
        except Exception as e:
            results[dept_type] = {"status": "error", "message": str(e)}
            logger.error(f"Cron registration error for {job_id}: {e}")

    return results


async def unregister_company_cron_jobs(slug: str) -> dict:
    """Remove all cron jobs for a company."""
    token = _get_gateway_token()
    results = {}

    for dept_type in DEFAULT_SCHEDULES:
        job_id = f"autobiz-{slug}-{dept_type}"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{GATEWAY_URL}/tools/invoke",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "tool": "cron.remove",
                        "args": {"jobId": job_id},
                    },
                    timeout=10.0,
                )
                results[dept_type] = "removed" if response.json().get("ok") else "not_found"
        except Exception as e:
            results[dept_type] = f"error: {e}"

    return results


async def list_company_cron_jobs(slug: str) -> list:
    """List all active cron jobs for a company."""
    token = _get_gateway_token()
    prefix = f"autobiz-{slug}-"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GATEWAY_URL}/tools/invoke",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={"tool": "cron.list", "args": {}},
                timeout=10.0,
            )
            result = response.json()
            if not result.get("ok"):
                return []

            # Filter to this company's jobs
            content = result.get("result", {}).get("content", [])
            jobs = []
            for item in content:
                if item.get("type") == "text":
                    try:
                        data = json.loads(item["text"])
                        for job in data.get("jobs", []):
                            if job.get("jobId", "").startswith(prefix):
                                jobs.append(job)
                    except (json.JSONDecodeError, KeyError):
                        pass
            return jobs
    except Exception:
        return []


# ──────────────────────────────────────────────
# LAYER 2: EVENT — webhook/API trigger handlers
# ──────────────────────────────────────────────

async def handle_user_chat(company_id: str, department_type: str, message: str) -> dict:
    """Event trigger: user sent a chat message."""
    from app.tasks.agent_cycles import run_chat_response
    task = run_chat_response.delay(company_id, department_type, message)
    return {"trigger": "event:chat", "task_id": task.id}


async def handle_stripe_webhook(company_id: str, event_type: str, event_data: dict) -> dict:
    """Event trigger: Stripe payment/subscription event."""
    from app.tasks.agent_cycles import run_department_execution_cycle

    # Route to finance department with event context
    task_desc = f"Stripe event: {event_type}. Data: {json.dumps(event_data)[:500]}"
    task = run_department_execution_cycle.delay(company_id, "finance", task_desc)
    return {"trigger": "event:stripe", "event_type": event_type, "task_id": task.id}


async def handle_deploy_webhook(company_id: str, deploy_data: dict) -> dict:
    """Event trigger: Vercel deployment completed."""
    from app.tasks.agent_cycles import run_department_execution_cycle

    status = deploy_data.get("status", "unknown")
    url = deploy_data.get("url", "")
    task_desc = f"Deployment {status}. URL: {url}. Verify the site works and update MEMORY.md."
    task = run_department_execution_cycle.delay(company_id, "developer", task_desc)
    return {"trigger": "event:deploy", "status": status, "task_id": task.id}


async def handle_github_webhook(company_id: str, event_type: str, event_data: dict) -> dict:
    """Event trigger: GitHub PR, issue, or push event."""
    from app.tasks.agent_cycles import run_department_execution_cycle

    task_desc = f"GitHub event: {event_type}. Data: {json.dumps(event_data)[:500]}"
    task = run_department_execution_cycle.delay(company_id, "developer", task_desc)
    return {"trigger": "event:github", "event_type": event_type, "task_id": task.id}


# ──────────────────────────────────────────────
# LAYER 3: CONDITION — pre-run filters
# ──────────────────────────────────────────────

def has_pending_tasks(slug: str, department_type: str) -> bool:
    """Check if department has unchecked tasks in PLAN.md."""
    plan_path = COMPANIES_DIR / slug / "departments" / department_type / "PLAN.md"
    try:
        content = plan_path.read_text()
        # Look for unchecked checkbox items
        return "- [ ]" in content
    except FileNotFoundError:
        return False


def has_steering_override(slug: str) -> bool:
    """Check if STEERING.md has active human overrides."""
    steering_path = COMPANIES_DIR / slug / "STEERING.md"
    try:
        content = steering_path.read_text()
        # Default template contains "No overrides"
        return "No overrides" not in content
    except FileNotFoundError:
        return False


async def check_budget_remaining(company_id: str, department_type: str) -> bool:
    """Check if department has budget remaining."""
    from app.services.cost_control import check_budget
    
    async with async_session() as db:
        result = await db.execute(
            select(Department).where(
                Department.company_id == uuid.UUID(company_id),
                Department.type == DepartmentType(department_type),
            )
        )
        department = result.scalar_one_or_none()
        if not department:
            return False

        budget_status = await check_budget(db, department)
        return budget_status["allowed"]


async def should_run(
    company_id: str,
    slug: str,
    department_type: str,
    force: bool = False,
) -> dict:
    """
    Condition layer: decide whether an agent run is worthwhile.
    Returns {run: bool, reason: str}
    
    Saves ~50-70% of token costs by skipping pointless runs.
    """
    if force:
        return {"run": True, "reason": "forced"}

    # Always run CEO (it creates tasks for others)
    if department_type == "ceo":
        return {"run": True, "reason": "CEO always runs (creates tasks)"}

    # Check steering override (always run if human is steering)
    if has_steering_override(slug):
        return {"run": True, "reason": "STEERING.md has active override"}

    # Check pending tasks
    if not has_pending_tasks(slug, department_type):
        return {"run": False, "reason": f"No pending tasks in {department_type}/PLAN.md"}

    # Check budget
    budget_ok = await check_budget_remaining(company_id, department_type)
    if not budget_ok:
        return {"run": False, "reason": "Budget exceeded"}

    return {"run": True, "reason": "Has pending tasks and budget available"}


# ──────────────────────────────────────────────
# COMBINED: Smart dispatch (cron callback uses this)
# ──────────────────────────────────────────────

async def smart_dispatch(
    company_id: str,
    slug: str,
    department_type: str,
    task_override: str | None = None,
    force: bool = False,
) -> dict:
    """
    Smart dispatch: condition check → Celery task.
    This is what cron jobs and the scheduler loop call.
    """
    # Layer 3: condition check
    check = await should_run(company_id, slug, department_type, force=force)
    if not check["run"]:
        logger.info(f"[{slug}/{department_type}] Skipped: {check['reason']}")
        return {"status": "skipped", "reason": check["reason"]}

    # Dispatch to Celery
    from app.tasks.agent_cycles import run_department_execution_cycle, run_ceo_planning_cycle

    if department_type == "ceo" and not task_override:
        task = run_ceo_planning_cycle.delay(company_id)
    else:
        task = run_department_execution_cycle.delay(company_id, department_type, task_override)

    logger.info(f"[{slug}/{department_type}] Dispatched: {check['reason']} → task {task.id}")
    return {
        "status": "dispatched",
        "reason": check["reason"],
        "task_id": task.id,
        "department": department_type,
    }


# ──────────────────────────────────────────────
# FALLBACK: AsyncIO scheduler loop
# (backup if OpenClaw cron isn't set up yet)
# ──────────────────────────────────────────────

async def scheduler_loop(interval_seconds: int = 1800):
    """
    Fallback scheduler loop. Runs inside FastAPI process.
    Checks all active companies every 30 minutes.
    Only needed if OpenClaw cron jobs aren't registered.
    """
    logger.info(f"Scheduler loop started (interval: {interval_seconds}s)")

    while True:
        try:
            async with async_session() as db:
                result = await db.execute(
                    select(Company).where(Company.is_active == True)
                )
                companies = result.scalars().all()

                for company in companies:
                    # Check each department
                    dept_result = await db.execute(
                        select(Department).where(Department.company_id == company.id)
                    )
                    departments = dept_result.scalars().all()

                    for dept in departments:
                        await smart_dispatch(
                            company_id=str(company.id),
                            slug=company.slug,
                            department_type=dept.type.value,
                        )

            logger.info(f"Scheduler loop: checked {len(companies)} companies")
        except Exception as e:
            logger.error(f"Scheduler loop error: {e}")

        await asyncio.sleep(interval_seconds)
