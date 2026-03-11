"""
Agent scheduling service.
Phase 1: Manual triggers only.
Phase 2: Celery Beat dynamic scheduling per company.
"""
import logging

logger = logging.getLogger(__name__)


def schedule_company_cycles(company_id: str):
    """Register periodic tasks for a company. Phase 2 will use celery-beat."""
    logger.info(f"[STUB] Would schedule cycles for company {company_id}")


def unschedule_company_cycles(company_id: str):
    """Remove periodic tasks for a company."""
    logger.info(f"[STUB] Would unschedule cycles for company {company_id}")


def trigger_department_cycle(company_id: str, department_type: str):
    """Manually trigger a department execution cycle."""
    from app.tasks.agent_cycles import run_department_execution_cycle

    task = run_department_execution_cycle.delay(company_id, department_type)
    logger.info(f"Triggered {department_type} cycle for {company_id}, task_id={task.id}")
    return task.id


def trigger_ceo_planning(company_id: str):
    """Manually trigger a CEO planning cycle."""
    from app.tasks.agent_cycles import run_ceo_planning_cycle

    task = run_ceo_planning_cycle.delay(company_id)
    logger.info(f"Triggered CEO planning for {company_id}, task_id={task.id}")
    return task.id
