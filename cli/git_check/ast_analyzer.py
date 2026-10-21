import ast
import re
from typing import Dict, Any, List

class ASTAnalyzer:
    """
    Extracts structural facts from diffs and code snippets to power the
    Adversarial Counterfactual Trap Generator.
    """
    @staticmethod
    def analyze_diff(diff: str) -> Dict[str, Any]:
        facts = {
            "functions": [],
            "classes": [],
            "exceptions_raised": [],
            "imports": [],
            "returns": [],
            "null_or_empty_checks": False,
            "has_error_handling": False,
        }

        # 1. Regex AST approximations across languages (Python, TS/JS, C#, Go)
        funcs = re.findall(r"(?:def|function|async\s+def|public\s+[a-zA-Z0-9_<>]+\s+|func\s+)\s*([a-zA-Z0-9_]+)\s*\(", diff)
        classes = re.findall(r"(?:class|interface|type|struct)\s+([a-zA-Z0-9_]+)", diff)
        exceptions = re.findall(r"(?:raise|throw|panic)\s+([a-zA-Z0-9_]+)", diff)
        imports = re.findall(r"(?:import|from|require|using)\s+([a-zA-Z0-9_\./@-]+)", diff)
        returns = re.findall(r"return\s+([^\n;]+)", diff)

        # Ignore boilerplate constructors / dunders
        ignored_funcs = {"__init__", "init", "__str__", "__repr__", "__call__", "__eq__", "constructor", "tostring", "main"}
        meaningful_funcs = [f for f in funcs if f.lower() not in ignored_funcs]

        facts["functions"] = list(dict.fromkeys(meaningful_funcs if meaningful_funcs else funcs))[:5]
        facts["classes"] = list(dict.fromkeys(classes))[:5]
        facts["exceptions_raised"] = list(dict.fromkeys(exceptions))[:5]
        facts["imports"] = list(dict.fromkeys(imports))[:5]
        facts["returns"] = list(dict.fromkeys([r.strip() for r in returns if r.strip()]))[:5]

        # 2. Check for null / error validation patterns
        if re.search(r"(if\s+[a-zA-Z0-9_]+\s+is\s+None|if\s*\(?!\w+\)?|if\s*\(?\w+\s*===?\s*null\)?|if\s+err\s*!=\s*nil)", diff):
            facts["null_or_empty_checks"] = True

        if re.search(r"(try\s*:|except|catch|recover\(\))", diff):
            facts["has_error_handling"] = True

        # 3. Python-specific deep AST parsing if python code block is found
        added_lines = [
            line[1:] for line in diff.splitlines()
            if line.startswith("+") and not line.startswith("+++")
        ]
        python_snippet = "\n".join(added_lines)

        try:
            tree = ast.parse(python_snippet)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if node.name not in facts["functions"]:
                        facts["functions"].append(node.name)
                elif isinstance(node, ast.ClassDef):
                    if node.name not in facts["classes"]:
                        facts["classes"].append(node.name)
                elif isinstance(node, ast.Raise):
                    if isinstance(node.exc, ast.Name):
                        facts["exceptions_raised"].append(node.exc.id)
                    elif isinstance(node.exc, ast.Call) and isinstance(node.exc.func, ast.Name):
                        facts["exceptions_raised"].append(node.exc.func.id)
        except Exception:
            # Fall back safely on regex facts if diff is partial or non-python
            pass

        return facts
