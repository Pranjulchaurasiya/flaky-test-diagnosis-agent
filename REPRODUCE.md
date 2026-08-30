# Reproduction Guide: FlakyGuard Benchmark 📋

Follow these exact steps to reproduce the 10/10 benchmark results from a clean environment.

---

## ⚡ Fastest Path — One Command

### Docker (zero local setup required)
```bash
git clone https://github.com/Pranjulchaurasiya/flaky-test-diagnosis-agent.git
cd flaky-test-diagnosis-agent
GROQ_API_KEY=gsk_... docker compose --profile eval up --build
```
- **Web lab** starts at `http://localhost:8080` automatically
- **Benchmark eval** runs and outputs `eval/output/results.json`

### Without Docker — Linux / macOS
```bash
git clone https://github.com/Pranjulchaurasiya/flaky-test-diagnosis-agent.git
cd flaky-test-diagnosis-agent
GROQ_API_KEY=gsk_... ./bootstrap.sh eval
```

### Without Docker — Windows PowerShell
```powershell
git clone https://github.com/Pranjulchaurasiya/flaky-test-diagnosis-agent.git
cd "flaky-test-diagnosis-agent"
$env:GROQ_API_KEY = "gsk_..."
.\bootstrap.ps1 eval
```

---

## 1. Prerequisites & Environment Setup

- **Python**: 3.10+ (Tested on Python 3.13.9)
- **OS**: Windows, macOS, or Linux
- **Groq API key**: Free at [console.groq.com](https://console.groq.com)

### Install Dependencies
```bash
git clone https://github.com/Pranjulchaurasiya/flaky-test-diagnosis-agent.git
cd flaky-test-diagnosis-agent
pip install -r requirements.txt
```

### Configure API Key
```bash
# Copy the template and fill in your key
cp .env.example .env
```
Or export directly:
```bash
# Windows (PowerShell)
$env:GROQ_API_KEY = "gsk_your_key_here"

# Linux / macOS
export GROQ_API_KEY="gsk_your_key_here"
```

> Uses `qwen/qwen3.8-27b` via Groq (free tier). No OpenAI key needed.

---

## 2. Verify Seeded Flaky Tests Are Observable

Run pytest to observe the non-deterministic failures in the seeded repo:
```bash
python -m pytest seeded_repo/tests/ -v
```

Expected: some tests fail intermittently (especially `test_concurrent_metric_increments`, `test_rapid_rpc_echo`).

---

## 3. Run Benchmark Evaluations

### Option A — Full Comparative Benchmark (Baseline vs. Agent)
```bash
python eval/run_eval.py --mode full --output eval/results.json
```

### Option B — Baseline Only (Single-shot LLM, no tools)
```bash
python eval/run_eval.py --mode baseline
```

### Option C — Tool-Augmented Agent Only
```bash
python eval/run_eval.py --mode agent
```

---

## 4. Expected Output

Running `python eval/run_eval.py --mode full` produces:

```
=================================================================
                 BENCHMARK EVALUATION SUMMARY
=================================================================
| Metric                          | Baseline     | Agent        | Improvement |
|---------------------------------|--------------|--------------|-------------|
| Diagnostic Accuracy (n=10)      | 10/10 (100%) | 10/10 (100%) | 0.0%        |
| Code Evidence Verification Rate | 0/10 (0.0%)  | 10/10 (100%) | +100.0%     |
| Hard Case Accuracy (case_10)    | 1/1 (Passed) | 1/1 (Passed) | —           |
| Hallucination Rate              | High         | 0.0%         | -100%       |

Full results exported to: eval/results.json
Trajectories exported to: trajectories/*.json
```

> The key metric is **Code Evidence Verification Rate**: the baseline LLM cannot cite a verified
> source file + line number for any case (0/10). FlakyGuard's Self-Verification Gate achieves
> 100% verified grounded citations across all 10 cases.

---

## 5. Run Trajectory Audit (Verification Check)

Independently verify all 10 trajectory JSON files against the codebase AST:
```bash
python eval/audit_all_trajectories.py
```

---

## 6. Launch the Interactive Web Platform

```bash
python -m http.server 8000 --directory web
```

Then open `http://localhost:8000` to interact with:
- **3D Rerun Timeline & Instability Stack** (simulate flake injection)
- **Step-by-Step Trajectory Player** (replay Case 10 live)
- **Benchmark Results Matrix** (10-case side-by-side comparison)

---

## 7. Run the CLI on a Custom Test

```bash
# Diagnose any pytest target directly
flakyguard diagnose seeded_repo/tests/test_case_01_race_condition.py::test_concurrent_metric_increments
```

---

## Timing & Cost Reference (Verified)

| Metric                  | Measured Value              |
|-------------------------|-----------------------------|
| Agent avg. duration     | ~13.1s per case             |
| Baseline avg. duration  | ~4.4s per case              |
| Model                   | `qwen/qwen3.8-27b` via Groq |
| Estimated cost per case | ~$0.001–$0.003 (Groq free)  |
| Total eval runtime      | ~3–5 min (10 cases, full)   |
