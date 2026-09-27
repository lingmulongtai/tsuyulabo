# Task W4-malecns-calibrate — make the real MaleCNS circuits pass the evaluation gates

Branch: `feat/malecns-calibrate`. Work in `services/brain/` only.

`malecns-v1.0` circuits are merged (see `services/brain/README.md`, `services/brain/reports/report-malecns.md`,
`src/tsuyu_brain/connectome/malecns*.py`, `scripts/ingest_malecns.py`, `scripts/calibrate_malecns.py`). The raw
Feather files are in your clone at `data/raw/malecns-v1.0/` (never commit them). Current result: 3/6 gates pass.

Failing gates and what we know:

1. **learning** — baseline banana PI is already +1.0 (saturated), so reward cannot raise it. The approach vs
   avoidance MBON groups receive very different total KC drive in the real data. Normalise per-MBON-group input
   (e.g. scale KC→MBON weights so both valence groups get comparable drive at baseline, or add the APL feedback /
   a homeostatic baseline), so the untrained PI is near 0 and training moves it both ways.
2. **trait_bias** — the steering circuit is silent (right-turn fraction 0.0 for everyone). Real photoreceptor →
   DNa02 paths are multi-synaptic; the extract probably dropped the intermediate visual projection neurons.
   Include the intermediate layer(s) needed (documented by type name), or, if that exceeds the neuron budget,
   document a principled reduction (e.g. collapse a well-defined intermediate population into a pooled node with
   summed weights) — never invent connectivity.
3. **decoder** — accuracy 46.6% vs 40.9% shuffled. Once the circuits respond, rerun; if still weak, improve the
   features (per-window rates of more output groups, left/right differences) rather than the classifier.

Rules: tune only documented global scales, input rates, and principled normalisations; record every choice with
its reason in the README and in `manifest.json`; regenerate artifacts with LF line endings (the manifest stores
sha256 of the committed bytes). Re-run `python -m tsuyu_brain.eval --version malecns-v1.0` and write the report.
**If all six gates pass, make `malecns-v1.0` the default version** (update the loader default, README, and the
root README's evaluation table numbers in `README.md` — that one root file is allowed) and make sure the whole
Python suite still passes with the new default. If not all pass, keep `toy-v0` default and report precisely.

## Done when

`uv run pytest` and `uv run pytest -m eval` pass, ruff clean, report updated. Atomic commit plan entries.
