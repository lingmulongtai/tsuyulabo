# Shiori research assistant

`tsuyu_shiori` is a database-independent, Japanese research assistant. The host supplies
asynchronous `RecordStore` and `Lab` implementations. No module imports `tsuyulabo_api`.
`MemoryRecordStore`, `MemoryLab`, and the default `MockProvider` work offline.

From the repository root in PowerShell:

```powershell
.\.tools\uv.exe run pytest services/shiori
.\.tools\uv.exe run pytest services/shiori -m eval
.\.tools\uv.exe run python -m tsuyu_shiori.eval
```

The last command writes ignored `eval-results/shiori-mock-mock-qa/report.json` and `report.md`, and exits
nonzero unless count accuracy is at least 0.80, sentence verification is at least 0.95,
topic accuracy and readability are both 1.0, and open accuracy is at least 0.70.
`--seed` and `--output-dir` are available. The evaluation generates 42 count questions from
a synthetic week, including zero counts, different days, cues and reinforcement types,
plus nine topic questions and ten realistic open questions (preferences, sleep,
presentation rank, and most frequent training). Readability requires nonempty answers of at most 160 characters,
at most six citation occurrences total, and one to four citations in every sentence.
Rejected sentences also fail readability, so verification cannot hide uncited prose.
It checks facts and citation validity; it does not prove semantic entailment.

## Offline answers

Mock answers select records for learning, a named cue, meals/great success, sleep,
cleaning, temperature, pupation sites, and eclosion/traits. They use recent relevant
evidence, report measured values without attributing feelings or inventing causes,
and normally contain two or three short sentences.
Learning questions without a cue follow the most recently trained cue. Named-cue
and learning questions read associations and run 20 odor-choice trials through the
host's copy-only lab; count questions do not run experiments.

Missing topic records are stated explicitly with a suggestion to collect observations.
If no existing evidence ID is available at all, Mock still generates no claims.
The agent returns a nonempty UI status with `empty_state=true` and no citations or
verification success; it asks for care records without inventing evidence.
Traits are described only when present in returned records, never inferred from care.
Older or live-provider answers can still have many evidence chips: the question UI
shows six initially and a native `+N件` disclosure for the rest.

## Host interface

```python
from tsuyu_shiori.features import answer_question
from tsuyu_shiori.gateway import CachedProvider, MockProvider
from tsuyu_shiori.records import MemoryLab, MemoryRecordStore, Record

store = MemoryRecordStore(
    [
        Record(
            "#0001",
            "training",
            {
                "research_day": 2,
                "cue": "banana",
                "valence": "reward",
                "value": 0.4,
            },
            week_id="week",
            fly_id="fly",
        ),
    ]
)
lab = MemoryLab(store, {"fly": {"banana": 0.4}})
provider = CachedProvider(MockProvider())  # Reuse across calls to retain the LRU.
# Inside an async function:
answer = await answer_question(
    "2日目にバナナで報酬を覚えた回数は何回？",
    store=store,
    lab=lab,
    week_id="week",
    fly_id="fly",
    provider=provider,
)
payload = answer.to_dict()
```

`morning_memo`, `coach_tip`, and `presentation_host` accept the same host dependencies as
keyword arguments. Morning memos select the previous JST civil day's care and sleep
sessions starting after noon that day and before the memo creation time. Pass an aware `now` for reproducible generation.
The coach accepts a `cue`. Presentation ranks come from a persisted `presentation`
care record with `data.rank`, so the rank has its own verifiable evidence.
Missing records produce fewer sentences or an explicit empty-state status instead of fabricated evidence.

The result contains text, evidence IDs, experiments, a verification report, and per-call
token/cost accounting. `ai_label` and `disclaimer` are separate UI metadata: display both.
Verification reports describe the generated answer before feature sentence limits.

Record IDs are opaque to Shiori; host implementations must check ownership. The SQL host
uses `#0001` for care, `#c-1` for experiments and `#s-<uuid>` for sleep. Data conventions:
care carries `research_day`, `cue`, `valence`, optional `value`; sleep carries `hours`;
experiments carry `toward`, `away`, `cue`, `trials`, and `seed`.

The five tools validate arguments, reject out-of-conversation week/fly IDs, and cap trials
at 1,000. The host lab owns state loading and copying; brain state is never entrusted to
the language model. A normal run makes at most four provider calls and executes at most four
tools per step; the last step allows only a final answer. Empty-answer Mock recovery
is bounded separately as described below. Repeated identical tool calls
reuse their result within the run, including persisted experiments.

## Compact record tools

Both `get_care_events` and `count_care_events` accept `week_id` and optional
`kinds`, `research_day` (1–7), `cue`, `valence`. Conditions intersect. Filtering runs
**after** host retrieval, so the API's existing DB-backed `RecordStore` remains unchanged.
Omitted kinds include all care and sleep records; `[]` selects none. Missing data fields
do not match their filters. Morning memo time windows apply to both tools.
The cue/valence enums carry Japanese labels in the schema, including イースト=yeast.

`get_care_events` returns `records`, `sleep_sessions`, `total`, `truncated`.
The combined arrays contain at most 20 records, newest first. `total` counts all matching
records before the cap. Request `kinds=["sleep"]` to examine sleep without other care.
Records contain `id`, `kind`, `research_day`, optional `occurred_at`, and `data` limited
to cue, valence, value, score, great_success, traits, rank and hours. Internal payloads,
week/fly identity and other unused data stay out of the model context.

`count_care_events` returns exact `count`, up to four citation `ids`, and `filters`
with week_id and all conditions (null for omitted conditions). For a zero count,
IDs refer to inspected records in the same feature time window, not matching events;
no records means no IDs. Counts never depend on the capped list. For example:

```json
{"count": 3, "ids": ["#0042", "#0041", "#0040"], "filters": {
  "week_id": "week", "kinds": ["training"], "research_day": 2,
  "cue": "banana", "valence": "reward"
}}
```

The general prompt has two brief tool-use examples, without a fixed answer template.
Any successful care/count/association/experiment tool satisfies the retrieval guard;
paper search alone does not. Only returned IDs can be cited.

## Providers and caching

`SHIORI_PROVIDER=mock` is the default even when API keys are present. Explicit options:

| Provider | Key | Journal default | Q&A default |
| --- | --- | --- | --- |
| `anthropic` | `ANTHROPIC_API_KEY` | `claude-haiku-4-5` | `claude-sonnet-4-6` |
| `openai` | `OPENAI_API_KEY` | `gpt-4.1-nano` | `gpt-4.1-mini` |
| `ollama` | none | `qwen3.5:2b-q4_K_M` | `qwen3.5:4b` |

Override models with `ANTHROPIC_JOURNAL_MODEL`, `ANTHROPIC_QA_MODEL`,
`OPENAI_JOURNAL_MODEL`, and `OPENAI_QA_MODEL`. The raw-httpx implementations follow the
[Messages tool protocol](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)
and [Responses function-calling protocol](https://developers.openai.com/api/docs/guides/function-calling).
HTTP tests use `httpx.MockTransport`; default tests and evaluation make no live calls.

Token counts come from vendor usage fields. Cost is an estimate using configurable
`<VENDOR>_INPUT_USD_PER_MILLION` and `<VENDOR>_OUTPUT_USD_PER_MILLION` rates, or the
constructor's `rates=(input, output)`. Default estimates are `(3, 15)` for Anthropic and
`(0.4, 1.6)` for OpenAI, applied to either configured model. They are not a current pricing
catalog; supply the selected model's billing rates for budget decisions. Mock tokens are
character-based estimates with zero dollar cost. Response-cache hits bill zero tokens and
dollars and increment `cache_hits`.

`CachedProvider` defaults to a bounded in-memory LRU (128 entries). Its key includes
provider, model, tools and the entire conversation, including week/fly identity and tool
results. Use `CachedProvider(provider, RedisCache(redis_async_client, ttl=3600))` for a
shared cache; the host owns the client and its lifetime. Do not store raw API keys in a
cache namespace. HTTP errors propagate and are not cached. Cloud requests have a 30-second timeout; Ollama defaults to 120 seconds.

## Evidence, research and model boundaries

The verifier splits Japanese sentences, rejects missing/unknown/unseen citations and
drops prohibited emotion attributions. It does not replace them with invented behavioral
claims. Empty output has verification rate zero. ID existence and provenance are checked;
semantic entailment of arbitrary live-provider prose is not guaranteed by this verifier.

`data/papers.jsonl` contains 20 original short summaries with bibliographic links: mushroom
body learning, PAM/PPL1, sparse coding, giant-fiber escape, MN9, circadian clocks and the
2017 Nobel announcement, Winding's 2023 larval connectome, and adult connectomes. The Nobel
entry is an institutional announcement, not a research paper. `#p-*` references are
validated only against retrieved documents. Literature describes biological research;
copy experiments describe the game's small model. Neither establishes the fly's emotions.

BM25 uses Latin words and Japanese character bigrams. `PgVectorRetriever` delegates to a
host `VectorIndex.nearest(embedding, k)` implementation, which should query cosine distance
on the API's `papers.embedding` vector(384) column. `hashing_embed` produces stable,
normalized 384-dimensional vectors without downloads. Hashing is a lexical baseline,
not a semantic embedding model. To upgrade, version the corpus/index, install a Japanese-
capable embedding model, re-embed every document and query with the same model, and
migrate the vector dimension/index together. Evaluate Japanese retrieval before switching
the production retriever; do not mix old hashing vectors and new semantic vectors.

## Local Ollama

Read [the measured local report](reports/local-llm.md) before switching the backend.
Keep `SHIORI_PROVIDER=mock` until then. `SHIORI_PROVIDER=ollama` needs no API key.
The adapter uses the [native chat API](https://docs.ollama.com/api/chat), replays assistant
messages with tool calls, and returns tool results with `tool_name`. Both QA and journal
model names enter the cache namespace. Model names are configuration, including future
LoRA models.

| Variable | Host default | Purpose |
| --- | --- | --- |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama endpoint (Compose: `http://host.docker.internal:11434`) |
| `OLLAMA_QA_MODEL` | `qwen3.5:4b` | Questions and coaching |
| `OLLAMA_JOURNAL_MODEL` | `qwen3.5:2b-q4_K_M` | Journal and morning memo |
| `OLLAMA_NUM_CTX` | `8192` | Always sent; avoids Ollama's huge default context |
| `OLLAMA_NUM_PREDICT` | `512` | Positive per-call generation cap; also part of cache identity |
| `OLLAMA_KEEP_ALIVE` | `30m` | Model residency |
| `OLLAMA_TIMEOUT` | `120` | Request timeout in seconds |

Every request sends `stream=false`, `think=false`, temperature 0.2 and the generation cap.
The cap bounds runaway output; reaching it can leave partial text for verification/recovery. Leaked think
blocks are removed. Native prompt/output token counts are recorded with zero USD cost.
A connection error names the endpoint. No CPU inference setting is forced.

The agent rejects answers before retrieval and asks again within its four-call budget.
If all verified sentences are lost, an offline Mock recovery uses the same context,
feature limits and tool-result cache. This can add at most four Mock calls; repeated
identical experiments are reused. If all original tool calls failed validation, recovery
uses those failed results without broadening retrieval or starting experiments.
`fallback_used=true` and `stopped_reason="fallback"` mark recovery. `provider_text` is
the original verified text and `provider_verification` records its verification; regular
`verification` describes the displayed recovery. Token accounting retains the original
provider's calls, excluding Mock's synthetic estimates during recovery.

Live evaluation is opt-in, sequential and forbidden in CI:

```powershell
$env:SHIORI_LIVE_EVAL = "1"
# First debug a small sample. A limited report does not certify the full gates.
.\.tools\uv.exe run python -m tsuyu_shiori.eval --provider ollama --limit 3
# Full QA evaluation (42 counts + 9 topics + 10 open questions), once per model:
.\.tools\uv.exe run python -m tsuyu_shiori.eval --provider ollama --qa-model qwen3.5:4b
.\.tools\uv.exe run python -m tsuyu_shiori.eval --provider ollama --qa-model qwen3.5:2b-q4_K_M
# Three morning memos from the journal model on the same synthetic week:
.\.tools\uv.exe run python -m tsuyu_shiori.eval_memos --provider ollama --journal-model qwen3.5:2b-q4_K_M
Remove-Item Env:SHIORI_LIVE_EVAL
```

`--journal-model` overrides the journal model selection (these evaluation questions use
QA, not journal generation). `--limit N`, `--seed`, and `--output-dir` are supported.
Reports go to ignored `eval-results/shiori-<provider>-<sanitized-qa-model>/`. Model-name
punctuation becomes `-`. Each JSON result includes latency, tokens and fallback status;
summary metrics include mean/p95 latency (nearest rank), generation tokens/s, load time
and calls stopped at the generation limit (`generation_limit_count`).
Input tokens per question report mean/max sums across model calls; maximum tokens per call
measures the largest single context. These are different quantities. Mock tokens remain estimates.
Accuracy, topic/open accuracy, verification and readability grade the original verified model
answer **before recovery**; `delivered_accuracy`, `delivered_topic_accuracy` and
`delivered_open_accuracy` separately
measure what the user receives. Fallbacks therefore cannot make an invalid model pass.
Count grading accepts a number beside 回, rejecting conflicting counts. Topic grading
checks numeric values, action counts and record IDs rather than Mock sentence templates.
Existing Mock thresholds remain unchanged, with the open gate added at 0.70. Live tests skip unless `SHIORI_LIVE_EVAL=1`
and always skip in CI. If generation drops to a few tokens/s, record the observed speed
and possible power-saving mode; do not switch to CPU inference.

`eval_memos` saves three morning samples (September 23, 25, 28 at 08:00 JST),
including native/delivered text, verification, fallback status, latency and tokens.
It uses the journal model and previous-day/night windows, excludes future sleep,
and requires the same live opt-in as QA evaluation. `--output` selects its JSON path.
