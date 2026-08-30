import subprocess
from typing import Dict, Any, List, Optional

class GitInspectorTool:
    """
    Inspects git blame, commit logs, and recent diffs for test files to detect recent changes.
    """
    def __init__(self, cwd: str = ".", repo_path: Optional[str] = None):
        self.cwd = repo_path or cwd

    def get_blame(self, file_path: str, start_line: int = 1, end_line: int = 50) -> str:
        """
        Run git blame on a file for a specific line range.
        """
        cmd = ["git", "blame", "-L", f"{start_line},{end_line}", "--", file_path]
        try:
            res = subprocess.run(cmd, cwd=self.cwd, capture_output=True, text=True, timeout=10)
            if res.returncode == 0:
                return res.stdout
            return f"Git blame notice: {res.stderr.strip() or 'No commit history available for uncommitted file'}"
        except Exception as e:
            return f"Git blame error: {e}"

    def get_recent_commits(self, file_path: str, max_count: int = 5) -> str:
        """
        Get recent commits touching a file.
        """
        cmd = ["git", "log", f"-n{max_count}", "--oneline", "--", file_path]
        try:
            res = subprocess.run(cmd, cwd=self.cwd, capture_output=True, text=True, timeout=10)
            if res.returncode == 0:
                return res.stdout
            return f"Git log notice: {res.stderr.strip() or 'No git log available'}"
        except Exception as e:
            return f"Git log error: {e}"
