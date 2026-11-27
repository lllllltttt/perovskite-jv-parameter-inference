# Known limitations

## Scope of the compute environment

* **COMSOL Multiphysics 6.3 + LiveLink for MATLAB** is required to regenerate any
  J–V curve, the 45-case back-substitution, and the mesh-independence study.  No
  commercial software or licence is distributed.  Everything else in this release
  runs in Python.
* Inference, all model metrics, all calibration and all collision statistics were
  produced on CPU.  No GPU is required to reproduce them.

## Model and normalisation

* The **main model's** parameter and current scalers were fitted on **all 102,046**
  retained curves before partitioning, exactly as the manuscript states.  The
  primary evaluation is therefore not a fully isolated holdout.  The
  training-only-scaling control is Table S15–S17; the leakage-free benchmark is
  Table S13.  Do not compare absolute skill across those rows.
* `best.weights.h5` is the training checkpoint saved by `ModelCheckpoint`.  It is
  shipped for completeness but is **not** the artifact used for evaluation.  The
  evaluated model is `encoder.h5` + `decoder.h5` + `param_head.h5`.
* The predictive scale follows σ = clip(softplus(raw) + 0.01, 0.01, 1.0).  An older
  script (`code/pipeline/VAE_v6_eval.py`) and `code/pipeline/uncertain_predict.py`
  use the earlier `exp(0.5·raw)` convention and hard-coded σ values.  Current
  results use `VAE_v6_eval_fixed.py`; the older files are kept for provenance.

## Training records

* The frozen main run trained for 688 epochs with early stopping.  Batch order and
  initial weights of that historical run were not recorded; only the final weights
  survive.  Retraining therefore does not reproduce the reported numbers
  bit-for-bit; loading the frozen weights does, and this release supports that.
* The H/L/T preprocessing-scope control used one seed (20260823) with identical
  seeds in L and T.  The paper explicitly does not treat their differences as an
  isolated causal estimate of the scaler effect.

## Data

* The retained CSV stores parameters rounded to three significant digits; the
  200,000-row LHS design file stores full precision.  Joining on `Sample_ID`
  recovers the unrounded values.
* `Sample_ID` is a 1-based row number of the LHS design, **not** a physical device
  identifier.
* The independent cohort (`JV_database_...-3.csv`, 153,067 curves) has its own
  `Sample_ID` numbering (1 … 300,000).  It is not interchangeable with the main
  dataset's numbering.
* Per-sample tables index the **zero-based test position** 0 … 15306, not
  `Sample_ID`.  Mapping between them goes through
  `data/splits/split_indices_seed42.npz`.
* Both sampling designs are archived: the 200,000-row table (in
  `dataset_main_102046.tar.gz`, columns `tau_interface_*`) and the 300,000-row
  table (`design_independent_300000.tar.gz`, columns `tau_ETL`/`tau_HTL`).  The
  column names differ between the two files for the same quantities.  The
  retained curves match their design tables to three significant digits; see
  `docs/SOURCE_VERIFICATION.md`.
* The server-side `Sample_*.mat` output of the two campaigns is not archived.
  The derived CSV tables, the 45 forward-validation curves and the mesh-study
  outputs are.

## Analysis conventions that changed during the project

* The nearest-neighbour pair rule was corrected from `i < NN(i)` (7,666 pairs) to
  the deduplicated undirected rule (11,245 pairs).  Current results use the
  corrected version; the earlier table is archived under
  `analysis/collision_analysis_superseded/`.
* `docs/` in the corrected collision package (`code/collision_revision_v2/report/`)
  states that the parameter scaler was "fit on the training split only".  That
  sentence is wrong: the saved scaler's `data_min_`/`data_max_` equal a fit over all
  102,046 rows (verified, see `docs/REPRODUCE.md` §1).  The manuscript and
  `docs/DATA_DICTIONARY.md` state the correct scope.

## Figures

* Figures were assembled as matplotlib panels, composed manually in PowerPoint, and
  exported to SVG for the Word document.  The panel scripts and the composition
  decks are released; the *layout* (panel placement, tick fonts) is the deck's, not
  the script's.
* Figure 1 is a schematic.  It is not to scale and does not draw the 0.01 nm
  interface slabs at physical thickness.

## Release mechanics

* **Paths.** Only a defined subset runs without editing (README, "Which scripts
  run as-is"): the smoke test, the full-metric verifier, the manifest verifier,
  `device_metrics.py`, the tests, and four pipeline entry points
  (`00_extract_frozen_predictions`, `VAE_v6_eval_fixed`,
  `forward_validation_unbiased`, `decoder_comsol_audit`).  Those resolve every
  path through `code/paths.py` (`JV_DATA_ROOT`, `JV_MODEL_ROOT`,
  `JV_RESULTS_ROOT`).
  The bulk of the archived scripts under `code/analysis/`, `code/experiments/`,
  `code/collision_revision_v2/` and `code/figures/build/` are shipped **as they
  were run**, with the original `E:/project/work1` or `/home/student2/...`
  constants at the top of the file; their outputs are shipped alongside them.
  They were deliberately not rewritten in the v1.0.x releases — changing them
  would alter
  the code that produced published figures without re-running those figures.
  `code/pipeline/pre-process.py` and `VAE-v6.py` also need `CSV_PATH` /
  `OUTPUT_DIR` editing.  Do not describe the repository as "all paths
  configurable"; it is not.
* **Device metrics.** Use `code/device_metrics.py` (interpolated downward
  crossing).  `analysis/forward_validation_unbiased/forward_metrics_summary.csv`
  contains a rounded-Voc device block that is superseded (see the
  `SUPERSEDED.md` beside it and `docs/REPRODUCE.md` §3).
* No open-source licence has been chosen.  See `LICENSE_STATUS.md`.
* No DOI exists.  The identifiers are the repository URL with its release tag
  for the code and documentation, and `v1.0.0` for the data archives.
* Asset archives were compressed with `gzip -3`; unpack before use.
