# Task W3-integration — wire the real brain engine end to end (API + worker)

Branch: `feat/integration`. Work in `services/api/`, `services/worker/`, `services/shiori/` (and
`services/brain/` only for small, tested façade additions such as a public `default_params` re-export or a
documented byte codec — separate `feat(brain): ...` commits).

All branches are now merged on `main`: the brain engine (`services/brain`, façade `tsuyu_brain.api`), the game
API with its lazy `brain_adapter.py`, and the worker with its own brain seam (see "Brain merge seam" in
`services/worker/README.md`). Read `AGENTS.md`, `docs/specs/brain.md`, `docs/specs/api.md`,
`docs/specs/game-rules.md` (§11 now defines research rank and clamps negative rewards), both READMEs.

## Do

1. **One brain codec.** Confirm the real façade names and signatures in `tsuyu_brain.api` and make the API
   adapter and the worker seam use the same persisted format: store the compact `FlyState` bytes (the
   engine's own serialisation) plus the `BrainParams` JSON on adults and on the week's larva, instead of
   replaying the training history on every read. Keep the training history as an audit log. Add a migration
   if columns change. Align sex conventions (`m`/`f`) across API, worker and brain.
2. **Performance.** `GET /v1/home` and `GET /v1/adults` must not run simulations on every call: cache
   preference indices on the row (refresh after training / eclosion), and keep per-request brain work
   bounded. Add a simple timing test (home with a trained week < 300 ms on SQLite; mark `eval` if flaky).
3. **Real-engine scenario.** Run the full-week scenario test once with the real engine (not the fake) —
   mark it `@pytest.mark.eval` if it takes > 30 s — and assert that training banana+reward three times raises
   the banana preference on the eclosed adult, and that the adult's team gathering favours bananas.
4. **Worker with the real engine.** `brain_run_experiment` and `shiori_answer` (which may call
   `run_odor_choice`) must work with the real engine and the stored codec; add a test using the real engine.
   Make the API's `BRAIN_MODE=queue` path and the worker agree on job kinds/payloads (one test that calls the
   worker function with exactly what the API enqueues).
5. **Loose ends.** Clamp negative presentation rewards to 0 (currently eclosion can fail with
   `insufficient_funds`); implement `research_rank` in `/v1/me` per game-rules.md §11; make sure
   `/v1/shiori/ask` → job → `GET /v1/jobs/{id}` returns the answer in inline mode (Mock provider) end to end.
6. Re-export the OpenAPI schema (`services/api/scripts/export_openapi.py`) if any response changed.

## Done when

`uv run pytest` (all packages) and `uv run pytest -m eval` pass, ruff clean. Atomic commit plan entries.
