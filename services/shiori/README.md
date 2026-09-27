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

The last command writes ignored `eval-results/shiori/report.json` and `report.md`, and exits
nonzero unless accuracy is at least 0.80 and sentence verification is at least 0.95.
`--seed` and `--output-dir` are available. The evaluation generates 42 count questions from
a synthetic week, including zero counts, different days, cues and reinforcement types.
It measures template accuracy and citation validity, not live-model reasoning quality.

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
sessions starting after noon that day. Pass an aware `now` for reproducible generation.
The coach accepts a `cue`. Presentation ranks come from a persisted `presentation`
care record with `data.rank`, so the rank has its own verifiable evidence.
Missing records produce fewer sentences or empty text instead of fabricated evidence.

The result contains text, evidence IDs, experiments, a verification report, and per-call
token/cost accounting. `ai_label` and `disclaimer` are separate UI metadata: display both.
Verification reports describe the generated answer before feature sentence limits.

Record IDs are opaque to Shiori; host implementations must check ownership. The SQL host
uses `#0001` for care, `#c-1` for experiments and `#s-<uuid>` for sleep. Data conventions:
care carries `research_day`, `cue`, `valence`, optional `value`; sleep carries `hours`;
experiments carry `toward`, `away`, `cue`, `trials`, and `seed`.

The four tools validate arguments, reject out-of-conversation week/fly IDs, and cap trials
at 1,000. The host lab owns state loading and copying; brain state is never entrusted to
the language model. A run makes at most four provider calls and executes at most four
tools per step; the last step allows only a final answer. Repeated identical tool calls
reuse their result within the run, including persisted experiments.

## Providers and caching

`SHIORI_PROVIDER=mock` is the default even when API keys are present. Explicit options:

| Provider | Key | Journal default | Q&A default |
| --- | --- | --- | --- |
| `anthropic` | `ANTHROPIC_API_KEY` | `claude-haiku-4-5` | `claude-sonnet-4-6` |
| `openai` | `OPENAI_API_KEY` | `gpt-4.1-nano` | `gpt-4.1-mini` |

Override models with `ANTHROPIC_JOURNAL_MODEL`, `ANTHROPIC_QA_MODEL`,
`OPENAI_JOURNAL_MODEL`, and `OPENAI_QA_MODEL`. The raw-httpx implementations follow the
[Messages tool protocol](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)
and [Responses function-calling protocol](https://developers.openai.com/api/docs/guides/function-calling).
HTTP tests use `httpx.MockTransport`; no paid calls are made by tests or evaluation.

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
cache namespace. HTTP errors propagate and are not cached. Requests have a 30-second timeout.

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
