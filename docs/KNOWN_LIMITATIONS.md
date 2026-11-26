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
  use the superseded `exp(0.5·raw)` convention and hard-coded σ values.  They are
  kept as provenance and **must not** be used to recompute any reported σ.

## Training records

* The frozen main run trained for 688 epochs with early stopping.  Batch order and
  initial weights of that historical run were not recorded; only the final weights
  survive.  The reported numbers therefore cannot be regenerated bit-for-bit by
  retraining — only by loading the frozen weights, which this release supports.
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

## Analysis conventions that changed during the project

* The nearest-neighbour pair rule was corrected from `i < NN(i)` (7,666 pairs) to
  the deduplicated undirected rule (11,245 pairs).  The corrected version is what
  the paper uses.  The old table is kept under
  `analysis/collision_analysis_superseded/` and must not be cited.
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

* **Paths.** The five entry points that produce the released results —
  `code/quickstart_inference.py`, `code/pipeline/00_extract_frozen_predictions.py`,
  `code/pipeline/VAE_v6_eval_fixed.py`, `code/pipeline/forward_validation_unbiased.py`
  and `code/pipeline/decoder_comsol_audit.py` — resolve every path through
  `code/paths.py` (`JV_DATA_ROOT`, `JV_MODEL_ROOT`, `JV_RESULTS_ROOT`) and contain no
  absolute path.  The remaining archived analysis scripts
  (`collision_analysis.py`, `noise_robustness.py`,
  `forward_validation_postprocess.py`, …) are shipped **as they were run**, with the
  original `E:/project/work1` constants at the top of the file; they are preserved
  as records of the analysis, and their outputs are shipped alongside them.  To
  re-run one, edit the three or four path constants at its top.
* No open-source licence has been chosen.  See `LICENSE_STATUS.md`.
* No DOI exists.  The GitHub URL and tag `v1.0.0` are the identifiers.
* Asset archives were compressed with `gzip -3`; unpack before use.
