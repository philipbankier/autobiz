import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.agent_message import AgentMessage, MessageRole
from app.models.company import Company
from app.models.department import Department
from app.models.user import User
from app.schemas.agent import AgentMessageCreate, AgentMessageRead

router = APIRouter(prefix="/api/companies/{company_id}/chat", tags=["chat"])


async def _verify_ownership(company_id: uuid.UUID, user: User, db: AsyncSession) -> Company:
    company = await db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    if company.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your company")
    return company


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def send_message(
    company_id: uuid.UUID,
    data: AgentMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _verify_ownership(company_id, current_user, db)

    # Find the department by type
    result = await db.execute(
        select(Department).where(
            Department.company_id == company_id,
            Department.type == data.department_type,
        )
    )
    department = result.scalar_one_or_none()
    if department is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    # Save user message
    user_msg = AgentMessage(
        company_id=company_id,
        department_id=department.id,
        role=MessageRole.user,
        content=data.content,
    )
    db.add(user_msg)
    await db.flush()
    await db.refresh(user_msg)

    # Stub: In production, this would trigger an agent run and return the response.
    # For now, create a placeholder agent response.
    agent_msg = AgentMessage(
        company_id=company_id,
        department_id=department.id,
        role=MessageRole.agent,
        content=f"[Stub] Received your message in the {data.department_type.value} department. "
                f"Agent integration pending.",
    )
    db.add(agent_msg)
    await db.flush()
    await db.refresh(agent_msg)

    return {
        "data": {
            "user_message": AgentMessageRead.model_validate(user_msg).model_dump(mode="json"),
            "agent_message": AgentMessageRead.model_validate(agent_msg).model_dump(mode="json"),
        },
        "error": None,
        "meta": None,
    }


@router.get("", response_model=dict)
async def get_chat_history(
    company_id: uuid.UUID,
    department_type: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _verify_ownership(company_id, current_user, db)

    query = select(AgentMessage).where(AgentMessage.company_id == company_id)

    if department_type:
        dept_result = await db.execute(
            select(Department).where(
                Department.company_id == company_id,
                Department.type == department_type,
            )
        )
        department = dept_result.scalar_one_or_none()
        if department:
            query = query.where(AgentMessage.department_id == department.id)

    query = query.order_by(AgentMessage.created_at.desc()).limit(limit)
    result = await db.execute(query)
    messages = list(result.scalars().all())
    messages.reverse()  # Return in chronological order

    return {
        "data": [AgentMessageRead.model_validate(m).model_dump(mode="json") for m in messages],
        "error": None,
        "meta": {"count": len(messages)},
    }
