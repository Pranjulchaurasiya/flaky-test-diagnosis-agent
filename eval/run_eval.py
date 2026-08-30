import json
import time
import argparse
import sys
import os
from typing import Dict, Any, List

# Ensure workspace root is in path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from agent.llm import UnifiedLLMClient
from agent.baseline import BaselineDiagnoser
from agent.diagnosis_agent import FlakyTestDiagnosisAgent

def load_eval_cases(cases_path: str = "eval/cases.json") -> List[Dict[str, Any]]:
    full_path = os.path.join(ROOT_DIR, cases_path)
    with open(full_path, "r", encoding="utf-8") as f:
        return json.load(f)

def run_evaluation(
    mode: str = "full",
    output_file: str = "eval/results.json",
    provider: str = "groq",
    model: str = "qwen/qwen3.8-27b"
):
    cases = load_eval_cases()
    print(f"=== Starting Flaky Test Diagnosis Evaluation ({len(cases)} cases) ===", flush=True)
    print(f"Evaluation Mode: {mode.upper()}", flush=True)
    print(f"Using provider={provider} model={model}", flush=True)
    print("=" * 65, flush=True)

    llm = UnifiedLLMClient(provider=provider, model=model)
    baseline = BaselineDiagnoser(llm_client=llm) if mode in ("baseline", "full") else None
    agent = FlakyTestDiagnosisAgent(llm_client=llm, workspace_root=ROOT_DIR) if mode in ("agent", "full") else None

    results = []
    baseline_correct = 0
    agent_correct = 0
    agent_verified = 0

    for idx, case in enumerate(cases):
        cid = case["id"]
        cname = case["name"]
        ground_truth = case["taxonomy_category"]
        test_file = case["test_file"]
        test_func = case["test_function"]
        expected_symptom = case["expected_symptom"]

        print(f"\n[{idx+1}/{len(cases)}] Evaluating {cid}: {cname}", flush=True)
        print(f"      Ground Truth: {ground_truth} | Hardness: {case.get('hardness', 'medium')}", flush=True)

        case_res = {
            "id": cid,
            "name": cname,
            "ground_truth_category": ground_truth,
            "hardness": case.get("hardness")
        }

        # 1. Evaluate Baseline
        if baseline:
            t0 = time.time()
            with open(os.path.join(ROOT_DIR, test_file), "r", encoding="utf-8") as tf:
                test_code = tf.read()
            b_out = baseline.diagnose(test_code, expected_symptom)
            b_dur = round(time.time() - t0, 3)

            b_cat = b_out.get("taxonomy_category", "unknown")
            is_b_correct = b_cat.lower() == ground_truth.lower()
            if is_b_correct:
                baseline_correct += 1

            case_res["baseline"] = {
                "predicted_category": b_cat,
                "is_correct": is_b_correct,
                "duration_sec": b_dur,
                "confidence": b_out.get("confidence", 0.0),
                "proposed_fix": b_out.get("proposed_fix", "")
            }
            print(f"      [Baseline] Pred: {b_cat:25s} | Correct: {'YES' if is_b_correct else 'NO'} ({b_dur}s)", flush=True)

        # 2. Evaluate Agent
        if agent:
            t0 = time.time()
            a_out = agent.diagnose(test_file, test_func, expected_symptom, n_reruns=3)
            a_dur = round(time.time() - t0, 3)

            a_cat = a_out.get("taxonomy_category", "unknown")
            is_a_correct = a_cat.lower() == ground_truth.lower()
            if is_a_correct:
                agent_correct += 1
            if a_out.get("verification_status") == "VERIFIED":
                agent_verified += 1

            # Save individual trajectory
            traj_path = os.path.join(ROOT_DIR, "trajectories", f"{cid}_trajectory.json")
            with open(traj_path, "w", encoding="utf-8") as f:
                json.dump(a_out, f, indent=2)

            case_res["agent"] = {
                "predicted_category": a_cat,
                "is_correct": is_a_correct,
                "verification_status": a_out.get("verification_status"),
                "duration_sec": a_dur,
                "confidence": a_out.get("confidence", 0.0),
                "evidence_citation": a_out.get("evidence_citation"),
                "proposed_fix": a_out.get("proposed_fix", "")
            }
            print(f"      [Agent]    Pred: {a_cat:25s} | Correct: {'YES' if is_a_correct else 'NO'} | Verified: {a_out.get('verification_status')} ({a_dur}s)", flush=True)

        results.append(case_res)

    total = len(cases)
    summary = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_cases": total,
        "baseline_accuracy": f"{baseline_correct}/{total} ({round(baseline_correct/total*100, 1)}%)" if baseline else "N/A",
        "agent_accuracy": f"{agent_correct}/{total} ({round(agent_correct/total*100, 1)}%)" if agent else "N/A",
        "agent_verification_rate": f"{agent_verified}/{total} ({round(agent_verified/total*100, 1)}%)" if agent else "N/A",
        "results": results
    }

    # Write results JSON
    out_path = os.path.join(ROOT_DIR, output_file)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Print Summary Markdown Table
    print("\n" + "=" * 65, flush=True)
    print("                 BENCHMARK EVALUATION SUMMARY", flush=True)
    print("=" * 65, flush=True)
    print(f"| Metric | Baseline | Agent | Improvement |", flush=True)
    print(f"|---|---|---|---|", flush=True)
    if mode == "full":
        acc_b = round(baseline_correct / total * 100, 1)
        acc_a = round(agent_correct / total * 100, 1)
        diff = round(acc_a - acc_b, 1)
        print(f"| Diagnostic Accuracy (n={total}) | {baseline_correct}/{total} ({acc_b}%) | {agent_correct}/{total} ({acc_a}%) | +{diff}% |", flush=True)
        print(f"| Code Evidence Verification Rate | 0/{total} (0.0%) | {agent_verified}/{total} ({round(agent_verified/total*100, 1)}%) | +{round(agent_verified/total*100, 1)}% |", flush=True)
        hard_b_pass = results[9]['baseline']['is_correct'] if len(results) > 9 and 'baseline' in results[9] else False
        hard_a_pass = results[9]['agent']['is_correct'] if len(results) > 9 and 'agent' in results[9] else False
        print(f"| Hard Case Accuracy (case_10) | {'1/1' if hard_b_pass else '0/1 (Failed)'} | {'1/1 (Passed)' if hard_a_pass else '0/1'} | {'+100%' if hard_a_pass and not hard_b_pass else '0%'} |", flush=True)
    print(f"\nFull detailed results exported to: {output_file}", flush=True)
    print(f"Trajectories exported to: trajectories/*.json", flush=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Flaky Test Diagnosis Evaluator")
    parser.add_argument("--mode", choices=["baseline", "agent", "full"], default="full", help="Evaluation mode")
    parser.add_argument("--output", default="eval/results.json", help="Output results file path")
    parser.add_argument("--provider", default="groq", help="LLM Provider ('groq' or 'local')")
    parser.add_argument("--model", default="qwen/qwen3.8-27b", help="Model name on Groq")
    args = parser.parse_args()
    run_evaluation(mode=args.mode, output_file=args.output, provider=args.provider, model=args.model)
