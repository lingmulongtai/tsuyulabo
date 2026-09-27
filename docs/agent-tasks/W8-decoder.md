# Task W8-decoder — lift the MaleCNS decoder past 85 % by extracting the missing output neurons

Branch: `feat/malecns-outputs`. Work in `services/brain/` only (+ root README evaluation table). Model tier: astra.

Two previous attempts reached 78–79 % (gate 85 %); `services/brain/reports/report-malecns.md` concludes that silent
output groups cap validation accuracy near 80 %: some behaviours have no responsive output neurons in the extracted
circuits, so their labels collapse. Raw Feather data is in your clone at `data/raw/malecns-v1.0/` (never commit it).

1. Identify which labels collapse and which real output populations would carry them (e.g. walking/turning
   descending neurons beyond DNa02 such as DNa01, DNb05/06, DNg11/13; feeding motor neurons beyond MN9 such as
   MN11/MN12 for the labellum; grooming DNs such as DNg12; MBON types for approach/avoid). Look them up by type in the
   annotations; report counts. Add them to the circuit selections within the ≤ 2000-neuron budget per circuit,
   documenting every addition (type, count, why) in the manifest and README. Never invent neurons or edges.
2. Re-ingest (LF artifacts, checksums), recalibrate only documented global scales, rerun all six gates on both
   versions. Keep every other gate passing.
3. If all six pass on `malecns-v1.0`, make it the default version, run the whole Python suite with the new default, and
   update both READMEs. Otherwise keep `toy-v0` and report the best number and the remaining cause.

Done when: `uv run pytest`, `uv run pytest -m eval`, ruff pass; report updated. Atomic commit plan entries.
