#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  FlakyGuard — One-Command Bootstrap (Linux / macOS)
#  Usage:
#    ./bootstrap.sh                          # Web lab only (no API key needed)
#    GROQ_API_KEY=gsk_... ./bootstrap.sh eval  # Full benchmark evaluation
#    GROQ_API_KEY=gsk_... ./bootstrap.sh mcp   # MCP server for IDE integration
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

MODE="${1:-web}"
GROQ_API_KEY="${GROQ_API_KEY:-}"

# ── Colour helpers ────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; CYAN='\033[0;36m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${CYAN}[FlakyGuard]${NC} $*"; }
ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
err()   { echo -e "${RED}[ERR]${NC} $*"; exit 1; }

# ── Pre-flight checks ─────────────────────────────────────────────────────────
info "FlakyGuard Bootstrap — mode: ${MODE}"
command -v python3 &>/dev/null || err "Python 3.11+ is required. Install from https://python.org"

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if [[ "$(echo "$PYTHON_VERSION < 3.10" | bc -l 2>/dev/null || python3 -c "print(int(float('$PYTHON_VERSION') < 3.10))")" == "1" ]]; then
    err "Python 3.10+ required (found $PYTHON_VERSION)"
fi
ok "Python $PYTHON_VERSION detected"

# ── Virtual Environment ───────────────────────────────────────────────────────
if [[ ! -d ".venv" ]]; then
    info "Creating virtual environment..."
    python3 -m venv .venv
fi
source .venv/bin/activate
info "Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
ok "Dependencies installed"

# ── Environment variables ─────────────────────────────────────────────────────
if [[ -f ".env" ]]; then
    set -a; source .env; set +a
    ok "Loaded .env"
elif [[ -n "$GROQ_API_KEY" ]]; then
    export GROQ_API_KEY
    ok "GROQ_API_KEY loaded from environment"
fi

# ── Mode dispatch ─────────────────────────────────────────────────────────────
case "$MODE" in
  web)
    ok "Starting interactive Forensic Lab at http://localhost:8080 ..."
    echo ""
    python3 -m http.server 8080 --directory web
    ;;

  eval)
    [[ -z "$GROQ_API_KEY" ]] && err "GROQ_API_KEY required. Export it or add to .env"
    EVAL_MODE="${EVAL_MODE:-full}"
    info "Running benchmark evaluation (mode: $EVAL_MODE)..."
    echo ""
    python3 eval/run_eval.py --mode "$EVAL_MODE"
    ;;

  mcp)
    [[ -z "$GROQ_API_KEY" ]] && err "GROQ_API_KEY required. Export it or add to .env"
    info "Starting MCP server (stdio mode for Cursor / Claude Code)..."
    python3 mcp/server.py
    ;;

  diagnose)
    [[ -z "$GROQ_API_KEY" ]] && err "GROQ_API_KEY required."
    [[ -z "${2:-}" ]] && err "Usage: ./bootstrap.sh diagnose <test_file::test_function>"
    info "Diagnosing: $2"
    python3 -m agent.cli diagnose "$2"
    ;;

  *)
    echo "Usage: $0 [web|eval|mcp|diagnose <target>]"
    echo "  web      — Launch interactive Forensic Lab at http://localhost:8080"
    echo "  eval     — Run full 10-case benchmark (requires GROQ_API_KEY)"
    echo "  mcp      — Start MCP server for Cursor / Claude Code (requires GROQ_API_KEY)"
    echo "  diagnose — Diagnose a specific test (requires GROQ_API_KEY)"
    exit 1
    ;;
esac
