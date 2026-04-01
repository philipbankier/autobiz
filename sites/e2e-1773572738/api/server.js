/**
 * FlowTest API Server
 * E2E Test Company — MVP API (SQLite-backed)
 * v0.3.0 — Railway-compatible (waitlist stored in SQLite, not filesystem)
 *
 * Endpoints:
 *   GET  /health              — health check
 *   POST /api/waitlist        — add email to waitlist
 *   GET  /api/waitlist        — list waitlist entries (internal use)
 *   POST /api/projects        — create project + API key
 *   GET  /api/projects/:id    — get project
 *   POST /api/runs            — ingest test run (auth required)
 *   GET  /api/runs            — list runs for project
 *   GET  /api/runs/:id        — get run details
 *   GET  /api/flakiness       — flakiness scores for project
 *   GET  /api/analytics/summary — suite health summary
 */

'use strict';

const Fastify = require('fastify');
const path = require('path');
const fs = require('fs');
const { randomUUID } = require('crypto');
const Database = require('better-sqlite3');

// ─── Config ────────────────────────────────────────────────────────────────

const PORT = process.env.PORT || 3000;
const HOST = process.env.HOST || '0.0.0.0';
const DATA_DIR = process.env.DATA_DIR || path.join(__dirname, '../data');
const DB_PATH = process.env.DB_PATH || path.join(DATA_DIR, 'flowtest.db');

// Ensure data directory exists
fs.mkdirSync(DATA_DIR, { recursive: true });

// ─── Database Setup ────────────────────────────────────────────────────────

const db = new Database(DB_PATH);

// Enable WAL mode for better concurrent read performance
db.pragma('journal_mode = WAL');
db.pragma('foreign_keys = ON');

// Schema migrations
db.exec(`
  CREATE TABLE IF NOT EXISTS projects (
    id         TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    api_key    TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
  );

  CREATE TABLE IF NOT EXISTS runs (
    id           TEXT PRIMARY KEY,
    project_id   TEXT NOT NULL REFERENCES projects(id),
    branch       TEXT NOT NULL,
    commit_sha   TEXT NOT NULL,
    triggered_at TEXT NOT NULL,
    duration_ms  INTEGER,
    status       TEXT NOT NULL,
    pass_count   INTEGER NOT NULL DEFAULT 0,
    fail_count   INTEGER NOT NULL DEFAULT 0,
    total_count  INTEGER NOT NULL DEFAULT 0
  );

  CREATE TABLE IF NOT EXISTS test_results (
    id            TEXT PRIMARY KEY,
    run_id        TEXT NOT NULL REFERENCES runs(id),
    test_name     TEXT NOT NULL,
    file_path     TEXT,
    status        TEXT NOT NULL,
    duration_ms   INTEGER,
    error_message TEXT
  );

  CREATE TABLE IF NOT EXISTS flakiness (
    project_id     TEXT NOT NULL REFERENCES projects(id),
    test_name      TEXT NOT NULL,
    run_count      INTEGER NOT NULL DEFAULT 0,
    fail_count     INTEGER NOT NULL DEFAULT 0,
    flakiness_rate REAL NOT NULL DEFAULT 0,
    last_updated   TEXT,
    PRIMARY KEY (project_id, test_name)
  );

  CREATE INDEX IF NOT EXISTS idx_runs_project_id     ON runs(project_id);
  CREATE INDEX IF NOT EXISTS idx_runs_triggered_at   ON runs(triggered_at DESC);
  CREATE INDEX IF NOT EXISTS idx_test_results_run_id ON test_results(run_id);
  CREATE INDEX IF NOT EXISTS idx_flakiness_project   ON flakiness(project_id, flakiness_rate DESC);

  CREATE TABLE IF NOT EXISTS waitlist (
    email      TEXT PRIMARY KEY,
    name       TEXT,
    source     TEXT,
    utm_source TEXT,
    utm_medium TEXT,
    utm_campaign TEXT,
    joined_at  TEXT NOT NULL
  );
`);

// ─── Prepared Statements ───────────────────────────────────────────────────

const stmts = {
  // Projects
  insertProject: db.prepare(
    'INSERT INTO projects (id, name, api_key, created_at) VALUES (?, ?, ?, ?)'
  ),
  getProjectById: db.prepare('SELECT * FROM projects WHERE id = ?'),
  getProjectByApiKey: db.prepare('SELECT * FROM projects WHERE api_key = ?'),

  // Runs
  insertRun: db.prepare(`
    INSERT INTO runs (id, project_id, branch, commit_sha, triggered_at, duration_ms, status, pass_count, fail_count, total_count)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `),
  getRunById: db.prepare('SELECT * FROM runs WHERE id = ?'),
  listRunsByProject: db.prepare(
    'SELECT * FROM runs WHERE project_id = ? ORDER BY triggered_at DESC LIMIT ?'
  ),
  countRunsByProject: db.prepare('SELECT COUNT(*) as cnt FROM runs WHERE project_id = ?'),

  // Test results
  insertTestResult: db.prepare(`
    INSERT INTO test_results (id, run_id, test_name, file_path, status, duration_ms, error_message)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `),
  getTestResultsByRun: db.prepare('SELECT * FROM test_results WHERE run_id = ?'),

  // Waitlist
  getWaitlistEntry: db.prepare('SELECT email FROM waitlist WHERE email = ?'),
  insertWaitlistEntry: db.prepare(`
    INSERT OR IGNORE INTO waitlist (email, name, source, utm_source, utm_medium, utm_campaign, joined_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `),
  listWaitlist: db.prepare('SELECT email, name, source, utm_source, utm_medium, utm_campaign, joined_at FROM waitlist ORDER BY joined_at DESC'),

  // Flakiness
  upsertFlakiness: db.prepare(`
    INSERT INTO flakiness (project_id, test_name, run_count, fail_count, flakiness_rate, last_updated)
    VALUES (?, ?, 1, ?, ?, ?)
    ON CONFLICT(project_id, test_name) DO UPDATE SET
      run_count      = run_count + 1,
      fail_count     = fail_count + excluded.fail_count,
      flakiness_rate = CAST(fail_count + excluded.fail_count AS REAL) / (run_count + 1),
      last_updated   = excluded.last_updated
  `),
  getFlakinessForProject: db.prepare(
    'SELECT * FROM flakiness WHERE project_id = ? ORDER BY flakiness_rate DESC'
  ),

  // Analytics
  getRecentRuns: db.prepare(
    'SELECT * FROM runs WHERE project_id = ? ORDER BY triggered_at DESC LIMIT 30'
  ),
};

// ─── Helpers ───────────────────────────────────────────────────────────────

function generateApiKey() {
  return 'ft_' + randomUUID().replace(/-/g, '');
}

function getAuthProject(request) {
  const authHeader = request.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) return null;
  const apiKey = authHeader.slice(7);
  return stmts.getProjectByApiKey.get(apiKey) || null;
}

const insertRunWithResults = db.transaction((run, testResults) => {
  stmts.insertRun.run(
    run.id, run.project_id, run.branch, run.commit_sha,
    run.triggered_at, run.duration_ms, run.status,
    run.pass_count, run.fail_count, run.total_count
  );
  for (const t of testResults) {
    stmts.insertTestResult.run(
      t.id, run.id, t.test_name, t.file_path || null,
      t.status, t.duration_ms || null, t.error_message || null
    );
    const isFail = (t.status === 'failed' || t.status === 'flaky') ? 1 : 0;
    stmts.upsertFlakiness.run(
      run.project_id, t.test_name, isFail, isFail,
      new Date().toISOString()
    );
  }
});

// ─── App ───────────────────────────────────────────────────────────────────

const app = Fastify({ logger: true });

// CORS
app.register(require('@fastify/cors'), {
  origin: '*',
  methods: ['GET', 'POST', 'OPTIONS'],
});

// Static files (serve landing page + dashboard)
const staticRoot = path.join(__dirname, '..');
if (fs.existsSync(staticRoot)) {
  app.register(require('@fastify/static'), {
    root: staticRoot,
    prefix: '/',
    decorateReply: false,
  });
}

// ─── Routes ────────────────────────────────────────────────────────────────

/** GET /health */
app.get('/health', async () => ({
  status: 'ok',
  service: 'flowtest-api',
  version: '0.3.0',
  storage: 'sqlite',
  uptime_seconds: Math.floor(process.uptime()),
  timestamp: new Date().toISOString(),
}));

/** POST /api/waitlist */
app.post('/api/waitlist', {
  schema: {
    body: {
      type: 'object',
      required: ['email'],
      properties: {
        email: { type: 'string', format: 'email' },
        name: { type: 'string' },
        source: { type: 'string' },
        utm_source: { type: 'string' },
        utm_medium: { type: 'string' },
        utm_campaign: { type: 'string' },
      },
    },
  },
}, async (request, reply) => {
  const { email, name, source, utm_source, utm_medium, utm_campaign } = request.body;

  // Check for duplicate
  const existing = stmts.getWaitlistEntry.get(email);
  if (existing) {
    return reply.code(200).send({ success: true, message: 'Already on the waitlist!' });
  }

  const result = stmts.insertWaitlistEntry.run(
    email,
    name || null,
    source || null,
    utm_source || null,
    utm_medium || null,
    utm_campaign || null,
    new Date().toISOString()
  );

  if (result.changes === 0) {
    return reply.code(200).send({ success: true, message: 'Already on the waitlist!' });
  }

  app.log.info(`Waitlist signup: ${email} (source: ${source || utm_source || 'direct'})`);
  reply.code(201).send({ success: true, message: "You're on the waitlist! We'll be in touch." });
});

/** GET /api/waitlist — internal use, lists all signups */
app.get('/api/waitlist', async (request, reply) => {
  const entries = stmts.listWaitlist.all();
  return { entries, total: entries.length };
});

/** POST /api/projects */
app.post('/api/projects', {
  schema: {
    body: {
      type: 'object',
      required: ['name'],
      properties: {
        name: { type: 'string', minLength: 1, maxLength: 100 },
      },
    },
  },
}, async (request, reply) => {
  const { name } = request.body;
  const project = {
    id: randomUUID(),
    name,
    api_key: generateApiKey(),
    created_at: new Date().toISOString(),
  };
  stmts.insertProject.run(project.id, project.name, project.api_key, project.created_at);
  reply.code(201).send(project);
});

/** GET /api/projects/:id */
app.get('/api/projects/:id', async (request, reply) => {
  const project = stmts.getProjectById.get(request.params.id);
  if (!project) return reply.code(404).send({ error: 'Project not found' });
  const { api_key, ...safe } = project;
  return safe;
});

/** POST /api/runs */
app.post('/api/runs', {
  schema: {
    body: {
      type: 'object',
      required: ['branch', 'commit_sha', 'test_results'],
      properties: {
        branch: { type: 'string' },
        commit_sha: { type: 'string' },
        duration_ms: { type: 'number' },
        test_results: {
          type: 'array',
          items: {
            type: 'object',
            required: ['test_name', 'status', 'duration_ms'],
            properties: {
              test_name: { type: 'string' },
              file_path: { type: 'string' },
              status: { type: 'string', enum: ['passed', 'failed', 'skipped', 'flaky'] },
              duration_ms: { type: 'number' },
              error_message: { type: 'string' },
            },
          },
        },
      },
    },
  },
}, async (request, reply) => {
  const project = getAuthProject(request);
  if (!project) return reply.code(401).send({ error: 'Unauthorized — provide a valid Bearer API key' });

  const { branch, commit_sha, duration_ms, test_results } = request.body;

  const passCount = test_results.filter(t => t.status === 'passed').length;
  const failCount = test_results.filter(t => t.status === 'failed').length;
  const totalCount = test_results.length;
  const runStatus = failCount === 0 ? 'passed' : passCount === 0 ? 'failed' : 'partial';

  const run = {
    id: randomUUID(),
    project_id: project.id,
    branch,
    commit_sha,
    triggered_at: new Date().toISOString(),
    duration_ms: duration_ms || test_results.reduce((s, t) => s + (t.duration_ms || 0), 0),
    status: runStatus,
    pass_count: passCount,
    fail_count: failCount,
    total_count: totalCount,
  };

  const resultRows = test_results.map(t => ({ id: randomUUID(), ...t }));

  insertRunWithResults(run, resultRows);

  reply.code(201).send({
    id: run.id,
    status: run.status,
    pass_count: passCount,
    fail_count: failCount,
    total_count: totalCount,
    triggered_at: run.triggered_at,
  });
});

/** GET /api/runs */
app.get('/api/runs', async (request, reply) => {
  const project = getAuthProject(request);
  if (!project) return reply.code(401).send({ error: 'Unauthorized' });

  const limit = Math.min(parseInt(request.query.limit || '20'), 100);
  const runs = stmts.listRunsByProject.all(project.id, limit);
  const { cnt: total } = stmts.countRunsByProject.get(project.id);

  return { runs, total };
});

/** GET /api/runs/:id */
app.get('/api/runs/:id', async (request, reply) => {
  const project = getAuthProject(request);
  if (!project) return reply.code(401).send({ error: 'Unauthorized' });

  const run = stmts.getRunById.get(request.params.id);
  if (!run) return reply.code(404).send({ error: 'Run not found' });
  if (run.project_id !== project.id) return reply.code(403).send({ error: 'Forbidden' });

  const test_results = stmts.getTestResultsByRun.all(run.id);
  return { ...run, test_results };
});

/** GET /api/flakiness */
app.get('/api/flakiness', async (request, reply) => {
  const project = getAuthProject(request);
  if (!project) return reply.code(401).send({ error: 'Unauthorized' });

  const scores = stmts.getFlakinessForProject.all(project.id);
  return { scores, total: scores.length };
});

/** GET /api/analytics/summary */
app.get('/api/analytics/summary', async (request, reply) => {
  const project = getAuthProject(request);
  if (!project) return reply.code(401).send({ error: 'Unauthorized' });

  const runs = stmts.getRecentRuns.all(project.id);

  if (runs.length === 0) {
    return { total_runs: 0, pass_rate: null, avg_duration_ms: null, trend: [] };
  }

  const passedCount = runs.filter(r => r.status === 'passed').length;
  const passRate = Math.round((passedCount / runs.length) * 1000) / 10;
  const avgDuration = Math.round(runs.reduce((s, r) => s + (r.duration_ms || 0), 0) / runs.length);

  const trend = [...runs].reverse().slice(-10).map(r => ({
    run_id: r.id,
    triggered_at: r.triggered_at,
    status: r.status,
    pass_count: r.pass_count,
    fail_count: r.fail_count,
    duration_ms: r.duration_ms,
  }));

  return { total_runs: runs.length, pass_rate: passRate, avg_duration_ms: avgDuration, trend };
});

// ─── Graceful shutdown ─────────────────────────────────────────────────────

process.on('SIGTERM', () => {
  app.log.info('SIGTERM received — shutting down gracefully');
  db.close();
  process.exit(0);
});

process.on('SIGINT', () => {
  db.close();
  process.exit(0);
});

// ─── Start ─────────────────────────────────────────────────────────────────

const start = async () => {
  try {
    await app.listen({ port: PORT, host: HOST });
    app.log.info(`FlowTest API v0.3.0 (SQLite, Railway-ready) running on http://${HOST}:${PORT}`);
    app.log.info(`Database: ${DB_PATH}`);
    app.log.info(`Health: http://localhost:${PORT}/health`);
  } catch (err) {
    app.log.error(err);
    process.exit(1);
  }
};

start();
