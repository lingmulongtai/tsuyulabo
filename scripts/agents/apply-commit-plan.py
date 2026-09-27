"""Turn a Codex commit plan into atomic git commits.

    python scripts/agents/apply-commit-plan.py <clone-dir> [--dry-run]

Reads <clone-dir>/.codex-runs/commits.jsonl. Each line:

    {"message": "feat(brain): add lif neurons", "body": "optional", "files": ["path", ...]}

Commits are created in order with the Codex trailer. A file that appears in several entries is
committed with the first entry that lists it (its final content). Changed files that no entry
lists are reported and left uncommitted so a human can decide.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

TRAILER = "Co-Authored-By: Codex <codex@openai.com>"


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True, encoding="utf-8"
    ).stdout


def changed_files(repo: Path) -> set[str]:
    out = git(repo, "status", "--porcelain", "-z", "--untracked-files=all")
    files: set[str] = set()
    entries = out.split("\0")
    i = 0
    while i < len(entries):
        entry = entries[i]
        if not entry:
            i += 1
            continue
        status, path = entry[:2], entry[3:]
        files.add(path)
        if status.startswith("R"):
            i += 1  # the next entry is the rename source
            files.add(entries[i])
        i += 1
    return files


def _is_pending(path: str, pending: set[str]) -> bool:
    prefix = path.rstrip("/") + "/"
    return path in pending or any(p.startswith(prefix) for p in pending)


def main() -> int:
    repo = Path(sys.argv[1]).resolve()
    dry = "--dry-run" in sys.argv
    plan_path = repo / ".codex-runs" / "commits.jsonl"
    lines = plan_path.read_text(encoding="utf-8-sig").splitlines()
    plan = [json.loads(line) for line in lines if line.strip()]

    pending = changed_files(repo)
    done: set[str] = set()
    made = 0
    for step in plan:
        files = [f.replace("\\", "/") for f in step["files"]]
        files = [f for f in files if f not in done and _is_pending(f, pending)]
        if not files:
            print(f"skip (nothing left to commit): {step['message']}")
            continue
        message = step["message"]
        body = step.get("body", "").strip()
        full = f"{message}\n\n{body}\n\n{TRAILER}" if body else f"{message}\n\n{TRAILER}"
        print(f"commit: {message}  ({len(files)} files)")
        if not dry:
            git(repo, "add", "-A", "--", *files)
            git(repo, "commit", "-q", "-m", full)
        done.update(files)
        made += 1

    left = sorted(changed_files(repo)) if not dry else sorted(pending - done)
    left = [f for f in left if not f.startswith((".codex-runs/", ".tools/", ".uv/"))]
    print(f"\n{made} commits created.")
    if left:
        print("Uncommitted changes not covered by the plan:")
        for f in left:
            print(f"  {f}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
