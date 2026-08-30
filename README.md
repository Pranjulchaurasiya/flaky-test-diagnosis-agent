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
         │  ┌────────────────────┐ ┌─────────────────────┐  │
         │  │ TestRunnerTool     │ │ CodeSearchTool      │  │
         │  │ (Rerun N times)    │ │ (AST & Module scan) │  │
         │  └────────────────────┘ └─────────────────────┘  │
         │  ┌────────────────────┐ ┌─────────────────────┐  │
         │  │ GitInspectorTool   │ │ FixtureAnalyzerTool │  │
         │  │ (Blame & Log)      │ │ (Class/Global state)│  │
         │  └────────────────────┘ └─────────────────────┘  │
         └────────────────────────┬─────────────────────────┘
                                   │
                                   ▼
         ┌──────────────────────────────────────────────────┐
         │       Self-Verification Gate (verifier.py)       │
         │  • Validates exact source file & line numbers    │
         │  • Checks for genuine evidence vs hallucination  │
         │  • Triggers self-correction pass if unproven     │
         └────────────────────────┬─────────────────────────┘
                                   │
                                   ▼
         ┌──────────────────────────────────────────────────┐
         │ Verified Root-Cause Diagnosis + Patch Fix        │
         └──────────────────────────────────────────────────┘
```

---

## 📊 Rigorous Evaluation & Measured Improvement

We seeded a testbed of **10 realistic flaky tests** spanning our root-cause taxonomy with documented ground-truth scoring keys in [`eval/cases.json`](eval/cases.json). Both the single-shot baseline and the autonomous agent are evaluated using live inference with Groq (`qwen/qwen3.8-27b`).

### Primary Finding: Code Evidence Verification Rate (+100.0%)

While classification accuracy between the single-shot baseline and the agent is tied at **100.0% (10/10)** due to the strength of the live reasoning model (`qwen/qwen3.8-27b`), the **single-shot baseline cannot provide or verify grounded source code evidence (0.0%)**. In contrast, the tool-augmented agent achieves a **100.0% Code Evidence Verification Rate**, proving every single diagnosis with exact, verified file and line citations from the codebase.

### Benchmark Results (Live Run `eval/run_eval.py`)

| Metric | Single-Shot Baseline | Flaky Test Agent | Measured Improvement |
|---|---|---|---|
| **Code Evidence Verification Rate** | **0 / 10 (0.0%)** | **10 / 10 (100.0%)** | **+100.0%** |
| **Diagnostic Classification Accuracy (n=10)** | **10 / 10 (100.0%)** | **10 / 10 (100.0%)** | **+0.0%** |
| **Hard Case Accuracy (case_10)** | **1 / 1 (Passed)** | **1 / 1 (Passed)** | **0%** |

### Per-Case Diagnostic Breakdown

| Case ID | Flake Taxonomy Category | Baseline | Agent | Verified Line Citation |
|---|---|---|---|---|
| `case_01` | `race_condition` | ✅ Pass (8.99s) | ✅ Pass (17.62s) | `seeded_repo/src/counter.py:14` |
| `case_02` | `shared_leaked_state` | ✅ Pass (1.86s) | ✅ Pass (13.32s) | `seeded_repo/src/cache.py:6` |
| `case_03` | `timing_sleep_assumption` | ✅ Pass (1.71s) | ✅ Pass (11.93s) | `seeded_repo/tests/test_case_03_timing_sleep.py:16` |
| `case_04` | `test_order_dependence` | ✅ Pass (11.07s) | ✅ Pass (14.61s) | `seeded_repo/tests/test_case_04_order_dependence.py:22` |
| `case_05` | `flaky_external_dependency` | ✅ Pass (1.70s) | ✅ Pass (13.57s) | `seeded_repo/src/currency.py:19` |
| `case_06` | `resource_exhaustion` | ✅ Pass (1.56s) | ✅ Pass (9.31s) | `seeded_repo/src/file_manager.py:16` |
| `case_07` | `datetime_clock_drift` | ✅ Pass (1.43s) | ✅ Pass (9.06s) | `seeded_repo/src/billing.py:11` |
| `case_08` | `unseeded_randomness` | ✅ Pass (4.43s) | ✅ Pass (9.92s) | `seeded_repo/src/security.py:14` |
| `case_09` | `environment_mutation` | ✅ Pass (5.60s) | ✅ Pass (11.13s) | `seeded_repo/tests/test_case_09_env_mutation.py:10` |
| `case_10` | `hard_ambiguous_case` | ✅ Pass (6.70s) | ✅ Pass (12.96s) | `seeded_repo/src/micro_server.py:24` |

---

## 🔍 The Hard Case: Case 10 Deep Dive

- **Symptom:** `test_rapid_rpc_echo` in `test_case_10_hard_ambiguous.py` tests an asynchronous background RPC server that binds to a port and serves requests.
- **Fixture Calibration & Discovery:** During testbed auditing, we discovered that `MicroRpcServer` originally bound synchronously without latency variance, causing 0/3 rerun failures. To ensure the case realistically modeled race-prone initialization, variable async startup jitter was added at line 24 of `seeded_repo/src/micro_server.py` (`time.sleep(0.005 + (0.015 * (time.time() % 1)))`), producing a real ~60% empirical flake rate and reproducing genuine `TimeoutError` exceptions (documented in [`CHANGELOG.md`](CHANGELOG.md)).
- **Agent Diagnostic Path:** The agent used `TestRunnerTool` to measure the empirical flake rate, used `CodeSearchTool` to inspect `MicroRpcServer.start()`, and pinpointed line 24 as the uncoordinated async delay. The self-verification gate verified the exact citation at `seeded_repo/src/micro_server.py:24` and generated a deterministic `threading.Event()` synchronization patch.

---

## 🔥 Hot Take & Engineering Insight

> **"Superficial error messages in CI are traps: 70% of timing errors aren't about sleep durations, they are about shared resource locks, leaked sockets in TIME_WAIT, and port collisions."**

A diagnostic LLM without empirical tools consistently defaults to the easiest explanation: *"increase the timeout"*. This creates tech debt by masking underlying concurrency bugs. 
An autonomous diagnostic agent **must have empirical execution tools (rerun in isolation vs session) and an uncompromising code verification gate** to turn flaky test diagnosis from guessing into deterministic science.

---

## 🚀 Quick Start

See **[`REPRODUCE.md`](REPRODUCE.md)** for complete reproduction steps from a clean environment.
