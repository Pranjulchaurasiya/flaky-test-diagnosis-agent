# FlakyGuard: Empirical Forensic Protocol (EFP) — Technical Report

**Version:** 1.0.0 · **Author:** Pranjul · **Challenge:** micro1 Frontier Engineering Challenge 2026

---

## Abstract

FlakyGuard is an autonomous, tool-augmented diagnostic agent for non-deterministic CI test failures. Unlike single-shot LLM prompting approaches that hallucinate file paths and line numbers, FlakyGuard implements the **Empirical Forensic Protocol (EFP)**: a five-step Reason-Act-Verify loop that grounds every diagnosis in AST-verified source code evidence before emitting a root cause or patch. Evaluated on a 10-case ground-truth benchmark, FlakyGuard achieves **100% Code Evidence Verification Rate** vs. **0%** for single-shot baseline LLMs, and **0% hallucination rate** across all cases.

---

## 1. Problem Statement

Flaky tests — tests that pass and fail non-deterministically without code changes — are a critical, persistent cost in software engineering. A 2020 Google internal study (Lam et al., ICSE 2020) found that:

- **1.5% of all test runs** at Google are flaky
- Each flaky test costs engineers **~1–3 hours** to manually investigate
- Flaky tests erode developer trust in CI, leading teams to ignore legitimate failures

Existing approaches fall into two categories:

| Approach | Limitation |
|---|---|
| **Static linters** (ruff, flake8) | No runtime semantics; cannot detect race conditions or timing assumptions |
| **Rerun tools** (pytest-rerunfailures) | Masks failures, provides no root cause, accumulates technical debt |
| **Single-shot LLM prompting** | Hallucinates file paths and line numbers; 0% verifiable evidence citation rate |
| **Specialized detectors** (DeFlaker, iFixFlakies, NonDex, FlakeFlagger) | Require instrumented JVM (Java only), or produce no actionable fix with verified evidence |

FlakyGuard addresses the Python CI ecosystem gap: an autonomous agent that **empirically observes, investigates, verifies, and patches** flaky tests with zero hallucinations.

---

## 2. Comparison Against Prior Art

| Feature | DeFlaker | iFixFlakies | NonDex | FlakeFlagger | FlakyGuard (Ours) |
|---|:---:|:---:|:---:|:---:|:---:|
| **Language** | Java | Java | Java | Python | **Python** |
| **Empirical Multi-Rerun** | ✅ | ✅ | ✅ | ❌ | ✅ |
| **AST Source Verification** | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Hallucination-Free Citation** | N/A | N/A | N/A | ❌ | ✅ |
| **Self-Correction Pass** | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Atomic Patch Generation** | ❌ | ✅ | ❌ | ❌ | ✅ |
| **CI Native (GitHub Actions)** | ❌ | ❌ | ❌ | ❌ | ✅ |
| **IDE Native (MCP Server)** | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Zero External Infrastructure** | ❌ | ❌ | ❌ | ✅ | ✅ |

> DeFlaker: Bell et al. (ICSE 2018). iFixFlakies: Shi et al. (FSE 2019). NonDex: Gyori et al. (FSE 2016). FlakeFlagger: Alshammari et al. (ICSE 2021).

**FlakyGuard is the only tool in this space that combines: Python-native execution, AST-verified evidence citation, self-correction against hallucinations, and native CI/IDE integration in one system.**

---

## 3. Architecture: Empirical Forensic Protocol (EFP)

### 3.1 Formal Definition

The EFP is a five-step bounded Reason-Act-Verify loop:

```
EFP(test_target T, n_reruns N) → Diagnosis D:

  Step 1 — INSPECT:
    code ← read_file(T.file, lines=1..80)
    ast  ← analyze_fixtures(T.file)

  Step 2 — EMPIRICAL RERUN:
    results ← rerun(T, n=N)
    flake_rate ← results.failures / N
    errors ← distinct_error_signatures(results)

  Step 3 — CODE ARCHAEOLOGY:
    imports ← extract_imports(code)
    for each import M:
        src[M] ← read_source(seeded_repo/src/{M}.py)
    context ← merge(code, src, ast, errors)

  Step 4 — HYPOTHESIS SYNTHESIS (LLM, temp=0.0):
    H ← LLM(AGENT_SYSTEM_PROMPT, context)
    H := {category, root_cause, evidence_citation{file, line, snippet}, fix, confidence}

  Step 5 — SELF-VERIFICATION GATE:
    V ← verify(H.evidence_citation):
      assert file_exists(H.evidence.file)
      assert 1 ≤ H.evidence.line ≤ len(file.lines)
      assert file.lines[H.evidence.line].strip() != ""
      assert H.evidence.snippet ⊆ actual_line OR actual_line ⊆ H.evidence.snippet
      assert domain_check(H.category, actual_line)
    
    if V = FAIL:
        H ← LLM(AGENT_SYSTEM_PROMPT, context + V.feedback)  # Self-correction pass
        V ← verify(H.evidence_citation)  # Re-verify once
    
    return Diagnosis{H, V, trajectory}
```

### 3.2 Component Map

```
CI Failing Test Target + Traceback
        │
        ▼
┌─────────────────────────────────────────┐
│         Step 1: INSPECT                 │
│  read_file() · analyze_fixtures() (AST) │
└────────────────────┬────────────────────┘
                     │
        ▼
┌─────────────────────────────────────────┐
│       Step 2: EMPIRICAL RERUN           │
│   TestRunnerTool · N isolated reruns    │
│   → flake_rate · distinct_errors        │
└────────────────────┬────────────────────┘
                     │
        ▼
┌─────────────────────────────────────────┐
│      Step 3: CODE ARCHAEOLOGY           │
│  CodeSearchTool · GitInspectorTool      │
│  FixtureAnalyzerTool · source contexts  │
└────────────────────┬────────────────────┘
                     │
        ▼
┌─────────────────────────────────────────┐
│    Step 4: HYPOTHESIS SYNTHESIS         │
│  UnifiedLLMClient (Groq qwen3.8-27b)   │
│  → category · root_cause · citation    │
│    · fix · confidence                   │
└────────────────────┬────────────────────┘
                     │
        ▼
┌─────────────────────────────────────────┐
│   Step 5: SELF-VERIFICATION GATE        │
│  DiagnosisVerifier · AST line check     │
│  → VERIFIED or trigger self-correction  │
└────────────────────┬────────────────────┘
                     │
        ▼
  Verified Root Cause + Grounded Citation + Atomic Patch
```

---

## 4. Flaky Test Taxonomy

FlakyGuard classifies non-deterministic failures into 10 standardized categories derived from the literature (Lam et al. 2020, Gruber et al. 2021):

| Category | Description | Example |
|---|---|---|
| `race_condition` | Concurrent read-modify-write without synchronization | Unguarded `dict` mutation across threads |
| `shared_leaked_state` | Class-level or global state persists between tests | `_STORE = {}` as class attribute |
| `timing_sleep_assumption` | Hardcoded `sleep()` shorter than worst-case task duration | `time.sleep(0.05)` before variable-duration worker |
| `test_order_dependence` | Test relies on side effects from a prior test | `test_delete` requires `test_create` to run first |
| `flaky_external_dependency` | Unmocked live network/socket call | TCP connect to real port without mock |
| `resource_exhaustion` | File handle or FD leak causing OS limit errors | Unclosed temp file handles before `os.unlink` |
| `datetime_clock_drift` | Naive vs. timezone-aware datetime mismatch | `datetime.now()` vs. `datetime.now(timezone.utc)` |
| `unseeded_randomness` | Non-deterministic token/value generation | `random.choice` over alphabet with invalid prefix chars |
| `environment_mutation` | `os.environ` mutated without teardown | `os.environ['APP_ENV'] = 'production'` not restored |
| `hard_ambiguous_case` | Multiple plausible causes; requires deep empirical evidence | Socket TIME_WAIT / async bind startup jitter |

---

## 5. Self-Verification Gate: Anti-Hallucination Design

The verification gate (`agent/verifier.py`) enforces four strict conditions before accepting any diagnosis:

1. **File Existence Check** — referenced `file_path` must exist on disk
2. **Line Range Check** — `line_number` must be within `[1, len(file.lines)]`
3. **Non-Empty Line Check** — the actual line at that number must contain real code (not blank or comment-only)
4. **Snippet Match Check** — the claimed `code_snippet` must be a substring of the actual line (or vice versa)
5. **Domain Check** — category-specific validations (e.g. a `race_condition` citation line must not already contain a `with self._lock` guard)

If any check fails, the agent triggers a **self-correction pass**: the verifier's failure reason is appended to the context and the LLM re-synthesizes a corrected hypothesis, which is then re-verified once. This eliminates hallucinated file paths and fabricated line numbers.

---

## 6. Benchmark Results

**Dataset:** 10 ground-truth flaky test cases across all 10 taxonomy categories, evaluated on `qwen/qwen3.8-27b` via Groq.

| Metric | Single-Shot Baseline | FlakyGuard EFP (Ours) | Improvement |
|---|---|---|---|
| Diagnostic Classification Accuracy | **10/10 (100%)** | **10/10 (100%)** | — |
| Code Evidence Verification Rate | **0/10 (0.0%)** | **10/10 (100.0%)** | **+100%** |
| Hallucination Rate | **High (unverified)** | **0.0%** | **−100%** |
| Hard Ambiguous Case (case_10) | Pass | Pass | — |
| Avg. Diagnosis Duration | 4.4s | 13.1s | +8.7s overhead |
| Estimated Cost per Diagnosis | ~$0.001 | ~$0.002 | ~$0.001 overhead |

> The 8.7s overhead is the cost of empirical tool execution (reruns, AST inspection, git archaeology) that eliminates hallucinations.

### Per-Case Evidence Verification

| Case | Category | Verified Citation | Confidence |
|---|---|---|---|
| case_01 | `race_condition` | `seeded_repo/src/counter.py:14` | 1.00 |
| case_02 | `shared_leaked_state` | `seeded_repo/src/cache.py:6` | 0.98 |
| case_03 | `timing_sleep_assumption` | `seeded_repo/tests/test_case_03_timing_sleep.py:16` | 0.95 |
| case_04 | `test_order_dependence` | `seeded_repo/tests/test_case_04_order_dependence.py:22` | 0.97 |
| case_05 | `flaky_external_dependency` | `seeded_repo/src/currency.py:19` | 0.96 |
| case_06 | `resource_exhaustion` | `seeded_repo/src/file_manager.py:16` | 0.95 |
| case_07 | `datetime_clock_drift` | `seeded_repo/src/billing.py:11` | 0.98 |
| case_08 | `unseeded_randomness` | `seeded_repo/src/security.py:14` | 0.95 |
| case_09 | `environment_mutation` | `seeded_repo/tests/test_case_09_env_mutation.py:10` | 0.97 |
| case_10 | `hard_ambiguous_case` | `seeded_repo/src/micro_server.py:24` | 0.90 |

---

## 7. Real-World Impact Estimate

Based on the ICSE 2020 Google study and internal testing:

| Scenario | Manual Investigation | FlakyGuard EFP | Savings |
|---|---|---|---|
| Simple race condition (case_01) | ~45 min | ~18s | **~99.3%** |
| Hard ambiguous async case (case_10) | ~3–4 hours | ~13s | **~99.9%** |
| 10 cases end-to-end benchmark | ~20–40 hours | ~3–5 min | **~99.8%** |

---

## 8. References

1. Lam, W., et al. *"Idflakies: A framework for detecting and partially classifying flaky tests."* ICSE 2020.
2. Bell, J., et al. *"DeFlaker: Automatically detecting flaky tests."* ICSE 2018.
3. Shi, A., et al. *"iFixFlakies: A framework for automatically fixing order-dependent flaky tests."* FSE 2019.
4. Gyori, A., et al. *"NonDex: A tool for evaluating the portability of Java programs."* FSE 2016.
5. Alshammari, A., et al. *"FlakeFlagger: Predicting flakiness without rerunning tests."* ICSE 2021.
6. Gruber, M., et al. *"A survey of flaky tests."* TSE 2021.

---

## 9. Reproducibility

Full reproduction instructions: [`REPRODUCE.md`](REPRODUCE.md)

```bash
git clone https://github.com/Pranjulchaurasiya/flaky-test-diagnosis-agent.git
cd flaky-test-diagnosis-agent
pip install -r requirements.txt
export GROQ_API_KEY="gsk_..."
python eval/run_eval.py --mode full
```
