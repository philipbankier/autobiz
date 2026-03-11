"""
Agent lifecycle tasks — spawns OpenClaw agent sessions via Gateway API.
Each agent gets full OpenClaw capabilities: exec, file access, MCP tools, memory, web search, etc.
"""
import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.config import settings
from app.models.agent_run import AgentRun, RunTrigger, RunStatus
from app.models.agent_task import AgentTask, TaskStatus
from app.models.agent_message import AgentMessage, MessageRole
from app.models.company import Company
from app.models.department import Department, DepartmentType
from app.models.cost_event import CostEvent, CostType
from app.models.user import User
from app.services.openclaw import spawn_agent_session
from app.worker import celery_app

logger = logging.getLogger(__name__)

_engine = None
_session_factory = None


def _get_session_factory():
    global _engine, _session_factory
    if _engine is None:
        _engine = create_async_engine(settings.DATABASE_URL)
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _session_factory


def _run_async(coro):
    """Run async code from sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _get_company_context(db, company_id: str) -> dict | None:
    """Fetch company + pending tasks + recent chat for agent context."""
    company = await db.get(Company, company_id)
    if not company:
        return None

    user = await db.get(User, company.user_id)

    # Get pending tasks
    result = await db.execute(
        select(AgentTask).where(
            AgentTask.company_id == company_id,
            AgentTask.status.in_([TaskStatus.todo, TaskStatus.in_progress]),
        ).order_by(AgentTask.priority.desc()).limit(20)
    )
    tasks = [
        {"title": t.title, "description": t.description or "", "priority": t.priority.value,
         "department": t.assigned_department.value if t.assigned_department else "unassigned"}
        for t in result.scalars().all()
    ]

    # Get recent chat
    result = await db.execute(
        select(AgentMessage).where(
            AgentMessage.company_id == company_id,
        ).order_by(AgentMessage.created_at.desc()).limit(10)
    )
    chat = [
        {"role": m.role.value, "content": m.content}
        for m in reversed(list(result.scalars().all()))
    ]

    return {
        "company": company,
        "user": user,
        "pending_tasks": tasks,
        "chat_history": chat,
    }


async def _spawn_department(
    company_id: str,
    department_type: str,
    task_description: str,
    trigger: RunTrigger = RunTrigger.scheduled,
) -> dict:
    """Spawn an OpenClaw agent session for a department."""
    session_factory = _get_session_factory()

    async with session_factory() as db:
        ctx = await _get_company_context(db, company_id)
        if not ctx:
            return {"status": "error", "message": f"Company {company_id} not found"}

        company = ctx["company"]
        user = ctx["user"]

        # Credits check
        if user and user.credits_balance <= 0:
            return {"status": "error", "message": "Insufficient credits"}

        # Get department
        result = await db.execute(
            select(Department).where(
                Department.company_id == company_id,
                Department.type == department_type,
            )
        )
        department = result.scalar_one_or_none()
        if not department:
            return {"status": "error", "message": f"Department {department_type} not found"}

        # Create agent run record
        run = AgentRun(
            id=uuid4(),
            department_id=department.id,
            company_id=company.id,
            trigger=trigger,
            status=RunStatus.running,
            started_at=datetime.now(timezone.utc),
        )
        db.add(run)
        department.status = "running"
        await db.commit()

        # Filter tasks for this department
        dept_tasks = [
            t for t in ctx["pending_tasks"]
            if t["department"] == department_type or department_type == "ceo"
        ]

    # Spawn via OpenClaw Gateway
    spawn_result = await spawn_agent_session(
        company_id=str(company_id),
        company_slug=company.slug,
        company_name=company.name,
        company_mission=company.mission,
        department_type=department_type,
        task_description=task_description,
        pending_tasks=dept_tasks,
        chat_history=ctx["chat_history"],
    )

    # Update run with spawn result
    async with session_factory() as db:
        run_record = await db.get(AgentRun, run.id)
        if run_record:
            if spawn_result.get("status") == "accepted":
                run_record.summary = f"Agent spawned: session={spawn_result.get('session_key', '?')}"
                # Agent is now running async — status stays "running"
                # Results will come back via announce or polling
            else:
                run_record.status = RunStatus.failed
                run_record.completed_at = datetime.now(timezone.utc)
                run_record.summary = spawn_result.get("message", "Spawn failed")

        # Reset department status if spawn failed
        if spawn_result.get("status") != "accepted":
            result = await db.execute(
                select(Department).where(
                    Department.company_id == company_id,
                    Department.type == department_type,
                )
            )
            dept = result.scalar_one_or_none()
            if dept:
                dept.status = "idle"

        await db.commit()

    logger.info(f"Spawn result for {department_type}/{company.slug}: {spawn_result.get('status')}")
    return spawn_result


@celery_app.task(name="run_ceo_planning_cycle")
def run_ceo_planning_cycle(company_id: str):
    """CEO reviews goals, creates/assigns tasks. Runs daily."""
    logger.info(f"CEO planning cycle for company {company_id}")
    return _run_async(
        _spawn_department(
            company_id, "ceo",
            """Review the company's current state by reading COMPANY.md and MEMORY.md.
Then:
1. Assess progress toward the mission
2. Identify the highest-priority work needed right now
3. Create task files in the workspace for other departments
4. Update COMPANY.md with any strategic adjustments
5. Update MEMORY.md with your observations""",
            trigger=RunTrigger.scheduled,
        )
    )


@celery_app.task(name="run_department_execution_cycle")
def run_department_execution_cycle(company_id: str, department_type: str):
    """Department agent wakes up, checks tasks, executes."""
    logger.info(f"{department_type} execution cycle for company {company_id}")
    return _run_async(
        _spawn_department(
            company_id, department_type,
            f"""Check your pending tasks and execute the highest priority one.
Read COMPANY.md for current context and MEMORY.md for your past work.
If no tasks are assigned to you, look for ways to advance the company mission.
Update MEMORY.md with what you accomplished.""",
            trigger=RunTrigger.scheduled,
        )
    )


@celery_app.task(name="run_finance_reporting_cycle")
def run_finance_reporting_cycle(company_id: str):
    """Finance agent compiles metrics."""
    logger.info(f"Finance reporting cycle for company {company_id}")
    return _run_async(
        _spawn_department(
            company_id, "finance",
            """Compile a daily financial report:
- Read any cost/revenue data available in the workspace
- Summarize total agent costs, revenue (if any), and profit
- Update knowledge/graph.jsonl with today's metrics
- Write a brief report to content/finance-report.md
- Update MEMORY.md with financial observations""",
            trigger=RunTrigger.scheduled,
        )
    )


@celery_app.task(name="run_weekly_learning_cycle")
def run_weekly_learning_cycle(company_id: str):
    """Weekly retrospective."""
    logger.info(f"Weekly learning cycle for company {company_id}")
    return _run_async(
        _spawn_department(
            company_id, "ceo",
            """Weekly retrospective:
1. Read COMPANY.md and MEMORY.md
2. What worked well this week?
3. What failed or underperformed?
4. What should we do differently next week?
5. Update MEMORY.md with lessons learned
6. Update COMPANY.md with revised strategy if needed""",
            trigger=RunTrigger.scheduled,
        )
    )


@celery_app.task(name="run_chat_response")
def run_chat_response(company_id: str, department_type: str, user_message: str):
    """Handle a chat message from the human owner."""
    logger.info(f"Chat response for {department_type} in company {company_id}")
    return _run_async(
        _spawn_department(
            company_id, department_type,
            f"""The human owner sent you a message. Read it, respond helpfully, and take action if requested.

Human message: {user_message}

After taking action, update MEMORY.md with any important context from this interaction.""",
            trigger=RunTrigger.manual,
        )
    )
