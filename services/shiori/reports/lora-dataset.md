# Shiori oracle SFT dataset

Generated on 2026-10-01 using `python -m tsuyu_shiori.dataset --out data/shiori-sft`.
No live model or player data was used. `MemoryLab` is a deterministic synthetic fake;
its copy experiments teach the tool contract, not real brain/animal behavior.

| Split | Examples | Seeds | Estimate mean / max | Qwen tokens mean / max |
| --- | ---: | --- | ---: | ---: |
| train | 4000 | 1000–1040 | 2450.7 / 2926 | 2305.7 / 2870 |
| valid | 400 | 2000–2004 | 2451.0 / 2921 | 2306.1 / 2872 |
| test | 159 | 37 | 2458.0 / 2874 | 2310.7 / 2790 |

| Intent | Train | Valid | Test |
| --- | ---: | ---: | ---: |
| cleaning | 40 | 4 | 3 |
| count_cue | 204 | 20 | 5 |
| count_day | 1640 | 168 | 82 |
| count_valence | 80 | 8 | 2 |
| count_weekday | 1230 | 120 | 30 |
| eclosion | 40 | 4 | 3 |
| injection | 40 | 4 | 1 |
| maximum | 40 | 4 | 2 |
| missing | 40 | 4 | 1 |
| preference | 203 | 20 | 7 |
| presentation | 40 | 4 | 2 |
| pupation_site | 40 | 4 | 2 |
| research | 40 | 4 | 1 |
| sleep | 40 | 4 | 3 |
| success | 40 | 4 | 3 |
| temperature | 40 | 4 | 3 |
| why | 203 | 20 | 9 |

`stats.json.max_length = 2944`. The estimate counts ASCII / 4 and
non-ASCII × 1.5, including complete function schemas. Actual lengths were checked with
`Qwen/Qwen3.5-2B` and Transformers 5.3.0 using the native non-thinking tool template.
All 4,559 examples tokenize below 3,000 tokens with assistant-only labels. No weights
were loaded for this check. Runtime training repeats the token/mask check before weights.

There are 17 intents and three question patterns per intent. Patterns 0/1 are used in
train and valid; pattern 2 is wholly reserved for test. Test also retains the exact 61
original eval questions on its unchanged seed-37 week. The extra 98 cases use held-out
wording. Train and valid worlds vary all five cues, counts, sleep, scores, ranks, traits,
association signs/strengths and copy outcomes. Each answer has three phrasing patterns.

Weekday counts map to research_day because synthetic weeks start Monday. Counts always
use `count_care_events`, including zero and totals above the list cap. Great-success
observations inspect a complete (at most eight-record) meal list. Pupation observations
use the current compact tool contract's score; they do not invent an unavailable site field.
No-record cases are absent topics in nonempty weeks and cite inspected records.
Prompt injections never fabricate IDs, deny AI identity or modify the real fly.

All exported traces were replayed through `tools.execute` with identical results and
every final answer passed `verify` with zero dropped sentences and the eval readability
rules (≤160 characters, ≤6 IDs, every sentence cited). Unit tests cover determinism,
split separation, JSON format, replay tampering, native token masking, dry-runs and
held-out fact grading. The existing offline Mock gate remains unchanged.

Seed/template provenance and SHA-256 hashes are in matching `.meta.jsonl` sidecars;
they are not present in student prompts. Generated data and training artifacts are ignored.
Training commands and the untested GPU/export boundary are in
[the training README](../../../ml/shiori-lora/README.md).

## Three sample traces

The shared system message is the unmodified
[SYSTEM_PROMPT](../src/tsuyu_shiori/agent/prompt.py); `tools` wraps the five real
[SCHEMAS](../src/tsuyu_shiori/tools/__init__.py) as OpenAI functions. To keep this report
small, those shared fields are referenced here. The remaining messages below are actual
exported chat messages, including JSON user payloads and exact tool-call/result IDs.

### Filtered count (seed 1000)

```json
{
  "messages": [
    {
      "role": "user",
      "content": "{\"question\": \"火曜のりんご酢の報酬は何回？\", \"feature\": \"answer\", \"week_id\": \"eval-week\", \"fly_id\": \"eval-fly\"}"
    },
    {
      "role": "assistant",
      "content": "",
      "tool_calls": [
        {
          "id": "call_0",
          "type": "function",
          "function": {
            "name": "count_care_events",
            "arguments": {
              "week_id": "eval-week",
              "kinds": [
                "training"
              ],
              "research_day": 2,
              "cue": "apple_vinegar",
              "valence": "reward"
            }
          }
        }
      ]
    },
    {
      "role": "tool",
      "name": "count_care_events",
      "tool_call_id": "call_0",
      "content": "{\"count\": 1, \"ids\": [\"#0018\"], \"filters\": {\"week_id\": \"eval-week\", \"kinds\": [\"training\"], \"research_day\": 2, \"cue\": \"apple_vinegar\", \"valence\": \"reward\"}}"
    },
    {
      "role": "assistant",
      "content": "記録を集計すると、該当件数は1回です #0018。記録外の行動までは分かりません #0018。"
    }
  ]
}
```

### Observation and copy experiment (seed 1000)

```json
{
  "messages": [
    {
      "role": "user",
      "content": "{\"question\": \"どうしてりんご酢に反応するの？\", \"feature\": \"answer\", \"week_id\": \"eval-week\", \"fly_id\": \"eval-fly\"}"
    },
    {
      "role": "assistant",
      "content": "",
      "tool_calls": [
        {
          "id": "call_0",
          "type": "function",
          "function": {
            "name": "get_association",
            "arguments": {
              "fly_id": "eval-fly",
              "cue": "apple_vinegar"
            }
          }
        },
        {
          "id": "call_1",
          "type": "function",
          "function": {
            "name": "run_odor_choice",
            "arguments": {
              "fly_id": "eval-fly",
              "cue": "apple_vinegar",
              "trials": 20,
              "seed": 0
            }
          }
        },
        {
          "id": "call_2",
          "type": "function",
          "function": {
            "name": "count_care_events",
            "arguments": {
              "week_id": "eval-week",
              "kinds": [
                "training"
              ],
              "cue": "apple_vinegar"
            }
          }
        }
      ]
    },
    {
      "role": "tool",
      "name": "get_association",
      "tool_call_id": "call_0",
      "content": "{\"records\": [{\"id\": \"#a-apple_vinegar\", \"kind\": \"association\", \"data\": {\"cue\": \"apple_vinegar\", \"value\": -0.32}, \"week_id\": \"eval-week\", \"fly_id\": \"eval-fly\", \"occurred_at\": null}]}"
    },
    {
      "role": "tool",
      "name": "run_odor_choice",
      "tool_call_id": "call_1",
      "content": "{\"records\": [{\"id\": \"#c-1\", \"kind\": \"experiment\", \"data\": {\"cue\": \"apple_vinegar\", \"trials\": 20, \"seed\": 0, \"toward\": 7, \"away\": 13, \"model\": \"deterministic-fake\"}, \"week_id\": null, \"fly_id\": \"eval-fly\", \"occurred_at\": null}]}"
    },
    {
      "role": "tool",
      "name": "count_care_events",
      "tool_call_id": "call_2",
      "content": "{\"count\": 17, \"ids\": [\"#0071\", \"#0055\", \"#0054\", \"#0044\"], \"filters\": {\"week_id\": \"eval-week\", \"kinds\": [\"training\"], \"research_day\": null, \"cue\": \"apple_vinegar\", \"valence\": null}}"
    },
    {
      "role": "assistant",
      "content": "直近に測ったりんご酢の連合値は-0.32でした #a-apple_vinegar。コピー実験20回では接近7回、回避13回でした #c-1。原因の断定はできません #c-1。"
    }
  ]
}
```

### General research (seed 1000)

```json
{
  "messages": [
    {
      "role": "user",
      "content": "{\"question\": \"キノコ体の学習を論文から教えて\", \"feature\": \"answer\", \"week_id\": \"eval-week\", \"fly_id\": \"eval-fly\"}"
    },
    {
      "role": "assistant",
      "content": "",
      "tool_calls": [
        {
          "id": "call_0",
          "type": "function",
          "function": {
            "name": "count_care_events",
            "arguments": {
              "week_id": "eval-week",
              "kinds": [
                "training"
              ]
            }
          }
        },
        {
          "id": "call_1",
          "type": "function",
          "function": {
            "name": "search_papers",
            "arguments": {
              "query": "キノコ体 嗅覚 学習",
              "k": 1
            }
          }
        }
      ]
    },
    {
      "role": "tool",
      "name": "count_care_events",
      "tool_call_id": "call_0",
      "content": "{\"count\": 115, \"ids\": [\"#9001\", \"#0076\", \"#0075\", \"#0074\"], \"filters\": {\"week_id\": \"eval-week\", \"kinds\": [\"training\"], \"research_day\": null, \"cue\": null, \"valence\": null}}"
    },
    {
      "role": "tool",
      "name": "search_papers",
      "tool_call_id": "call_1",
      "content": "{\"papers\": [{\"id\": \"#p-01\", \"title\": \"The neuronal architecture of the mushroom body provides a logic for associative learning\", \"authors\": [\"Yoshinori Aso et al.\"], \"year\": 2014, \"doi\": \"10.7554/eLife.04577\", \"url\": \"https://elifesciences.org/articles/04577\", \"summary\": \"キノコ体の Kenyon cell、MBON、ドーパミン細胞の配置を区画として整理し、嗅覚連合学習を調べる回路の土台を示した。\"}]}"
    },
    {
      "role": "assistant",
      "content": "文献の要約では、キノコ体の Kenyon cell、MBON、ドーパミン細胞の配置を区画として整理し、嗅覚連合学習を調べる回路の土台を示した #p-01。文献の結果をこの個体の観測とは混同しません #p-01。"
    }
  ]
}
```
