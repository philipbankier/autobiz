# FlowTest API

MVP API for E2E Test Company — SQLite-backed Fastify server.

---

## Full Stack Quick Start

The easiest way to run everything (API + static frontend) is the root-level launcher:

```bash
cd /home/philip/TinkerLab/autobiz/sites/e2e-1773572738
./start.sh
```

This will:
1. Auto-run `npm install` if `node_modules` is missing
2. Start the Fastify API on **port 3000** (or `$API_PORT`)
3. Start a static file server on **port 8080** (or `$STATIC_PORT`) using `npx serve` or `python3`
4. Print a summary with links to the landing page, dashboard, and API health check
5. Gracefully shut down both servers on `Ctrl+C`

### Custom Ports

```bash
API_PORT=4000 STATIC_PORT=9000 ./start.sh
```

---

## API Only

```bash
cd /home/philip/TinkerLab/autobiz/sites/e2e-1773572738/api
npm install
npm start
```

API runs on `http://localhost:3000` by default.

---

## Environment Variables

| Variable        | Default                                          | Description                     |
|-----------------|--------------------------------------------------|---------------------------------|
| `PORT`          | `3000`                                           | API port                        |
| `HOST`          | `0.0.0.0`                                        | API bind host                   |
| `DATA_DIR`      | `../data`                                        | Directory for SQLite DB         |
| `DB_PATH`       | `$DATA_DIR/flowtest.db`                          | SQLite database path            |
| `WAITLIST_FILE` | `../../../companies/e2e-1773572738/waitlist.json`| Waitlist storage path           |
| `API_PORT`      | `3000`                                           | (start.sh) API port             |
| `STATIC_PORT`   | `8080`                                           | (start.sh) Static server port   |

---

## Storage

- **Database:** SQLite via `better-sqlite3`
- **Location:** `/home/philip/TinkerLab/autobiz/sites/e2e-1773572738/data/flowtest.db`
- **Schema:** 4 tables — `projects`, `runs`, `test_results`, `flakiness`
- **WAL mode:** Enabled for better concurrent read performance
- **Migrations:** Idempotent (`CREATE TABLE IF NOT EXISTS`) — safe to restart anytime

---

## Endpoints

### Health Check
```
GET /health
```
```json
{
  "status": "ok",
  "service": "flowtest-api",
  "version": "0.2.0",
  "storage": "sqlite",
  "uptime_seconds": 42,
  "timestamp": "2026-03-27T00:00:00.000Z"
}
```

### Waitlist
```
POST /api/waitlist
Content-Type: application/json

{ "email": "user@example.com", "name": "Alice" }
```

### Projects
```
POST /api/projects
Content-Type: application/json

{ "name": "My Project" }
```
Returns: `{ id, name, api_key, created_at }`

Use `api_key` as the Bearer token for all authenticated endpoints.

```
GET /api/projects/:id
Authorization: Bearer ft_<your-api-key>
```

### Test Runs
```
POST /api/runs
Authorization: Bearer ft_<your-api-key>
Content-Type: application/json

{
  "branch": "main",
  "commit_sha": "abc123",
  "duration_ms": 45000,
  "test_results": [
    {
      "test_name": "login test",
      "file_path": "tests/auth.spec.ts",
      "status": "passed",
      "duration_ms": 1200
    },
    {
      "test_name": "checkout flow",
      "file_path": "tests/checkout.spec.ts",
      "status": "failed",
      "duration_ms": 3400,
      "error_message": "Expected button to be visible"
    }
  ]
}
```

```
GET /api/runs
Authorization: Bearer ft_<your-api-key>
```

```
GET /api/runs/:id
Authorization: Bearer ft_<your-api-key>
```

### Analytics
```
GET /api/analytics/summary
Authorization: Bearer ft_<your-api-key>
```

### Flakiness
```
GET /api/flakiness
Authorization: Bearer ft_<your-api-key>
```

---

## Architecture Notes

- **Storage:** SQLite (v0.2.0+). Data persists across restarts.
- **Auth:** Simple API key in Bearer token header. One key per project, generated on project creation.
- **Framework:** Fastify + Node.js — fast, low overhead, TypeScript-friendly.
- **Transactions:** Run ingestion (run + test_results + flakiness upserts) is a single atomic transaction.
- **Flakiness scoring:** Rolling `fail_count / run_count` per test name per project. Updated on every run.

---

## Project Structure

```
e2e-1773572738/
├── start.sh              # ← Full-stack launcher (API + static files)
├── index.html            # Landing page with waitlist form
├── dashboard.html        # Product dashboard (currently mock data)
├── data/
│   └── flowtest.db       # SQLite database (auto-created on first run)
└── api/
    ├── server.js         # Fastify API server
    ├── package.json
    └── README.md         # ← You are here
```

---

## Next Steps

- **M5:** Wire up `dashboard.html` to real API endpoints (replace mock JS arrays with `fetch()` calls)
- **M4:** Flakiness scoring improvements — weighted decay for old runs
- **M6:** Email/webhook alerts when flakiness rate exceeds threshold
