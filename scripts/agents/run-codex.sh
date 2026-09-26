#!/usr/bin/env bash
# Run one Codex task brief in its own clone (outside OneDrive) on its own branch, inside Codex's
# workspace-write sandbox.
#
#   scripts/agents/run-codex.sh <task-id> <branch> [reasoning-effort]
#
# The sandbox cannot write to .git, so Codex does not commit. It writes a commit plan to
# .codex-runs/commits.jsonl and scripts/agents/apply-commit-plan.py turns that into atomic commits.
#
# Logs: $AGENTS_DIR/<task-id>.log, final message: $AGENTS_DIR/<task-id>.last.md
set -euo pipefail

TASK="$1"
BRANCH="$2"
EFFORT="${3:-high}"
AGENTS_DIR="${AGENTS_DIR:-/c/Users/lingm/dev/tsuyulabo-agents}"
REPO_URL="${REPO_URL:-https://github.com/lingmulongtai/tsuyulabo.git}"
CLONE="$AGENTS_DIR/$TASK"
UV_BIN="${UV_BIN:-/c/Users/lingm/bin/uv.exe}"

# The Codex CLI bundled with the desktop app (the standalone one in ~/.codex is too old for the model).
APP_DIR="$(powershell.exe -NoProfile -Command '(Get-AppxPackage OpenAI.Codex).InstallLocation' | tr -d '\r')"
CODEX="$(cygpath -u "$APP_DIR")/app/resources/codex.exe"

mkdir -p "$AGENTS_DIR"
if [ ! -d "$CLONE/.git" ]; then
  git clone -q "$REPO_URL" "$CLONE"
fi
cd "$CLONE"
git fetch -q origin
if git show-ref --quiet "refs/heads/$BRANCH"; then
  git checkout -q "$BRANCH"
else
  git checkout -q -b "$BRANCH" origin/main
fi

# Everything Codex needs must live inside the workspace: the sandbox cannot read the home folder.
mkdir -p .tools .codex-runs
[ -f .tools/uv.exe ] || cp "$UV_BIN" .tools/uv.exe
grep -qx '.tools/' .git/info/exclude 2>/dev/null || printf '.tools/\n.uv/\n.codex-runs/\n' >> .git/info/exclude
WIN_CLONE="$(cygpath -w "$CLONE")"
export UV_CACHE_DIR="$WIN_CLONE\\.uv\\cache"
export UV_PYTHON_INSTALL_DIR="$WIN_CLONE\\.uv\\python"
export UV_PYTHON_PREFERENCE=only-managed
export UV_LINK_MODE=copy

BRIEF="docs/agent-tasks/$TASK.md"
PROMPT="You are working in a clone of the Tsuyu Labo repo on branch $BRANCH.
Follow AGENTS.md strictly, including the section 'Committing from the Codex sandbox':
you cannot write to .git, so do NOT run git add/commit. Instead append one JSON object per atomic
commit to .codex-runs/commits.jsonl, in order, as you finish each step.
Use uv via .\\.tools\\uv.exe (e.g. '.\\.tools\\uv.exe run pytest services/brain'). Use npm.cmd / npx.cmd
instead of npm / npx (PowerShell execution policy blocks the .ps1 shims).
Stay inside this directory. Do not edit docs/HANDOFF.md even if the brief says so (the commander keeps the log;
put your report in your final message instead). Your task brief follows.

$(cat "$BRIEF")"

"$CODEX" exec -C "$CLONE" \
  -s workspace-write \
  -c sandbox_workspace_write.network_access=true \
  -c model_reasoning_effort="$EFFORT" \
  -o "$AGENTS_DIR/$TASK.last.md" \
  "$PROMPT" < /dev/null > "$AGENTS_DIR/$TASK.log" 2>&1
