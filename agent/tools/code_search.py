import os
import re
from typing import List, Dict, Any, Optional

class CodeSearchTool:
    """
    Searches the codebase for patterns (e.g. globals, fixtures, locks, sleep, class variables).
    """
    def __init__(self, root_dir: str = ".", workspace_root: Optional[str] = None):
        self.root_dir = workspace_root or root_dir

    def search_pattern(self, pattern: str, directory: str = "seeded_repo", file_extension: str = ".py") -> List[Dict[str, Any]]:
        """
        Search for regex pattern across python files in a directory.
        """
        matches = []
        target_dir = os.path.join(self.root_dir, directory)
        if not os.path.exists(target_dir):
            target_dir = self.root_dir

        regex = re.compile(pattern, re.IGNORECASE)

        for root, _, files in os.walk(target_dir):
            for file in files:
                if file.endswith(file_extension):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            for idx, line in enumerate(f, 1):
                                if regex.search(line):
                                    matches.append({
                                        "file": os.path.relpath(filepath, self.root_dir).replace("\\", "/"),
                                        "line_number": idx,
                                        "content": line.strip()
                                    })
                    except Exception:
                        pass
        return matches

    def read_file_range(self, file_path: str, start_line: int = 1, end_line: int = 80) -> str:
        """
        Read a range of lines from a file.
        """
        full_path = os.path.join(self.root_dir, file_path) if not os.path.isabs(file_path) else file_path
        if not os.path.exists(full_path):
            return f"File '{file_path}' not found."

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            sliced = lines[max(0, start_line - 1):end_line]
            return "".join(sliced)
        except Exception as e:
            return f"Error reading file '{file_path}': {e}"
