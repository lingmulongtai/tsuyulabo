# CLAUDE.md

Follow [AGENTS.md](AGENTS.md) — the same rules apply to Claude (atomic commits above all).

- Plan and roles: [docs/DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md)
- Specs (source of truth): [docs/specs/](docs/specs/)
- Progress / handoff log: [docs/HANDOFF.md](docs/HANDOFF.md) — read it first when resuming, update it when stopping.
- New machine setup (commit email, tools, what is not in git): [docs/NEW_PC.md](docs/NEW_PC.md)

Claude's role in this repo: commander (split tasks, dispatch Codex, review, merge) and designer (design system,
character art, screens, effects). Heavy implementation goes to Codex via `codex exec` (see HANDOFF.md for the
exact command and the clone directories).
