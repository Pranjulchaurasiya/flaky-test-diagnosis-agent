import json
import time
import os
import re
from typing import Dict, Any, List, Optional

from agent.llm import UnifiedLLMClient
from agent.tools.test_runner import TestRunnerTool
from agent.tools.code_search import CodeSearchTool
from agent.tools.git_inspector import GitInspectorTool
from agent.tools.fixture_analyzer import FixtureAnalyzerTool
from agent.verifier import DiagnosisVerifier

AGENT_SYSTEM_PROMPT = """You are an Autonomous Flaky Test Diagnostic Agent.
You investigate why a software test is non-deterministic (flaky) or failing unexpectedly.

Available Taxonomy:
- race_condition
- shared_leaked_state
- timing_sleep_assumption
- test_order_dependence
- flaky_external_dependency
- resource_exhaustion
- datetime_clock_drift
- unseeded_randomness
- environment_mutation
- hard_ambiguous_case

You have access to investigative tool findings:
1. Rerun statistics (flake rate, intermittent pattern across N runs)
2. Source code context of the test and implementation
3. Code search results (locks, globals, class attributes, unclosed handles, time calls)
4. Fixture AST analysis

YOUR JOB:
Synthesize the tool findings, pinpoint the exact root cause, cite the exact source file and line number as evidence, and propose a concrete fix.

Respond with valid JSON conforming to this schema:
{
  "taxonomy_category": "<taxonomy category>",
  "root_cause_analysis": "<detailed explanation grounded in the evidence>",
  "evidence_citation": {
    "file_path": "<relative file path e.g. seeded_repo/src/counter.py>",
    "line_number": <integer line number>,
    "code_snippet": "<exact code line or snippet demonstrating the bug>"
  },
  "proposed_fix": "<concrete code changes or patch>",
  "confidence": <float between 0.0 and 1.0>
}
"""

class FlakyTestDiagnosisAgent:
    """
    Tool-Augmented Autonomous Flaky Test Diagnostic Agent with Self-Verification Gate.
    """
    def __init__(
        self,
        llm_client: Optional[UnifiedLLMClient] = None,
        workspace_root: str = "."
    ):
        self.workspace_root = workspace_root
        self.llm = llm_client or UnifiedLLMClient()
        self.test_runner = TestRunnerTool(cwd=workspace_root)
        self.code_search = CodeSearchTool(workspace_root=workspace_root)
        self.git_inspector = GitInspectorTool(repo_path=workspace_root)
        self.fixture_analyzer = FixtureAnalyzerTool(workspace_root=workspace_root)
        self.verifier = DiagnosisVerifier(code_search=self.code_search)

    def diagnose(
        self,
        test_file: str,
        test_function: str,
        initial_traceback: str,
        n_reruns: int = 5
    ) -> Dict[str, Any]:
        """
        Execute full autonomous diagnosis workflow with trajectory tracking.
        """
        trajectory: List[Dict[str, Any]] = []
        t_start = time.time()

        test_target = f"{test_file}::{test_function}" if test_function else test_file
        
        # --- Step 1: Initial Context Gathering ---
        test_code = self.code_search.read_file_range(test_file, 1, 80)
        trajectory.append({
            "step": 1,
            "action": "read_test_file",
            "target": test_file,
            "result_summary": f"Read {len(test_code.splitlines())} lines of test code."
        })

        # --- Step 2: Tool Execution - Rerun Test ---
        rerun_results = self.test_runner.rerun_test(test_target, n_runs=n_reruns)
        trajectory.append({
            "step": 2,
            "action": "rerun_test",
            "target": test_target,
            "result": {
                "total_runs": rerun_results["total_runs"],
                "fail_count": rerun_results["fail_count"],
                "flake_rate": rerun_results["flake_rate"],
                "is_intermittent_flaky": rerun_results["is_intermittent_flaky"],
                "distinct_errors": rerun_results["distinct_errors"]
            }
        })

        # Helper to format code with 1-indexed line numbers
        def _add_line_numbers(code_str: str, start: int = 1) -> str:
            lines = code_str.splitlines()
            return "\n".join(f"{start + i}: {line}" for i, line in enumerate(lines))

        # --- Step 3: Tool Execution - Code Search & AST Analysis ---
        imported_modules = re.findall(r'from\s+([a-zA-Z0-9_]+)\s+import', test_code)
        source_contexts = []
        for mod in set(imported_modules):
            src_path = f"seeded_repo/src/{mod}.py"
            if os.path.exists(os.path.join(self.workspace_root, src_path)):
                mod_content = self.code_search.read_file_range(src_path, 1, 100)
                source_contexts.append(f"### {src_path}:\n```python\n{_add_line_numbers(mod_content, 1)}\n```\n")

        ast_data = self.fixture_analyzer.inspect_fixtures(test_file)
        trajectory.append({
            "step": 3,
            "action": "code_and_fixture_search",
            "imported_sources": [f"seeded_repo/src/{m}.py" for m in imported_modules],
            "ast_insights": ast_data
        })

        # Cap distinct errors to keep prompt compact and prevent 413 payload errors
        truncated_errors = [err[:300] for err in rerun_results['distinct_errors'][:3]]

        # --- Step 4: LLM Hypothesis Generation ---
        user_prompt = f"""### Target Test:
File: `{test_file}`
Function: `{test_function}`

### Test Source Code (with Line Numbers):
```python
{_add_line_numbers(test_code, 1)}
```

### Initial Failure Traceback:
```
{initial_traceback[:500]}
```

### Rerun Empirical Data (Ran {rerun_results['total_runs']} times):
- Failures: {rerun_results['fail_count']}/{rerun_results['total_runs']} (Flake Rate: {rerun_results['flake_rate']})
- Intermittent Flake: {rerun_results['is_intermittent_flaky']}
- Observed Error Signatures: {json.dumps(truncated_errors, indent=2)}

### Related Application Source Files (with Line Numbers):
{"".join(source_contexts)}

Analyze all evidence and provide your diagnosis in JSON. In `evidence_citation`, you MUST use the exact line number shown in the numbered code above."""


        raw_response = self.llm.generate(AGENT_SYSTEM_PROMPT, user_prompt, temperature=0.0)
        parsed_diagnosis = self._parse_json_response(raw_response)

        trajectory.append({
            "step": 4,
            "action": "synthesize_hypothesis",
            "candidate_category": parsed_diagnosis.get("taxonomy_category"),
            "claimed_evidence": parsed_diagnosis.get("evidence_citation")
        })

        # --- Step 5: Self-Verification Gate ---
        evidence = parsed_diagnosis.get("evidence_citation", {})
        is_verified, v_feedback, v_data = self.verifier.verify_hypothesis(
            parsed_diagnosis.get("taxonomy_category", "unknown"),
            evidence,
            parsed_diagnosis.get("root_cause_analysis", "")
        )

        trajectory.append({
            "step": 5,
            "action": "self_verification_gate",
            "verification_passed": is_verified,
            "verifier_feedback": v_feedback,
            "verified_data": v_data
        })

        # If verification failed, perform one self-correction pass
        if not is_verified:
            correction_prompt = f"""{user_prompt}

### Self-Verification Gate Feedback:
"{v_feedback}"

Please re-evaluate the source code and find the EXACT file and line number that proves the root cause.
Provide the corrected JSON output conforming to the required schema."""
            raw_response_corrected = self.llm.generate(AGENT_SYSTEM_PROMPT, correction_prompt, temperature=0.0)
            corrected_diagnosis = self._parse_json_response(raw_response_corrected)
            
            # Re-verify
            is_v2, v_fb2, v_d2 = self.verifier.verify_hypothesis(
                corrected_diagnosis.get("taxonomy_category", "unknown"),
                corrected_diagnosis.get("evidence_citation", {}),
                corrected_diagnosis.get("root_cause_analysis", "")
            )
            parsed_diagnosis = corrected_diagnosis
            is_verified = is_v2
            v_feedback = v_fb2
            v_data = v_d2

            trajectory.append({
                "step": 6,
                "action": "self_correction_pass",
                "corrected_category": parsed_diagnosis.get("taxonomy_category"),
                "verification_passed": is_verified,
                "verifier_feedback": v_feedback,
                "verified_data": v_data
            })

        duration = round(time.time() - t_start, 3)

        return {
            "test_target": test_target,
            "taxonomy_category": parsed_diagnosis.get("taxonomy_category", "unknown"),
            "root_cause_analysis": parsed_diagnosis.get("root_cause_analysis", "No analysis provided."),
            "evidence_citation": parsed_diagnosis.get("evidence_citation", {}),
            "proposed_fix": parsed_diagnosis.get("proposed_fix", "No fix proposed."),
            "confidence": parsed_diagnosis.get("confidence", 0.5),
            "verification_status": "VERIFIED" if is_verified else "UNVERIFIED",
            "verifier_details": v_data if is_verified else {"verified": False, "reason": v_feedback},
            "rerun_summary": {
                "runs": rerun_results["total_runs"],
                "failures": rerun_results["fail_count"],
                "flake_rate": rerun_results["flake_rate"]
            },
            "diagnosis_duration_sec": duration,
            "trajectory": trajectory
        }

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Safely extract and parse JSON object from LLM response string."""
        if not text or not isinstance(text, str):
            return {
                "taxonomy_category": "unknown",
                "root_cause_analysis": "Empty response.",
                "evidence_citation": {},
                "proposed_fix": "Inspect manually.",
                "confidence": 0.0
            }
        
        # 1. Direct JSON parse
        try:
            return json.loads(text.strip())
        except Exception:
            pass

        # 2. Markdown code block
        try:
            json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
            if json_match:
                return json.loads(json_match.group(1))
        except Exception:
            pass

        # 3. Outer brace match
        try:
            start_idx = text.find('{')
            end_idx = text.rfind('}')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                return json.loads(text[start_idx:end_idx + 1])
        except Exception:
            pass

        return {
            "taxonomy_category": "unknown",
            "root_cause_analysis": text[:300],
            "evidence_citation": {},
            "proposed_fix": "Inspect manually.",
            "confidence": 0.3
        }
