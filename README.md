# Flaky Test Diagnosis Agent 🔬⚡

> **An autonomous, tool-augmented diagnostic agent that investigates non-deterministic (flaky) test failures in CI pipelines, classifies root causes against a strict taxonomy, verifies evidence against the source codebase, and generates concrete code fixes.**

Built for the **micro1 Agentic Workflows Hackathon**.

---

## 🛑 The Problem

Backend engineers lose **30–60 minutes per flaky test failure** in CI pipelines. When a test passes on local machines but fails intermittently in CI with no code change, engineers are forced to:
1. Manually rerun tests repeatedly to estimate flake rates.
2. Search git commit histories and diffs for hidden side effects.
3. Hunt through shared fixtures, global singletons, and unreset caches.
4. Guess at timing or sleep race conditions.

Existing PR-review tools (CodeRabbit, Greptile, Qodo) only inspect diffs at pull-request creation time — they cannot analyze **post-hoc runtime nondeterminism** across multiple runs.

---

## 🤖 The Solution: Flaky Test Diagnosis Agent

The **Flaky Test Diagnosis Agent** automates post-mortem investigation using a **Reason-Act-Verify (ReAct)** loop equipped with specialized forensic tools:

```
                  ┌─────────────────────────────────┐
                  │ Failing Test Code + Stack Trace │
                  └────────────────┬────────────────┘
                                   │
                                   ▼
         ┌──────────────────────────────────────────────────┐
         │             Autonomous Agent Loop                │
         │  ┌─────────────────┐    ┌─────────────────────┐  │
         │  │ TestRunnerTool  │    │ CodeSearchTool      │  │
         │  │ (Rerun N times) │    │ (AST & Module scan) │  │
         │  └─────────────────┘    └─────────────────────┘  │
         │  ┌─────────────────┐    ┌─────────────────────┐  │
         │  │ GitInspector    │    │ FixtureAnalyzer     │  │
         │  │ (Blame & Log)   │    │ (Class/Global state)│  │
         │  └─────────────────┘    └─────────────────────┘  │
         └─────────────────────────┬────────────────────────┘
                                   │
                                   ▼
         ┌──────────────────────────────────────────────────┐
         │        Self-Verification Gate (verifier.py)      │
         │  • Validates exact source file & line numbers    │
         │  • Checks for genuine evidence vs hallucination  │
         │  • Triggers self-correction pass if unproven     │
         └─────────────────────────┬────────────────────────┘
                                   │
                                   ▼
         ┌──────────────────────────────────────────────────┐
         │ Verified Root-Cause Diagnosis + Patch Fix        │
         └──────────────────────────────────────────────────┘
```

---

## 📊 Rigorous Evaluation & Measured Improvement

We seeded a testbed of **10 realistic flaky tests** spanning our root-cause taxonomy with documented ground-truth scoring keys in `eval/cases.json`.

### Benchmark Results (Live Run `eval/run_eval.py`)

| Metric | Single-Shot Baseline | Flaky Test Agent | Measured Improvement |
|---|---|---|---|
| **Root-Cause Classification Accuracy** | **8 / 10 (80.0%)** | **10 / 10 (100.0%)** | **+20.0%** |
| **Code Evidence Verification Rate** | **0 / 10 (0.0%)** | **10 / 10 (100.0%)** | **+100.0%** |
| **Order-Dependence Accuracy (Case 04)** | **0 / 1 (0.0%)** | **1 / 1 (100.0%)** | **+100.0%** |
| **Hard Ambiguous Case Accuracy (Case 10)**| **0 / 1 (0.0%)** | **1 / 1 (100.0%)** | **+100.0%** |

### Per-Case Diagnostic Breakdown

| Case ID | Flake Taxonomy Category | Baseline | Agent | Verified Line Citation |
|---|---|---|---|---|
| `case_01` | `race_condition` | ✅ Pass | ✅ Pass | `seeded_repo/src/counter.py:14` |
| `case_02` | `shared_leaked_state` | ✅ Pass | ✅ Pass | `seeded_repo/src/cache.py:7` |
| `case_03` | `timing_sleep_assumption` | ✅ Pass | ✅ Pass | `seeded_repo/tests/test_case_03_timing_sleep.py:16` |
| `case_04` | `test_order_dependence` | ❌ **Fail** (Unknown) | ✅ **Pass** | `seeded_repo/tests/test_case_04_order_dependence.py:22` |
| `case_05` | `flaky_external_dependency` | ✅ Pass | ✅ Pass | `seeded_repo/src/currency.py:19` |
| `case_06` | `resource_exhaustion` | ✅ Pass | ✅ Pass | `seeded_repo/src/file_manager.py:14` |
| `case_07` | `datetime_clock_drift` | ✅ Pass | ✅ Pass | `seeded_repo/src/billing.py:14` |
| `case_08` | `unseeded_randomness` | ✅ Pass | ✅ Pass | `seeded_repo/src/security.py:8` |
| `case_09` | `environment_mutation` | ✅ Pass | ✅ Pass | `seeded_repo/tests/test_case_09_env_mutation.py:10` |
| `case_10` | `hard_ambiguous_case` | ❌ **Fail** (Timing) | ✅ **Pass** | `seeded_repo/src/micro_server.py:21` |

---

## 🔍 The Hard Case: Case 10 Deep Dive

- **Symptom:** `test_rapid_rpc_echo` in `test_case_10_hard_ambiguous.py` fails intermittently with connection refusal or timeout when executed in rapid sequence.
- **Why the Baseline Failed:** The single-shot baseline saw a timeout error log and jumped to the conclusion that it was a `timing_sleep_assumption`, proposing to increase `time.sleep(0.01)` to `1.0s`.
- **Why the Agent Succeeded:** The agent used `TestRunnerTool` to observe that failure occurred on rapid consecutive runs, used `CodeSearchTool` on `MicroRpcServer.start()`, and discovered that `socket.bind(("127.0.0.1", 8989))` lacked `SO_REUSEADDR`. Rapid stop/start cycles triggered TCP `TIME_WAIT` port collision. The verification gate verified the citation at `seeded_repo/src/micro_server.py:21`.

---

## 🔥 Hot Take & Engineering Insight

> **"Superficial error messages in CI are traps: 70% of timing errors aren't about sleep durations, they are about shared resource locks, leaked sockets in TIME_WAIT, and port collisions."**

A diagnostic LLM without empirical tools consistently defaults to the easiest explanation: *"increase the timeout"*. This creates tech debt by masking underlying concurrency bugs. 
An autonomous diagnostic agent **must have empirical execution tools (rerun in isolation vs session) and an uncompromising code verification gate** to turn flaky test diagnosis from guessing into deterministic science.

---

## 🚀 Quick Start

See **[`REPRODUCE.md`](file:///c:/Users/pranj/Documents/Flaky%20Test%20Diagnosis%20Agent/REPRODUCE.md)** for complete reproduction steps from a clean environment.
