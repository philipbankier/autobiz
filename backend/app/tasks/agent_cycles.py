"""
Celery tasks for agent department cycles.
Implements:
- Budget check before every run
- Model tiering per department
- Ralph loop task execution (one task per run)
- Post-run quality gates (LLM judge)
- Post-run memory consolidation (async)
"""
import asyncio
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.worker import celery_app
from app.database import async_session
from app.models.agent_run import AgentRun, RunStatus
from app.models.company import Company
from app.models.department import Department, DepartmentType, DepartmentStatus
from app.models.cost_event import CostType
from app.services.openclaw import spawn_agent_session
from app.services.cost_control import (
    check_budget,
    record_cost,
    estimate_cost,
    get_model_for_department,
)
from app.services.site_deploy import deploy_to_vercel, copy_site_to_code
from app.services.git_service import git_commit, git_push, git_status
from app.services.event_bus import publish_sync, EventType
from app.services.judge import evaluate_output, should_give_up, consolidate_memory
from app.services.retry_tracker import (
    get_retry_count,
    get_attempt_history,
    increment_retry,
    clear_retry,
    _task_id,
)

logger = logging.getLogger(__name__)

COMPANIES_DIR = Path(os.environ.get("COMPANIES_DIR", "/app/companies"))


def _run_async(coro):
    """Helper to run async code in sync Celery tasks."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _post_run_deploy(slug: str) -> dict:
    """Auto-deploy after a developer agent run if files changed."""
    status = await git_status(slug)
    if not status.get("has_changes"):
        return {"status": "no_changes"}

    # Copy site/ into code/ if site files exist
    copied = copy_site_to_code(slug)

    # Commit and push
    commit_result = await git_commit(slug, "auto-deploy: developer agent changes")
    if commit_result["status"] == "error":
        return commit_result

    if commit_result["status"] == "no_changes":
        return {"status": "no_changes"}

    push_result = await git_push(slug)
    if push_result["status"] == "error":
        return push_result

    return {
        "status": "deployed",
        "commit": commit_result.get("sha"),
        "branch": push_result.get("branch"),
        "files_copied": len(copied),
    }


async def _dispatch_queued_content(slug: str) -> dict:
    """
    After marketing/sales/support agent runs, check for queued content
    in content/tweets.json, content/linkedin.json, and content/emails.json.
    Process pending items and update their status.
    """
    import json
    from pathlib import Path
    from datetime import datetime, timezone as tz

    content_dir = COMPANIES_DIR / slug / "content"
    results = {"dispatched": 0, "tweets": 0, "linkedin": 0, "emails": 0, "errors": []}

    # ── Tweets ──
    tweets_file = content_dir / "tweets.json"
    if tweets_file.exists():
        try:
            entries = json.loads(tweets_file.read_text())
            from app.services.social_media import post_tweet

            changed = False
            for entry in entries:
                if entry.get("status") != "pending":
                    continue
                result = await post_tweet(slug, entry["text"])
                if result["status"] == "ok":
                    entry["status"] = "sent"
                    entry["sent_at"] = datetime.now(tz.utc).isoformat()
                    entry["tweet_id"] = result.get("tweet_id")
                    results["tweets"] += 1
                    results["dispatched"] += 1
                else:
                    entry["status"] = "failed"
                    entry["error"] = result.get("message")
                    results["errors"].append(f"tweet: {result.get('message')}")
                changed = True

            if changed:
                tweets_file.write_text(json.dumps(entries, indent=2))
        except Exception as e:
            results["errors"].append(f"tweets.json: {e}")

    # ── LinkedIn ──
    linkedin_file = content_dir / "linkedin.json"
    if linkedin_file.exists():
        try:
            entries = json.loads(linkedin_file.read_text())
            from app.services.social_media import post_linkedin

            changed = False
            for entry in entries:
                if entry.get("status") != "pending":
                    continue
                result = await post_linkedin(slug, entry["text"])
                if result["status"] == "ok":
                    entry["status"] = "sent"
                    entry["sent_at"] = datetime.now(tz.utc).isoformat()
                    entry["post_id"] = result.get("post_id")
                    results["linkedin"] += 1
                    results["dispatched"] += 1
                else:
                    entry["status"] = "failed"
                    entry["error"] = result.get("message")
                    results["errors"].append(f"linkedin: {result.get('message')}")
                changed = True

            if changed:
                linkedin_file.write_text(json.dumps(entries, indent=2))
        except Exception as e:
            results["errors"].append(f"linkedin.json: {e}")

    # ── Emails ──
    emails_file = content_dir / "emails.json"
    if emails_file.exists():
        try:
            entries = json.loads(emails_file.read_text())
            from app.services.email_service import send_email

            changed = False
            for entry in entries:
                if entry.get("status") != "pending":
                    continue
                result = await send_email(
                    slug,
                    to=entry["to"],
                    subject=entry["subject"],
                    html_body=entry["html_body"],
                    text_body=entry.get("text_body"),
                )
                if result["status"] == "ok":
                    entry["status"] = "sent"
                    entry["sent_at"] = datetime.now(tz.utc).isoformat()
                    entry["email_id"] = result.get("email_id")
                    results["emails"] += 1
                    results["dispatched"] += 1
                else:
                    entry["status"] = "failed"
                    entry["error"] = result.get("message")
                    results["errors"].append(f"email: {result.get('message')}")
                changed = True

            if changed:
                emails_file.write_text(json.dumps(entries, indent=2))
        except Exception as e:
            results["errors"].append(f"emails.json: {e}")

    return results


def _read_plan_md(slug: str, dept: str) -> str:
    """Read a department's PLAN.md, return content or empty string."""
    path = COMPANIES_DIR / slug / "departments" / dept / "PLAN.md"
    if path.exists():
        return path.read_text()
    return ""


def _find_current_task(plan_content: str) -> str | None:
    """Find the first checked task in PLAN.md (most recently completed)."""
    # Look for the last `[x]` checkbox line — that's what the agent just did
    matches = re.findall(r"- \[x\]\s+(.+)", plan_content, re.IGNORECASE)
    return matches[-1].strip() if matches else None


def _revert_task_checkbox(slug: str, dept: str, task_text: str) -> None:
    """Revert a task from [x] back to [ ] in PLAN.md."""
    path = COMPANIES_DIR / slug / "departments" / dept / "PLAN.md"
    if not path.exists():
        return
    content = path.read_text()
    # Replace the specific checked task back to unchecked
    content = content.replace(f"- [x] {task_text}", f"- [ ] {task_text}", 1)
    path.write_text(content)


def _mark_task_blocked(slug: str, dept: str, task_text: str, note: str) -> None:
    """Mark a task as blocked [!] in PLAN.md with a note."""
    path = COMPANIES_DIR / slug / "departments" / dept / "PLAN.md"
    if not path.exists():
        return
    content = path.read_text()
    replacement = f"- [!] {task_text}\n  <!-- BLOCKED: {note} -->"
    # Try checked first, then unchecked
    if f"- [x] {task_text}" in content:
        content = content.replace(f"- [x] {task_text}", replacement, 1)
    elif f"- [ ] {task_text}" in content:
        content = content.replace(f"- [ ] {task_text}", replacement, 1)
    path.write_text(content)


def _add_task_comment(slug: str, dept: str, task_text: str, comment: str) -> None:
    """Add a comment below a task in PLAN.md."""
    path = COMPANIES_DIR / slug / "departments" / dept / "PLAN.md"
    if not path.exists():
        return
    content = path.read_text()
    target = f"- [ ] {task_text}"
    if target in content:
        content = content.replace(target, f"{target}\n  <!-- Judge: {comment} -->", 1)
        path.write_text(content)


async def _run_quality_gate(
    slug: str,
    company_name: str,
    company_id: str,
    department_type: str,
    task_description: str,
    session_output: str,
) -> dict:
    """
    Post-run quality gate: evaluate output, handle retries, consolidate memory.
    Returns {passed: bool, feedback: str, action: str}.
    """
    # Read the plan to find what task was just completed
    plan_content = _read_plan_md(slug, department_type)
    current_task = _find_current_task(plan_content)
    task_text = current_task or task_description

    # Use agent output or session output for evaluation
    eval_text = session_output or f"Task completed: {task_text}"

    # Run judge evaluation
    judge_result = await evaluate_output(
        department_type=department_type,
        company_name=company_name,
        task_description=task_text,
        agent_output=eval_text,
    )

    tid = _task_id(task_text)

    if not judge_result["pass"]:
        # FAIL path
        feedback = judge_result.get("feedback", "Quality below threshold")
        score = judge_result.get("overall", 0)

        # Revert the task checkbox
        if current_task:
            _revert_task_checkbox(slug, department_type, current_task)
            _add_task_comment(slug, department_type, current_task, feedback)

        # Track retry
        attempt_count = increment_retry(slug, department_type, tid, feedback)

        if attempt_count >= 3:
            # Check if we should give up
            history = get_attempt_history(slug, department_type, tid)
            give_up_result = await should_give_up(task_text, history)

            if give_up_result["give_up"]:
                if current_task:
                    _mark_task_blocked(
                        slug, department_type, current_task,
                        f"Gave up after {attempt_count} attempts: {give_up_result['reason']}"
                    )
                clear_retry(slug, department_type, tid)

                publish_sync(
                    company_id, EventType.agent_failed,
                    department=department_type,
                    message=f"Task blocked after {attempt_count} attempts: {task_text[:80]}",
                    data={
                        "task": task_text,
                        "attempts": attempt_count,
                        "reason": give_up_result["reason"],
                        "action": "blocked",
                    },
                )
                return {"passed": False, "feedback": feedback, "action": "blocked"}

        publish_sync(
            company_id, EventType.agent_failed,
            department=department_type,
            message=f"Judge failed (score {score}/10): {feedback[:100]}",
            data={
                "task": task_text,
                "score": score,
                "attempt": attempt_count,
                "feedback": feedback,
                "action": "retry",
            },
        )
        return {"passed": False, "feedback": feedback, "action": "retry"}

    # PASS path — consolidate memory
    if current_task:
        clear_retry(slug, department_type, tid)

    memory_path = COMPANIES_DIR / slug / "departments" / department_type / "MEMORY.md"
    current_memory = memory_path.read_text() if memory_path.exists() else ""

    try:
        updated_memory = await consolidate_memory(
            company_name=company_name,
            department_type=department_type,
            session_output=eval_text,
            current_memory=current_memory,
        )
        if updated_memory and updated_memory != current_memory:
            memory_path.parent.mkdir(parents=True, exist_ok=True)
            memory_path.write_text(updated_memory)
            logger.info(f"[{slug}/{department_type}] Memory consolidated")
    except Exception as e:
        logger.warning(f"[{slug}/{department_type}] Memory consolidation failed: {e}")

    publish_sync(
        company_id, EventType.agent_completed,
        department=department_type,
        message=f"Judge passed (score {judge_result['overall']}/10)",
        data={
            "task": task_text,
            "score": judge_result["overall"],
            "feedback": judge_result.get("feedback", ""),
        },
    )
    return {"passed": True, "feedback": judge_result.get("feedback", ""), "action": "completed"}


async def _execute_department_cycle(
    company_id: str,
    department_type: str,
    task_override: str | None = None,
) -> dict:
    """Core logic for running a department agent cycle."""
    async with async_session() as db:
        # Load company and department
        company = await db.get(Company, uuid.UUID(company_id))
        if not company:
            return {"status": "error", "message": f"Company {company_id} not found"}

        result = await db.execute(
            select(Department).where(
                Department.company_id == company.id,
                Department.type == DepartmentType(department_type),
            )
        )
        department = result.scalar_one_or_none()
        if not department:
            return {"status": "error", "message": f"Department {department_type} not found"}

        # 1. BUDGET CHECK
        budget_status = await check_budget(db, department)
        if not budget_status["allowed"]:
            logger.warning(
                f"[{company.slug}/{department_type}] Budget exceeded: "
                f"${budget_status['spend']:.2f}/${budget_status['budget']:.2f}"
            )
            return {
                "status": "budget_exceeded",
                "spend": str(budget_status["spend"]),
                "budget": str(budget_status["budget"]),
            }

        if budget_status["warning"]:
            logger.info(f"[{company.slug}/{department_type}] {budget_status['warning']}")

        # Emit budget warning event
        if budget_status["warning"] and budget_status["allowed"]:
            publish_sync(
                company_id, EventType.budget_warning,
                department=department_type,
                message=budget_status["warning"],
                data={"spend": str(budget_status["spend"]), "budget": str(budget_status["budget"]), "pct": budget_status["pct"]},
            )
        elif not budget_status["allowed"]:
            publish_sync(
                company_id, EventType.budget_exceeded,
                department=department_type,
                message=budget_status["warning"] or "Budget exceeded",
                data={"spend": str(budget_status["spend"]), "budget": str(budget_status["budget"])},
            )

        # 2. CREATE AGENT RUN RECORD
        from app.models.agent_run import RunTrigger
        agent_run = AgentRun(
            company_id=company.id,
            department_id=department.id,
            trigger=RunTrigger.manual if task_override else RunTrigger.scheduled,
            status=RunStatus.running,
        )
        db.add(agent_run)

        # Mark department as running
        department.status = DepartmentStatus.running
        await db.flush()
        await db.commit()

        # Emit agent_started event
        publish_sync(
            company_id, EventType.agent_started,
            department=department_type,
            message=f"{department_type} agent cycle started",
        )

        # 3. BUILD TASK DESCRIPTION
        task = task_override or (
            f"Check your PLAN.md for the next unchecked task and execute it. "
            f"If no tasks exist, review COMPANY.md and create an initial plan "
            f"in departments/{department_type}/PLAN.md."
        )

        # 4. SPAWN AGENT (with model tiering)
        model = get_model_for_department(department_type)
        
        try:
            spawn_result = await spawn_agent_session(
                company_id=str(company.id),
                company_slug=company.slug,
                company_name=company.name,
                company_mission=company.mission or "",
                department_type=department_type,
                task_description=task,
                model=model,
                timeout_seconds=300,
            )
        except Exception as e:
            logger.error(f"[{company.slug}/{department_type}] Spawn failed: {e}")
            spawn_result = {"status": "error", "message": str(e)}

        # 5. UPDATE RUN STATUS
        async with async_session() as db2:
            run = await db2.get(AgentRun, agent_run.id)
            dept = await db2.get(Department, department.id)

            if spawn_result.get("status") == "accepted":
                run.status = RunStatus.completed
                if dept:
                    dept.agent_session_id = spawn_result.get("session_key")
                    dept.status = DepartmentStatus.idle

                # 6. RECORD ESTIMATED COST
                # Estimate ~5K input + ~2K output tokens per run
                estimated_cost = estimate_cost(model, 5000, 2000)
                await record_cost(
                    db2,
                    company_id=company.id,
                    department_id=department.id,
                    cost_type=CostType.llm_tokens,
                    amount=estimated_cost,
                    description=f"{department_type} cycle run (estimated)",
                )
            else:
                run.status = RunStatus.failed
                run.error = spawn_result.get("message", "Unknown error")
                if dept:
                    dept.status = DepartmentStatus.idle

            await db2.commit()

        # Run quality gate on successful runs, emit failure event on spawn errors
        judge_result = None
        if spawn_result.get("status") == "accepted":
            try:
                session_output = spawn_result.get("output", "") or spawn_result.get("result", "")
                judge_result = await _run_quality_gate(
                    slug=company.slug,
                    company_name=company.name,
                    company_id=company_id,
                    department_type=department_type,
                    task_description=task,
                    session_output=str(session_output),
                )
            except Exception as e:
                logger.warning(f"[{company.slug}/{department_type}] Quality gate error, defaulting to pass: {e}")
                publish_sync(
                    company_id, EventType.agent_completed,
                    department=department_type,
                    message=f"{department_type} agent cycle completed (judge skipped)",
                    data={"model": model},
                )
        else:
            publish_sync(
                company_id, EventType.agent_failed,
                department=department_type,
                message=f"{department_type} agent cycle failed: {spawn_result.get('message', 'Unknown error')}",
                data={"error": spawn_result.get("message")},
            )

        # 7. POST-RUN CONTENT DISPATCH (marketing, sales, support)
        if department_type in ("marketing", "sales", "support") and spawn_result.get("status") == "accepted":
            try:
                dispatch_result = await _dispatch_queued_content(company.slug)
                if dispatch_result.get("dispatched"):
                    logger.info(f"[{company.slug}/{department_type}] Content dispatched: {dispatch_result}")
            except Exception as e:
                logger.error(f"[{company.slug}/{department_type}] Content dispatch failed: {e}")

        # 8. POST-RUN DEPLOY HOOK (developer only)
        deploy_result = None
        if department_type == "developer" and spawn_result.get("status") == "accepted":
            publish_sync(
                company_id, EventType.deploy_started,
                department="developer",
                message="Auto-deploy started after developer changes",
            )
            try:
                deploy_result = await _post_run_deploy(company.slug)
                if deploy_result.get("status") == "deployed":
                    logger.info(f"[{company.slug}/developer] Auto-deployed: {deploy_result.get('commit')}")
                    publish_sync(
                        company_id, EventType.deploy_completed,
                        department="developer",
                        message=f"Deploy completed: {deploy_result.get('commit', '')[:8]}",
                        data=deploy_result,
                    )
            except Exception as e:
                logger.error(f"[{company.slug}/developer] Post-run deploy failed: {e}")
                deploy_result = {"status": "error", "message": str(e)}

        result = {
            "status": spawn_result.get("status"),
            "department": department_type,
            "company": company.slug,
            "model": model,
            "budget": {
                "spend": str(budget_status["spend"]),
                "budget": str(budget_status["budget"]),
                "pct": budget_status["pct"],
            },
            **spawn_result,
        }
        if judge_result:
            result["judge"] = judge_result
        if deploy_result:
            result["deploy"] = deploy_result
        return result


@celery_app.task(name="run_department_execution_cycle")
def run_department_execution_cycle(company_id: str, department_type: str, task: str | None = None):
    """Celery task: Execute a single department cycle."""
    return _run_async(_execute_department_cycle(company_id, department_type, task))


@celery_app.task(name="run_ceo_planning_cycle")
def run_ceo_planning_cycle(company_id: str):
    """
    CEO planning cycle — runs with Opus model.
    Creates/updates strategic plan and assigns tasks to departments.
    """
    return _run_async(_execute_department_cycle(
        company_id,
        "ceo",
        task_override=(
            "Review the company's current state in COMPANY.md and all department PLAN.md files. "
            "Then:\n"
            "1. Update COMPANY.md with any strategic changes\n"
            "2. Review each department's progress (check completed vs pending tasks)\n"
            "3. Add new tasks to department PLAN.md files as needed\n"
            "4. Prioritize: what's the single most important thing for each department today?\n"
            "5. Update your own departments/ceo/PLAN.md with your strategic tasks"
        ),
    ))


@celery_app.task(name="run_finance_reporting_cycle")
def run_finance_reporting_cycle(company_id: str):
    """Finance reporting cycle — runs daily."""
    return _run_async(_execute_department_cycle(
        company_id,
        "finance",
        task_override=(
            "Generate a daily financial summary:\n"
            "1. Check agent spending records in your memory\n"
            "2. Check Stripe for any revenue (if configured)\n"
            "3. Calculate burn rate and runway\n"
            "4. Update departments/finance/PLAN.md with any action items\n"
            "5. Write a brief report to COMPANY.md under ## Latest Financial Report"
        ),
    ))


@celery_app.task(name="run_weekly_learning_cycle")
def run_weekly_learning_cycle(company_id: str):
    """Weekly learning cycle — all departments reflect and consolidate."""
    results = []
    for dept in ["ceo", "developer", "marketing", "finance"]:
        result = _run_async(_execute_department_cycle(
            company_id,
            dept,
            task_override=(
                "Weekly reflection:\n"
                "1. Review your department's MEMORY.md\n"
                "2. What worked well this week? What didn't?\n"
                "3. What should we change for next week?\n"
                "4. Update MEMORY.md with lessons learned\n"
                "5. Suggest improvements to COMPANY.md strategy"
            ),
        ))
        results.append({dept: result})
    return results


@celery_app.task(name="run_chat_response")
def run_chat_response(company_id: str, department_type: str, message: str):
    """Handle a chat message from the user — route to appropriate department."""
    return _run_async(_execute_department_cycle(
        company_id,
        department_type,
        task_override=f"The human owner sent this message. Respond and take action:\n\n{message}",
    ))


@celery_app.task(name="run_onboarding")
def run_onboarding(company_id: str, business_idea: str):
    """
    CEO onboarding — the user described their business idea.
    CEO agent ralph-loops on it to create a full business plan.
    Then auto-registers cron jobs so the company runs autonomously.
    """
    result = _run_async(_execute_department_cycle(
        company_id,
        "ceo",
        task_override=f"""The human owner just created this company with the following business idea:

"{business_idea}"

Your job is to turn this into a real business plan. Do the following:

1. **Research**: Think about the market, competitors, and target audience
2. **Strategy**: Define the business model, pricing, and go-to-market approach
3. **Update COMPANY.md** with:
   - Refined mission statement
   - Target audience description
   - Business model
   - Revenue strategy
   - Competitive advantages
   - Key metrics to track
4. **Create initial PLAN.md for each department**:
   - departments/developer/PLAN.md — product MVP tasks (checkboxes)
   - departments/marketing/PLAN.md — launch marketing tasks
   - departments/sales/PLAN.md — sales funnel tasks
   - departments/finance/PLAN.md — financial setup tasks
   - departments/support/PLAN.md — customer support setup
5. **Update your own plan** in departments/ceo/PLAN.md

Make the plans specific and actionable. Each task should be small enough for one agent run.
Think like a founder — what's the fastest path to first paying customer?
""",
    ))

    # Auto-register cron jobs after successful onboarding
    if result and result.get("status") == "accepted":
        try:
            from app.services.agent_scheduler import schedule_company_cycles
            slug = result.get("company", "")
            cron_result = schedule_company_cycles(company_id, slug=slug or None)
            logger.info(f"Auto-registered cron jobs after onboarding for {company_id}: {cron_result}")
            result["cron_jobs"] = cron_result
        except Exception as e:
            logger.error(f"Failed to auto-register cron jobs for {company_id}: {e}")
            result["cron_jobs_error"] = str(e)

    return result
