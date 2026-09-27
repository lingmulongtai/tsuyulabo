# Task W3-malecns — build circuits from the real MaleCNS v1.0 connectome

Branch: `feat/malecns`. Work in `services/brain/` (and `pyproject.toml` / `uv.lock` only to add `pyarrow`
and `pandas` to a new optional dependency group `ingest` of `tsuyu-brain`; do not make them runtime deps).

The owner approved downloading the data. These files are already in your clone at
`data/raw/malecns-v1.0/` (git-ignored; never commit them):

- `body-annotations-male-cns-v1.0-minconf-0.5.feather` (13 MB) — per body: type, instance, class, side, …
- `body-neurotransmitters-male-cns-v1.0.feather` (42 MB) — predicted transmitter per body
- `connectome-weights-male-cns-v1.0-minconf-0.5.feather` (1.1 GB) — body→body synapse counts

Source: https://male-cns.janelia.org/download/ (CC-BY 4.0; Berg et al., 2026, Cell; FlyEM / HHMI Janelia,
University of Cambridge, MRC LMB, Google Research). Read `AGENTS.md`, `docs/specs/brain.md`,
`services/brain/README.md`, `services/brain/scripts/ingest_malecns.py` (skeleton), the `Circuit` class and
`connectome/toy_v0.py` + `npz_io.py`.

Inspect the Feather schemas first (column names, dtypes, row counts) with pyarrow — read the 1.1 GB weights
table with column projection / filtering so memory stays reasonable.

## Build

1. `scripts/ingest_malecns.py` — real pipeline: load annotations + transmitters, select the cell types for each
   circuit in brain.md by their **real type names** (e.g. ORNs by glomerulus, uniglomerular PNs, KCs (sample a
   fixed, seeded subset if needed), APL, MBONs (map to `MBON_ap` / `MBON_av` groups by the published valence of
   each MBON type — document the mapping with citations in the README), PAM / PPL1 DANs, Gr64f / Gr66a GRNs,
   MN9, LPLC2 / LC4, DNp01 (giant fiber), DNa02, JO neurons, aDN, walking DNs). Keep each circuit ≤ 2000
   neurons. Signs from predicted transmitter (ACh +, GABA −, Glu − as inhibitory by default in the fly CNS —
   document this choice). Weights = synapse counts × a per-circuit scale. Write versioned `.npz` files with the
   same `Circuit` interface to `src/tsuyu_brain/connectome/malecns_v1/` plus a `manifest.json` (source files,
   sha256 of inputs, selection rules, neuron counts per group, license + citation). Keep committed files small
   (target < 2 MB total; store sparse matrices; use float16 where lossless enough).
   If a type cannot be found under the expected name, search annotations for aliases, record what you used, and
   leave a clear TODO rather than inventing neurons.
2. Register version `malecns-v1.0` in the loader: `load_circuit(name, version="malecns-v1.0")`. Keep
   `toy-v0` as the default until the evaluation passes on the real circuits.
3. **Calibration + evaluation**: run the brain.md evaluation table on `malecns-v1.0` (sugar → MN9, looming →
   DNp01, bitter suppresses feeding, training shifts PI, traits show up, decoder accuracy vs shuffled). Tune only
   the global per-circuit scales / input rates (document them). Extend `python -m tsuyu_brain.eval` with
   `--version` and write `eval-results/brain/report-malecns.md` + JSON. If every gate passes, make
   `malecns-v1.0` the default version and say so; otherwise keep `toy-v0` default and report which gates fail.
4. Tests: loader tests for the committed npz (shapes, groups present, sign conventions, manifest integrity),
   and the sanity checks on the real circuits (mark heavy ones `eval`).
5. README: data provenance, citation, what is real / model / game, how to re-run the ingest.

## Done when

`uv run pytest services/brain` and `-m eval` pass, ruff clean, npz + manifest committed (in the plan), raw data
not committed. Atomic commit plan entries.
