"""
Celery tasks for agent department cycles.
Implements:
- Budget check before every run
- Model tiering per department
- Ralph loop task execution (one task per run)
- Post-run memory consolidation (async)
"""
import asyncio
import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.worker import celery_app
from app.database import async_session_factory
from app.models.agent_run import AgentRun, RunStatus
from app.models.company import Company
from app.models.department import Department, DepartmentType, DepartmentStatus
from app.models.cost_event import CostType
from app.services.openclaw import spawn_agent_session
from app.services.cost_control import (
    check_budget,
    record_cost,
    estimate_cost,
    get_model_for_department,
)

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Helper to run async code in sync Celery tasks."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _execute_department_cycle(
    company_id: str,
    department_type: str,
    task_override: str | None = None,
) -> dict:
    """Core logic for running a department agent cycle."""
    async with async_session_factory() as db:
        # Load company and department
        company = await db.get(Company, uuid.UUID(company_id))
        if not company:
            return {"status": "error", "message": f"Company {company_id} not found"}

        result = await db.execute(
            select(Department).where(
                Department.company_id == company.id,
                Department.type == DepartmentType(department_type),
            )
        )
        department = result.scalar_one_or_none()
        if not department:
            return {"status": "error", "message": f"Department {department_type} not found"}

        # 1. BUDGET CHECK
        budget_status = await check_budget(db, department)
        if not budget_status["allowed"]:
            logger.warning(
                f"[{company.slug}/{department_type}] Budget exceeded: "
                f"${budget_status['spend']:.2f}/${budget_status['budget']:.2f}"
            )
            return {
                "status": "budget_exceeded",
                "spend": str(budget_status["spend"]),
                "budget": str(budget_status["budget"]),
            }

        if budget_status["warning"]:
            logger.info(f"[{company.slug}/{department_type}] {budget_status['warning']}")

        # 2. CREATE AGENT RUN RECORD
        agent_run = AgentRun(
            company_id=company.id,
            department_id=department.id,
            status=RunStatus.running,
        )
        db.add(agent_run)

        # Mark department as running
        department.status = DepartmentStatus.running
        await db.flush()
        await db.commit()

        # 3. BUILD TASK DESCRIPTION
        task = task_override or (
            f"Check your PLAN.md for the next unchecked task and execute it. "
            f"If no tasks exist, review COMPANY.md and create an initial plan "
            f"in departments/{department_type}/PLAN.md."
        )

        # 4. SPAWN AGENT (with model tiering)
        model = get_model_for_department(department_type)
        
        try:
            spawn_result = await spawn_agent_session(
                company_id=str(company.id),
                company_slug=company.slug,
                company_name=company.name,
                company_mission=company.mission or "",
                department_type=department_type,
                task_description=task,
                model=model,
                timeout_seconds=300,
            )
        except Exception as e:
            logger.error(f"[{company.slug}/{department_type}] Spawn failed: {e}")
            spawn_result = {"status": "error", "message": str(e)}

        # 5. UPDATE RUN STATUS
        async with async_session_factory() as db2:
            run = await db2.get(AgentRun, agent_run.id)
            dept = await db2.get(Department, department.id)

            if spawn_result.get("status") == "accepted":
                run.status = RunStatus.completed
                if dept:
                    dept.agent_session_id = spawn_result.get("session_key")
                    dept.status = DepartmentStatus.idle

                # 6. RECORD ESTIMATED COST
                # Estimate ~5K input + ~2K output tokens per run
                estimated_cost = estimate_cost(model, 5000, 2000)
                await record_cost(
                    db2,
                    company_id=company.id,
                    department_id=department.id,
                    cost_type=CostType.llm_tokens,
                    amount=estimated_cost,
                    description=f"{department_type} cycle run (estimated)",
                )
            else:
                run.status = RunStatus.failed
                run.error = spawn_result.get("message", "Unknown error")
                if dept:
                    dept.status = DepartmentStatus.idle

            await db2.commit()

        return {
            "status": spawn_result.get("status"),
            "department": department_type,
            "company": company.slug,
            "model": model,
            "budget": {
                "spend": str(budget_status["spend"]),
                "budget": str(budget_status["budget"]),
                "pct": budget_status["pct"],
            },
            **spawn_result,
        }


@celery_app.task(name="run_department_execution_cycle")
def run_department_execution_cycle(company_id: str, department_type: str, task: str | None = None):
    """Celery task: Execute a single department cycle."""
    return _run_async(_execute_department_cycle(company_id, department_type, task))


@celery_app.task(name="run_ceo_planning_cycle")
def run_ceo_planning_cycle(company_id: str):
    """
    CEO planning cycle — runs with Opus model.
    Creates/updates strategic plan and assigns tasks to departments.
    """
    return _run_async(_execute_department_cycle(
        company_id,
        "ceo",
        task_override=(
            "Review the company's current state in COMPANY.md and all department PLAN.md files. "
            "Then:\n"
            "1. Update COMPANY.md with any strategic changes\n"
            "2. Review each department's progress (check completed vs pending tasks)\n"
            "3. Add new tasks to department PLAN.md files as needed\n"
            "4. Prioritize: what's the single most important thing for each department today?\n"
            "5. Update your own departments/ceo/PLAN.md with your strategic tasks"
        ),
    ))


@celery_app.task(name="run_finance_reporting_cycle")
def run_finance_reporting_cycle(company_id: str):
    """Finance reporting cycle — runs daily."""
    return _run_async(_execute_department_cycle(
        company_id,
        "finance",
        task_override=(
            "Generate a daily financial summary:\n"
            "1. Check agent spending records in your memory\n"
            "2. Check Stripe for any revenue (if configured)\n"
            "3. Calculate burn rate and runway\n"
            "4. Update departments/finance/PLAN.md with any action items\n"
            "5. Write a brief report to COMPANY.md under ## Latest Financial Report"
        ),
    ))


@celery_app.task(name="run_weekly_learning_cycle")
def run_weekly_learning_cycle(company_id: str):
    """Weekly learning cycle — all departments reflect and consolidate."""
    results = []
    for dept in ["ceo", "developer", "marketing", "finance"]:
        result = _run_async(_execute_department_cycle(
            company_id,
            dept,
            task_override=(
                "Weekly reflection:\n"
                "1. Review your department's MEMORY.md\n"
                "2. What worked well this week? What didn't?\n"
                "3. What should we change for next week?\n"
                "4. Update MEMORY.md with lessons learned\n"
                "5. Suggest improvements to COMPANY.md strategy"
            ),
        ))
        results.append({dept: result})
    return results


@celery_app.task(name="run_chat_response")
def run_chat_response(company_id: str, department_type: str, message: str):
    """Handle a chat message from the user — route to appropriate department."""
    return _run_async(_execute_department_cycle(
        company_id,
        department_type,
        task_override=f"The human owner sent this message. Respond and take action:\n\n{message}",
    ))


@celery_app.task(name="run_onboarding")
def run_onboarding(company_id: str, business_idea: str):
    """
    CEO onboarding — the user described their business idea.
    CEO agent ralph-loops on it to create a full business plan.
    """
    return _run_async(_execute_department_cycle(
        company_id,
        "ceo",
        task_override=f"""The human owner just created this company with the following business idea:

"{business_idea}"

Your job is to turn this into a real business plan. Do the following:

1. **Research**: Think about the market, competitors, and target audience
2. **Strategy**: Define the business model, pricing, and go-to-market approach
3. **Update COMPANY.md** with:
   - Refined mission statement
   - Target audience description
   - Business model
   - Revenue strategy
   - Competitive advantages
   - Key metrics to track
4. **Create initial PLAN.md for each department**:
   - departments/developer/PLAN.md — product MVP tasks (checkboxes)
   - departments/marketing/PLAN.md — launch marketing tasks
   - departments/sales/PLAN.md — sales funnel tasks
   - departments/finance/PLAN.md — financial setup tasks
   - departments/support/PLAN.md — customer support setup
5. **Update your own plan** in departments/ceo/PLAN.md

Make the plans specific and actionable. Each task should be small enough for one agent run.
Think like a founder — what's the fastest path to first paying customer?
""",
    ))
