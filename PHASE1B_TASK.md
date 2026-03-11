# Phase 1B: Wire Frontend + Celery Scheduler

## Context
The backend API is fully functional at http://localhost:8000. All endpoints work.
The frontend scaffold exists with page shells and components but they're not connected to the backend.
Read the existing code before making changes.

## Task 1: Wire Frontend to Backend API

### Install dependencies
```bash
cd frontend && npm install
```

### Wire these pages to the real API:

**1. `/login/page.tsx`** — Form submits to `POST /api/auth/login`, stores JWT in localStorage, redirects to `/dashboard`

**2. `/register/page.tsx`** — Form submits to `POST /api/auth/register`, stores JWT, redirects to `/dashboard`

**3. `/dashboard/page.tsx`** — Fetches `GET /api/companies` on mount, displays company cards. Each card links to `/dashboard/[companyId]`. Show "No companies yet" + create button if empty.

**4. `/dashboard/new/page.tsx`** — Create company form submits to `POST /api/companies` with name, mission, slug. On success redirects to `/dashboard/[companyId]`.

**5. `/dashboard/[companyId]/page.tsx`** — Overview page. Fetches `GET /api/companies/{id}/dashboard`. Shows:
- Company name + status badge
- Department status grid (6 departments, each with status indicator)
- Key metrics: active runs, completed runs, total cost, credits balance
- Recent activity (last 10 items from `GET /api/companies/{id}/activity`)

**6. `/dashboard/[companyId]/chat/page.tsx`** — Chat interface. 
- Dropdown to select department (CEO, Developer, Marketing, etc.)
- Message input + send button
- Fetches `GET /api/companies/{id}/chat?department_type=ceo` for history
- Sends via `POST /api/companies/{id}/chat` with {department_type, content}
- Auto-scrolls to latest message

**7. `/dashboard/[companyId]/tasks/page.tsx`** — Task board.
- Fetches `GET /api/companies/{id}/tasks`
- Groups by status (todo, in_progress, done, blocked) in columns
- "Add Task" button opens dialog → `POST /api/companies/{id}/tasks`
- Each task card shows: title, priority badge, assigned department, status

**8. `/dashboard/[companyId]/activity/page.tsx`** — Activity log.
- Fetches `GET /api/companies/{id}/activity`
- Chronological list of agent runs with: department, trigger, status, duration, cost, summary

**9. `/dashboard/[companyId]/settings/page.tsx`** — Department settings.
- Fetches `GET /api/companies/{id}/departments`
- For each department: autonomy level dropdown (full_auto/notify/approve/manual), budget cap input
- Save button calls `PUT /api/companies/{id}/departments/{type}`

### Frontend patterns to follow:
- Use the existing `src/lib/api.ts` for all API calls (it should handle auth headers)
- Use the existing `src/lib/auth.ts` for JWT management
- Use `"use client"` directive on pages that need interactivity
- Show loading states while fetching
- Show error messages from API responses
- Use existing shadcn/ui components (Button, Card, Badge, Input, etc.)
- Keep it clean and functional — no fancy animations, just working UI

### Auth guard:
- Dashboard layout should check for JWT token on mount
- If no token, redirect to /login
- Add a logout button in the header/sidebar

## Task 2: Celery Scheduler Setup

### Backend additions needed:

**1. Create `backend/app/worker.py`:**
```python
from celery import Celery
from app.config import settings

celery_app = Celery(
    "autobiz",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Import tasks so Celery discovers them
celery_app.autodiscover_tasks(["app.tasks"])
```

**2. Create `backend/app/tasks/__init__.py` and `backend/app/tasks/agent_cycles.py`:**

The agent cycle tasks (these are STUBS that log what they would do - real OpenClaw integration comes in Phase 2):

```python
# agent_cycles.py
import logging
from app.worker import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(name="run_ceo_planning_cycle")
def run_ceo_planning_cycle(company_id: str):
    """CEO reviews goals, creates/assigns tasks. Runs daily at 6 AM."""
    logger.info(f"[STUB] CEO planning cycle for company {company_id}")
    # Phase 2: Spawn OpenClaw CEO agent session, feed it company context,
    # have it review goals and create tasks
    return {"status": "stub", "company_id": company_id, "cycle": "ceo_planning"}

@celery_app.task(name="run_department_execution_cycle") 
def run_department_execution_cycle(company_id: str, department_type: str):
    """Department agent wakes up, checks tasks, executes. Runs hourly."""
    logger.info(f"[STUB] {department_type} execution cycle for company {company_id}")
    # Phase 2: Spawn OpenClaw agent for this department, feed it pending tasks,
    # let it execute using MCP tools
    return {"status": "stub", "company_id": company_id, "department": department_type}

@celery_app.task(name="run_finance_reporting_cycle")
def run_finance_reporting_cycle(company_id: str):
    """Finance agent compiles metrics. Runs daily at 10 PM."""
    logger.info(f"[STUB] Finance reporting cycle for company {company_id}")
    return {"status": "stub", "company_id": company_id, "cycle": "finance_reporting"}

@celery_app.task(name="run_weekly_learning_cycle")
def run_weekly_learning_cycle(company_id: str):
    """All agents review what worked/failed. Runs Sundays."""
    logger.info(f"[STUB] Weekly learning cycle for company {company_id}")
    return {"status": "stub", "company_id": company_id, "cycle": "weekly_learning"}
```

**3. Update `backend/app/services/agent_scheduler.py`:**

Add functions to schedule/unschedule cycles for a company:

```python
from celery import current_app
from celery.schedules import crontab

def schedule_company_cycles(company_id: str):
    """Register periodic tasks for a company."""
    # For now, just log. Phase 2 will use celery-beat dynamic scheduling
    # or a custom DB-backed scheduler
    pass

def trigger_department_cycle(company_id: str, department_type: str):
    """Manually trigger a department cycle (e.g., from chat)."""
    from app.tasks.agent_cycles import run_department_execution_cycle
    return run_department_execution_cycle.delay(company_id, department_type)
```

**4. Add trigger endpoint to backend:**

In `backend/app/routers/departments.py`, add:
```
POST /api/companies/{id}/departments/{type}/trigger
```
This calls `trigger_department_cycle()` and returns the celery task ID.

**5. Update `docker-compose.yml`** to add celery worker service:
```yaml
  celery-worker:
    build: ./backend
    command: celery -A app.worker worker --loglevel=info
    environment:
      DATABASE_URL: postgresql+asyncpg://autobiz:autobiz_dev@db:5432/autobiz
      REDIS_URL: redis://redis:6379
      JWT_SECRET: dev-secret-change-me
    depends_on:
      - db
      - redis
    volumes:
      - ./backend:/app

  celery-beat:
    build: ./backend
    command: celery -A app.worker beat --loglevel=info
    environment:
      DATABASE_URL: postgresql+asyncpg://autobiz:autobiz_dev@db:5432/autobiz
      REDIS_URL: redis://redis:6379
      JWT_SECRET: dev-secret-change-me
    depends_on:
      - db
      - redis
    volumes:
      - ./backend:/app
```

## Important
- Make sure `npm install` works and the frontend builds without errors
- Make sure `frontend/.env.local.example` has `NEXT_PUBLIC_API_URL=http://localhost:8000`
- Create `frontend/.env.local` with that value set
- Test that the full flow works: register → login → create company → view dashboard → chat → create task → view tasks
- Do NOT break existing backend code — only add to it
- Commit all changes when done
