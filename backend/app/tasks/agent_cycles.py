"""
Agent lifecycle tasks — stub implementations for Phase 1.
Phase 2 will replace these with real OpenClaw agent sessions.
"""
import logging
from datetime import datetime, timezone

from app.worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="run_ceo_planning_cycle")
def run_ceo_planning_cycle(company_id: str):
    """CEO reviews goals, creates/assigns tasks. Runs daily at 6 AM."""
    logger.info(f"[STUB] CEO planning cycle for company {company_id}")
    return {
        "status": "stub",
        "company_id": company_id,
        "cycle": "ceo_planning",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@celery_app.task(name="run_department_execution_cycle")
def run_department_execution_cycle(company_id: str, department_type: str):
    """Department agent wakes up, checks tasks, executes. Runs hourly."""
    logger.info(f"[STUB] {department_type} execution cycle for company {company_id}")
    return {
        "status": "stub",
        "company_id": company_id,
        "department": department_type,
        "cycle": "department_execution",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@celery_app.task(name="run_finance_reporting_cycle")
def run_finance_reporting_cycle(company_id: str):
    """Finance agent compiles metrics. Runs daily at 10 PM."""
    logger.info(f"[STUB] Finance reporting cycle for company {company_id}")
    return {
        "status": "stub",
        "company_id": company_id,
        "cycle": "finance_reporting",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@celery_app.task(name="run_weekly_learning_cycle")
def run_weekly_learning_cycle(company_id: str):
    """All agents review what worked/failed. Runs Sundays."""
    logger.info(f"[STUB] Weekly learning cycle for company {company_id}")
    return {
        "status": "stub",
        "company_id": company_id,
        "cycle": "weekly_learning",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
