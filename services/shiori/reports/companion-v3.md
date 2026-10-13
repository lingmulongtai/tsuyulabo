# W17 companion delivery — 2026-10-13

Implemented individual diary history, deterministic selection of recorded moments, nightly
03:30 JST generation, a diary screen with one paused 3D reconstruction at a time, a Japanese
PNG share card, dismissible measured-state hints and contextual behaviour explanations.
Free-form questions live inside the diary disclosure and carry an ownership-checked fly ID.
The vivarium internals are unchanged; glass selection/public props and the explicit selected-fly
button are used. Copies are labelled as copies in diary text and explanations.

## Offline evidence

- `pytest services/shiori services/worker`: 161 passed, 5 slow eval tests deselected.
- Targeted API suites: 19 passed (one slow eval deselected), including migrations,
  ownership, stale behaviour, diary idempotency, hint cooldown/dismissal, odor-copy
  provenance, OpenAPI export and a full rearing week.
- Ruff: API, Shiori, worker and the extended GPU data validator clean.
- Mock: original 61 cases and 13 companion fact checks pass; original accuracy,
  verification and readability are 1.0, with no QA fallbacks.
- The extended 163-case held-out diagnostic passes at 82.2% accuracy and 100% citation
  verification/readability. The new intents, maxima, missing-record and injection cases
  pass. Mock still has weak weekday/paraphrased-why coverage; this is not live LoRA evidence.
- Web lint/typecheck/build pass; 294 unit tests pass.
- Edge browser with synthetic API responses: desktop/mobile diary, no horizontal overflow,
  evidence disclosure, collapsed questions, individual switching and a 1080×1350 PNG export
  pass. Browser screenshots and PNG are under the ignored `.codex-runs/` directory.
- Generated `data/shiori-sft-v3`: 4,000 train / 400 valid / 163 test. Four new intents
  have 200 train / 20 valid examples each. Seed and phrasing ranges remain disjoint.
  Estimated maximum 3,772 tokens, rounded training length 3,840. Complete stdlib
  training dry-run validates all traces, tools, split hashes and provenance.

## Acceptance boundaries

Production QA stays on its existing v2 configuration. New intent routing defaults to Mock;
the commander can enable each intent after real v3 acceptance. GPU/WSL training, true
tokenizer lengths, GGUF export, live Ollama quality/latency and physical mobile performance
remain to be verified using `ml/shiori-lora/README.md`.

3D diary moments reconstruct stored state and behavior; they are not pixel captures of the
original animation frame. The public vivarium API has no fly raycast or frame-capture callback.
Glass selection and the accessible selected-fly control expose “どうして？”. The share PNG
contains the dated diary prose, individual name and AI label. The current decoder has no
flight output or mould stimulus: those event selectors require such future real records and
never manufacture them. Adults have no persisted current habitat, so environmental hints
remain quiet for them. Days with no observations are skipped.

No `.git` writes, publication, model switch or `docs/HANDOFF.md` edit. Atomic steps are
listed exactly once per changed file in `.codex-runs/commits.jsonl` for the commander.
