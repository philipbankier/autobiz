# AutoBiz

**AI-powered business automation platform.** Describe your business idea, and AutoBiz spins up autonomous AI departments — CEO, Developer, Marketing, Sales, Finance, and Support — that execute tasks, manage budgets, and report back to you in real time. From company creation to live deployment in 90 seconds.

## Features

- **6 AI Departments** — CEO, Developer, Marketing, Sales, Finance, Support — each with role-specific instructions and autonomous task execution
- **Ralph Loop** — Single-task-per-run execution pattern with plan tracking, validation, memory consolidation, and git commits
- **3-Layer Hybrid Scheduler** — CRON (timed autonomy), EVENT (webhook-driven), and CONDITION filters (skip runs with no pending work, saving 50–70% token costs)
- **LLM-as-Judge Quality Gates** — Claude Haiku scores every agent output 1–10; retry tracker with circuit breaker after N failures
- **Per-Department Budget Control** — Daily spend limits, model tiering (Opus/Sonnet/Haiku), real-time cost tracking
- **Real-Time Dashboard** — Department cards with budget bars, live SSE activity feed, steering editor, scheduler controls
- **One-Click Deploy Pipeline** — GitHub repo creation, Vercel deployment, custom domain — triggered by the Developer agent
- **Human Steering** — Edit `STEERING.md` per department to override priorities without stopping agents
- **Integration Skills** — Social media posting (Twitter/LinkedIn via Late API), email dispatch (Resend), post-run hooks
- **Server-Sent Events** — Live activity stream from all departments to the dashboard
- **Stripe Billing** — Usage-based billing with credit balance and per-company cost breakdown
- **E2E Benchmarked** — 17/17 tests passing, 72s total, 20s company creation

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                             │
│                   Next.js 14 + React 18                     │
│              Tailwind CSS + Lucide Icons                    │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP / SSE
┌────────────────────────▼────────────────────────────────────┐
│                        Backend                              │
│                   FastAPI + Celery                           │
│                                                             │
│  ┌─────────┐  ┌───────────┐  ┌──────────┐  ┌────────────┐  │
│  │Scheduler│  │Cost Control│  │  Judge   │  │Retry Tracker│ │
│  │(3-layer)│  │ (budgets)  │  │(Haiku)  │  │ (backoff)   │ │
│  └────┬────┘  └─────┬─────┘  └────┬─────┘  └──────┬─────┘  │
│       └──────────────┼─────────────┼───────────────┘        │
│                      ▼                                      │
│              ┌──────────────┐                               │
│              │ OpenClaw Svc │                               │
│              └──────┬───────┘                               │
└─────────────────────┼───────────────────────────────────────┘
          ┌───────────┼───────────┐
          ▼           ▼           ▼
   ┌──────────┐ ┌──────────┐ ┌──────────────────┐
   │ Postgres │ │  Redis   │ │ OpenClaw Gateway  │
   │  (data)  │ │ (queue)  │ │  (agent sessions) │
   └──────────┘ └──────────┘ └──────────────────┘
                                     │
                              ┌──────▼──────┐
                              │ Claude API  │
                              │ (Opus/Sonnet│
                              │  /Haiku)    │
                              └─────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+
- OpenClaw gateway (or Anthropic API key)

### 1. Clone & Install

```bash
git clone https://github.com/philipbankier/autobiz.git
cd autobiz

# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ..

# Frontend
cd frontend
npm install
cd ..
```

### 2. Configure

```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your credentials
```

### 3. Database Setup

```bash
# Start Postgres + Redis (via Docker)
docker compose up -d db redis

# Run migrations
cd backend
source .venv/bin/activate
alembic upgrade head
cd ..
```

### 4. Run

```bash
# Terminal 1: Backend
cd backend && source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2: Celery worker
cd backend && source .venv/bin/activate
celery -A app.worker worker --loglevel=info

# Terminal 3: Frontend
cd frontend && npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### Docker (full stack)

```bash
docker compose up --build
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string (`postgresql+asyncpg://...`) |
| `REDIS_URL` | Yes | Redis connection string for Celery task queue |
| `JWT_SECRET` | Yes | Secret key for signing JWT auth tokens |
| `OPENCLAW_GATEWAY_URL` | No | OpenClaw gateway WebSocket URL (default: `http://127.0.0.1:18789`) |
| `OPENCLAW_GATEWAY_TOKEN` | No | Auth token for OpenClaw gateway |
| `ANTHROPIC_API_KEY` | No | Fallback API key if not using OpenClaw |
| `STRIPE_SECRET_KEY` | No | Stripe secret key (test mode) |
| `STRIPE_PUBLISHABLE_KEY` | No | Stripe publishable key for frontend |
| `STRIPE_WEBHOOK_SECRET` | No | Stripe webhook signing secret |
| `GITHUB_PAT` | No | GitHub personal access token for repo creation |
| `VERCEL_TOKEN` | No | Vercel API token for site deployment |
| `LATE_API_KEY` | No | Late API key for social media posting (Twitter/LinkedIn) |
| `RESEND_API_KEY` | No | Resend API key for email dispatch |

## API Reference

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Create account (email + password) |
| POST | `/api/auth/login` | Get JWT token |
| GET | `/api/auth/me` | Current user info |

### Companies
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/companies` | Create new company |
| GET | `/api/companies` | List user's companies |
| GET | `/api/companies/{id}` | Company details + departments |
| PUT | `/api/companies/{id}` | Update company settings |
| DELETE | `/api/companies/{id}` | Archive company |

### Departments
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/companies/{id}/departments` | List departments + status |
| PUT | `/api/companies/{id}/departments/{type}` | Update autonomy/budget |

### Activity & Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/companies/{id}/activity` | Activity log (paginated) |
| GET | `/api/companies/{id}/activity/sse` | Live Server-Sent Events stream |
| GET | `/api/companies/{id}/dashboard` | Aggregated metrics |

### Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/companies/{id}/chat` | Send message to department agent |
| GET | `/api/companies/{id}/chat` | Chat history |

### Tasks
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/companies/{id}/tasks` | All tasks |
| POST | `/api/companies/{id}/tasks` | Create human task |
| PUT | `/api/companies/{id}/tasks/{task_id}` | Update task status |

### Billing
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/billing/balance` | Credit balance |
| GET | `/api/billing/usage` | Usage breakdown |

### Sites & Integrations
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/sites` | Create site |
| GET | `/api/sites/{id}` | Site details |
| POST | `/api/sites/{id}/deploy` | Deploy to Vercel |
| GET | `/api/integrations/status` | Integration health check |
| POST | `/api/integrations/trigger` | Force-run a department |

### Webhooks
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/webhooks/github` | GitHub event handler |
| POST | `/api/webhooks/stripe` | Stripe payment events |
| POST | `/api/webhooks/vercel` | Vercel deployment events |

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Service health check |

## Project Structure

```
autobiz/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + router registration
│   │   ├── config.py            # Environment settings (Pydantic)
│   │   ├── database.py          # SQLAlchemy async engine
│   │   ├── worker.py            # Celery configuration
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── routers/             # API endpoint handlers
│   │   ├── services/            # Business logic
│   │   │   ├── scheduler.py     # 3-layer hybrid scheduler
│   │   │   ├── openclaw.py      # OpenClaw gateway integration + Ralph Loop
│   │   │   ├── judge.py         # LLM-as-Judge quality scoring
│   │   │   ├── cost_control.py  # Budget enforcement + model tiering
│   │   │   ├── retry_tracker.py # Per-task retry tracking
│   │   │   ├── site_deploy.py   # Vercel deployment
│   │   │   ├── social_media.py  # Twitter/LinkedIn posting
│   │   │   └── email_service.py # Resend email dispatch
│   │   ├── tasks/               # Celery task definitions
│   │   └── middleware/          # JWT auth middleware
│   ├── alembic/                 # Database migrations
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js pages (App Router)
│   │   ├── components/          # React components
│   │   │   ├── ui/              # Base UI primitives
│   │   │   └── dashboard/       # Department cards, activity feed, etc.
│   │   ├── lib/                 # API client, auth, utils
│   │   └── types/               # TypeScript type definitions
│   ├── package.json
│   └── Dockerfile
├── companies/                   # Runtime workspace per company
│   └── {slug}/
│       ├── COMPANY.md           # Company identity + mission
│       ├── departments/
│       │   └── {dept}/
│       │       ├── PLAN.md      # Task backlog (checkbox format)
│       │       ├── MEMORY.md    # Agent learnings
│       │       ├── STEERING.md  # Human priority overrides
│       │       └── retries.json # Retry tracking data
│       └── .git/                # Auto-committed by agents
├── docker-compose.yml
├── Makefile
└── README.md
```

## How It Works

### Ralph Loop

Each department follows a single-task execution loop per run:

1. **Read** `PLAN.md` → find the next unchecked task (`- [ ]`)
2. **Execute** that one task with role-specific instructions
3. **Validate** the output (run tests, check for errors)
4. **Score** via LLM-as-Judge (pass threshold: 6/10)
5. **Commit** — mark task done (`- [x]`), update `MEMORY.md`, git commit
6. **Report** — publish event to SSE activity feed

If validation fails, the retry tracker records feedback and the task is re-attempted on the next run (up to 3 attempts before circuit breaker triggers).

### Condition Filters

Before each scheduled run, the scheduler checks:

1. **Force flag** — always run if explicitly triggered by user
2. **CEO exemption** — CEO always runs (creates work for others)
3. **Steering override** — run if human set active priorities
4. **Pending tasks** — skip if no unchecked items in PLAN.md
5. **Budget check** — skip if daily budget exhausted

This saves 50–70% of token costs by avoiding pointless runs.

### Judge System

Every agent output is scored by Claude Haiku (~$0.001/eval) on four dimensions: relevance, quality, completeness, and safety. Outputs scoring below 6/10 are retried with the judge's feedback included in the next attempt.

## Benchmark Results

```
E2E Benchmark — 17/17 PASS
Total time:          72.0s
Company creation:    20.1s

Tests:
  01 health          ✓  API health check
  02 register        ✓  User registration
  03 create          ✓  Company creation (20.1s)
  04 workspace       ✓  8/8 workspace files
  05 depts           ✓  6/6 departments
  06 dashboard       ✓  Dashboard metrics
  07 onboard         ✓  Onboarding flow
  08 condition       ✓  Condition filter (skip: no tasks)
  09 sched_status    ✓  6 cron jobs registered
  10 sched_stop      ✓  6 jobs removed
  11 sched_start     ✓  6/6 jobs re-registered
  12 integrations    ✓  Integration health
  13 git             ✓  Git repo clean
  14a steer_read     ✓  STEERING.md readable
  14b steer_write    ✓  STEERING.md writable
  15 events          ✓  Event publishing
  16 site            ✓  Site deployment check
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, React 18, TypeScript, Tailwind CSS, Lucide Icons |
| Backend | FastAPI, Pydantic, SQLAlchemy (async), Celery |
| Database | PostgreSQL 15+ (asyncpg), Redis 7+ |
| AI | Claude Opus/Sonnet/Haiku via OpenClaw gateway |
| Auth | JWT (python-jose), bcrypt (passlib) |
| Payments | Stripe |
| Deploy | Vercel (sites), Docker Compose (infra) |
| Email | Resend |
| Social | Late API (Twitter/LinkedIn) |
| Realtime | Server-Sent Events (sse-starlette) |

## License

MIT
