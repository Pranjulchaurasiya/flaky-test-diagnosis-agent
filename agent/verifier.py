import os
from typing import Dict, Any, Tuple
from agent.tools.code_search import CodeSearchTool

class DiagnosisVerifier:
    """
    Self-Verification Gate.
    Validates that the agent's diagnosis is supported by concrete, verified code evidence
    at exact file paths and line numbers in the repository.
    Rejects hallucinations, unverified citations, empty lines, and mismatched snippets.
    """
    def __init__(self, code_search: CodeSearchTool = None):
        self.code_search = code_search or CodeSearchTool()

    def verify_hypothesis(
        self,
        taxonomy_category: str,
        evidence_citation: Dict[str, Any],
        root_cause_explanation: str
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Verify that evidence_citation points to real existing non-empty code lines in the codebase.
        Returns:
            (is_verified: bool, feedback: str, verified_evidence: dict)
        """
        if not evidence_citation or not isinstance(evidence_citation, dict):
            return False, "Verification failed: No evidence citation dictionary provided.", {}

        file_path = evidence_citation.get("file_path", "")
        line_number = evidence_citation.get("line_number")
        claimed_code = evidence_citation.get("code_snippet", "")

        if not file_path:
            return False, "Verification failed: No evidence file_path provided.", {}

        if line_number is None:
            return False, "Verification failed: No evidence line_number provided.", {}

        try:
            line_number = int(line_number)
        except (ValueError, TypeError):
            return False, f"Verification failed: Invalid line_number '{line_number}'. Must be an integer.", {}

        # Resolve file path on disk
        resolved_path = file_path
        if not os.path.exists(resolved_path):
            alt_path = os.path.join("seeded_repo", file_path) if not file_path.startswith("seeded_repo") else file_path
            if os.path.exists(alt_path):
                resolved_path = alt_path
            else:
                return False, f"Verification failed: Referenced file '{file_path}' does not exist on disk.", {}

        try:
            with open(resolved_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            return False, f"Verification failed: Could not read '{resolved_path}': {e}", {}

        # Check line number range
        if line_number < 1 or line_number > len(lines):
            return False, f"Verification failed: Line number {line_number} is out of range for '{file_path}' (file has {len(lines)} lines).", {}

        # Read the exact claimed line
        actual_line = lines[line_number - 1].strip()

        # Strict check: evidence line cannot be empty or whitespace
        if not actual_line:
            return False, f"Verification failed: Line {line_number} in '{file_path}' is empty or whitespace. Evidence must cite actual source code.", {}

        # Strict check: if claimed code snippet is provided, it must match the actual line
        if claimed_code:
            claimed_clean = claimed_code.strip()
            if not claimed_clean:
                return False, f"Verification failed: Claimed code snippet is empty whitespace.", {}

            if claimed_clean not in actual_line and actual_line not in claimed_clean:
                return (
                    False,
                    f"Verification failed: Code at {file_path}:{line_number} ('{actual_line}') does not match claimed snippet ('{claimed_clean}').",
                    {}
                )

        # Domain-specific verification checks
        if taxonomy_category == "race_condition" and "lock" in actual_line.lower() and "with " in actual_line.lower():
            return False, "Verification warning: Line appears to already have a lock. Re-examine race condition hypothesis.", {}

        if taxonomy_category == "timing_sleep_assumption" and "sleep" not in root_cause_explanation.lower() and "sleep" not in actual_line:
            return False, "Verification warning: Timing hypothesis requires locating hardcoded sleep or timeout threshold.", {}

        normalized_path = file_path.replace("\\", "/")

        verified_evidence = {
            "verified": True,
            "file_path": normalized_path,
            "line_number": line_number,
            "verified_line_content": actual_line
        }

        # Explicit safety assertion
        assert verified_evidence["verified"] is True
        assert len(verified_evidence["verified_line_content"]) > 0
        assert verified_evidence["line_number"] == line_number

        return True, f"Evidence successfully verified at {normalized_path}:{line_number} -> '{actual_line}'", verified_evidence

    def verify(self, diagnosis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convenience wrapper to verify a diagnosis dictionary directly.
        """
        category = diagnosis.get("taxonomy_category", "")
        citation = diagnosis.get("evidence_citation", {})
        explanation = diagnosis.get("root_cause_analysis", "")
        passed, feedback, details = self.verify_hypothesis(category, citation, explanation)
        return {
            "verified": passed,
            "feedback": feedback,
            "details": details
        }
