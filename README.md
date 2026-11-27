# perovskite-jv-parameter-inference

Data, code and frozen models for the manuscript

> **Parameter Recoverability and Predictive Uncertainty from Single J–V Curves
> in Perovskite Solar Cells**

This repository releases the frozen model, the analysis code and the source data
behind the reported numbers, together with the material needed to audit them.
It corresponds to `Manuscript_20261126_final` and its Supplementary Information
`Supplementary_Information_20261126_final`.

The paper studies a variational autoencoder (VAE-v6) that maps a single simulated
J–V curve (131 voltage points, 0–1.3 V) to nine drift–diffusion parameters plus a
per-parameter predictive scale, using 102,046 COMSOL curves retained from a
200,000-curve Latin hypercube campaign.

**Release status.** Code and documentation: the latest tag (see
[Releases](https://github.com/lllllltttt/perovskite-jv-parameter-inference/releases)).
The large data and model archives are unchanged since `v1.0.0` and are
downloaded from that release — same files, same checksums. No later tag adds a
new archive.

---

## What is in this repository

```
code/
  quickstart_inference.py      smoke test on a fixed 200-curve subset (~30 s)
  verify_frozen_metrics.py     full 15,307-curve check of the published metrics
  verify_manifest.py           checksum verification for a clone and the assets
  device_metrics.py            canonical Jsc/Voc/FF/PCE extraction
  paths.py                     path resolution (JV_DATA_ROOT / JV_MODEL_ROOT)
  tests/                       boundary tests for device_metrics.py
  pipeline/                    preprocessing, model definition, training, evaluation
  analysis/                    per-analysis scripts and their result tables
  experiments/                 reviewer experiments, ratio-range comparison,
                               preprocessing-scope control, interval baseline
  collision_revision_v2/       corrected nearest-neighbour analysis (11,245 pairs)
  figures/                     figure-generating scripts + per-panel source tables
  comsol/                      COMSOL model and MATLAB batch drivers
  comsol_validation/           mesh / inversion studies (Tables S18a-b)
data/
  splits/split_indices_seed42.npz   recorded train/val/test partition + Sample_ID map
  examples/test_subset_200.npz      200-curve smoke-test subset
  examples/expected_smoke_results.json   expected values for the smoke test
  tables/                          small result tables that back the SI
models/
  vae-v6/{encoder,decoder,param_head}.h5   frozen weights used for every reported result
  vae-v6/best.weights.h5                   training checkpoint (not used for evaluation)
  param_scaler.pkl, J_scaler.pkl           fitted on all 102,046 retained curves
docs/
  DATA_DICTIONARY.md        every array, column order, unit, shape and scaler scope
  REPRODUCE.md              what was verified, how, and what was not
  FIGURE_SOURCE_MAP.md      paper figure → source data → script → output
  KNOWN_LIMITATIONS.md      COMSOL/archived-material requirements, path tiers
  FILE_MANIFEST_SHA256.txt  checksums of every tracked file
  ASSET_MANIFEST_SHA256.txt checksums of the release archives
requirements.txt, env/environment.yml
```

---

## Quick start (CPU only, ~30 s)

```bash
git clone https://github.com/lllllltttt/perovskite-jv-parameter-inference.git
cd perovskite-jv-parameter-inference
pip install -r requirements.txt

python code/quickstart_inference.py        # smoke test, exits 0 on PASS
python -m unittest discover -s code/tests  # device-metric boundary tests
```

`quickstart_inference.py` is a **smoke test on a fixed 200-curve subset**, not a
reproduction of the paper: it asserts the array shapes, finiteness, the mean
reconstruction MSE, the mean predictive scale and the nine per-parameter
correlations against `data/examples/expected_smoke_results.json`, within
tolerances documented in the script (10 % on the MSE, 0.01 on the scale, 0.02 on
each r — more than 1,000× the measured numerical drift).

For the **published** metrics run

```bash
tar -xzf dataset_main_102046.tar.gz -C data/_assets     # see downloads below
JV_DATA_ROOT="$PWD/data/_assets" python code/verify_frozen_metrics.py
```

which checks the 15,307-curve reconstruction MSE, the nine Pearson r, the nine
95 % coverages and the mean Spearman correlation against the values printed in
the paper and its SI.

---

## Large downloads

Thirteen archives come from the **`v1.0.0` release** and are unchanged; one
(`design_independent_300000.tar.gz`) is attached to **v1.0.5**.
Download links, sizes and contents:

| Asset | Size | Contents |
|---|---|---|
| [`dataset_main_102046.tar.gz`](https://github.com/lllllltttt/perovskite-jv-parameter-inference/releases/download/v1.0.0/dataset_main_102046.tar.gz) | 262 MB | 102,046-curve retained dataset, 200,000-row LHS design, preprocessed arrays, both scalers, recorded split indices |
| [`dataset_independent_153067.tar.gz`](https://github.com/lllllltttt/perovskite-jv-parameter-inference/releases/download/v1.0.0/dataset_independent_153067.tar.gz) | 185 MB | 153,067-curve same-domain cohort (Table S14) |
| [`exp1_benchmark.tar.gz`](https://github.com/lllllltttt/perovskite-jv-parameter-inference/releases/download/v1.0.0/exp1_benchmark.tar.gz) | 462 MB | Leakage-free multi-seed benchmark, 15 trained models (Table S13) |
| [`exp2_latent.tar.gz`](https://github.com/lllllltttt/perovskite-jv-parameter-inference/releases/download/v1.0.0/exp2_latent.tar.gz) | 136 MB | Latent-uncertainty decomposition, 500 draws (Table S12) |
| [`expanded_ratio.tar.gz`](https://github.com/lllllltttt/perovskite-jv-parameter-inference/releases/download/v1.0.0/expanded_ratio.tar.gz) | 175 MB | Two-arm ratio-range comparison, both arms and ten models (Tables S19–S25) |
| [`preprocessing_control.tar.gz`](https://github.com/lllllltttt/perovskite-jv-parameter-inference/releases/download/v1.0.0/preprocessing_control.tar.gz) | 118 MB | H/L/T preprocessing-scope control (Tables S15–S17) |
| [`interval_repair_A1.tar.gz`](https://github.com/lllllltttt/perovskite-jv-parameter-inference/releases/download/v1.0.0/interval_repair_A1.tar.gz) | 12 MB | Empirical-quantile interval baseline (Table S17b) |
| [`independent_validation.tar.gz`](https://github.com/lllllltttt/perovskite-jv-parameter-inference/releases/download/v1.0.0/independent_validation.tar.gz) | 272 MB | Preprocessed independent cohort and its evaluation |
| [`comsol_config.tar.gz`](https://github.com/lllllltttt/perovskite-jv-parameter-inference/releases/download/v1.0.0/comsol_config.tar.gz) | 11 MB | `dmodel.xml` from the `.mph`, Table S9 configuration extract and QC, database closure audit |
| [`figure_source.tar.gz`](https://github.com/lllllltttt/perovskite-jv-parameter-inference/releases/download/v1.0.0/figure_source.tar.gz) | 133 MB | `_frozen_preds.npz`, per-panel value tables, composed SVG artwork, PowerPoint decks |
| [`pipeline_scripts.tar.gz`](https://github.com/lllllltttt/perovskite-jv-parameter-inference/releases/download/v1.0.0/pipeline_scripts.tar.gz) | 18 MB | Complete original `script/` folder (LHS sampler, CSV builder, training) |
| [`submission_v8_tables.tar.gz`](https://github.com/lllllltttt/perovskite-jv-parameter-inference/releases/download/v1.0.0/submission_v8_tables.tar.gz) | 9 MB | SI source tables incl. `T8.2_per_sample_full_precision.csv` |
| [`hc_revision_v2.tar.gz`](https://github.com/lllllltttt/perovskite-jv-parameter-inference/releases/download/v1.0.0/hc_revision_v2.tar.gz) | 44 KB | v2 tables behind Tables S18c–S18e |
| [`design_independent_300000.tar.gz`](https://github.com/lllllltttt/perovskite-jv-parameter-inference/releases/download/v1.0.5/design_independent_300000.tar.gz) | 16 MB | 300,000-row sampling design of the independent cohort (v1.0.5) |

Verify what you downloaded:

```bash
python code/verify_manifest.py --assets <download-dir>   # assets + repository files
```

`docs/ASSET_MANIFEST_SHA256.txt` lists the archive checksums;
`docs/FILE_MANIFEST_SHA256.txt` lists every tracked file, computed from the
committed blobs (`.gitattributes` pins `eol=lf`), so a fresh clone matches byte
for byte.

Unpack and point the code at the result:

```bash
mkdir -p data/_assets && tar -xzf dataset_main_102046.tar.gz -C data/_assets
export JV_DATA_ROOT="$PWD/data/_assets"     # Windows: set JV_DATA_ROOT=...
```

---

## Which scripts run as-is

Not every archived script is ready to run; the three tiers are:

**Tier A — run directly, no editing.** `code/quickstart_inference.py`,
`code/verify_frozen_metrics.py`, `code/verify_manifest.py`,
`code/device_metrics.py`, `code/tests/`, and four inference/evaluation entry
points: `code/pipeline/00_extract_frozen_predictions.py`,
`VAE_v6_eval_fixed.py`, `forward_validation_unbiased.py` and
`decoder_comsol_audit.py`.  These resolve paths through `code/paths.py`
(`JV_DATA_ROOT`, `JV_MODEL_ROOT`, `JV_RESULTS_ROOT`) and contain no absolute
path.  `code/pipeline/pre-process.py` and `VAE-v6.py` are the data- and
model-generation steps; they still carry the original `/home/student2/...`
constants at the top and need `CSV_PATH` / `OUTPUT_DIR` set before use.

**Tier B — archived analysis scripts, need path configuration.** Everything under
`code/analysis/`, `code/experiments/`, `code/collision_revision_v2/` and most of
`code/figures/build/`.  They are shipped exactly as they were run, with the
original `E:/project/work1` or `/home/student2/...` constants at the top of each
file, and they were **not** rewritten in the v1.0.x releases (rewriting them would change
the code that produced published figures without re-running those figures).
To use one, edit the three or four path constants at its head.  Their outputs
are shipped alongside them.

**Tier C — archived versions, kept for provenance.**  `analysis/collision_analysis_superseded/`
holds the earlier 7,666-pair collision rule; current results use
`collision_revision_v2/` (11,245 pairs).  `analysis/forward_validation_unbiased/forward_metrics_summary.csv`
holds rounded-Voc device metrics; current results use `code/device_metrics.py`
(see the `SUPERSEDED.md` beside it).  `pipeline/VAE_v6_eval.py` and
`pipeline/uncertain_predict.py` use the earlier σ convention `exp(0.5·raw)`;
current results use `VAE_v6_eval_fixed.py`.

---

## Reproducing specific results

`docs/REPRODUCE.md` has the details.  Summary:

| Step | Needs COMSOL? | Status in this release |
|---|---|---|
| Frozen-model inference, all model metrics (Tables 2, S2–S7, S11–S12, S14) | no | **re-run from the released dataset and model — passes** |
| Device metrics, coverage, interval scores, Fig. 4e | no | **recomputed from archived curves — passes** |
| Collision analysis, Fig. S8 (Tables S6, S10) | no | recomputed from the archived pair tables |
| Ratio-range comparison (Tables S19–S25) | no | models, both arms' data and all per-run predictions archived; **not re-run** |
| Leakage-free benchmark (Table S13) | no | 15 trained models and their eval bundles archived; **not re-trained** |
| Preprocessing-scope control (Tables S15–S17) | no | archived runs and per-sample output; **not re-run** |
| COMSOL back-substitution, cycle gap, mesh study (Tables S18a–e, Figs. S3–S4) | **yes** | models, drivers and archived outputs included; rerun needs COMSOL 6.3 |
| Data generation from scratch | **yes** | 200,000-row design and drivers included; the main-database batch driver is not available |

The archived models, inputs and drivers support rerunning the 45-case
back-substitution, the mesh studies and both simulation campaigns with COMSOL
Multiphysics 6.3, the Semiconductor Module and LiveLink for MATLAB.  The
200,000-row design of the main campaign and the 300,000-row design of the
independent cohort are archived alongside the retained curves, and the four
MATLAB segments of each campaign are in `code/comsol/`.

---

## COMSOL inputs

`code/comsol/` contains the shared model and the drivers of both simulation
campaigns (details in `code/comsol/README.md`):

* `1D_PSC_wen.mph` — COMSOL 6.3.0.290, base COMSOL plus the Semiconductor
  Module; FTO / HTL / perovskite / C₆₀ / SnO₂ / Ag, 131-point sweep.
* `main_200k/run_PSC_9D_5..8.m` — the four segments of the 200,000-row campaign
  that produced the main database (rows 1–50,000 / 50,001–100,000 /
  100,001–150,000 / 150,001–200,000; ports 2036–2039).
* `independent_300k/run_PSC_9D_5..8.m` — the four segments of the independent
  campaign (rows 1–75,000 … 225,001–300,000; ports 2036–2039), whose design
  table is the asset `design_independent_300000.tar.gz`.

`code/analysis/forward_validation_unbiased/run_forward_validation_unbiased.m` is
the 45-case back-substitution driver (COMSOL 6.3 + MATLAB R2024b + LiveLink 6.3),
and `code/comsol_validation/` holds the mesh and inversion studies behind
Tables S18a/b.

To use the drivers, install COMSOL 6.3 with the Semiconductor Module and
LiveLink for MATLAB, then edit `addpath`, `input_path`, `mph_path`, `result_dir`
and the row range at the top of each `.m` file.

---

## Licence and citation

No open-source licence has been chosen; see [`LICENSE_STATUS.md`](LICENSE_STATUS.md).
Public availability does **not** grant an open-source licence.  No DOI has been
registered — cite the repository with its released tag for the code and docs,
and `v1.0.0` for the data archives, not a DOI.

## Contact

Issues and questions: please open an issue in this repository.
