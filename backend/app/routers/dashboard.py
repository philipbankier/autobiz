import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.company import Company
from app.models.department import Department
from app.models.agent_run import AgentRun, RunStatus
from app.models.agent_task import AgentTask, TaskStatus
from app.models.cost_event import CostEvent, CostType
from app.models.user import User
from app.services.knowledge_graph import get_stats as kg_stats

router = APIRouter(prefix="/api/companies/{company_id}/dashboard", tags=["dashboard"])


@router.get("", response_model=dict)
async def get_dashboard(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = await db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    if company.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your company")

    # Department status
    result = await db.execute(
        select(Department).where(Department.company_id == company_id)
    )
    departments = [
        {"type": d.type.value, "status": d.status, "autonomy": d.autonomy_level.value}
        for d in result.scalars().all()
    ]

    # Agent runs stats
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())

    # Active runs
    result = await db.execute(
        select(func.count()).select_from(AgentRun).where(
            AgentRun.company_id == company_id,
            AgentRun.status == RunStatus.running,
        )
    )
    active_runs = result.scalar()

    # Completed runs (all time)
    result = await db.execute(
        select(func.count()).select_from(AgentRun).where(
            AgentRun.company_id == company_id,
            AgentRun.status == RunStatus.completed,
        )
    )
    completed_runs = result.scalar()

    # Completed runs today
    result = await db.execute(
        select(func.count()).select_from(AgentRun).where(
            AgentRun.company_id == company_id,
            AgentRun.status == RunStatus.completed,
            AgentRun.started_at >= today_start,
        )
    )
    runs_today = result.scalar()

    # Failed runs
    result = await db.execute(
        select(func.count()).select_from(AgentRun).where(
            AgentRun.company_id == company_id,
            AgentRun.status == RunStatus.failed,
        )
    )
    failed_runs = result.scalar()

    # Task stats
    result = await db.execute(
        select(AgentTask.status, func.count()).where(
            AgentTask.company_id == company_id,
        ).group_by(AgentTask.status)
    )
    task_stats = {row[0].value: row[1] for row in result.all()}

    # Cost breakdown
    result = await db.execute(
        select(func.coalesce(func.sum(CostEvent.amount), 0)).where(
            CostEvent.company_id == company_id,
        )
    )
    total_cost = float(result.scalar())

    # Cost today
    result = await db.execute(
        select(func.coalesce(func.sum(CostEvent.amount), 0)).where(
            CostEvent.company_id == company_id,
            CostEvent.created_at >= today_start,
        )
    )
    cost_today = float(result.scalar())

    # Cost this week
    result = await db.execute(
        select(func.coalesce(func.sum(CostEvent.amount), 0)).where(
            CostEvent.company_id == company_id,
            CostEvent.created_at >= week_start,
        )
    )
    cost_this_week = float(result.scalar())

    # Cost by department
    result = await db.execute(
        select(Department.type, func.coalesce(func.sum(CostEvent.amount), 0)).join(
            Department, CostEvent.department_id == Department.id
        ).where(
            CostEvent.company_id == company_id,
        ).group_by(Department.type)
    )
    cost_by_dept = {row[0].value: float(row[1]) for row in result.all()}

    # Recent runs (last 5)
    result = await db.execute(
        select(AgentRun).where(
            AgentRun.company_id == company_id,
        ).order_by(AgentRun.started_at.desc()).limit(5)
    )
    recent_runs = []
    for run in result.scalars().all():
        # Get department type
        dept = await db.get(Department, run.department_id)
        recent_runs.append({
            "id": str(run.id),
            "department": dept.type.value if dept else "unknown",
            "status": run.status.value,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "summary": run.summary[:200] if run.summary else None,
            "cost": str(run.cost) if run.cost else "0",
        })

    # Knowledge graph stats
    knowledge = kg_stats(company.slug)

    # Credits balance
    user = await db.get(User, company.user_id)
    credits = str(user.credits_balance) if user else "0"

    return {
        "data": {
            "company_status": company.status.value,
            "departments": departments,
            # Agent metrics
            "active_runs": active_runs,
            "completed_runs": completed_runs,
            "runs_today": runs_today,
            "failed_runs": failed_runs,
            # Task metrics
            "task_stats": task_stats,
            "total_tasks": sum(task_stats.values()),
            # Financial metrics
            "total_cost": f"{total_cost:.4f}",
            "cost_today": f"{cost_today:.4f}",
            "cost_this_week": f"{cost_this_week:.4f}",
            "cost_by_department": cost_by_dept,
            # Revenue (Phase 3+)
            "total_revenue": "0.00",
            "mrr": "0.00",
            "customers": 0,
            "profit": f"{-total_cost:.4f}",
            # Knowledge graph
            "knowledge_graph": knowledge,
            # Account
            "credits_balance": credits,
            # Recent activity
            "recent_runs": recent_runs,
        },
        "error": None,
        "meta": None,
    }
