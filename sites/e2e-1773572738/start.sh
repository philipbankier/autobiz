#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# FlowTest — Full Stack Launcher
# Starts the API server + a static file server for the frontend
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_DIR="$SCRIPT_DIR/api"
API_PORT="${API_PORT:-3000}"
STATIC_PORT="${STATIC_PORT:-8080}"

# ─── Colors ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log()  { echo -e "${CYAN}[flowtest]${NC} $*"; }
ok()   { echo -e "${GREEN}[flowtest]${NC} $*"; }
warn() { echo -e "${YELLOW}[flowtest]${NC} $*"; }
err()  { echo -e "${RED}[flowtest]${NC} $*"; }

# ─── Cleanup on exit ─────────────────────────────────────────────────────────
API_PID=""
STATIC_PID=""

cleanup() {
  echo ""
  log "Shutting down..."
  [ -n "$API_PID" ]    && kill "$API_PID"    2>/dev/null && log "API server stopped (PID $API_PID)"
  [ -n "$STATIC_PID" ] && kill "$STATIC_PID" 2>/dev/null && log "Static server stopped (PID $STATIC_PID)"
  ok "Done. Goodbye!"
  exit 0
}

trap cleanup SIGINT SIGTERM

# ─── Preflight checks ────────────────────────────────────────────────────────
log "FlowTest — starting full stack..."
echo ""

# Check node is available
if ! command -v node &>/dev/null; then
  err "node is not installed or not in PATH."
  exit 1
fi

# Install API dependencies if node_modules is missing
if [ ! -d "$API_DIR/node_modules" ]; then
  warn "node_modules not found — running npm install..."
  (cd "$API_DIR" && npm install --silent)
  ok "Dependencies installed."
fi

# ─── Start API Server ─────────────────────────────────────────────────────────
log "Starting API server on port $API_PORT..."
PORT="$API_PORT" node "$API_DIR/server.js" &
API_PID=$!

# Wait for API to be ready (up to 10s)
API_URL="http://localhost:$API_PORT/health"
for i in {1..20}; do
  sleep 0.5
  if curl -sf "$API_URL" &>/dev/null; then
    ok "API server ready  →  http://localhost:$API_PORT"
    break
  fi
  if ! kill -0 "$API_PID" 2>/dev/null; then
    err "API server process exited unexpectedly."
    exit 1
  fi
  if [ "$i" -eq 20 ]; then
    err "API server did not become healthy within 10s."
    kill "$API_PID" 2>/dev/null
    exit 1
  fi
done

# ─── Start Static File Server ────────────────────────────────────────────────
# Try npx serve (most common), fall back to python3 http.server
if command -v npx &>/dev/null && npx --yes serve --version &>/dev/null 2>&1; then
  log "Starting static server (serve) on port $STATIC_PORT..."
  npx --yes serve "$SCRIPT_DIR" --listen "$STATIC_PORT" --no-clipboard &>/tmp/flowtest-static.log &
  STATIC_PID=$!
elif command -v python3 &>/dev/null; then
  log "Starting static server (python3) on port $STATIC_PORT..."
  python3 -m http.server "$STATIC_PORT" --directory "$SCRIPT_DIR" &>/tmp/flowtest-static.log &
  STATIC_PID=$!
else
  warn "No static server found (serve / python3). Skipping — open files directly."
  warn "  Landing page: file://$SCRIPT_DIR/index.html"
  warn "  Dashboard:    file://$SCRIPT_DIR/dashboard.html"
fi

sleep 1

# ─── Summary ─────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  FlowTest is running!${NC}"
echo ""
echo -e "  🌐  Landing page   →  ${CYAN}http://localhost:$STATIC_PORT/index.html${NC}"
echo -e "  📊  Dashboard      →  ${CYAN}http://localhost:$STATIC_PORT/dashboard.html${NC}"
echo -e "  ⚡  API server     →  ${CYAN}http://localhost:$API_PORT${NC}"
echo -e "  ❤️   Health check   →  ${CYAN}http://localhost:$API_PORT/health${NC}"
echo ""
echo -e "  Press ${YELLOW}Ctrl+C${NC} to stop all services."
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# ─── Keep running ────────────────────────────────────────────────────────────
wait
