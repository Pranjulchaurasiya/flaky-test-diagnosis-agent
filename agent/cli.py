import argparse
import sys
import json
import os
from dotenv import load_dotenv

load_dotenv()

from agent.llm import UnifiedLLMClient
from agent.diagnosis_agent import FlakyTestDiagnosisAgent

def main():
    parser = argparse.ArgumentParser(
        prog="flakyguard",
        description="FlakyGuard: Autonomous CI Diagnostic Agent for Non-Deterministic Tests."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: diagnose
    diag_parser = subparsers.add_parser("diagnose", help="Diagnose a failing/flaky pytest test target")
    diag_parser.add_argument("test_target", help="Pytest target e.g. tests/test_orders.py::test_checkout")
    diag_parser.add_argument("--root", default=".", help="Root directory of the target codebase (default: .)")
    diag_parser.add_argument("--format", choices=["markdown", "json", "summary"], default="markdown", help="Output format")
    diag_parser.add_argument("--model", default="groq/qwen/qwen3.8-27b", help="LLM model identifier")

    # Command: verify
    verify_parser = subparsers.add_parser("verify", help="Run self-verification check on a diagnosis JSON file")
    verify_parser.add_argument("diagnosis_file", help="Path to diagnosis JSON file")
    verify_parser.add_argument("--root", default=".", help="Root directory of the codebase")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "diagnose":
        if not os.environ.get("GROQ_API_KEY"):
            print("⚠️ Error: GROQ_API_KEY is not set. Please set GROQ_API_KEY in your environment or .env file.", file=sys.stderr)
            sys.exit(1)

        llm_client = UnifiedLLMClient(model=args.model)
        agent = FlakyTestDiagnosisAgent(llm_client=llm_client, workspace_root=args.root)

        print(f"🔬 FlakyGuard starting forensic investigation on: {args.test_target}...", file=sys.stderr)
        diagnosis = agent.diagnose(args.test_target)

        if args.format == "json":
            print(json.dumps(diagnosis, indent=2))
        elif args.format == "markdown":
            cite = diagnosis.get("evidence_citation", {})
            cite_str = f"`{cite.get('file_path')}:{cite.get('line_number')}`" if cite.get("file_path") else "N/A"
            ver_status = diagnosis.get("verification_status", "UNKNOWN")
            ver_badge = "✅ **VERIFIED (100% Grounded)**" if ver_status == "VERIFIED" else "❌ **UNVERIFIED**"

            md_out = f"""# 🔬 FlakyGuard Diagnostic Report

### Test Target: `{diagnosis.get('test_target')}`
- **Root Cause Category:** `{diagnosis.get('taxonomy_category')}`
- **Verification Status:** {ver_badge}
- **Evidence Citation:** {cite_str}
- **Confidence:** `{diagnosis.get('confidence', 1.0) * 100:.0f}%`

---

## 🔍 Root Cause Analysis
{diagnosis.get('root_cause_analysis', 'No explanation provided.')}

---

## 🛠️ Proposed Fix
{diagnosis.get('proposed_fix', 'No code fix provided.')}
"""
            print(md_out)
        else:
            print(f"Category: {diagnosis.get('taxonomy_category')}")
            print(f"Status:   {diagnosis.get('verification_status')}")
            print(f"Citation: {diagnosis.get('evidence_citation')}")

    elif args.command == "verify":
        from agent.verifier import DiagnosisVerifier
        with open(args.diagnosis_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        verifier = DiagnosisVerifier(workspace_root=args.root)
        result = verifier.verify(data)
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
