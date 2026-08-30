# Reproduction Guide: Flaky Test Diagnosis Agent 📋

Follow these exact steps to reproduce the evaluation and benchmark results from a clean environment.

---

## 1. Prerequisites & Environment Setup

- **Python**: Python 3.10+ (Tested on Python 3.13.9)
- **OS**: Windows, macOS, or Linux

### Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### Environment Configuration
Configure your Groq API key by either creating a `.env` file from the provided template:
```bash
cp .env.example .env
# Edit .env and paste your GROQ_API_KEY
```
Or export it directly in your shell:
```bash
# Windows (PowerShell)
$env:GROQ_API_KEY = "your-groq-api-key-here"

# Linux / macOS
export GROQ_API_KEY="your-groq-api-key-here"
```
*(Groq is used exclusively as the LLM backend for both the baseline and the autonomous diagnostic agent, using model `qwen/qwen3.8-27b`).*


---

## 2. Verify Seeded Flaky Tests

Run pytest to observe the seeded non-deterministic and failing test behaviors:
```bash
python -m pytest seeded_repo/tests/ -v
```

---

## 3. Run Benchmark Evaluations

### Option A: Run Full Comparative Benchmark (Baseline vs Agent)
```bash
python eval/run_eval.py --mode full --output eval/results.json
```

### Option B: Run Baseline Only (Zero-shot, No Tools)
```bash
python eval/run_eval.py --mode baseline
```

### Option C: Run Tool-Augmented Agent Only
```bash
python eval/run_eval.py --mode agent
```

---

## 4. Expected Output & Benchmark Scoring

Upon running `python eval/run_eval.py --mode full`:
```
=================================================================
                 BENCHMARK EVALUATION SUMMARY
=================================================================
| Metric | Baseline | Agent | Improvement |
|---|---|---|---|
| Diagnostic Accuracy (n=10) | 8/10 (80.0%) | 10/10 (100.0%) | +20.0% |
| Code Evidence Verification Rate | 0/10 (0.0%) | 10/10 (100.0%) | +100.0% |
| Hard Case Accuracy (case_10) | 0/1 (Failed) | 1/1 (Passed) | +100% |

Full detailed results exported to: eval/results.json
Trajectories exported to: trajectories/*.json
```

---

## 5. Launch the 3D Interactive Web Platform

Open `web/index.html` in any modern web browser or serve with Python:
```bash
python -m http.server 8000 --directory web
```
Then visit `http://localhost:8000` to interact with:
- The **3D Rerun Timeline & Dependency Web**
- Interactive **Step-by-Step Trajectory Player**
- Live **Benchmark Results Matrix**
