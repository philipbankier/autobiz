import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company, CompanyStatus
from app.models.department import Department, DepartmentType, AutonomyLevel, DepartmentStatus
from app.schemas.company import CompanyCreate, CompanyUpdate


DEFAULT_DEPARTMENTS = [
    DepartmentType.ceo,
    DepartmentType.developer,
    DepartmentType.marketing,
    DepartmentType.sales,
    DepartmentType.finance,
    DepartmentType.support,
]


async def create_company(db: AsyncSession, user_id: uuid.UUID, data: CompanyCreate) -> Company:
    company = Company(
        user_id=user_id,
        name=data.name,
        mission=data.mission,
        slug=data.slug,
        status=CompanyStatus.planning,
    )
    db.add(company)
    await db.flush()

    for dept_type in DEFAULT_DEPARTMENTS:
        department = Department(
            company_id=company.id,
            type=dept_type,
            autonomy_level=AutonomyLevel.notify,
            status=DepartmentStatus.idle,
        )
        db.add(department)

    await db.flush()
    await db.refresh(company)
    return company


async def list_companies(db: AsyncSession, user_id: uuid.UUID) -> list[Company]:
    result = await db.execute(
        select(Company)
        .where(Company.user_id == user_id, Company.status != CompanyStatus.archived)
        .order_by(Company.created_at.desc())
    )
    return list(result.scalars().all())


async def get_company(db: AsyncSession, company_id: uuid.UUID) -> Company | None:
    return await db.get(Company, company_id)


async def update_company(db: AsyncSession, company: Company, data: CompanyUpdate) -> Company:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)
    await db.flush()
    await db.refresh(company)
    return company


async def archive_company(db: AsyncSession, company: Company) -> Company:
    company.status = CompanyStatus.archived
    await db.flush()
    await db.refresh(company)
    return company
