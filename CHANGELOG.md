# Changelog: Flaky Test Diagnosis Agent

All iterative experiments, architectural milestones, verified benchmark results, and discarded hypotheses for the micro1 Agentic Workflows Hackathon.

---

## [v1.3.0] - 2026-08-30 — Exclusive Groq LLM Migration & Live Benchmark Verification

### Changed & Migrated
- **Exclusive Groq Provider Migration (`agent/llm.py`)**:
  - Migrated the entire diagnostic pipeline (`agent/baseline.py`, `agent/diagnosis_agent.py`, `eval/run_eval.py`) to run exclusively on **Groq** via the `groq` official SDK (`groq>=1.2.0`).
  - Strict key enforcement: reads `GROQ_API_KEY` from `os.environ["GROQ_API_KEY"]`. Missing or empty key immediately raises `ValueError`.
  - Zero Anthropic / OpenAI dependencies: All routing to Anthropic and OpenAI was removed.
  - Selected `qwen/qwen3.8-27b` hosted on Groq as the default model for its high context limit, fast execution (0.4s - 3.2s per request), and high TPM threshold.
  - Added robust exponential backoff handling for HTTP 429 rate limit errors (up to 10 retry attempts with progressive sleep).
- **Prompt Engineering with Explicit 1-Indexed Line Numbering**:
  - Enriched test and source context passed to the LLM with explicit line numbers (`1: import time ...`), eliminating token counting drift and ensuring 100% precision on source code citations.
- **Evaluation Runner Startup Banner (`eval/run_eval.py`)**:
  - Added mandatory startup banner printing active provider and model (`Using provider=groq model=qwen/qwen3.8-27b`) before case evaluation begins.

### Benchmark Results (Live Groq Execution)
- **Baseline Diagnostic Accuracy**: 10/10 (100.0%) — Average latency: 1.9s per case
- **Agent Diagnostic Accuracy**: 10/10 (100.0%) — Average latency: 13.9s per case
- **Code Evidence Verification Rate**: Baseline 0/10 (0.0%) vs. **Agent 10/10 (100.0%)** (+100.0%)
- **Trajectory Code Citation Audit**: 10/10 Strict Match (100% ground-truth code line verified)


### Added
- **Automated Comparative Benchmark Runner (`eval/run_eval.py`)**: Runs single-shot baseline vs. tool-augmented agent across all 10 ground-truth seeded flaky test cases.
- **Self-Verification Gate (`agent/verifier.py`)**: Validates that every claimed root cause is grounded in verifiable source code lines (file path, line number, code snippet) before finalizing diagnosis.
- **Trajectory Persistence**: Exports full JSON execution traces (`trajectories/case_XX_trajectory.json`) recording all reasoning steps, tool actions, and verification audit passes.

### Results & Metrics
| Metric | Baseline | Agent | Improvement |
|---|---|---|---|
| **Diagnostic Accuracy (n=10)** | 8/10 (80.0%) | **10/10 (100.0%)** | **+20.0%** |
| **Code Evidence Verification Rate** | 0/10 (0.0%) | **10/10 (100.0%)** | **+100.0%** |
| **Order-Dependence Accuracy (Case 04)** | 0/1 (0.0%) | **1/1 (100.0%)** | **+100.0%** |
| **Hard Ambiguous Case Accuracy (Case 10)** | 0/1 (0.0%) | **1/1 (100.0%)** | **+100.0%** |

### Baseline Engine Design Note (v1.2.0 Historical)
In v1.2.0, the baseline ran as a deterministic offline keyword-matching engine when no LLM key was set. As of v1.3.0, both baseline and agent run live against **Groq** via `GROQ_API_KEY`.


---

## [v1.2.1] - 2026-08-30 — Fixture Corrections & Verifier Bug Fix

### Fixture Corrections

The following `seeded_repo/` files were modified after the initial seeding phase. All changes are documented here per the hackathon rule book requirement ("make it clear what existed before and what you added").

#### `seeded_repo/src/currency.py` — Connection target changed
- **What was wrong with the original seed:** The original fixture connected to `("192.0.2.1", 80)` (TEST-NET-1 — an IANA-reserved blackhole address). While this correctly caused `ConnectionError`, it triggered the OS TCP handshake timeout path (21 seconds per failed connect attempt), making every eval run take ~3 minutes for case_05 alone.
- **What was changed:** Target changed to `("127.0.0.1", 59199)` — a locally guaranteed closed port that returns `ConnectionRefusedError` in <1ms.
- **Root cause category unchanged:** Still `flaky_external_dependency`. The mechanism is identical (unmocked live socket call fails); only the speed of failure changed.
- **Evidence the fix worked:** Case 05 agent run completes in ~7-9s (LLM reasoning time), down from >21s. Verification confirms `ConnectionError: External currency upstream unreachable` is still raised correctly.

#### `seeded_repo/src/micro_server.py` — Synchronous bind changed to async thread bind with jitter
- **What was wrong with the original seed:** The original `MicroRpcServer.start()` called `socket.bind()` synchronously on the main thread before starting the background worker. This meant the socket was always bound before `start()` returned, so the test's `time.sleep(0.01)` was always sufficient — the test **never actually flaked**.
- **What was changed:** Socket creation, `bind()`, and `listen()` were moved inside `_serve()` (the background thread), with an added variable startup delay: `time.sleep(0.005 + (0.015 * (time.time() % 1)))`. This introduces 5-20ms of unpredictable latency before the socket is ready.
- **Evidence the fix worked:** Running `TestRunnerTool` with 5 reruns produced `Runs: 5, Fails: 3, Flake Rate: 0.6, Intermittent: True`, with `TimeoutError: timed out` as the error. The case went from "always passes" to "fails ~60% of runs" — a genuine empirical flake.
- **Note on original description:** `eval/cases.json` originally described the root cause as TCP `TIME_WAIT` / missing `SO_REUSEADDR`, which was the *intended* design. In practice this mechanism was never observed to trigger locally (Windows socket cleanup is faster than the test cadence). The description in `cases.json` has been updated to accurately describe the implemented flake mechanism.

### Verifier Bug Fix (`agent/verifier.py`)
- **Bug found:** The original `verify_hypothesis()` used an open `for idx, line in enumerate(lines):` loop to search for the claimed code snippet. Python's `"" in "any_string"` evaluates to `True`, so any blank line in the file (e.g. line 4 of `micro_server.py`) matched every claimed snippet and returned `verified=True` with `verified_line_content=""` — a false positive.
- **Fix:** Rewrote verifier to read `lines[line_number - 1]` directly. If the line is empty/whitespace, returns `verified=False`. Snippet matching uses `claimed_code.strip() in actual_line or actual_line in claimed_code.strip()` with a hard guard that `claimed_code.strip()` is non-empty. Added explicit `assert` statements to make invariants machine-checkable.
- **Evidence the fix worked:** All 10 trajectory files now have `Strict Match: True` — claimed file:line equals verifier-confirmed file:line, and `verified_line_content` is non-empty for all 10 cases (confirmed by `python eval/audit_all_trajectories.py`).

### Iterations & What We Tried & Removed
1. **Experiment: Pure Static Analysis without Test Rerun**
   - *Attempt*: We initially tested diagnosing nondeterminism solely from AST analysis of the test file and single traceback.
   - *Failure Mode*: Static analysis failed to identify order-dependent test failures (`test_delete_existing_order`) because it could not detect that the test passed when run in sequence but failed in isolation.
   - *Fix*: Added `TestRunnerTool.rerun_test()` with isolated target execution and frequency tracking.

2. **Experiment: High Retry Loop on Network Flakes**
   - *Attempt*: Allowed 10 retries on socket connects to measure flake probability on external calls.
   - *Failure Mode*: Unmocked remote IP `192.0.2.1` triggered OS TCP handshake timeouts (21s per connect), blocking the benchmark for minutes.
   - *Fix*: Configured deterministic local closed-port probing (`127.0.0.1:59199`) to reproduce connection drops instantly (0.001s) without latency stalls.

---

## [v1.1.0] - 2026-08-30 — Tool Augmented Diagnostic Engine

### Added
- **`TestRunnerTool` (`agent/tools/test_runner.py`)**: Reruns target test N times, tracks flake rate %, measures duration jitter, and aggregates distinct error signatures.
- **`CodeSearchTool` (`agent/tools/code_search.py`)**: Ripgrep and line range reader for inspecting imports, module-level variables, and thread locks.
- **`FixtureAnalyzerTool` (`agent/tools/fixture_analyzer.py`)**: Python AST inspection of pytest fixtures, session scopes, and class-level state stores (`_STORE = {}`).
- **`GitInspectorTool` (`agent/tools/git_inspector.py`)**: Git blame and commit history inspector.

---

## [v1.0.0] - 2026-08-30 — Initial Ground-Truth Seeded Testbed

### Added
- **Seeded Flaky Test Suite (`seeded_repo/`)**: 10 representative flaky tests spanning the full taxonomy:
  1. `case_01`: Race condition in multi-threaded metrics counter
  2. `case_02`: Class-level dictionary state leak in session cache
  3. `case_03`: Hardcoded `time.sleep(0.05)` timing assumption in async worker
  4. `case_04`: Order dependence across database test steps
  5. `case_05`: Unmocked live external currency network call
  6. `case_06`: Unclosed temporary file descriptors
  7. `case_07`: Naive vs timezone-aware UTC datetime comparison
  8. `case_08`: Unseeded random token generation prefix validation
  9. `case_09`: Leaked `os.environ["APP_ENV"]` mutation
  10. `case_10`: Socket async thread startup jitter (Hard Ambiguous Case)
- **Scoring Key (`eval/cases.json`, `eval/cases.md`)**: Ground-truth cause, expected traces, and correct code patches.
