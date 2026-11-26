# EXP2 — LATENT-UNCERTAINTY DECOMPOSITION (FROZEN VAE-v6)

Date: 2026-08-25 · Project: `E:\project\work1`
Frozen manuscript `manuscript_stage1_submission_clean.md` and frozen Stage-I model
`data/vae-v6/` **untouched** (md5-verified in `EXP2_QC.md`; this experiment writes only
under `reviewer_experiments/exp2_latent_uncertainty_decomposition/`).

## Purpose
Quantify how much of the frozen VAE-v6's **model-implied predictive uncertainty** comes
from (i) the Gaussian parameter head and (ii) stochastic uncertainty in q(z|J), and
determine whether propagating latent uncertainty improves calibration or error ranking
relative to the manuscript's current z_mean evaluation.

**Inference-only.** No model is trained; no weight is updated; the decomposition is a set
of forward passes through the frozen encoder + ParamHead.

## Outcome (verdict)
> **C. GAUSSIAN HEAD DOMINATES — LATENT CONTRIBUTION MINOR.**
> Latent share of predictive variance: median **f_latent = 0.0005** (mean 0.0011,
> q95 0.0041). σ_total/σ_current median **1.0003**. Latent propagation changes 95%
> coverage by ≤ 0.0002, σ–error ranking by ≈ 0.0000, point Pearson by +0.000009.
> Root cause: near-point encoder posterior (exp(0.5·z_log_var) ≈ 0.002–0.004) with
> informative means. All four gates answered in `EXP2_FINAL_REPORT.md` §15.

## Directory
```
EXP2_FINAL_REPORT.md            15-section report + verdict + 4 gates (READ FIRST)
EXP2_MANUSCRIPT_IMPACT.md       10 reviewer questions + §24 wording candidates (Outcome C)
FROZEN_MODEL_REPRODUCTION_CHECK.md  Phase-0 anchor reproduction (all references exact)
MC_CONVERGENCE.md               Monte-Carlo gate: M = 500 selected
EXP2_QC.md                      15/15 programmatic assertions PASS
README.md                       this file
scripts/                        all experiment code (exp2_lib.py + 10 pipeline scripts)
results/                        decomposition arrays + all CSVs + meta
results/sample_level_decomposition.npz   per-sample decomposition (15307×9) + C_latent
figures/                        EXP2_FigA–G (300 dpi PNG)
server_qc/                      self-contained cross-environment QC package (see below)
```

## Key results files
| file | contents |
|---|---|
| `results/variance_decomposition_by_parameter.csv` | V_head / V_latent / V_total / f_latent stats + σ in log10 decades, per parameter |
| `results/calibration_comparison.csv` | coverage current / moment-matched / MC-mixture, levels 50/80/90/95% |
| `results/error_ranking_comparison.csv` | ρ_current / ρ_latent / ρ_total per parameter |
| `results/point_prediction_comparison.csv` | Pearson/MAE/RMSE current vs latent-mean |
| `results/encoder_latent_diagnostics.csv` | per-dim z_mean stats, posterior std, KL |
| `results/latent_induced_pairwise_covariance.csv` | 36 latent-induced correlations (descriptive) |
| `results/exp1_multiseed_decomposition_summary.csv` | 5-seed robustness (f_latent ≈ 0.00052 ± 0.00003) |
| `results/cross_env_local.json` | local leg of cross-environment QC (500 samples) |
| `results/decomposition_meta.json` | M=500, eps_seed 20260825, ddof=0, N=15307 |

## Reproduce
Use the conda interpreter (WindowsApps `python` stub exits 49):
`C:\Users\Administrator\anaconda3\envs\pytorch-2.60-gpu\python.exe`
(TF 2.20.0 / Keras 3, CPU). From this directory:

```powershell
& C:\Users\Administrator\anaconda3\envs\pytorch-2.60-gpu\python.exe scripts/phase0_repro.py
& C:\Users\Administrator\anaconda3\envs\pytorch-2.60-gpu\python.exe scripts/mc_convergence.py
& C:\Users\Administrator\anaconda3\envs\pytorch-2.60-gpu\python.exe scripts/decompose.py      # ~fast on CPU
& C:\Users\Administrator\anaconda3\envs\pytorch-2.60-gpu\python.exe scripts/calibration.py
& C:\Users\Administrator\anaconda3\envs\pytorch-2.60-gpu\python.exe scripts/ranking.py
& C:\Users\Administrator\anaconda3\envs\pytorch-2.60-gpu\python.exe scripts/point_pred.py
& C:\Users\Administrator\anaconda3\envs\pytorch-2.60-gpu\python.exe scripts/encoder_diag.py
& C:\Users\Administrator\anaconda3\envs\pytorch-2.60-gpu\python.exe scripts/multiseed.py       # ~1 min
& C:\Users\Administrator\anaconda3\envs\pytorch-2.60-gpu\python.exe scripts/server_qc.py --out results/cross_env_local.json
& C:\Users\Administrator\anaconda3\envs\pytorch-2.60-gpu\python.exe scripts/make_figures.py
& C:\Users\Administrator\anaconda3\envs\pytorch-2.60-gpu\python.exe scripts/qc.py
```

## Cross-environment QC (COMPLETE)
Both legs done and compared (EXP2_FINAL_REPORT.md §12):
- `results/cross_env_local.json` — local (TF 2.20/Keras 3), bit-reproducible.
- `results/cross_env_server.json` — server (TF 2.13/Keras 2), returned 2026-08-25.
- Max |server − local| over all five fields × 9 params: **1.2e-07** (tolerance 0.02) → PASS.
- The `server_qc/` folder is the self-contained package used for the server leg; it can
  be re-run anytime (`python server_qc.py`, or double-click `RUN_ME.bat`).

## Terminology
Use "model-implied predictive distribution", "latent-induced predictive variation",
"Gaussian-head conditional predictive variance", "total model-implied predictive
variance" — never "Bayesian posterior", "true posterior", "epistemic/aleatoric
uncertainty" for these quantities.
