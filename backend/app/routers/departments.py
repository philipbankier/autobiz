import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.company import Company
from app.models.department import Department, DepartmentType
from app.models.user import User
from app.schemas.department import DepartmentRead, DepartmentUpdate

router = APIRouter(prefix="/api/companies/{company_id}/departments", tags=["departments"])


async def _verify_ownership(company_id: uuid.UUID, user: User, db: AsyncSession) -> Company:
    company = await db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    if company.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your company")
    return company


@router.get("", response_model=dict)
async def list_departments(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _verify_ownership(company_id, current_user, db)
    result = await db.execute(
        select(Department).where(Department.company_id == company_id).order_by(Department.type)
    )
    departments = list(result.scalars().all())
    return {
        "data": [DepartmentRead.model_validate(d).model_dump(mode="json") for d in departments],
        "error": None,
        "meta": {"count": len(departments)},
    }


@router.put("/{dept_type}", response_model=dict)
async def update_department(
    company_id: uuid.UUID,
    dept_type: DepartmentType,
    data: DepartmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _verify_ownership(company_id, current_user, db)
    result = await db.execute(
        select(Department).where(
            Department.company_id == company_id,
            Department.type == dept_type,
        )
    )
    department = result.scalar_one_or_none()
    if department is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(department, field, value)

    await db.flush()
    await db.refresh(department)
    return {
        "data": DepartmentRead.model_validate(department).model_dump(mode="json"),
        "error": None,
        "meta": None,
    }
