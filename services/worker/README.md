# Tsuyu background worker

The worker binds Shiori's protocols to the API's SQLAlchemy models and session factory.
The shared SQL/Shiori bindings live in `tsuyulabo_api.services` and are re-exported by the worker.
Tests use SQLite with explicit fakes or the real brain codec; Redis is not needed for direct calls.

```powershell
.\.tools\uv.exe run pytest services/shiori services/worker
.\.tools\uv.exe run pytest services/shiori services/worker -m eval
.\.tools\uv.exe run ruff check services/shiori services/worker
.\.tools\uv.exe run arq tsuyu_worker.main.WorkerSettings
```

Set `DATABASE_URL` for the API database and `REDIS_URL` for arq (default
`redis://localhost:6379/0`). `SHIORI_PROVIDER` defaults to `mock`; see the
[Shiori README](../shiori/README.md) for opt-in HTTP providers. Worker startup creates the
engine and a shared cached provider, and shutdown disposes the engine.

## Jobs and API wiring

The registered arq names are `brain_run_experiment`, `shiori_answer`,
`shiori_morning_memo`, and `run_brain_job`. The latter accepts `(job_id, kind, params)`
and matches the current API `ArqJobQueue` dispatch contract. Job kinds are
`brain.experiment`, `brain.training`, and `shiori.answer`. Legacy underscore names remain aliases.

Direct calls use the functions in `tsuyu_worker.jobs`:

```python
result = await shiori_answer(
    job_id,
    sessions=api_session_factory,
    params={"question": "しつけは何回？", "week_id": week_id},
)
result = await brain_run_experiment(
    job_id,
    sessions=api_session_factory,
    params={"fly_id": adult_or_week_id, "cue": "banana", "trials": 20, "seed": 0},
)
memo = await shiori_morning_memo(user_id, sessions=api_session_factory)
```

Omit `sessions` to create a short-lived engine using API settings. User identity always
comes from the job row or authenticated host, never tool arguments. Explicit fly/week IDs
are checked for ownership and consistency; absent IDs resolve to the active week.

**Input persistence:** the API commits `Job.params` before dispatch. The worker prefers these
persisted inputs; direct callers may still supply `params` for older jobs. The legacy
`result = {"input": params}` convention is accepted for old pending jobs. Canonical experiment
inputs include a base64 snapshot, experiment ID and game timestamp; the worker uses the exact
accepted snapshot, not a newer state. Training consumes ordered accepted care events and updates
larval/adult bytes and preference caches transactionally, including late completion after eclosion.

The API's existing `InlineJobQueue` owns job status itself. Bind its handlers with
`inline_handlers(sessions, authenticated_user_id, provider=..., brain=...)` and pass the
returned mapping to `InlineJobQueue`. Do not point that queue at the job-ID functions,
which would attempt to manage the same row/transaction again. Hosts which want direct
worker-owned status can call the job-ID functions after committing the pending row.

Worker-owned jobs lock the job row and commit status, result/cost, messages, and experiments
in one transaction. Duplicate completed deliveries return the saved result. Failures roll
back generated rows and persist a generic error with `failed` status and `finished_at`.
Cancellation/process death rolls the transaction back, allowing redelivery. Terminal
failed jobs are not retried automatically. Since the transaction holds a lock while work
runs, `running` is not separately visible to other connections; they see pending then the
terminal result. This favors atomic effects for the alpha. A future lease/outbox design
can expose progress without holding a transaction during model calls. SQLite serializes
writers through the API engine's `BEGIN IMMEDIATE`; PostgreSQL uses row locks.

Q&A stores `user` and `assistant` rows in `shiori_messages`. Memos use role `morning_memo`.
The final Q&A result includes `answer`, `text`, `evidence`, `experiments`, `cost`,
`verification`, and AI disclosure metadata. The API should return this result unchanged.
The memo endpoint can select the latest `morning_memo` row for its authenticated user.

## Nightly memo generation

arq runs `nightly_journal` at **03:30 JST** with an explicit UTC+09:00 timezone, independent
of the machine's timezone. It generates the next morning's observation memo. Each user
gets at most one saved memo per JST civil date; a user row lock protects concurrent calls.
Users without an active week are skipped. One user's failure does not stop the batch;
the result reports generated/reused/skipped/failed user IDs and logs failures without
provider exception details.

There is no `last_seen_at` in the current API schema. Activity within the previous 24 hours
is therefore defined by persisted registration, care events, puzzle issue/submission,
job creation, or sleep start/end timestamps. Read-only visits are not observable until the
host tracks them. Generated memo rows do not count as activity, so the cron cannot keep
inactive users active indefinitely. The cron uses real timestamps, not debug clock offsets.

## Brain merge seam

`brain_adapter.py` imports `tsuyu_brain.api` lazily. The real engine is the default and
raises `BrainUnavailable` when absent; fake measurements are never silently substituted.
Tests explicitly inject `FakeBrainEngine`. A missing engine does not prevent imports,
ordinary record-only Q&A, or memo generation.

`BrainSnapshot` holds copied adult or larval parameters and `FlyState` bytes. Both API and worker
use the public `tsuyu_brain.api.FlyState.from_bytes` codec and lower-case `m` / `f` sex values.
Stored bytes are authoritative; audit training is never replayed after decoding them. Old API
replay snapshots are understood for migration compatibility. Run the API's documented backfill
before serving existing databases. Missing states fail explicitly rather than inventing a fly.

Shiori experiments operate on private decoded states. Association lookup supports the API's
nested `association: {cue, valence, value}` audit payload. Standalone worker/Shiori experiments
use `#c-N` evidence IDs; API experiment results retain their `display_id: c-N` response contract.

## Validation

The suite covers ownership, copy-only experiments, duplicate delivery, transactional
rollback, both API dispatch paths, JST scheduling and memo deduplication. HTTP providers
are tested with mocked transports. Real engine tests cover both stored larvae and adults, copy-only experiments, Shiori answers,
and the exact API arq payloads for all three canonical job kinds. Live Redis/PostgreSQL
integration still requires those external services.

Optional source type check (the API package currently has no `py.typed` marker):

```powershell
$env:MYPYPATH = 'services/api/src;services/shiori/src;services/worker/src'
.\.tools\uv.exe run mypy services/shiori/src services/worker/src --follow-imports=silent
```
