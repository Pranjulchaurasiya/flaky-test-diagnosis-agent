import json
import re
from typing import Dict, Any
from agent.llm import UnifiedLLMClient

BASELINE_SYSTEM_PROMPT = """You are an automated software test diagnostic system.
Given a single failing test's source code and a single traceback log, determine the root cause of the failure and propose a fix.

You must categorize the root cause into one of the following taxonomy categories:
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
- unknown

Respond strictly with valid JSON conforming to this schema:
{
  "taxonomy_category": "<one of the taxonomy categories above>",
  "root_cause_analysis": "<detailed explanation of what caused the failure>",
  "proposed_fix": "<concrete code or configuration changes to fix the test>",
  "confidence": <float between 0.0 and 1.0>
}
"""

class BaselineDiagnoser:
    """
    Single-shot LLM baseline (zero-shot, no tools, no reruns, no repository search).
    """
    def __init__(self, llm_client: UnifiedLLMClient = None):
        self.llm = llm_client or UnifiedLLMClient()

    def diagnose(self, test_code: str, traceback_log: str) -> Dict[str, Any]:
        user_prompt = f"""### Failing Test Code:
```python
{test_code}
```

### Traceback / Error Log:
```
{traceback_log}
```

Provide your diagnosis in JSON format."""

        raw_response = self.llm.generate(BASELINE_SYSTEM_PROMPT, user_prompt, temperature=0.0)
        
        # Clean JSON markdown fences if present
        clean_json = raw_response.strip()
        if clean_json.startswith("```json"):
            clean_json = clean_json[7:]
        if clean_json.startswith("```"):
            clean_json = clean_json[3:]
        if clean_json.endswith("```"):
            clean_json = clean_json[:-3]
        clean_json = clean_json.strip()

        try:
            parsed = json.loads(clean_json)
        except json.JSONDecodeError:
            # Fallback regex extraction
            cat_match = re.search(r'"taxonomy_category"\s*:\s*"([^"]+)"', raw_response)
            parsed = {
                "taxonomy_category": cat_match.group(1) if cat_match else "unknown",
                "root_cause_analysis": raw_response,
                "proposed_fix": "Review test logic manually.",
                "confidence": 0.3
            }

        return parsed
