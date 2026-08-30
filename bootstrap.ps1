# ─────────────────────────────────────────────────────────────────────────────
#  FlakyGuard — One-Command Bootstrap (Windows PowerShell)
#  Usage:
#    .\bootstrap.ps1                                     # Web lab only
#    $env:GROQ_API_KEY="gsk_..."; .\bootstrap.ps1 eval  # Full benchmark eval
#    $env:GROQ_API_KEY="gsk_..."; .\bootstrap.ps1 mcp   # MCP server for IDE
# ─────────────────────────────────────────────────────────────────────────────

param(
    [ValidateSet("web","eval","mcp","diagnose","help")]
    [string]$Mode = "web",
    [string]$Target = ""
)

$ErrorActionPreference = "Stop"

function Write-Info  { param($msg) Write-Host "[FlakyGuard] $msg" -ForegroundColor Cyan }
function Write-Ok    { param($msg) Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Err   { param($msg) Write-Host "[ERR] $msg" -ForegroundColor Red; exit 1 }

# ── Pre-flight checks ─────────────────────────────────────────────────────────
Write-Info "FlakyGuard Bootstrap — mode: $Mode"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Err "Python 3.11+ is required. Install from https://python.org"
}

$pyVersion = python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")'
Write-Ok "Python $pyVersion detected"

# ── Virtual Environment ───────────────────────────────────────────────────────
$pythonExec = "python"
if (-not (Test-Path ".venv")) {
    Write-Info "Creating virtual environment..."
    python -m venv .venv
}

if (Test-Path ".\.venv\Scripts\python.exe") {
    $pythonExec = ".\.venv\Scripts\python.exe"
}

Write-Info "Installing dependencies via $pythonExec..."
& $pythonExec -m pip install --quiet --disable-pip-version-check -r requirements.txt
Write-Ok "Dependencies installed"

# ── Environment variables ─────────────────────────────────────────────────────
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^\s*([^#][^=]+)=(.+)$") {
            [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
        }
    }
    Write-Ok "Loaded .env"
}

$groqKey = $env:GROQ_API_KEY

# ── Mode dispatch ─────────────────────────────────────────────────────────────
switch ($Mode) {
    "web" {
        Write-Ok "Starting interactive Forensic Lab at http://localhost:8080 ..."
        Write-Host ""
        & $pythonExec -m http.server 8080 --directory web
    }
    "eval" {
        if (-not $groqKey) { Write-Err "GROQ_API_KEY required. Set `$env:GROQ_API_KEY or add to .env" }
        $evalMode = if ($env:EVAL_MODE) { $env:EVAL_MODE } else { "full" }
        Write-Info "Running benchmark evaluation (mode: $evalMode)..."
        Write-Host ""
        & $pythonExec eval/run_eval.py --mode $evalMode
    }
    "mcp" {
        if (-not $groqKey) { Write-Err "GROQ_API_KEY required." }
        Write-Info "Starting MCP server (stdio mode for Cursor / Claude Code)..."
        & $pythonExec mcp/server.py
    }
    "diagnose" {
        if (-not $groqKey) { Write-Err "GROQ_API_KEY required." }
        if (-not $Target)  { Write-Err "Usage: .\bootstrap.ps1 diagnose -Target <test_file::test_function>" }
        Write-Info "Diagnosing: $Target"
        & $pythonExec -m agent.cli diagnose $Target
    }
    "help" {
        Write-Host ""
        Write-Host "Usage: .\bootstrap.ps1 [web|eval|mcp|diagnose] [-Target <test>]"
        Write-Host "  web      — Launch interactive Forensic Lab at http://localhost:8080"
        Write-Host "  eval     — Run full 10-case benchmark (requires GROQ_API_KEY)"
        Write-Host "  mcp      — Start MCP server for Cursor / Claude Code"
        Write-Host "  diagnose — Diagnose a specific test (requires -Target)"
    }
}
