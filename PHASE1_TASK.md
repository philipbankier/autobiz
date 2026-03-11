# Phase 1 Task: AutoBiz Foundation

Read PRD.md for full context. You are building Phase 1 of AutoBiz.

## What To Build

### 1. FastAPI Backend (`/backend`)
- Python 3.11+, FastAPI, SQLAlchemy (async), Alembic for migrations
- Use `uv` for dependency management if available, otherwise `pip` + `requirements.txt`
- PostgreSQL connection via asyncpg

**API Endpoints (Phase 1):**
```
POST   /api/auth/register          # Email + password signup (simple, no OAuth yet)
POST   /api/auth/login             # JWT token auth
GET    /api/auth/me                # Current user

POST   /api/companies              # Create new company (name, mission, slug)
GET    /api/companies              # List user's companies
GET    /api/companies/{id}         # Company details + department status
PUT    /api/companies/{id}         # Update company settings
DELETE /api/companies/{id}         # Soft delete (archive)

GET    /api/companies/{id}/departments        # List departments + status
PUT    /api/companies/{id}/departments/{type} # Update dept autonomy/budget

GET    /api/companies/{id}/activity           # Agent activity log (paginated)
POST   /api/companies/{id}/chat               # Send message to agent dept
GET    /api/companies/{id}/chat               # Chat history

GET    /api/companies/{id}/dashboard          # Aggregated metrics
GET    /api/companies/{id}/tasks              # All tasks across departments
POST   /api/companies/{id}/tasks              # Human-created task

GET    /api/billing/balance                   # Credit balance
GET    /api/billing/usage                     # Usage breakdown
```

**Database Schema (SQLAlchemy models):**
```python
# Users
users: id (UUID), email, password_hash, name, credits_balance (Decimal), created_at, updated_at

# Companies 
companies: id (UUID), user_id (FK), name, mission, slug (unique), status (enum: planning/building/running/paused/archived), config (JSON), created_at, updated_at

# Departments
departments: id (UUID), company_id (FK), type (enum: ceo/developer/marketing/sales/finance/support), autonomy_level (enum: full_auto/notify/approve/manual), budget_cap_daily (Decimal), status (enum: idle/running/waiting), agent_session_id (nullable), created_at, updated_at

# Agent Runs
agent_runs: id (UUID), department_id (FK), company_id (FK), trigger (enum: scheduled/manual/chat), status (enum: pending/running/completed/failed), started_at, completed_at, tokens_used (int), cost (Decimal), summary (text)

# Agent Tasks
agent_tasks: id (UUID), company_id (FK), department_id (FK, nullable), title, description, status (enum: todo/in_progress/done/blocked), priority (enum: low/medium/high/urgent), created_by (enum: human/agent), assigned_department (enum), created_at, completed_at

# Agent Messages (chat)
agent_messages: id (UUID), company_id (FK), department_id (FK), role (enum: user/agent), content (text), created_at

# Cost Events
cost_events: id (UUID), company_id (FK), department_id (FK, nullable), type (enum: llm_tokens/api_call/deployment), amount (Decimal), description, created_at
```

**Project structure:**
```
backend/
  app/
    __init__.py
    main.py              # FastAPI app, CORS, middleware
    config.py            # Settings from env vars
    database.py          # Async SQLAlchemy engine + session
    models/
      __init__.py
      user.py
      company.py
      department.py
      agent_run.py
      agent_task.py
      agent_message.py
      cost_event.py
    schemas/             # Pydantic request/response models
      __init__.py
      user.py
      company.py
      department.py
      agent.py
      billing.py
    routers/
      __init__.py
      auth.py
      companies.py
      departments.py
      activity.py
      chat.py
      tasks.py
      billing.py
      dashboard.py
    services/
      __init__.py
      auth.py            # JWT, password hashing
      company.py         # Company CRUD + business logic
      agent_scheduler.py # Celery task scheduling
      billing.py         # Credit tracking
    middleware/
      __init__.py
      auth.py            # JWT auth dependency
  alembic/
    env.py
    versions/
  alembic.ini
  requirements.txt
  Dockerfile
  .env.example
```

### 2. PostgreSQL + Docker Compose (`/docker-compose.yml`)
```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: autobiz
      POSTGRES_USER: autobiz
      POSTGRES_PASSWORD: autobiz_dev
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://autobiz:autobiz_dev@db:5432/autobiz
      REDIS_URL: redis://redis:6379
      JWT_SECRET: dev-secret-change-me
    depends_on:
      - db
      - redis
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

volumes:
  pgdata:
```

### 3. Next.js Frontend Scaffold (`/frontend`)
- Next.js 14+ with App Router
- TypeScript
- Tailwind CSS + shadcn/ui components
- Basic pages (no full implementation yet, just shells):
  - `/` — Landing page (placeholder)
  - `/login` — Login form
  - `/register` — Register form
  - `/dashboard` — Companies list (protected)
  - `/dashboard/[companyId]` — Company detail with tabs:
    - Overview (placeholder metrics)
    - Activity (agent log)
    - Chat (message agents)
    - Tasks (task board)
    - Settings (department configs)
  - `/dashboard/new` — Create company wizard

**Frontend project structure:**
```
frontend/
  src/
    app/
      layout.tsx
      page.tsx                    # Landing
      login/page.tsx
      register/page.tsx  
      dashboard/
        layout.tsx                # Sidebar nav
        page.tsx                  # Companies list
        new/page.tsx              # Create company
        [companyId]/
          layout.tsx              # Company tabs
          page.tsx                # Overview
          activity/page.tsx
          chat/page.tsx
          tasks/page.tsx
          settings/page.tsx
    components/
      ui/                        # shadcn components
      layout/
        sidebar.tsx
        header.tsx
      company/
        company-card.tsx
        create-company-form.tsx
      activity/
        activity-log.tsx
      chat/
        chat-interface.tsx
      tasks/
        task-board.tsx
    lib/
      api.ts                     # Fetch wrapper for backend API
      auth.ts                    # JWT token management
      utils.ts
    types/
      index.ts                   # TypeScript types matching backend schemas
  tailwind.config.ts
  next.config.js
  package.json
  Dockerfile
  .env.local.example
```

## Important Notes
- Use modern Python patterns: async/await everywhere, Pydantic v2, type hints
- Use modern React patterns: server components where possible, client components only when needed
- All API responses follow consistent format: `{data: ..., error: ..., meta: ...}`
- Include proper error handling, validation, and HTTP status codes
- Include `.env.example` files with all required env vars documented
- The frontend should be functional enough to create a company and see placeholder data
- Do NOT implement actual OpenClaw integration yet (that's Phase 2) — just create the interface/service stubs
- Add a `Makefile` at the root with common commands (dev, build, migrate, etc.)
