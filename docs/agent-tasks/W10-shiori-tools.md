# Task W10-shiori-tools — small-model friendly tools and a general prompt for Shiori

Branch: `feat/shiori-tools`. Work in `services/shiori/`. Do not change `services/api` (the API's DB-backed `RecordStore`
must keep working unchanged: filter inside the tools layer, after `store.care_events(...)`).

## Why

W9 (`services/shiori/reports/local-llm.md`) measured Shiori on local Ollama models. `qwen3.5:4b` reached 64.3% count
accuracy and 33% topic accuracy with 100% citation verification, `qwen3.5:2b-q4_K_M` 2.4%. Two causes stand out:

1. **The context overflows.** The 4B run used 446,472 input tokens for 51 questions — about 8,750 per question, more
   than `num_ctx=8192` — because `get_care_events` returns every record of the week as full JSON. The model then
   miscounts records it can no longer see.
2. **The prompt is fitted to the eval.** `agent/prompt.py` now prescribes 「報酬の記録はN回です #ID。」 and "answer count
   questions in one sentence". Real players ask 「なんで？」, preferences, sleep, the presentation; those answers must stay
   natural, and the same prompt also drives the Anthropic/OpenAI providers.

The owner will later LoRA-finetune a small model on Shiori's tool traces, so the tool contract designed here is what
that model will learn. Keep it small, explicit and stable.

## What to build

1. **Compact, filterable `get_care_events`**: optional `research_day`, `cue`, `valence`, `kinds` filters applied in the
   tools layer; return compact records (`id`, `kind`, `research_day`, and only the data fields that matter, e.g. `cue`,
   `valence`, `value`, `score`, `great_success`, `traits`, `rank`, `hours`) plus `total` and `truncated`. Cap the list
   (e.g. 20 records, newest first) so one call can never fill the context. Sleep sessions stay available.
2. **`count_care_events`** tool: same filters, returns the exact `count` computed by code and up to 4 `ids` to cite
   (and the applied filters echoed back). Counting is code's job, not the model's.
3. **Enums the model can read**: cue and valence parameters as enums whose descriptions include the Japanese names
   (バナナ=banana, りんご酢=apple_vinegar, イースト=yeast, ぶどう=grape, 青い光=blue_light; 報酬=reward, 罰=punish), so
   the mapping lives in the tool schema instead of the system prompt.
4. **General prompt** (`agent/prompt.py`): remove the count-specific answer template and eval-specific rules; keep the
   four promises from `docs/specs/shiori.md`, "look up records with tools before answering", "cite only returned IDs".
   At most two short few-shot examples: one count question (using `count_care_events`) and one 「なんで？」 question
   (using `get_association` / `run_odor_choice`). Keep the W9 empty-answer fallback and the "retrieve first" loop guard,
   but the guard must accept any successful record tool, not only `get_care_events`.
5. **Eval**: add an `open` category of ~10 realistic player questions graded by phrase-independent facts (e.g.
   「どうしてバナナに寄っていくの？」, 「最近よく眠れてる？」, 「発表会のランクは？」, 「今週いちばん多かったしつけは？」), alongside the
   existing count and topic categories. Report input tokens per question (mean / max). Mock must still pass every gate.
6. **Measure again** on this PC with Ollama (see W9 for the setup; GPU ≈42 tokens/s for 4B, 83 for 2B): full eval once
   per model for `qwen3.5:4b` and `qwen3.5:2b-q4_K_M` as the QA model, plus 3 morning memos from the journal model on
   the synthetic week. Update `services/shiori/reports/local-llm.md` with a before/after table (W9 vs W10) and samples.
   Targets for 4B: count accuracy ≥ 0.8, topic ≥ 0.8, open ≥ 0.7, verification ≥ 0.95, input tokens per question
   well under `num_ctx`. Report honest numbers if you miss them, and what fails.
7. **Docs**: update the tool list in `docs/specs/shiori.md` (`docs(spec): …`, its own commit) and
   `services/shiori/README.md`.

The host CPU cools poorly: no CPU inference, no repeated full live evals — debug with `--limit`, run each full eval
once at the end.

## Done when

- `uv run pytest services/shiori services/worker` passes, `uv run ruff check .` is clean.
- `uv run python -m tsuyu_shiori.eval` (Mock) passes all gates, including the new `open` category.
- `services/shiori/reports/local-llm.md` has the W10 numbers.
- Many small atomic commits (filters, compact output, count tool, enums, prompt, guard, eval category, token metrics,
  report, docs — each separate).
