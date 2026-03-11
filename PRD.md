# AutoBiz — Product Requirements Document v1
## "Launch autonomous businesses powered by AI agents"

**Status:** Draft
**Author:** Orchestrator Agent + Philip Bankier
**Date:** March 11, 2026
**Working Title:** AutoBiz (final name TBD)

---

## 1. Product Vision

AutoBiz lets anyone launch an autonomous micro-business that builds its own product, markets itself, acquires customers, and generates revenue — all powered by specialized AI agent departments. The human owner monitors from a dashboard and can optionally steer via chat, but doesn't have to.

**One-liner:** "Your AI company that works while you sleep."

**How it differs from NanoCorp:** NanoCorp is one agent pretending to be a company. AutoBiz is a real multi-department operation with specialized agents, shared memory, business intelligence, and active growth loops.

---

## 2. Target Users

### Primary: Solo founders & indie hackers
- Want passive income streams
- Technical enough to understand AI but don't want to manage agents themselves
- Currently spending hours on marketing, content, customer support
- Budget: $5-50/month for tools

### Secondary: "Curious experimenters"
- Saw NanoCorp / Paperclip / OpenClaw trending, want to try autonomous business
- May not have a specific business idea
- Need guided experience (templates, "surprise me" mode)

### Tertiary: Small agencies
- Want to spin up micro-businesses for clients
- Need multi-company management ("conglomerate" view)

---

## 3. Core User Stories

### Company Creation
- **US-1:** As a user, I can describe a business idea in plain English and AutoBiz generates a business plan, validates the market, and starts building it
- **US-2:** As a user, I can pick from curated business templates (social media tool, newsletter, API directory, etc.)
- **US-3:** As a user, I can click "surprise me" and get a randomly generated but validated business idea
- **US-4:** As a user, I review and approve/modify the business plan before agents start building

### Agent Operations
- **US-5:** As a user, I can see all agent departments and their current status/tasks in real-time
- **US-6:** As a user, I can chat with any agent department to give feedback, ask questions, or override decisions
- **US-7:** As a user, I can set autonomy levels per department (full auto / notify / approve / manual)
- **US-8:** As a user, I receive notifications when agents complete major milestones or need input

### Business Dashboard
- **US-9:** As a user, I can see revenue, customers, traffic, and costs on a single dashboard
- **US-10:** As a user, I can see a P&L statement (revenue - agent costs - infra costs = profit)
- **US-11:** As a user, I can see agent activity log with full transparency on what each agent did and why
- **US-12:** As a user, I can see week-over-week growth trends

### Account & Billing
- **US-13:** As a user, I start with $5 free credit and add more via Stripe
- **US-14:** As a user, I can see real-time token usage and cost breakdown per department
- **US-15:** As a user, I can set budget caps per department and overall

---

## 4. Dogfood Business: Social Media Micro-SaaS

Before opening AutoBiz to users, we run our own autonomous business on it to prove the system works.

### The Business: AI Social Media Manager
**Why this:** Validated market (PostClaw hit 9 users at $39/mo in day 1, Buffer/Hootsuite are billion-dollar companies), simple enough for agents to build and operate, recurring revenue, and agents can market it using themselves.

**What the agents build and run:**

| Department | What They Do for This Business |
|-----------|-------------------------------|
| **CEO** | Sets weekly goals, reviews metrics, adjusts strategy, delegates |
| **Developer** | Builds the web app: dashboard, social account linking, scheduling UI, analytics |
| **Marketing** | Creates content about the tool, posts on X/Reddit/LinkedIn/dev.to, SEO |
| **Sales** | Optimizes landing page, A/B tests pricing, creates lead magnets |
| **Finance** | Tracks Stripe revenue, calculates CAC/LTV, manages agent budget |
| **Support** | Monitors feedback email, categorizes issues, auto-responds to common questions |

**Product the agents build:** A web app where users connect social accounts, describe what they want to say, and the app adapts + publishes across platforms. Priced $19-39/mo.

**Success criteria for dogfood:**
- Deployed, functional product website within 1 week of agents starting
- First non-us paying customer within 2 weeks
- $500 MRR within 30 days
- Positive unit economics (revenue > agent costs)

---

## 5. Architecture

### 5.1 Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Frontend** | TypeScript + React (Next.js) | Philip's preference, SSR for SEO, fast iteration |
| **Backend** | FastAPI (Python) | Philip's preference, async, fast, great for AI workloads |
| **Agent Runtime** | OpenClaw | Already running, proven harness features, trending standard |
| **Database** | PostgreSQL | Business data, company state, user accounts |
| **Cache/Queue** | Redis + Celery | Scheduled agent runs, real-time updates |
| **Knowledge Graph** | MCP Memory Server | Shared persistent memory between all agents |
| **Tool Integration** | MCP Tool Servers | Stripe, GitHub, social APIs, email, analytics |
| **File Storage** | Local filesystem → S3 (cloud phase) | Generated assets, websites, logs |
| **Deployment** | Docker Compose (self-hosted) | Phase 1. Kubernetes for cloud phase |
| **Generated Sites** | Vercel / Cloudflare Pages | Agent-built business websites |

### 5.2 System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                     AutoBiz Web Dashboard (Next.js)                  │
│                                                                      │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐       │
│  │ Company    │ │ Business   │ │ Agent      │ │ Chat       │       │
│  │ Creation   │ │ Dashboard  │ │ Activity   │ │ Interface  │       │
│  │ Wizard     │ │ (metrics)  │ │ Log        │ │ (per-dept) │       │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘       │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐                      │
│  │ Autonomy   │ │ Budget     │ │ Conglom-   │                      │
│  │ Controls   │ │ & Billing  │ │ erate View │                      │
│  └────────────┘ └────────────┘ └────────────┘                      │
└───────────────────────────┬──────────────────────────────────────────┘
                            │ REST + WebSocket
┌───────────────────────────┴──────────────────────────────────────────┐
│                     FastAPI Backend                                   │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Company      │  │ Agent        │  │ Billing      │              │
│  │ Service      │  │ Scheduler    │  │ Service      │              │
│  │              │  │ (Celery)     │  │ (Stripe)     │              │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤              │
│  │ Business     │  │ Chat         │  │ Analytics    │              │
│  │ Plan Gen     │  │ Router       │  │ Collector    │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└───────────────────────────┬──────────────────────────────────────────┘
                            │
┌───────────────────────────┴──────────────────────────────────────────┐
│                Agent Orchestration Layer                              │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    OpenClaw Gateway                             │ │
│  │                                                                │ │
│  │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐│ │
│  │  │ CEO  │  │ Dev  │  │ Mktg │  │Sales │  │ Fin  │  │ Supp ││ │
│  │  │Agent │  │Agent │  │Agent │  │Agent │  │Agent │  │Agent ││ │
│  │  └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘│ │
│  │     │         │         │         │         │         │     │ │
│  │  ┌──┴─────────┴─────────┴─────────┴─────────┴─────────┴──┐ │ │
│  │  │              MCP Knowledge Graph (Shared Memory)        │ │ │
│  │  │  Entities: customers, products, decisions, lessons,     │ │ │
│  │  │           metrics, competitors, content                 │ │ │
│  │  └────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    MCP Tool Servers                           │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐   │   │
│  │  │Stripe  │ │GitHub  │ │Social  │ │Email   │ │Deploy  │   │   │
│  │  │(pay)   │ │(code)  │ │(X,Reddit│ │(Resend)│ │(Vercel)│   │   │
│  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘   │   │
│  └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────┴──────────────────────────────────────────┐
│  PostgreSQL  │  Redis/Celery  │  Filesystem/S3  │  Stripe           │
└──────────────────────────────────────────────────────────────────────┘
```

### 5.3 Agent Department Definitions

Each agent is defined as a structured config (inspired by Portugal Solo Company Guy's markdown approach):

```yaml
# Example: Marketing Department Agent
department: marketing
role: "Marketing Director"
responsibilities:
  - Content strategy and calendar management
  - Social media posting (X, Reddit, LinkedIn, dev.to)
  - SEO optimization for the product website
  - Community engagement and brand building
  - Growth metric tracking and optimization

tools:
  - social_publisher  # MCP server for X, Reddit, LinkedIn APIs
  - analytics         # MCP server for Plausible/Umami
  - content_writer    # Built-in skill for adapting content per platform
  - seo_analyzer      # Built-in skill for on-page SEO

schedule:
  daily:
    - Check content calendar, publish scheduled posts
    - Monitor engagement metrics, respond to mentions
    - Research trending topics in the niche
  weekly:
    - Create next week's content calendar
    - Write 2-3 long-form pieces (blog posts, threads)
    - Report growth metrics to CEO agent

autonomy: full_auto  # User can override to: notify, approve, manual

budget_cap_daily: $2.00  # Max LLM spend per day for this department
```

### 5.4 Agent Lifecycle / Scheduling

```
                    ┌─────────────────────┐
                    │   COMPANY CREATED    │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  CEO: PLANNING CYCLE │ ← Daily (6 AM)
                    │  Review goals,       │
                    │  create/assign tasks  │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
    ┌─────────▼───────┐ ┌─────▼─────┐ ┌────────▼──────┐
    │ DEV: EXECUTION  │ │MKTG: EXEC │ │ SALES: EXEC   │  ← Hourly
    │ Build features, │ │Post content│ │Optimize pages │
    │ fix bugs, deploy│ │engage comm │ │follow up leads│
    └─────────┬───────┘ └─────┬─────┘ └────────┬──────┘
              │                │                │
              └────────────────┼────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │ FINANCE: REPORTING  │ ← Daily (10 PM)
                    │ Compile metrics,    │
                    │ update P&L, costs   │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ CEO: REVIEW CYCLE   │ ← Daily (11 PM)
                    │ Review metrics,     │
                    │ adjust strategy     │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ WEEKLY: LEARNING    │ ← Sunday
                    │ What worked/failed, │
                    │ update knowledge    │
                    │ graph, evolve plans │
                    └─────────────────────┘
```

### 5.5 Knowledge Graph Schema (MCP Memory)

```
Entity Types:
  - company: {name, mission, stage, created_at}
  - product: {name, url, features[], stack, status}
  - customer: {id, email, plan, signup_date, ltv, interactions[]}
  - competitor: {name, url, pricing, strengths, weaknesses}
  - decision: {what, why, who_decided, outcome, date}
  - lesson: {what_happened, what_we_learned, applies_to}
  - metric: {name, value, date, trend}
  - content: {type, platform, url, engagement, published_at}
  - task: {id, department, description, status, created, completed}

Relation Types:
  - owns, uses, built_with, depends_on
  - decided_by, resulted_in, learned_from
  - targets, converted_to, churned_from
  - outperforms, competes_with
```

### 5.6 Data Model (PostgreSQL)

```sql
-- Core tables
users (id, email, name, stripe_customer_id, created_at)
companies (id, user_id, name, mission, slug, status, config_json, created_at)
departments (id, company_id, type, autonomy_level, budget_cap_daily, agent_config_json)

-- Agent execution
agent_runs (id, department_id, trigger, started_at, completed_at, status, tokens_used, cost)
agent_tasks (id, company_id, department_id, title, description, status, priority, created_by, created_at, completed_at)
agent_messages (id, company_id, department_id, role, content, timestamp)  -- chat history

-- Business metrics
revenue_events (id, company_id, amount, currency, stripe_event_id, customer_email, created_at)
traffic_events (id, company_id, page, referrer, visitor_id, created_at)
cost_events (id, company_id, department_id, type, amount, description, created_at)

-- Billing
credits (id, user_id, amount, type, stripe_payment_id, created_at)
usage (id, user_id, company_id, department_id, tokens, cost, created_at)
```

---

## 6. Generated Business Sites

When agents build a product, it deploys as:
- **Default:** `{slug}.autobiz.app` (subdomain on our domain)
- **Custom:** User can CNAME their own domain

Sites are deployed via:
1. Agent writes code → pushes to GitHub repo (auto-created per company)
2. Vercel/Cloudflare Pages auto-deploys from repo
3. Analytics via Plausible/Umami (self-hosted, privacy-friendly)
4. Payments via Stripe (connected account per business)

---

## 7. API Design (Key Endpoints)

```
POST   /api/companies                    # Create new company
GET    /api/companies                    # List user's companies
GET    /api/companies/{id}               # Company details
PUT    /api/companies/{id}               # Update company settings
DELETE /api/companies/{id}               # Archive company

GET    /api/companies/{id}/dashboard     # Business metrics
GET    /api/companies/{id}/activity      # Agent activity log (paginated)
GET    /api/companies/{id}/departments   # Department status
PUT    /api/companies/{id}/departments/{dept}  # Update dept config/autonomy

POST   /api/companies/{id}/chat          # Send message to agent
GET    /api/companies/{id}/chat          # Chat history (WebSocket upgrade available)

GET    /api/companies/{id}/tasks         # All tasks across departments
POST   /api/companies/{id}/tasks         # Human-created task for agents

GET    /api/companies/{id}/financials    # P&L, revenue, costs
GET    /api/companies/{id}/customers     # Customer list

POST   /api/billing/credits              # Add credits (Stripe checkout)
GET    /api/billing/usage                # Usage breakdown
GET    /api/billing/balance              # Current credit balance
```

---

## 8. Phased Delivery

### Phase 1: Foundation (Weeks 1-3)
- [ ] FastAPI backend scaffold with auth, company CRUD
- [ ] PostgreSQL schema + migrations
- [ ] OpenClaw integration: spawn agents per company, manage sessions
- [ ] Agent department configs (CEO + Developer initially)
- [ ] Basic Next.js dashboard: company creation, activity log
- [ ] Celery scheduler for agent heartbeats

### Phase 2: Agent Intelligence (Weeks 3-5)
- [ ] MCP knowledge graph server (shared memory)
- [ ] CEO agent: planning cycles, task delegation
- [ ] Developer agent: code generation, GitHub push, deploy to Vercel
- [ ] Marketing agent: content creation, social posting via MCP tools
- [ ] Agent chat interface (WebSocket)
- [ ] Activity log with real-time streaming

### Phase 3: Business Operations (Weeks 5-7)
- [ ] Stripe integration (both for AutoBiz billing AND for generated businesses)
- [ ] Finance agent: revenue tracking, P&L compilation
- [ ] Business dashboard: revenue, traffic, customers, costs
- [ ] Sales agent: landing page optimization, lead tracking
- [ ] Subdomain provisioning ({slug}.autobiz.app)
- [ ] Budget caps and autonomy controls

### Phase 4: Dogfood & Polish (Weeks 7-9)
- [ ] Launch our own social media tool business on AutoBiz
- [ ] Support agent: email monitoring, auto-responses
- [ ] Graduated autonomy UI (per-department controls)
- [ ] Conglomerate view (multi-company dashboard)
- [ ] Onboarding flow: templates, "surprise me," guided creation
- [ ] Bug fixes, performance, UX polish from real usage

### Phase 5: Cloud Prep (Weeks 9-12)
- [ ] Docker → Kubernetes migration
- [ ] Multi-tenant isolation
- [ ] User auth (OAuth, magic links)
- [ ] Custom domain support
- [ ] Public launch prep: landing page, docs, pricing page

---

## 9. Cost Model

### For Us (Running AutoBiz)
- LLM costs: ~$0.50-2.00/day per active company (depending on agent activity)
- Infrastructure: PostgreSQL + Redis + OpenClaw on existing hardware = ~$0
- Vercel free tier for generated sites (initially)

### For Users
- **Free tier:** $5 credit on signup (enough for ~3-5 days of agent activity)
- **Pay-as-you-go:** LLM costs passed through at cost + 20% margin
- **Future premium ($29-49/mo):** Priority execution, more departments, custom domains, higher budgets, analytics

### Unit Economics Target
- Average company burns $0.50-1.50/day in LLM costs
- At $29/mo subscription → $0.97/day revenue per user
- Break-even at ~$0.75/day agent cost (achievable with smart scheduling + caching)

---

## 10. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Agents build low-quality products | Users churn, reputation damage | Quality gates: CEO agent reviews all output before shipping. Ralph-loop pattern for iteration |
| Runaway LLM costs | Burn through credits fast | Hard budget caps per department, smart scheduling (not every hour), caching common operations |
| Social media API changes/rate limits | Marketing agent breaks | MCP tool abstraction makes swapping APIs easy. Graceful degradation |
| NanoCorp moves fast, copies our features | Competition | Our advantage: real departments, shared memory, business intelligence. They'd need to rebuild from scratch |
| Generated businesses don't make money | Value prop questioned | Honest business validation step before building. Show P&L transparently. Some businesses will fail — that's OK if the platform clearly shows why |
| Stripe compliance for generated businesses | Legal complexity | Start with simple products (digital, subscriptions). Stripe Connect for proper isolation |

---

## 11. Success Metrics

### Platform Metrics
- Companies created per week
- Active companies (agents ran in last 24h)
- User retention (7d, 30d)
- Credit purchase conversion rate

### Dogfood Business Metrics
- Time to deployed product
- Time to first paying customer
- MRR growth
- Agent cost / revenue ratio

### Quality Metrics
- Agent task completion rate
- Agent output quality (human rating sample)
- Time from task creation to completion
- Knowledge graph entity count (growing = agents are learning)

---

## 12. Open for Future Phases (Not in v1)

- Marketplace: share/sell company templates
- Agent-to-Agent protocol (A2A) for cross-company collaboration
- Local model support via Ollama (reduce costs)
- Mobile app for monitoring
- Webhook integrations for external tools
- White-label option for agencies
- Revenue share model (AutoBiz takes % of generated business revenue)

---

*PRD v1 — March 11, 2026*
*Next: Philip review → Additional research on specific technical decisions → Development kickoff*
