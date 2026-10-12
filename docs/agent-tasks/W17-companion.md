# Task W17-companion — AI where it matters: a diary, a quiet hint, and "why?" on tap

Branch: `feat/companion`. Read `docs/specs/vision-v2.md` §5 (source of truth), `docs/specs/terms-v2.md` (W15),
`docs/specs/shiori.md`, `services/shiori/reports/lora-models.md`. Work in `services/shiori/`, `services/worker/`,
`services/api/` (endpoints), and `apps/web/src/components/shiori/**` + where these surface (avoid the vivarium internals;
use its public API only).

## Goal

The owner: "AI in a chat box nobody uses is meaningless." The meaningful AI is the fly's brain (already there). Shiori's
language model should only appear where it adds something a player wants:

1. **Observation diary** — each night the worker picks the day's notable events for each individual (first flight,
   approached banana after training, avoided mould, grew fast after a good meal, eclosion…) from records and brain
   outputs, and writes a 2–3 sentence diary entry in Shiori's warm voice, plus which 3D snapshot moment to show.
   A diary screen to read back through the individual's life; a share card (image) of an entry.
2. **A quiet hint when something is wrong** — rules detect trouble (too hot/cold, dry food, mould, missed meals, stress
   behaviour); the LLM phrases one short sentence about what the fly is showing and what would help. Rate-limited,
   dismissible, never a chat.
3. **Tap the fly → "どうして？"** — ask about the behaviour happening right now; Shiori answers in 1–2 sentences from that
   individual's brain/association state and recent care (existing agent + tools), evidence behind a small "根拠" disclosure.
4. **Persona**: Shiori is a caretaker partner, not a researcher (terms-v2). Update the system prompt and Mock templates,
   regenerate the SFT dataset with the new prompt and the new intents (diary, hint, behaviour-why, morning memo, plus the
   v2 weaknesses listed in `lora-models.md`: unmeasured cues must not get invented values, maxima name the cue,
   injection answers state the AI identity), and write the commands for the commander to retrain LoRA v3 in WSL
   (`ml/shiori-lora/README.md`). Until v3 is trained and passes, production keeps v2 for answers and Mock text for the
   new intents — make the fallback per intent so nothing breaks.
5. Remove the always-visible "ask Shiori" entry points; the free-form question box can stay inside the diary screen.

## Done when

- `uv run pytest services/shiori services/worker` and targeted API tests pass, ruff clean, Mock eval passes (extend it with
  diary/hint/behaviour-why cases graded by facts), web lint/typecheck/test/build pass.
- Many small atomic commits (event detection, diary job, diary API, diary screen, share card, hint rules, hint phrasing,
  tap-why, persona/prompt, dataset intents, eval cases, docs — each separate).
