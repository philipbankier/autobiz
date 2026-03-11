import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func as sqlfunc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.agent_run import AgentRun, RunStatus
from app.models.agent_task import AgentTask, TaskStatus
from app.models.company import Company
from app.models.cost_event import CostEvent
from app.models.department import Department, DepartmentStatus
from app.models.user import User

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

    # Department statuses
    dept_result = await db.execute(
        select(Department.type, Department.status)
        .where(Department.company_id == company_id)
    )
    departments = [
        {"type": row.type.value, "status": row.status.value}
        for row in dept_result.all()
    ]

    # Active runs count
    active_runs_result = await db.execute(
        select(sqlfunc.count(AgentRun.id))
        .where(AgentRun.company_id == company_id, AgentRun.status == RunStatus.running)
    )
    active_runs = active_runs_result.scalar() or 0

    # Completed runs count
    completed_runs_result = await db.execute(
        select(sqlfunc.count(AgentRun.id))
        .where(AgentRun.company_id == company_id, AgentRun.status == RunStatus.completed)
    )
    completed_runs = completed_runs_result.scalar() or 0

    # Task stats
    task_stats_result = await db.execute(
        select(AgentTask.status, sqlfunc.count(AgentTask.id))
        .where(AgentTask.company_id == company_id)
        .group_by(AgentTask.status)
    )
    task_stats = {row.status.value: row[1] for row in task_stats_result.all()}

    # Total cost
    cost_result = await db.execute(
        select(sqlfunc.sum(CostEvent.amount))
        .where(CostEvent.company_id == company_id)
    )
    total_cost = cost_result.scalar() or Decimal("0")

    return {
        "data": {
            "company_status": company.status.value,
            "departments": departments,
            "active_runs": active_runs,
            "completed_runs": completed_runs,
            "task_stats": task_stats,
            "total_cost": str(total_cost),
            "credits_balance": str(current_user.credits_balance),
        },
        "error": None,
        "meta": None,
    }
