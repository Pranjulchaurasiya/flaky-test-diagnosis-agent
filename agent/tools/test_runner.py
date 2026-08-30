import subprocess
import sys
import time
from typing import Dict, Any, List

class TestRunnerTool:
    """
    Reruns a target test N times to calculate flake rate, detect intermittent failures,
    and aggregate failure messages across runs.
    """
    def __init__(self, cwd: str = "."):
        self.cwd = cwd

    def rerun_test(self, test_target: str, n_runs: int = 5) -> Dict[str, Any]:
        """
        Rerun a given pytest target N times.
        Returns:
            pass_count, fail_count, flake_rate, execution_times, distinct_errors
        """
        pass_count = 0
        fail_count = 0
        execution_times: List[float] = []
        distinct_errors: List[str] = []
        outputs: List[str] = []

        for i in range(n_runs):
            t0 = time.time()
            cmd = [
                sys.executable, "-m", "pytest",
                test_target,
                "-q", "--tb=short",
                "-p", "no:deepeval", "-p", "no:langsmith", "-p", "no:warnings",
                "-p", "no:asyncio", "-p", "no:hypothesis", "-p", "no:rerunfailures"
            ]
            res = subprocess.run(
                cmd,
                cwd=self.cwd,
                capture_output=True,
                text=True,
                timeout=30
            )
            duration = round(time.time() - t0, 4)
            execution_times.append(duration)

            stdout = res.stdout + res.stderr
            outputs.append(stdout)

            if res.returncode == 0:
                pass_count += 1
            else:
                fail_count += 1
                # Extract main error line
                lines = [l.strip() for l in stdout.splitlines() if l.strip().startswith("E   ") or "Error:" in l]
                err_summary = " | ".join(lines[:3]) if lines else f"Exit code {res.returncode}"
                if err_summary not in distinct_errors:
                    distinct_errors.append(err_summary)

        flake_rate = round(fail_count / n_runs, 2)
        is_flaky = 0 < fail_count < n_runs
        is_consistent_fail = fail_count == n_runs

        return {
            "test_target": test_target,
            "total_runs": n_runs,
            "pass_count": pass_count,
            "fail_count": fail_count,
            "flake_rate": flake_rate,
            "is_intermittent_flaky": is_flaky,
            "is_consistent_failure": is_consistent_fail,
            "avg_duration_sec": round(sum(execution_times) / len(execution_times), 4),
            "distinct_errors": distinct_errors,
            "sample_output": outputs[0] if outputs else ""
        }
