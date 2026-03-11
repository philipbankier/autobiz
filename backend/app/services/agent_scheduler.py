"""
Agent scheduler service — stub for Celery task scheduling.
Actual OpenClaw integration will be implemented in a later phase.
"""

import uuid
from datetime import datetime, timezone


async def schedule_agent_run(
    company_id: uuid.UUID,
    department_id: uuid.UUID,
    trigger: str = "manual",
) -> dict:
    """Stub: Schedule an agent run via Celery. Returns placeholder data."""
    return {
        "run_id": uuid.uuid4(),
        "company_id": company_id,
        "department_id": department_id,
        "trigger": trigger,
        "status": "pending",
        "scheduled_at": datetime.now(timezone.utc).isoformat(),
        "message": "Agent run scheduled (stub — OpenClaw integration pending)",
    }


async def cancel_agent_run(run_id: uuid.UUID) -> dict:
    """Stub: Cancel a scheduled or running agent run."""
    return {
        "run_id": run_id,
        "status": "cancelled",
        "message": "Agent run cancelled (stub — OpenClaw integration pending)",
    }
