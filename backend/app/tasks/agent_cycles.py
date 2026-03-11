"""
Agent lifecycle tasks — real implementations using OpenClaw/Claude.
"""
import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import settings
from app.models.agent_run import AgentRun, RunTrigger, RunStatus
from app.models.agent_task import AgentTask, TaskStatus
from app.models.agent_message import AgentMessage
from app.models.company import Company
from app.models.department import Department, DepartmentType
from app.models.cost_event import CostEvent, CostType
from app.models.user import User
from app.services.openclaw import run_agent_session
from app.services.knowledge_graph import get_context_summary, add_entity
from app.worker import celery_app

logger = logging.getLogger(__name__)

# Create a separate engine for Celery tasks (they run in sync context)
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


async def _get_company_context(db: AsyncSession, company_id: str) -> dict | None:
    """Fetch company + departments + pending tasks + recent chat."""
    company = await db.get(Company, company_id)
    if not company:
        return None

    # Get user for credits check
    user = await db.get(User, company.user_id)

    # Get pending tasks
    result = await db.execute(
        select(AgentTask).where(
            AgentTask.company_id == company_id,
            AgentTask.status.in_([TaskStatus.todo, TaskStatus.in_progress]),
        ).order_by(AgentTask.priority.desc())
    )
    tasks = [
        {"title": t.title, "description": t.description or "", "priority": t.priority.value, "department": t.assigned_department.value if t.assigned_department else "unassigned"}
        for t in result.scalars().all()
    ]

    # Get recent chat messages
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


async def _execute_department_cycle(
    company_id: str,
    department_type: str,
    task_description: str,
    trigger: RunTrigger = RunTrigger.scheduled,
) -> dict:
    """Core logic for running a department agent cycle."""
    session_factory = _get_session_factory()

    async with session_factory() as db:
        ctx = await _get_company_context(db, company_id)
        if not ctx:
            return {"status": "failed", "summary": f"Company {company_id} not found"}

        company = ctx["company"]
        user = ctx["user"]

        # Check credits
        if user and user.credits_balance <= 0:
            return {"status": "failed", "summary": "Insufficient credits"}

        # Get department
        result = await db.execute(
            select(Department).where(
                Department.company_id == company_id,
                Department.type == department_type,
            )
        )
        department = result.scalar_one_or_none()
        if not department:
            return {"status": "failed", "summary": f"Department {department_type} not found"}

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

        # Update department status
        department.status = "running"
        await db.commit()

        # Get knowledge graph context
        kg_context = get_context_summary(company.slug)

        # Filter tasks for this department
        dept_tasks = [
            t for t in ctx["pending_tasks"]
            if t["department"] == department_type or department_type == "ceo"
        ]

    # Run the actual agent (outside db session since it's long-running)
    try:
        agent_result = await run_agent_session(
            company_id=str(company_id),
            company_slug=company.slug,
            company_name=company.name,
            company_mission=company.mission,
            department_type=department_type,
            task_description=task_description,
            knowledge_context=kg_context,
            pending_tasks=dept_tasks,
            chat_history=ctx["chat_history"],
        )
    except Exception as e:
        agent_result = {
            "status": "failed",
            "summary": f"Agent error: {str(e)[:500]}",
            "tokens_used": 0,
            "cost": 0,
        }

    # Update records with results
    async with session_factory() as db:
        run = await db.get(AgentRun, run.id)
        if run:
            run.status = RunStatus.completed if agent_result["status"] != "failed" else RunStatus.failed
            run.completed_at = datetime.now(timezone.utc)
            run.tokens_used = agent_result.get("tokens_used", 0)
            run.cost = Decimal(str(agent_result.get("cost", 0)))
            run.summary = agent_result.get("summary", "")[:2000]

        # Update department status back to idle
        result = await db.execute(
            select(Department).where(
                Department.company_id == company_id,
                Department.type == department_type,
            )
        )
        dept = result.scalar_one_or_none()
        if dept:
            dept.status = "idle"

        # Record cost event
        cost = Decimal(str(agent_result.get("cost", 0)))
        if cost > 0:
            cost_event = CostEvent(
                id=uuid4(),
                company_id=company.id,
                department_id=department.id,
                type=CostType.llm_tokens,
                amount=cost,
                description=f"{department_type} cycle: {agent_result.get('summary', '')[:200]}",
            )
            db.add(cost_event)

            # Deduct from user credits
            user = await db.get(User, company.user_id)
            if user:
                user.credits_balance = max(Decimal("0"), user.credits_balance - cost)

        # Add any entities to knowledge graph
        for entity in agent_result.get("entities_added", []):
            if isinstance(entity, dict) and "type" in entity and "name" in entity:
                add_entity(
                    company.slug,
                    entity["type"],
                    entity["name"],
                    entity.get("properties"),
                    source_department=department_type,
                )

        await db.commit()

    return agent_result


@celery_app.task(name="run_ceo_planning_cycle")
def run_ceo_planning_cycle(company_id: str):
    """CEO reviews goals, creates/assigns tasks. Runs daily."""
    logger.info(f"CEO planning cycle for company {company_id}")
    result = _run_async(
        _execute_department_cycle(
            company_id,
            "ceo",
            """Review the company's current state, progress, and pending tasks.
Create new tasks for departments that need work.
Prioritize the most impactful actions.
Update the knowledge graph with any strategic decisions.""",
            trigger=RunTrigger.scheduled,
        )
    )
    logger.info(f"CEO cycle result: {result.get('status')} - {result.get('summary', '')[:100]}")
    return result


@celery_app.task(name="run_department_execution_cycle")
def run_department_execution_cycle(company_id: str, department_type: str):
    """Department agent wakes up, checks tasks, executes."""
    logger.info(f"{department_type} execution cycle for company {company_id}")
    result = _run_async(
        _execute_department_cycle(
            company_id,
            department_type,
            f"""Check your pending tasks and execute the highest priority one.
If no tasks are assigned to you, look for ways to advance the company mission.
Report what you accomplished.""",
            trigger=RunTrigger.scheduled,
        )
    )
    logger.info(f"{department_type} cycle result: {result.get('status')} - {result.get('summary', '')[:100]}")
    return result


@celery_app.task(name="run_finance_reporting_cycle")
def run_finance_reporting_cycle(company_id: str):
    """Finance agent compiles metrics."""
    logger.info(f"Finance reporting cycle for company {company_id}")
    result = _run_async(
        _execute_department_cycle(
            company_id,
            "finance",
            """Compile today's financial metrics:
- Total agent costs across all departments
- Revenue (if any Stripe events)
- P&L summary
- Budget utilization per department
Update the knowledge graph with today's metrics.""",
            trigger=RunTrigger.scheduled,
        )
    )
    return result


@celery_app.task(name="run_weekly_learning_cycle")
def run_weekly_learning_cycle(company_id: str):
    """All agents review what worked/failed."""
    logger.info(f"Weekly learning cycle for company {company_id}")
    result = _run_async(
        _execute_department_cycle(
            company_id,
            "ceo",
            """Weekly review:
- What worked well this week?
- What failed or underperformed?
- What should we do differently next week?
- Record lessons learned in the knowledge graph.
- Adjust strategy if needed.""",
            trigger=RunTrigger.scheduled,
        )
    )
    return result


@celery_app.task(name="run_chat_response")
def run_chat_response(company_id: str, department_type: str, user_message: str):
    """Handle a chat message from the human owner."""
    logger.info(f"Chat response for {department_type} in company {company_id}")
    result = _run_async(
        _execute_department_cycle(
            company_id,
            department_type,
            f"""The human owner sent you a message. Respond helpfully and take action if requested.

Human message: {user_message}

Respond to their message and take any requested actions.""",
            trigger=RunTrigger.manual,
        )
    )
    return result
