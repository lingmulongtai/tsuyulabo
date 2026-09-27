# Tsuyu background worker

The worker binds Shiori's protocols to the API's SQLAlchemy models and session factory.
It never changes the API or brain packages. Tests create the real API schema in SQLite and
inject an explicit fake brain; Redis is not needed for direct job calls or tests.

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
`brain_run_experiment` and `shiori_answer`.

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

**Current schema integration:** `Job` has no input column. Existing queue callers pass
`params` separately. To invoke only by job ID, persist `job.result = {"input": params}`
while the job is pending; completion replaces it with the final result. No migration is
required. The commander's API routes must choose one of these input paths. Q&A requires
`question`; experiments accept `fly_id`, `cue`, `trials`, and `seed`.

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

`BrainSnapshot` holds copied adult parameters/bytes and ordered training records.
For a week without stored brain state, the adapter deterministically creates an individual
and replays `training` care payloads (`cue`, `valence`, `learning_strength` or `strength`,
optional `seed`). Association lookup reads a recorded `association_value` or `value`;
it does not invent a fresh measurement. Experiments run on private state and are persisted
with a per-user `#c-N` sequence, params, counts and engine name. Adult columns remain unchanged.

W1's task specifies the façade but not the exact byte codec. The isolated default seam
expects `tsuyu_brain.learning.FlyState.from_bytes(blob)` for stored adult states and
`tsuyu_brain.params.BrainParams(**params)` when no blob exists. After W1 merges, the
commander must confirm these names, the `F`/`M` sex convention, and the persisted training
seed/initial-state convention, or adapt this one module. A blob is treated as a complete
serialized state and is not followed by another training replay. A weights-only codec
must instead combine the weights with the persisted parameters in this adapter.

## Validation

The suite covers ownership, copy-only experiments, duplicate delivery, transactional
rollback, both API dispatch paths, JST scheduling and memo deduplication. HTTP providers
are tested with mocked transports. Live Redis, PostgreSQL locks and real brain codec
integration require checks in the combined stack after the parallel branches merge.

Optional source type check (the API package currently has no `py.typed` marker):

```powershell
$env:MYPYPATH = 'services/api/src;services/shiori/src;services/worker/src'
.\.tools\uv.exe run mypy services/shiori/src services/worker/src --follow-imports=silent
```
