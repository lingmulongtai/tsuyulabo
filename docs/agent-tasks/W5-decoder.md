# Task W5-decoder — pass the last MaleCNS gate (behaviour decoder ≥ 85 %)

Branch: `feat/malecns-decoder`. Work in `services/brain/` only (+ the evaluation table in the root `README.md`).

State (see `services/brain/reports/report-malecns.md`): 5/6 gates pass on `malecns-v1.0`. The decoder reaches
75.6 % (logistic) / 79.0 % (MLP) vs 41–43 % on shuffled wiring; the gate is ≥ 85 %. Raw Feather data is in your
clone at `data/raw/malecns-v1.0/` (never commit it).

1. Diagnose with the confusion matrix which labels collapse (likely `rest` vs `approach`/`avoid` or
   `turn_left` vs `turn_right`) and why (silent outputs, saturated groups, identical scenarios in the dataset).
2. Fix at the right level, in this order of preference: dataset/scenario definitions that make labels
   indistinguishable → circuit responsiveness (documented scales / input rates) → feature engineering (e.g. per
   window left−right differences, MBON balance, onset latency) → model capacity (small MLP hyper-parameters,
   early stopping). Never tune on the test split; keep a fixed seed and report the split.
3. Keep every previous gate passing on both `toy-v0` and `malecns-v1.0`. If all six pass on `malecns-v1.0`,
   **make it the default version** (loader default, brain README, root README table) and ensure the whole Python
   suite passes with the new default (the game API uses the default — run `uv run pytest` fully). If it cannot
   reach 85 % honestly, stop, keep `toy-v0`, and report the best achieved number and the reason.
4. Regenerate artifacts with LF line endings if they change (manifest stores sha256 of the committed bytes).

Done when: `uv run pytest`, `uv run pytest -m eval`, ruff pass; report updated. Atomic commit plan entries.
