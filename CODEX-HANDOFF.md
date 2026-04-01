# AutoBiz (oneidea.app) — Comprehensive Codex Handoff

## Project Overview
AutoBiz is a platform that lets users describe a business idea and get a live autonomous business — website, payments, marketing, AI agent team — all handled. Built with FastAPI backend + Next.js frontend + Celery workers + PostgreSQL + Redis.

**Repo:** `~/TinkerLab/autobiz/`
**Live frontend:** https://oneidea.app (deployed on Vercel)
**Live API:** https://autobiz-api.metaportallabs.xyz (Cloudflare tunnel → localhost:8000)
**GitHub:** github.com/philipbankier/autobiz (private)

## Current State (as of April 1, 2026)
- Frontend on Vercel: ✅ Live and serving
- Docker containers: ❌ ALL DOWN (db, redis, backend, celery-worker, celery-beat, frontend, cron-proxy)
- Cloudflare tunnel: ❌ Down (API unreachable)
- CC-Bridge (LLM proxy): Need to verify at localhost:8322
- Last security audit: March 31 — found critical issues NOT yet fixed

## Stack
- **Backend:** FastAPI (Python), SQLAlchemy async, Alembic migrations
- **Frontend:** Next.js 14, TypeScript, Tailwind, shadcn/ui
- **Workers:** Celery with Redis broker
- **DB:** PostgreSQL 16 (Docker)
- **Cache/Broker:** Redis 7 (Docker)
- **LLM:** CC-Bridge at http://127.0.0.1:8322/v1 (OpenAI-compatible, api_key: "dummy")
- **Deploy:** Vercel (frontend), Cloudflare tunnel (API), Docker Compose (infra)

## File Structure
```
~/TinkerLab/autobiz/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── worker.py            # Celery app
│   │   ├── routers/             # API endpoints
│   │   ├── services/            # Business logic
│   │   │   ├── provisioning.py  # Company creation flow
│   │   │   ├── openclaw.py      # LLM integration via CC-Bridge
│   │   │   ├── agent_scheduler.py
│   │   │   ├── scheduler.py     # Celery Beat scheduling
│   │   │   ├── event_bus.py     # SSE activity stream
│   │   │   ├── judge.py         # LLM-as-judge quality gates
│   │   │   ├── knowledge_graph.py
│   │   │   ├── git_service.py
│   │   │   ├── site_deploy.py
│   │   │   ├── social_media.py
│   │   │   ├── email_service.py
│   │   │   ├── stripe_service.py
│   │   │   ├── cost_control.py
│   │   │   ├── billing.py
│   │   │   └── retry_tracker.py
│   │   └── tasks/
│   │       └── agent_cycles.py  # Celery tasks for agent runs
│   ├── .env                     # Environment variables
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/app/
│   │   ├── page.tsx             # Landing page
│   │   ├── login/page.tsx
│   │   ├── register/page.tsx
│   │   └── dashboard/
│   │       ├── page.tsx         # Company list
│   │       ├── new/page.tsx     # Onboarding wizard
│   │       └── [id]/            # Company detail pages
│   ├── src/lib/api.ts           # API client
│   ├── src/lib/auth.ts          # JWT auth helpers
│   └── src/components/          # UI components
├── companies/                   # Company workspaces (gitignored)
├── docker-compose.yml
├── .env                         # Root env (Zernio keys, etc.)
├── PRD.md                       # Full product requirements
└── README.md
```

---

## TASKS — Fix, Harden, and Verify Everything

### TASK 1: Fix Critical Security Issues (MUST DO FIRST)

**1a. Generate proper JWT_SECRET**
- File: `backend/.env`
- Current value: `JWT_SECRET=dev-test` ← CRITICAL, anyone can forge tokens
- Generate a 64-char random hex secret: `python3 -c "import secrets; print(secrets.token_hex(32))"`
- Update in `backend/.env`

**1b. Add webhook signature verification**
- File: `backend/app/routers/webhooks.py`
- Stripe webhook endpoint must verify `stripe-signature` header using `STRIPE_WEBHOOK_SECRET`
- Vercel/GitHub webhook endpoints need basic token verification (check `X-Vercel-Signature` / `X-Hub-Signature-256`)
- Add `WEBHOOK_SECRET` env var for non-Stripe webhooks

**1c. Add security headers middleware**
- File: `backend/app/main.py`
- Add middleware that sets: `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Strict-Transport-Security: max-age=31536000`, `X-XSS-Protection: 1; mode=block`

**1d. Fix company data isolation**
- Audit ALL routers in `backend/app/routers/` — every company-scoped endpoint MUST filter by `current_user.id`
- Specifically check: companies.py, departments.py, chat.py, tasks.py, activity.py, site.py, billing.py
- Add a `get_user_company()` dependency that raises 403 if the company doesn't belong to the current user

### TASK 2: Fix Agent Output Pipeline (CEO agent runs but output isn't saved)

The CEO agent successfully calls CC-Bridge and generates a business plan, but `_apply_agent_output()` in `backend/app/tasks/agent_cycles.py` doesn't write the output to the company workspace files.

**Fix:**
- In `agent_cycles.py`, after the LLM returns output, parse it and write to the appropriate department files:
  - CEO output → `companies/{slug}/ceo/PLAN.md` (business plan, task assignments)
  - Developer output → `companies/{slug}/developer/PLAN.md`
  - Marketing output → `companies/{slug}/marketing/PLAN.md`
  - etc.
- The `_apply_agent_output()` function should:
  1. Parse the LLM response for file write instructions (look for markdown headers, file paths, or structured JSON)
  2. Write parsed content to the correct department workspace files
  3. If the CEO assigns tasks to other departments, create entries in those departments' PLAN.md files with `- [ ]` checkboxes
  4. Emit SSE events via `event_bus.publish()` for each file written
  5. Update the agent_runs table with status="completed" and the output summary

### TASK 3: Fix Docker Environment Issues

**3a. Ensure all containers start cleanly**
```bash
cd ~/TinkerLab/autobiz
docker compose down -v  # Clean slate
docker compose up -d --build
```

**3b. Verify container networking**
- Backend and celery-worker use `network_mode: host` — they access DB at localhost:5432, Redis at localhost:6379, CC-Bridge at localhost:8322
- celery-beat uses Docker bridge networking — it needs `db:5432` and `redis:6379`
- This inconsistency is fragile. Consider making celery-beat also use host networking for consistency.

**3c. Fix the frontend Docker port binding**
- Current: `ports: ["3002:3000"]` — binds to 0.0.0.0 (public)
- Fix: `ports: ["127.0.0.1:3002:3000"]` — bind to localhost only (Vercel is the public frontend)

**3d. Verify CC-Bridge connectivity**
- CC-Bridge runs at `http://127.0.0.1:8322/v1`
- Test: `curl -s http://127.0.0.1:8322/v1/models` — should return model list
- If CC-Bridge is down, it needs to be started separately (it's not in docker-compose)
- The backend env has `ANTHROPIC_API_BASE=http://127.0.0.1:8322` and `ANTHROPIC_API_KEY=dummy`

### TASK 4: Fix and Test the Full E2E Flow

Run through the complete user journey and fix anything that breaks:

**4a. Auth flow**
```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","password":"testpass123"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}'
# Should return JWT token
```

**4b. Company creation**
```bash
TOKEN="<jwt from login>"
curl -X POST http://localhost:8000/api/companies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Pet Care AI","slug":"petcare-ai","idea":"AI-powered pet care subscription box with personalized recommendations"}'
# Should provision: workspace dirs, GitHub repo, Vercel project, Stripe Connect, email config
# Scheduler should be deferred (cron-manifest.json) — that's expected
```

**4c. Department trigger (Run button)**
```bash
COMPANY_ID="<id from create>"
curl -X POST "http://localhost:8000/api/departments/ceo/trigger?company_id=$COMPANY_ID" \
  -H "Authorization: Bearer $TOKEN"
# Should dispatch Celery task → call CC-Bridge → generate business plan → write to workspace
```

**4d. Verify output was written**
```bash
cat ~/TinkerLab/autobiz/companies/petcare-ai/ceo/PLAN.md
# Should contain the generated business plan
```

**4e. SSE activity stream**
```bash
curl -N "http://localhost:8000/api/companies/$COMPANY_ID/activity/stream?token=$TOKEN"
# Should receive Server-Sent Events as agents run
```

**4f. Chat with department**
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"company_id":"'$COMPANY_ID'","department":"ceo","message":"What is your current business plan?"}'
# Should return AI-generated response from CEO agent
```

### TASK 5: Fix SSE Progress Tracker in Onboarding Wizard

- File: `frontend/src/components/onboarding/step-progress.tsx` (or similar)
- File: `backend/app/services/provisioning.py`
- The provisioning service should emit SSE events at each step. Events added in a previous fix but never verified.
- Event types expected by frontend: `company.provisioned`, `git.repo_created`, `deploy.linked`, `agent.run_started`, `agent.run_completed`, `onboard.completed`
- The frontend's `connectActivityStream()` in `frontend/src/lib/api.ts` connects to `/api/companies/{id}/activity/stream`
- Verify: create a company via the API, connect to SSE stream, confirm events arrive in the right order

### TASK 6: Fix Landing Page Pricing Bug

The pricing section on the landing page shows `$$0`, `$$9`, `$$29` (double dollar signs).
- File: `frontend/src/app/page.tsx`
- Find the pricing section and fix the template literal — likely `$${price}` should be `$${price}` with proper escaping, or hardcoded `$0`, `$9`, `$29`

### TASK 7: Verify Alembic Migrations

```bash
cd ~/TinkerLab/autobiz/backend
alembic current   # Should show current revision
alembic heads     # Should show latest migration
alembic upgrade head  # Apply any pending migrations
```

If tables are missing or schema is stale, generate a new migration:
```bash
alembic revision --autogenerate -m "sync schema"
alembic upgrade head
```

### TASK 8: Verify and Fix Vercel Deployment

```bash
cd ~/TinkerLab/autobiz/frontend
npx vercel --prod
```

Ensure these env vars are set on Vercel:
- `NEXT_PUBLIC_API_URL=https://autobiz-api.metaportallabs.xyz`

The domain `oneidea.app` should be configured as a custom domain on the Vercel project.

### TASK 9: Start Cloudflare Tunnel

The API tunnel config is at `~/.cloudflared/` — look for a config file that routes `autobiz-api.metaportallabs.xyz` to `http://localhost:8000`.

```bash
# Find the tunnel
cloudflared tunnel list | grep autobiz

# Start it
cloudflared tunnel run autobiz
# Or if using a config file:
cloudflared tunnel --config ~/.cloudflared/autobiz-config.yml run autobiz
```

Verify: `curl -s https://autobiz-api.metaportallabs.xyz/api/health`

### TASK 10: Run Full Test Suite and Commit

After all fixes:
1. Run the backend import check: `cd backend && python -c "from app.main import app; print('OK')"`
2. Run the frontend build: `cd frontend && npm run build`
3. Test the full E2E flow from Task 4
4. Commit all changes with descriptive message
5. Push to GitHub
6. Redeploy frontend to Vercel if frontend changes were made

---

## Environment Variables Reference

**backend/.env** should contain:
```
DATABASE_URL=postgresql+asyncpg://autobiz:autobiz_dev@localhost:5432/autobiz
REDIS_URL=redis://localhost:6379
JWT_SECRET=<GENERATE NEW 64-CHAR HEX>
OPENCLAW_GATEWAY_URL=http://127.0.0.1:18789
OPENCLAW_GATEWAY_TOKEN=<existing token>
GITHUB_PAT=<existing PAT>
VERCEL_TOKEN=<existing token>
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=<SET THIS>
LATE_API_KEY=<existing>
RESEND_API_KEY=<existing>
ANTHROPIC_API_BASE=http://127.0.0.1:8322
ANTHROPIC_API_KEY=dummy
ZERNIO_API_KEY=<existing>
ZERNIO_USER_ID=<existing>
```

## Success Criteria
- [ ] All Docker containers start and stay healthy
- [ ] Security issues fixed (JWT secret, webhook verification, security headers, data isolation)
- [ ] User can register → login → create company → see dashboard
- [ ] CEO agent runs and writes business plan to company workspace
- [ ] SSE events stream to frontend during provisioning and agent runs
- [ ] Chat with departments returns AI responses
- [ ] Landing page renders correctly (no double dollar signs)
- [ ] API accessible via Cloudflare tunnel
- [ ] Frontend accessible via oneidea.app
- [ ] All changes committed and pushed
