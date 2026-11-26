# perovskite-jv-parameter-inference

Data, code and frozen models for the manuscript

> **Parameter Recoverability and Predictive Uncertainty from Single J–V Curves
> in Perovskite Solar Cells**

This repository releases everything needed to (i) reproduce the inference-side
numbers of the paper from the frozen model, and (ii) regenerate every analysis and
figure from the archived source data.  It corresponds to the final manuscript
`Manuscript_20261126_final.docx` and its Supplementary Information
`Supplementary_Information_20261126_final.docx`.

The paper studies a variational autoencoder (VAE-v6) that maps a single simulated
J–V curve (131 voltage points, 0–1.3 V) to nine drift–diffusion parameters plus a
per-parameter predictive scale, using 102,046 COMSOL curves retained from a
200,000-curve Latin hypercube campaign.

---

## What is in this repository

```
code/
  quickstart_inference.py      minimal end-to-end check (no COMSOL, no training)
  paths.py                     path resolution (JV_DATA_ROOT / JV_MODEL_ROOT)
  pipeline/                    preprocessing, model definition, training, evaluation
  analysis/                    per-analysis scripts and their result tables
  experiments/                 reviewer experiments, ratio-range comparison,
                               preprocessing-scope control, interval baseline
  collision_revision_v2/       corrected nearest-neighbour analysis (11,245 pairs)
  figures/                     figure-generating scripts
  comsol/                      COMSOL model and MATLAB batch drivers
data/
  splits/split_indices_seed42.npz   recorded train/val/test partition + Sample_ID map
  examples/test_subset_200.npz      200-curve smoke-test subset
  tables/                          small result tables that back the SI
models/
  vae-v6/{encoder,decoder,param_head}.h5   frozen weights used for every reported result
  vae-v6/best.weights.h5                   training checkpoint (not used for evaluation)
  param_scaler.pkl, J_scaler.pkl           fitted on all 102,046 retained curves
docs/
  DATA_DICTIONARY.md    every array, column order, unit, shape and scaler scope
  REPRODUCE.md          what was verified here and how
  FIGURE_SOURCE_MAP.md  paper figure → source data → script → output
  KNOWN_LIMITATIONS.md   what is not reproducible and why
  FILE_MANIFEST_SHA256.txt
requirements.txt, env/environment.yml
```

The large data files and model bundles are **release assets**, not tracked files.
Download links are in [Large downloads](#large-downloads).

---

## Quick start (CPU only, ~30 s)

```bash
git clone https://github.com/lllllltttt/perovskite-jv-parameter-inference.git
cd perovskite-jv-parameter-inference
pip install -r requirements.txt

python code/quickstart_inference.py
```

Expected output (exact numbers depend on the TensorFlow build):

```
reconstruction MSE  mean=8.478683e-06  median=2.659554e-06
predictive scale    mean=0.1332  (normalized units)
per-parameter Pearson r ... bulk parameters 0.880-0.931
PASS
```

The script evaluates a fixed 200-curve subset of the held-out test set that ships
with the repository.  On the **full** 15,307-curve test set the frozen model gives
mean / median reconstruction MSE of **1.211e-5 / 2.969e-6** and per-parameter
Pearson r of 0.878–0.919 for the six bulk parameters; `docs/REPRODUCE.md` records
that check.

---

## Large downloads

All files are attached to the release
[`v1.0.0`](https://github.com/lllllltttt/perovskite-jv-parameter-inference/releases/tag/v1.0.0).
SHA-256 values for every asset are in `docs/FILE_MANIFEST_SHA256.txt`.

| Asset | Size | Contents |
|---|---|---|
| [`dataset_main_102046.tar.gz`](https://github.com/lllllltttt/perovskite-jv-parameter-inference/releases/download/v1.0.0/dataset_main_102046.tar.gz) | 262 MB | The 102,046-curve retained dataset, the 200,000-row LHS design, preprocessed arrays, both scalers and the recorded split indices |
| [`dataset_independent_153067.tar.gz`](https://github.com/lllllltttt/perovskite-jv-parameter-inference/releases/download/v1.0.0/dataset_independent_153067.tar.gz) | 185 MB | The separately generated 153,067-curve same-domain cohort (Table S14) |
| [`exp1_benchmark.tar.gz`](https://github.com/lllllltttt/perovskite-jv-parameter-inference/releases/download/v1.0.0/exp1_benchmark.tar.gz) | 462 MB | Leakage-free multi-seed benchmark, incl. 15 trained models (Table S13) |
| [`exp2_latent.tar.gz`](https://github.com/lllllltttt/perovskite-jv-parameter-inference/releases/download/v1.0.0/exp2_latent.tar.gz) | 136 MB | Latent-uncertainty decomposition, 500 draws (Table S12) |
| [`expanded_ratio.tar.gz`](https://github.com/lllllltttt/perovskite-jv-parameter-inference/releases/download/v1.0.0/expanded_ratio.tar.gz) | 175 MB | Two-arm ratio-range comparison, both arms' data and ten models (Tables S19–S25, Figs. S9–S11) |
| [`preprocessing_control.tar.gz`](https://github.com/lllllltttt/perovskite-jv-parameter-inference/releases/download/v1.0.0/preprocessing_control.tar.gz) | 118 MB | H/L/T preprocessing-scope control runs (Tables S15–S17) |
| [`interval_repair_A1.tar.gz`](https://github.com/lllllltttt/perovskite-jv-parameter-inference/releases/download/v1.0.0/interval_repair_A1.tar.gz) | 12 MB | Empirical-quantile interval baseline (Table S17b) |
| [`independent_validation.tar.gz`](https://github.com/lllllltttt/perovskite-jv-parameter-inference/releases/download/v1.0.0/independent_validation.tar.gz) | 272 MB | Preprocessed independent cohort and its evaluation |
| [`comsol_config.tar.gz`](https://github.com/lllllltttt/perovskite-jv-parameter-inference/releases/download/v1.0.0/comsol_config.tar.gz) | 11 MB | `dmodel.xml` extracted from the `.mph`, device-configuration extract and QC, 200k-database closure audit |
| [`figure_source.tar.gz`](https://github.com/lllllltttt/perovskite-jv-parameter-inference/releases/download/v1.0.0/figure_source.tar.gz) | 133 MB | `_frozen_preds.npz`, per-panel value tables, composed SVG artwork and the PowerPoint decks |
| [`pipeline_scripts.tar.gz`](https://github.com/lllllltttt/perovskite-jv-parameter-inference/releases/download/v1.0.0/pipeline_scripts.tar.gz) | 18 MB | The complete original `script/` folder, including the LHS sampler and the CSV builder |
| [`submission_v8_tables.tar.gz`](https://github.com/lllllltttt/perovskite-jv-parameter-inference/releases/download/v1.0.0/submission_v8_tables.tar.gz) | 9 MB | Source tables cited by the SI, incl. `T8.2_per_sample_full_precision.csv` |

Unpack them next to the repository and point the code at the result:

```bash
mkdir -p data/_assets && tar -xzf dataset_main_102046.tar.gz -C data/_assets
export JV_DATA_ROOT="$PWD/data/_assets"     # Windows: set JV_DATA_ROOT=...
```

`code/paths.py` resolves every input through `JV_DATA_ROOT` (default `./data`) and
`JV_MODEL_ROOT` (default `./models`), so no absolute path from the authoring
machine is required.

---

## Reproducing specific results

See `docs/REPRODUCE.md` for the exact commands and the verification status of each
step.  In short:

| Step | COMSOL needed? | Status |
|---|---|---|
| Frozen-model inference and all model metrics (Tables 2, S2–S7, S11–S12, S14) | no | **verified in this release** |
| Collision analysis and Figs. S8 (Tables S6, S10) | no | verified from archived pair tables |
| Ratio-range comparison (Tables S19–S25) | no | archived models + data; re-evaluation not re-run |
| Leakage-free benchmark (Table S13) | no | archived models + data; 15 trainings not re-run |
| Preprocessing-scope control (Tables S15–S17) | no | archived runs |
| Device metrics, coverage, interval scores | no | verified |
| COMSOL back-substitution and cycle gap (Table S18c–e, Figs. S3–S4) | **yes** | archived outputs; generation needs COMSOL |
| Data generation from scratch | **yes** | needs COMSOL 6.3 + MATLAB; scripts provided |

The 45-case forward validation, the mesh-independence study (Table S18a–b) and the
original 200,000-curve campaign all require a licensed COMSOL Multiphysics 6.3
installation driven through LiveLink for MATLAB.  **No commercial software or
licence file is distributed here.**  Everything else runs in Python.

---

## COMSOL inputs

`code/comsol/` contains:

* `1D_PSC_wen.mph` — the one-dimensional drift–diffusion model (FTO / HTL /
  perovskite / C₆₀ / SnO₂ / Ag, 131-point voltage sweep).  The file records
  `COMSOL 6.3.0.290 (win64)` and uses the base COMSOL plus the **Semiconductor
  Module**.
* `run_PSC_9D_5.m` … `run_PSC_9D_8.m` — the MATLAB LiveLink batch drivers that
  read a table of parameter sets, solve the model and write the J–V curve.
* `code/analysis/forward_validation_unbiased/run_forward_validation_unbiased.m` —
  the 45-case back-substitution driver (COMSOL 6.3 + MATLAB R2024b + LiveLink 6.3).

`code/comsol_validation/` holds the four mesh and inversion studies behind
Tables S18a/b (coarse chain, `m = 0.35/0.25`, fine mesh `m = 0.18/0.125`, and the
fixed-reference recomputation), with the raw 131-point curves and the tables built
from them.

To use the drivers, install COMSOL Multiphysics 6.3 with the Semiconductor Module
and LiveLink for MATLAB, adjust the `addpath` line and the file paths at the top of
the `.m` file, and run it from MATLAB.  The model file is provided so that the
geometry, mesh and solver settings can be inspected without rerunning the campaign.

**Known provenance gap.**  The four archived database drivers read
`PSC_LHS_9D_interface_lifetimes_300000_5.csv` and write the *independent* campaign.
The driver that generated the main 102,046-curve database, and the 300,000-row LHS
design behind the independent cohort, are **not** on disk and could not be
recovered.  The 200,000-row design used for the main dataset *is* included, and the
retained database was verified to close against it (102,046/102,046 rows).

---

## Licence and citation

No open-source licence has been chosen for this release yet; see
[`LICENSE_STATUS.md`](LICENSE_STATUS.md).  Public availability here does **not**
by itself grant an open-source licence.  A `CITATION.cff` and a DOI will be added
if the authors register an archival copy; until then please cite the GitHub
repository URL and the tag `v1.0.0`, not a DOI.

## Contact

Issues and questions: please open an issue in this repository.
