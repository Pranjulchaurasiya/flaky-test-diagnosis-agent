import os
import ast
from typing import Dict, Any, List, Optional

class FixtureAnalyzerTool:
    """
    Parses pytest test files and conftest.py files using Python AST
    to identify shared fixtures, global variables, autouse scopes, and mutation targets.
    """
    def __init__(self, root_dir: str = ".", workspace_root: Optional[str] = None):
        self.root_dir = workspace_root or root_dir

    def inspect_fixtures(self, file_path: str) -> Dict[str, Any]:
        full_path = os.path.join(self.root_dir, file_path)
        if not os.path.exists(full_path):
            return {"error": f"File '{file_path}' not found."}

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source)
        except Exception as e:
            return {"error": f"AST parse error: {e}"}

        fixtures = []
        global_vars = []
        class_stores = []

        for node in ast.walk(tree):
            # Check for pytest fixture decorators
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    dec_name = ""
                    if isinstance(decorator, ast.Name):
                        dec_name = decorator.id
                    elif isinstance(decorator, ast.Attribute):
                        dec_name = decorator.attr
                    elif isinstance(decorator, ast.Call):
                        if isinstance(decorator.func, (ast.Name, ast.Attribute)):
                            dec_name = getattr(decorator.func, 'id', getattr(decorator.func, 'attr', ''))

                    if "fixture" in dec_name:
                        fixtures.append({
                            "name": node.name,
                            "line": node.lineno,
                            "args": [a.arg for a in node.args.args]
                        })

            # Check for class-level shared stores like _STORE = {}
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                class_stores.append({
                                    "class": node.name,
                                    "attribute": target.id,
                                    "line": item.lineno
                                })

            # Check for module-level globals
            if isinstance(node, ast.Global):
                global_vars.extend(node.names)

        return {
            "file": file_path,
            "detected_fixtures": fixtures,
            "class_level_stores": class_stores,
            "explicit_globals": global_vars,
            "has_potential_shared_state": len(class_stores) > 0 or len(global_vars) > 0
        }
