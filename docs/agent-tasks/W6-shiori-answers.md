# Task W6-shiori-answers — make Shiori's Mock answers read like a researcher, not a record dump

Branch: `feat/shiori-answers`. Work in `services/shiori/` and `apps/web/src/components/shiori/` (display only).

A live run asked 「しつけをすると、ツユの脳はどう変わるの？」 and the MockProvider answered
「お世話の記録は46件あります #0001 #0002 … #0046。」 — correct but useless, and ugly in the UI. The Mock provider is
what runs without an API key (CI, demo, portfolio screenshots), so it must produce good answers on its own.

1. **Topic-aware Mock answers** built only from tool results (no invented facts): detect the question's topic
   (learning/training, a specific cue like バナナ/りんご酢, meals/great success, sleep, cleaning/temperature,
   eclosion/traits, "why does it avoid/approach X" → run `run_odor_choice` on a copy) and answer in 2–3 short
   Japanese sentences in Shiori's voice (observes and measures, never speaks for Tsuyu's feelings). Examples of the
   shape: 「火曜と水曜に、バナナの匂いとあまいごほうびを3回覚えました #0012 #0015 #0019。いまの好みの値は +0.47 で、
   コピーで20回試すと14回バナナのほうへ進みました #c-3。」
2. **Cite few, relevant records**: at most 4 record IDs per sentence and 6 per answer, picked by relevance
   (matching cue/kind, most recent), plus experiment IDs when an experiment ran. Verification must still pass (every
   sentence keeps ≥1 existing ID). If there are no relevant records, say so honestly and suggest what to do.
3. **Eval**: extend `python -m tsuyu_shiori.eval` with topic questions and a "readability" gate (max IDs per
   answer ≤ 6, answer length ≤ 160 chars, each sentence cited) alongside accuracy / verification; keep existing gates.
4. **Web display** (`src/components/shiori/*`): if an answer still has many evidence chips, show the first 6 and a
   「+N件」 chip that expands.

Done when: `uv run pytest services/shiori services/worker services/api` and `-m eval` pass, web lint/typecheck/test
pass. Atomic commit plan entries.
