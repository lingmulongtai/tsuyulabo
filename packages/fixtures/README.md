# Shared puzzle fixtures

Each UTF-8 JSON file at `puzzles/<kind>/<name>.json` contains:

```json
{
  "kind": "meal",
  "description": "human-readable rule or edge case",
  "params": {},
  "submission": {},
  "expected": {"valid": false, "reason": "cell_occupied"}
}
```

`params` is the issued public puzzle; `submission` is the client's operation log.
Compare the entire deterministic result with `expected`. Successful results contain
`valid: true` and only the scoring fields for that kind: meal has `score`, `lines`,
`max_combo`, `theme_cells`; training has `stars`; cleaning has `score`, `grades`;
temperature has `score`, `grade`. Failed results contain only `valid` and `reason`.
Secrets and luck rolls (great success, hirameki, site hit) are deliberately excluded.
Some edge cases use hand-built params (including short piece streams or a constant
temperature needle); a verifier must use the issued params, not assume generator defaults.

Regenerate from the repository root:

```powershell
.\.tools\uv.exe run python services/api/scripts/gen_puzzle_fixtures.py
.\.tools\uv.exe run python services/api/scripts/gen_puzzle_fixtures.py --check
.\.tools\uv.exe run pytest services/api/tests/domain/test_fixtures.py
```

The generator asserts independently calculated expected scores against the Python
domain implementation before writing a fixture. Seeded training solutions remain
only in test submissions. The TypeScript suite should load the same files.

Coverage includes every reason in `docs/specs/puzzles.md`, at least six successful
and six rejected submissions per kind, simultaneous row/column clearing with one
intersection, consecutive combos and combo reset, mixed ingredient theme bonuses,
time grace limits, star thresholds for both grid sizes, and temperature rounding.

Timing contract: milliseconds are nonnegative integers. Operations must precede or
equal `elapsed_ms`; a decreasing/negative/invalid timestamp is `non_monotonic_time`.
Meal move times allow 1500 ms grace beyond the issued limit, cleaning taps allow
10000 ms inclusive and must strictly increase. Training and temperature have no
additional hard play limit in the spec: the common ten-minute issuance lifetime
applies. Wall-clock anti-cheat and expiry are checked separately using server times.
Temperature uses half-up rounding, matching JavaScript `Math.round` for positive
scores. Invalid path precedence is length, bounds, revisit, adjacency, start, end,
checkpoint order, then elapsed time; meal checks timing before replaying moves.
Cleaning includes a `1e-12` numerical tolerance on zone comparisons so binary
floating point error does not turn an exact inclusive boundary into a miss.
