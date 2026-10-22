import subprocess
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

class GitService:
    def __init__(self, repo_path: Optional[str] = None):
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()

    def _run(self, cmd: List[str]) -> Tuple[int, str, str]:
        res = subprocess.run(
            cmd,
            cwd=str(self.repo_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        return res.returncode, res.stdout.strip(), res.stderr.strip()

    def is_git_repo(self) -> bool:
        code, out, _ = self._run(["git", "rev-parse", "--is-inside-work-tree"])
        return code == 0 and out == "true"

    def get_git_root(self) -> Optional[Path]:
        code, out, _ = self._run(["git", "rev-parse", "--show-toplevel"])
        return Path(out) if code == 0 and out else None

    def get_branch_name(self) -> str:
        code, out, _ = self._run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        return out if code == 0 else "unknown-branch"

    def get_author_info(self) -> Tuple[str, str]:
        _, name, _ = self._run(["git", "config", "user.name"])
        _, email, _ = self._run(["git", "config", "user.email"])
        return name or "Developer", email or "dev@internal"

    def get_latest_commit_hash(self) -> str:
        code, out, _ = self._run(["git", "rev-parse", "--short", "HEAD"])
        return out if code == 0 else "staged"

    def get_staged_diff(self, allow_last_commit: bool = False) -> str:
        # 1. Check staged diff (git add)
        code, out, _ = self._run(["git", "diff", "--cached", "--no-color"])
        if code == 0 and out.strip():
            return out
        # 2. Check unstaged working tree diff
        code, out, _ = self._run(["git", "diff", "--no-color"])
        if code == 0 and out.strip():
            return out
        # 3. Only inspect last commit if explicitly requested
        if allow_last_commit:
            code, out, _ = self._run(["git", "show", "--no-color", "--stat", "-p", "HEAD"])
            if code == 0 and out.strip():
                return out
        return ""

    def get_diff_stats(self) -> Dict[str, Any]:
        code, out, _ = self._run(["git", "diff", "--cached", "--stat"])
        if not out:
            code, out, _ = self._run(["git", "diff", "--stat", "HEAD"])

        code_num, numstat, _ = self._run(["git", "diff", "--cached", "--numstat"])
        if not numstat:
            _, numstat, _ = self._run(["git", "diff", "--numstat", "HEAD"])

        files_changed = []
        lines_added = 0
        lines_removed = 0

        for line in numstat.splitlines():
            parts = line.strip().split("\t")
            if len(parts) >= 3:
                added = int(parts[0]) if parts[0].isdigit() else 0
                removed = int(parts[1]) if parts[1].isdigit() else 0
                fname = parts[2]
                files_changed.append(fname)
                lines_added += added
                lines_removed += removed

        return {
            "summary_stat": out,
            "files_changed": files_changed,
            "lines_added": lines_added,
            "lines_removed": lines_removed
        }

    def extract_ticket_number(self, branch_name: Optional[str] = None) -> Optional[str]:
        branch = branch_name or self.get_branch_name()
        # Look for standard ticket patterns like PROJ-1234, FEAT-402, APP-99
        match = re.search(r"([A-Z]{2,10}-[0-9]+)", branch, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        # Look for number in branch (e.g. issue-42 or 1234-feature)
        match_num = re.search(r"(?:issue|ticket|task)[-_/]?([0-9]+)", branch, re.IGNORECASE)
        if match_num:
            return f"TICK-{match_num.group(1)}"
        return None

    def install_pre_commit_hook(self) -> Tuple[bool, str]:
        root = self.get_git_root()
        if not root:
            return False, "Not inside a valid git repository."
        
        hooks_dir = root / ".git" / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        hook_file = hooks_dir / "pre-commit"

        hook_script = """#!/bin/sh
# GitCheck Pre-Commit Verification Gate
# Checks author comprehension of AI-generated / modified code before committing

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"

if command -v git-check >/dev/null 2>&1; then
    exec git-check run --hook
elif [ -x "$REPO_ROOT/GitCheck/cli/bin/git-check" ]; then
    exec "$REPO_ROOT/GitCheck/cli/bin/git-check" run --hook
elif command -v python3 >/dev/null 2>&1; then
    PYTHONPATH="$REPO_ROOT/GitCheck/cli:$PYTHONPATH" exec python3 -m git_check.main run --hook
else
    echo "[GitCheck] Warning: git-check command not found in PATH. Skipping pre-commit gate."
    exit 0
fi
"""
        try:
            with open(hook_file, "w", encoding="utf-8") as f:
                f.write(hook_script)
            hook_file.chmod(0o755)
            return True, f"Hook installed successfully at {hook_file}"
        except Exception as e:
            return False, f"Failed to install hook: {str(e)}"
