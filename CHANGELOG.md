# Changelog

## v1.0.5 — 2026-11-27

Recovered source material added.  No model, figure or published value changed.

* **Main-campaign drivers.**  The four MATLAB segments that generated the main
  database (`code/comsol/main_200k/`, rows 1–50,000 / 50,001–100,000 /
  100,001–150,000 / 150,001–200,000, ports 2036–2039) are now archived.  Their
  identity is established in `docs/SOURCE_VERIFICATION.md` from the input
  design, the row coverage, the `.mat` field names read by `script/mat-csv.py`,
  and a row-level match of all 102,046 retained curves to the 200,000-row
  design.
* **Independent-cohort design.**  `PSC_LHS_9D_interface_lifetimes_300000_5.csv`
  (300,000 rows) is attached as the new asset `design_independent_300000.tar.gz`.
  Its `Sample_ID` is the row number, and all 153,067 retained curves equal it to
  three significant digits.
* **Layout.**  The existing drivers are moved to `code/comsol/independent_300k/`
  and the recovered ones added at `code/comsol/main_200k/`, so the two campaigns
  no longer share filenames.  `code/comsol/README.md` documents both.
* **Checks.**  New `code/verify_source_provenance.py` repeats the join and
  rounding comparison; `docs/DATA_DICTIONARY.md`, `docs/REPRODUCE.md` §3 and §6,
  `docs/KNOWN_LIMITATIONS.md` and the README are updated accordingly.

## v1.0.4 — 2026-11-27

Documentation and verification only.  No archived data, model or published value
changed.

* **Reproduction scope.**  The README section on what can be rerun was rewritten
  so it matches the files: the archived models, inputs and drivers support
  rerunning the 45-case back-substitution and the mesh studies with COMSOL 6.3 +
  Semiconductor Module + LiveLink; for the main campaign the 200,000-row design
  and retained curves are available but the original batch driver was not
  recovered; the retained independent-cohort curves are available but its
  300,000-row design was not recovered.  `docs/REPRODUCE.md` §6, README tier C
  and `docs/KNOWN_LIMITATIONS.md` were aligned with this.
* **Finite-value checks.**  `code/verify_frozen_metrics.py` now checks inputs,
  model outputs and every derived metric for NaN/Inf and for shape before
  comparing with the published values; a non-finite value is named and the
  script exits non-zero without PASS.  The earlier comparison
  `abs(v - ref)/ref > tol` was False for `v = NaN`, so a corrupted input could
  pass silently.  New `code/metric_checks.py` and
  `code/tests/test_metric_checks.py` (11 tests).
* No version number is pinned in the README.

## v1.0.3 — 2026-11-27

Documentation bookkeeping only; code, data and manifests are identical in
content to v1.0.1.  The README no longer pins a tag name in its "release
status" line (inside the v1.0.2 tree it still named v1.0.1) and the clone
command no longer uses `--branch`.  **Use this tag** when citing the code and
documentation; the data archives remain those of v1.0.0.

## v1.0.2 — 2026-11-27

Correction of one sentence in this file.  v1.0.1 said
`docs/FILE_MANIFEST_SHA256.txt` covered "1313 tracked files" while the manifest
at that tag lists 1314 — the count was taken before the changelog itself was
added.  The tag was not moved; this one carries the corrected wording.  Code
and data identical to v1.0.1.

## v1.0.1 — 2026-11-27

Docs, code and verification only. **No archived data or model file changed**, and
no value reported in the paper changed.

### Device metrics
* New `code/device_metrics.py`: canonical Jsc / Voc / FF / PCE extraction —
  first **downward** zero crossing, linear root, explicit NaN rules.  It is
  bit-identical (≤ 1e-12) to the archived `v2lib.device_metrics` behind
  Figure 4e and Table S8, checked on 15,307 test curves and 90 forward curves.
* `docs/REPRODUCE.md` now attributes |ΔVoc| = 0.022439 V and
  |ΔFF| = 0.015533 (= 1.5533 pp) to `Figure4e_per_sample.csv`, the table
  behind Figure 4e and Table S8.  v1.0.0 listed 0.030 V and 0.0141 from
  `forward_metrics_summary.csv`, which rounds Voc to 0.01 V before differencing.
* FF (dimensionless) and PCE (already percentage points) are now distinguished
  explicitly, so FF is multiplied by 100 exactly once.
* `SUPERSEDED.md` beside `forward_metrics_summary.csv`; the file itself is kept
  unchanged for provenance.

### Voc extraction
* `00_extract_frozen_predictions.device_observables()` had two defects: it took
  the first sign change of either direction, and it called `np.interp` with a
  decreasing argument array.  It now delegates to `device_metrics`.
* Impact measured, not assumed: on all 15,307 test curves the first sign change
  is downward, so only the interpolation acted.  `voc` moves by ≤ 0.01 V, `ff`
  by ≤ 0.008, `pce` by 3.6e-15 (FF cancels Voc), everything else is identical,
  and the Figure 2b representative samples are unchanged.
* The frozen `_frozen_preds.npz` is **not** overwritten; the corrected output
  was written to a separate directory and compared item by item.
* `code/tests/test_device_metrics.py`: 11 boundary tests, including the known
  `J = [1, -1]` over `V = [1.26, 1.27]` → 1.265 V case.

### Repository hygiene
* `.gitignore` no longer excludes every `results/` directory — only the
  regenerated output directory at the repository root.  The 39 archived
  experiment result tables that Tables S10–S13 are built from are now tracked.
* `.gitattributes` pins `eol=lf` for text and marks binaries, so a fresh clone
  is byte-identical to the manifest on any platform.
* Checksums split into `docs/FILE_MANIFEST_SHA256.txt` (every tracked file,
  hashed from `git archive`) and `docs/ASSET_MANIFEST_SHA256.txt` (13 archives).
* `code/verify_manifest.py` verifies a clone and downloaded archives and
  reports ok / eol / failed / missing separately.

### Verification entry points
* `quickstart_inference.py` is now an explicit 200-curve **smoke test** with
  assertions on shape, finiteness, MSE, predictive scale and nine correlations
  against `data/examples/expected_smoke_results.json`, with tolerances justified
  by measured batch-size and version stability.
* New `code/verify_frozen_metrics.py`: full 15,307-curve check of the published
  reconstruction MSE, per-parameter r, 95 % coverage and mean Spearman.
* `code/comsol_validation/_tools/`: vendored `v2lib.py` and `infer_frozen.py`,
  which the Figure 4 script imports but which were missing from v1.0.0.

### Documentation
* README: three explicit tiers — runs as-is / needs path configuration /
  historical only — a complete asset table (including `hc_revision_v2`) and the
  two kinds of gap kept separate: "complete inputs, commercial software
  required" versus "source material genuinely missing".
* `docs/KNOWN_LIMITATIONS.md`, `docs/FIGURE_SOURCE_MAP.md` and
  `docs/DATA_DICTIONARY.md` updated to match.

### Not changed
* The 13 release archives are the v1.0.0 files, byte for byte; their checksums
  are unchanged and v1.0.1 adds no new archive.
* No licence chosen, no DOI registered.

## v1.0.0 — 2026-11-26

First public release: frozen VAE-v6 model, both scalers, the recorded
train/validation/test partition, the COMSOL model and drivers, all analysis and
figure code, and 13 data/model archives.
