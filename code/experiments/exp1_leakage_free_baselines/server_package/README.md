# EXP1 — LEAKAGE-FREE MULTI-SEED MATCHED BASELINE BENCHMARK

Date: 2026-08-24 · Project: `E:\project\work1`
Frozen manuscript: `manuscript_stage1_submission_clean.md` (NOT modified — this experiment
writes only under `reviewer_experiments/exp1_leakage_free_baselines/`).
Frozen model/weights/results untouched: `data/vae-v6/`, `evaluation_fixed/`, `final_figures/`.

## Purpose
Three methodological reviewer questions:
1. Does fitting normalization scalers on the full retained dataset materially inflate
   reported performance (preprocessing leakage)?
2. Is the reported recoverability hierarchy stable across independent training seeds?
3. Does the VAE architecture add measurable value over matched deterministic alternatives
   (deterministic autoencoder, direct MLP)?

## The single controlled intervention
The frozen Stage-I study scaled parameters and J-V on the FULL retained dataset
(`script/pre-process.py` fits `MinMaxScaler` on all N rows, lines 118–122, *then* splits).
EXP1 re-fits every scaler on TRAINING samples only and transforms val/test with those
constants. All three benchmark models are trained on the resulting leakage-free data under
exactly the frozen training conventions (see `LOSS_REDUCTION_VERIFICATION.md`).

## Split membership — record of a discrepancy
`script/pre-process.py` documents a two-step sklearn split of the retained set
(`train_test_split(arange(N), test_size=0.30, random_state=42)`, then
`train_test_split(temp, test_size=0.50, random_state=42)`).

**Independent reproduction does NOT reproduce the archived npz block membership.**
- The archived blocks are `dataset_normalized.npz` (J_train/val/test, params_train/val/test).
- A seed-42 two-step re-derivation over arange(102046) yields a crosstab against the archived
  blocks that is essentially uniform (≈54,972/102,046 diagonal overlap, i.e. chance level).
- Scanning `random_state = 0..400` finds no state that reproduces it (best 54,972 ≈ chance).
- The observed block counts (71,432 / 15,307 / 15,307 = 70/15/15% of 102,046) are exactly
  what a uniform ~49% invalid-sample drop across three splits of a 200,000-sample pre-filter
  set would produce ⇒ the archived split was evidently applied before/independently of the
  retained-set order (filter-after-split hypothesis). The independent indices are therefore
  not recoverable from code + seed 42 alone.

**Resolution:** the archived npz blocks ARE the exact Stage-I membership (the ground truth of
what the study used). EXP1 uses them verbatim: `split_indices_original_reproduced.npz`
indexes the concatenated archive (train = positions 0..71431, val = 71432..86738,
test = 86739..102045). Train-only scalers are fit on the exact archived train rows. This
satisfies the spec requirement "Use EXACTLY the same train / validation / test sample
membership". Raw physical values are recovered from the archived scaled arrays by inverting
the frozen full-data scalers (float64-exact; verified to 4.7e-15 relative error against the
stored raw test rows in `preprocessing_statistics.md`).

## Preprocessing statistics (summary)
- Parameter (log10) extrapolation outside [0,1] on val/test: ≤ 0.0001 fraction per parameter;
  max extrapolation val 0.0064, test 0.0279. ⇒ Parameter leakage is negligible (the 70% train
  subset of an LHS domain covers it almost completely).
- J-V extrapolation is the real effect: val fraction <0 = 0.00002, >1 = 0.00000 (min −0.092);
  test fraction <0 = 0.00003, >1 = 0.00002 (min −0.249, max 1.0001), concentrated at the
  lowest-voltage columns (0–0.18 V) and the highest-voltage columns (1.24–1.30 V).
- Full detail: `preprocessing_statistics.md`. Scaler objects: `train_only_scalers.pkl`.

## Framework decision
The environment's TensorFlow 2.20.0 is the CPU-only Windows wheel (`is_cuda_build=False`);
the NVIDIA RTX 4060 Ti is visible only to PyTorch. Training in TF-CPU was chosen deliberately:
**all benchmark models run in the exact frozen framework and code conventions** (Keras 3
subclass model, same loss reductions, same sigma transform, same callbacks), so the leakage-free
VAE differs from the frozen VAE-v6 in exactly the one controlled way (train-only scaling), with
no framework confound. ~4 s/epoch measured; each run self-terminates via early stopping
(val_param_loss, patience 50). Reproducibility: `random`/`numpy`/`tf` seeds set per run and the
data-shuffle buffer seeded per run (a deliberate improvement over the frozen code, which did not
seed its shuffle); bitwise determinism is NOT claimed (oneDNN/CPU threading).

## Environment
- Python 3.12.9 (conda env `pytorch-2.60-gpu`)
- TensorFlow 2.20.0 (CPU), Keras 3.13.2, sklearn 1.7.0rc1, numpy 2.0.1, scipy 1.16.0
- CUDA: none for TF; torch 2.6.0+cu126 sees NVIDIA GeForce RTX 4060 Ti (not used for TF)
- 16 logical CPUs

## File map
```
reviewer_experiments/exp1_leakage_free_baselines/
├── README.md
├── split_indices_original_reproduced.npz      archived-membership indices (+record)
├── train_only_scalers.pkl                     leakage-free scalers
├── leakage_free_dataset.npz                   train-only scaled splits (float32)
├── preprocessing_statistics.md                extrapolation / min-max tables
├── LOSS_REDUCTION_VERIFICATION.md             reduction conventions (spec §H)
├── phase0_frozen_eval_repro.txt               frozen VAE-v6 anchor (reproduces manuscript)
├── verify_frozen_eval.py / prep_leakage_free.py / exp1_lib.py / train_one.py /
│   evaluate_one.py / pilot_gate.py / run_benchmark.py / summarize_results.py / make_figures.py
├── pilot/pilot_vAE_seed20260824/              pilot (VAE, seed 20260824) + gate result
├── models/{vae,det_ae,mlp}/seed<seed>/        benchmark checkpoints + eval bundles
├── results/per_seed_metrics.csv               per model×seed×parameter metrics
├── results/multiseed_summary.csv              mean/SD/median across the 5 seeds
├── results/model_level_summary.csv            architecture-level summary
├── figures/EXP1_Fig{A..F}.*                   reviewer-analysis figures
├── EXP1_MANUSCRIPT_IMPACT.md
└── EXP1_FINAL_REPORT.md
```
