# Task W9-shiori-local — run Shiori on a local LLM (Ollama) and measure it

Branch: `feat/shiori-local`. Work in `services/shiori/`. Small, mentioned changes are allowed in `docker-compose.yml`,
`docker-compose.selfhost.yml`, `.env.example` and `docs/specs/shiori.md`.

## Why

The owner wants Shiori to use a real LLM **running on the owner's PC**, with no API keys: an RTX 4050 laptop GPU with
6 GB of VRAM, 63 GB RAM, and Ollama 0.34 at `http://127.0.0.1:11434`. These models are already pulled:

| model | use | size |
| --- | --- | --- |
| `qwen3.5:4b` | questions (QA) | 3.4 GB, fits in VRAM |
| `qwen3.5:2b-q4_K_M` | night journal / morning memo | 1.9 GB |
| `gemma4:e4b` | optional comparison only | 9.6 GB, does **not** fit in VRAM (≈55 s per call) |

Later we will LoRA-finetune a small model and serve it through Ollama, so nothing may assume a specific model name.

Measured on this PC (2026-09-29): generation is slow right now — about 2.7 tokens/s for `qwen3.5:4b` and 7.7
tokens/s for `qwen3.5:2b-q4_K_M` — because the GPU is held at its minimum clock and shared with desktop apps. So a
full 42-question live eval takes a long time: build and debug with `--limit`, and run the full eval once at the end.
`qwen3.5:4b` sometimes answers **without calling a tool** and invents a number (「0 回」); the prompt and agent loop
must make it look the records up first. Ollama's native `/api/chat` returns tool calls from these models, e.g.
`{"role":"assistant","content":"","tool_calls":[{"id":"call_8wwh3b05","function":{"index":0,"name":"get_care_events","arguments":{"week_id":"w1"}}}]}`.
Ollama loads models with a huge default context (131072) unless `options.num_ctx` is set, which pushes most of the
model off the GPU — always send `num_ctx`.

## What to build

1. **`OllamaProvider`** (`gateway/ollama.py`, exported from `gateway/__init__.py`), implementing the existing
   `Provider` protocol (`cache_namespace`, `model_for`, `complete`). Follow the style of `gateway/http.py`
   (injectable `httpx.AsyncClient` so tests need no server).
   - `POST {OLLAMA_BASE_URL}/api/chat` (default `http://127.0.0.1:11434`), `stream: false`, `think: false`,
     `keep_alive` (env `OLLAMA_KEEP_ALIVE`, default `"30m"`),
     `options: {"num_ctx": OLLAMA_NUM_CTX (default 8192), "temperature": 0.2}`, `tools` in the OpenAI function format.
   - Models: `OLLAMA_QA_MODEL` (default `qwen3.5:4b`), `OLLAMA_JOURNAL_MODEL` (default `qwen3.5:2b-q4_K_M`).
   - Ollama is stateless: replay the native assistant message (with its `tool_calls`) through
     `Response.continuation`, and send tool results as `{"role": "tool", "tool_name": <name>, "content": <json>}`.
   - Be tolerant of small models: `arguments` may be a dict or a JSON string; ids may be missing (generate stable ids);
     strip any leaked `<think>…</think>` from `content`.
   - Cost: `input_tokens = prompt_eval_count`, `output_tokens = eval_count`, `usd = 0.0`.
     `cache_namespace` must include both model names so switching models never reuses cached answers.
   - Timeout from `OLLAMA_TIMEOUT` (default 120 s). A connection error must raise a clear error that names the URL.
   - Unit tests with `httpx.MockTransport` (see `tests/test_http_providers.py`): request body shape (num_ctx, think,
     tools), dict and string arguments, missing ids, think stripping, continuation replay, connection errors.
2. **`default_provider()`** accepts `SHIORI_PROVIDER=ollama` (update the error message).
3. **Never show an empty answer.** A small model may cite badly, and verification then drops every sentence. When the
   verified text is empty, fall back to `MockProvider` for that request, built from the same tools/context, and mark
   it (`stopped_reason="fallback"`, plus a field the eval can count). Mock behaviour itself must not change.
4. **Prompting for small models**: improve `SYSTEM_PROMPT` (and, if needed, a short few-shot example of an answer with
   `#0412`-style citations) so small models cite IDs from tool results. Keep the Mock path and the four promises in
   `docs/specs/shiori.md` intact.
5. **Live evaluation** in `python -m tsuyu_shiori.eval`:
   - `--provider mock|ollama` (default mock, unchanged gates), `--qa-model`, `--journal-model`, `--limit N`.
   - Count grading currently parses the Mock phrase 「該当する記録は(\d+)回」. Make it phrase-independent (e.g. the
     number in the answer next to 回) while Mock still scores the same. Topic grading currently expects exact Mock
     phrases (「接近15回」); change the expectations to phrase-independent facts (numbers, values, record IDs) that any
     correct answer must contain, and keep Mock at 100%.
   - Report per answer latency (mean / p95 seconds), tokens, fallback count, accuracy, topic accuracy, verification
     rate, readability. Write to `eval-results/shiori-<provider>-<model>/` (git-ignored).
   - Live runs must never run in CI: any live test is skipped unless `SHIORI_LIVE_EVAL=1`.
6. **Run the live eval** on this PC for `qwen3.5:4b` (QA) and `qwen3.5:2b-q4_K_M` (both as QA model too, for
   comparison), then commit a short report `services/shiori/reports/local-llm.md`: a table per model (accuracy,
   topic accuracy, verification, readability, fallback rate, mean/p95 latency) and 3–5 sample answers. Tune the prompt
   (step 4) until qwen3.5:4b reaches the Mock gates (accuracy ≥ 0.8, verification ≥ 0.95) if you can; if not, report
   the honest numbers and what fails.
7. **Wiring**: pass `SHIORI_PROVIDER`, `OLLAMA_BASE_URL`, `OLLAMA_QA_MODEL`, `OLLAMA_JOURNAL_MODEL`, `OLLAMA_NUM_CTX`
   through the backend environment in `docker-compose.yml` (container default for the URL:
   `http://host.docker.internal:11434`) and in `docker-compose.selfhost.yml`; add
   `extra_hosts: ["host.docker.internal:host-gateway"]` to `api` and `worker`. Document the variables in
   `.env.example`. Keep `mock` as the default everywhere — the owner switches after reading the report.
8. **Docs**: add the Ollama provider to `docs/specs/shiori.md` (`docs(spec): …`, its own commit) and to
   `services/shiori/README.md`.

## Done when

- `uv run pytest services/shiori services/worker services/api` passes and `uv run ruff check .` is clean.
- `uv run python -m tsuyu_shiori.eval` (Mock) still passes all gates.
- `services/shiori/reports/local-llm.md` has the measured live numbers.
- Many small atomic commits (provider, its tests, default_provider, fallback, prompt, eval grading, eval options,
  report, wiring, docs — each separate).
