import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.agent_task import AgentTask, TaskCreator
from app.models.company import Company
from app.models.department import Department
from app.models.user import User
from app.schemas.agent import AgentTaskCreate, AgentTaskRead

router = APIRouter(prefix="/api/companies/{company_id}/tasks", tags=["tasks"])


async def _verify_ownership(company_id: uuid.UUID, user: User, db: AsyncSession) -> Company:
    company = await db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    if company.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your company")
    return company


@router.get("", response_model=dict)
async def list_tasks(
    company_id: uuid.UUID,
    status_filter: str | None = Query(None, alias="status"),
    department_type: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _verify_ownership(company_id, current_user, db)

    query = select(AgentTask).where(AgentTask.company_id == company_id)

    if status_filter:
        query = query.where(AgentTask.status == status_filter)
    if department_type:
        query = query.where(AgentTask.assigned_department == department_type)

    query = query.order_by(AgentTask.created_at.desc())
    result = await db.execute(query)
    tasks = list(result.scalars().all())

    return {
        "data": [AgentTaskRead.model_validate(t).model_dump(mode="json") for t in tasks],
        "error": None,
        "meta": {"count": len(tasks)},
    }


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_task(
    company_id: uuid.UUID,
    data: AgentTaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _verify_ownership(company_id, current_user, db)

    # Optionally link to department
    department_id = None
    if data.assigned_department:
        result = await db.execute(
            select(Department).where(
                Department.company_id == company_id,
                Department.type == data.assigned_department,
            )
        )
        department = result.scalar_one_or_none()
        if department:
            department_id = department.id

    task = AgentTask(
        company_id=company_id,
        department_id=department_id,
        title=data.title,
        description=data.description,
        priority=data.priority,
        created_by=TaskCreator.human,
        assigned_department=data.assigned_department,
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)

    return {
        "data": AgentTaskRead.model_validate(task).model_dump(mode="json"),
        "error": None,
        "meta": None,
    }
