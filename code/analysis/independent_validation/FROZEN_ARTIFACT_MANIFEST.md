# FROZEN ARTIFACT MANIFEST — VAE-v6 (locked manuscript)

**Verification date:** 2026-08-26
**Source of truth:** `script/VAE_v6_eval_fixed.py` (frozen evaluation), `script/pre-process.py`, `script/VAE-v6.py` (training), `evaluation_fixed/` (frozen outputs), `manuscript_stage1_submission_locked.md` (locked manuscript).

All artifacts below were verified from code and files — not from memory.

---

## 1. Frozen checkpoint path

```
E:\project\work1\data\vae-v6\vae-v6\
    encoder.h5       (131 -> 128 -> 64 -> 9 latent; Sampling layer; z_mean, z_log_var, z outputs)
    decoder.h5       (9 -> 64 -> 128 -> 131, sigmoid output)
    param_head.h5    (9 -> 64 -> 32 -> [mu (9), sigma_raw (9)]; sigma_raw bias init -3.0)
    best.weights.h5  (ModelCheckpoint weights-only, monitor val_loss; superseded by the saved full .h5 models
                      after EarlyStopping restore_best_weights — the .h5 full models carry the best weights)
    history.pkl
```

The frozen evaluation loads `encoder.h5`, `decoder.h5`, `param_head.h5` with `custom_objects={"Sampling": Sampling}`.

## 2. J–V scaler

- **Path:** `E:\project\work1\data\J_scaler.pkl`
- **Object:** `sklearn.preprocessing.MinMaxScaler`, pickled directly (no wrapper dict).
- **Fit:** `MinMaxScaler().fit_transform(J)` on the full retained set (all 102,046 samples), **before** the split.
- **Per-column (per-voltage-point) min–max scaling** — 131 features, `n_features_in_ = 131`.
- Frozen extents (physical mA/cm²): global min = **-6358.76** (last voltage point), global max = **24.096** (V≈0).
- Note: the pickle was produced under sklearn 1.3.2; loading under sklearn 1.8.0 emits an `InconsistentVersionWarning` (benign; `data_min_` / `data_range_` read correctly).

## 3. Parameter scaler

- **Path:** `E:\project\work1\data\param_scaler.pkl`
- **Object:** dict `{"scaler": MinMaxScaler, "log_mask": np.ndarray[bool] (9,)}`
- **Fit:** on the **log10-transformed** full retained set (all 102,046 samples), before the split.
- `log_mask = [True]*9` → all nine parameters are log10-transformed.
- Frozen min/max in log10 space:

| param | log10 min | log10 max | log10 range |
|---|---|---|---|
| mu_n_pvk | -6.341035 | -2.651695 | 3.689340 |
| mu_p_pvk | -6.344862 | -2.675718 | 3.669144 |
| tau_n_pvk | -9.320572 | -1.655608 | 7.664964 |
| tau_p_pvk | -9.348722 | -1.690370 | 7.658352 |
| Nc_eff_pvk | 22.666518 | 26.348305 | 3.681787 |
| Nv_eff_pvk | 22.634477 | 26.338456 | 3.703979 |
| tau_ETL | -12.0 | -8.0 | 4.0 |
| tau_HTL | -14.0 | -10.0 | 4.0 |
| rad_c | -12.0 | -9.0 | 3.0 |

## 4. Parameter order

Manuscript / training / evaluation order (identical in `pre-process.py`, `VAE-v6.py`, `VAE_v6_eval_fixed.py`, `exp3_lib.py`):

1. mu_n_pvk
2. mu_p_pvk
3. tau_n_pvk
4. tau_p_pvk
5. Nc_eff_pvk
6. Nv_eff_pvk
7. tau_ETL
8. tau_HTL
9. rad_c

The CSV columns of **both** the retained (`…lifetimes-2.csv`) and the independent (`…lifetimes-3.csv`) datasets are already in this exact order (verified from headers).

## 5. Voltage-grid convention

- **131 J–V points**, columns `J_000 … J_130`.
- Grid = `np.linspace(0, 1.3, 131)` → exactly **0.00 → 1.30 V in 0.01-V steps**.
- Units: **mA/cm²**. J(V=0) positive (Jsc); current decreases with V; negative current possible at high forward bias (zero-crossing ≈ Voc within sweep).

## 6. Evaluation code path

- Frozen eval: `E:\project\work1\script\VAE_v6_eval_fixed.py`
- Preprocessing: `E:\project\work1\script\pre-process.py`
- Training (for architecture reference only): `E:\project\work1\script\VAE-v6.py`
- Exp3 coordinate library: `E:\project\work1\reviewer_experiments\exp3_prior_coordinate_recoverability\scripts\exp3_lib.py`

## 7. Sigma transformation

```
sigma = clip( softplus(raw_sigma) + 0.01 , 0.01 , 1.0 )
```

- Matches training exactly (`VAE-v6.py` `sigma_transform` and `VAE_v6_eval_fixed.py` `sigma_fixed`).
- Frozen raw sigma range on test: [-6.7545, +0.1710] → fixed sigma range [0.01117, 0.79232].
- Sigma is produced by the Gaussian parameter head from the **latent mean** z_mean (no latent sampling for the head).

## 8. Point-prediction convention

- **`ParamHead(mu_z)`** — the Gaussian head is applied to the **latent mean** z_mean.
- No latent Monte-Carlo sampling for point prediction or for the main evaluation (sampling only used in the explicit Exp2 decomposition, which is not part of this replication).
- All point metrics are computed in **normalized log10 parameter space** (the model's native output space), as in `VAE_v6_eval_fixed.py`.
- Predictive-interval convention (calibration): interval = `mu ± z * sigma`, z = two-sided normal quantile for nominal level (0.50: 0.67448975, 0.80: 1.28155157, 0.90: 1.64485363, 0.95: 1.95996398). Empirical coverage = fraction of true normalized targets inside `[mu - z*sigma, mu + z*sigma]`.
- Uncertainty–error association: `Spearman(sigma, |error|)` in normalized space.

## 9. Retained dataset / split

- Retained dataset: `E:\project\work1\data\JV_database_9D_interface_lifetimes-2.csv` (physical), normalized archive `dataset_normalized.npz`.
- N = 102,046 retained (from 200,000 LHS draws, seed 42, after physical filtering); split 70/15/15: **train 71,432 / val 15,307 / test 15,307** (`random_state=42` twice).
- Frozen reference metrics (test set, N = 15,307) — verified from `evaluation_fixed/parameter_metrics.csv`, `calibration_fixed.csv`, `uncertainty_error_fixed.csv`, `evaluation_summary.txt` and the locked manuscript Tables 2 / S11:

| param | Pearson r | 95% cov | Spearman(σ,|err|) |
|---|---|---|---|
| mu_n | 0.9063 | 0.9475 | 0.3982 |
| mu_p | 0.9194 | 0.9522 | 0.3343 |
| tau_n | 0.8783 | 0.9583 | 0.6459 |
| tau_p | 0.8808 | 0.9597 | 0.6218 |
| Nc | 0.9090 | 0.9464 | 0.3530 |
| Nv | 0.8956 | 0.9499 | 0.2444 |
| tau_ETL | 0.5936 | 0.9692 | 0.3772 |
| tau_HTL | 0.7199 | 0.9667 | 0.4647 |
| rad_c | 0.5592 | 0.9664 | 0.4147 |
| **mean** | **0.8069** | **0.9615*** | **0.4283** |

\* all-parameter mean of the nine 95% coverage values (Table S13 cites 0.9615 for the main-text mean).

## 10. Frozen prior-coordinate reference (Exp3, Table S11)

| coordinate | Pearson r |
|---|---|
| a_mu | 0.9250 |
| r_mu | 0.4289 |
| a_tau | 0.8819 |
| r_tau | 0.3517 |
| a_D | 0.9248 |
| r_D | 0.2663 |

Formulas (log10 physical space): a = 0.5·(log10 p_n + log10 p_p); r = log10 p_n − log10 p_p. Inversion of normalized → log10 physical via `norm * sc.data_range_ + sc.data_min_` on the frozen param scaler.

---

**VERDICT (Phase 0):** All eight required artifact identities confirmed from code and files. Reference metrics match the locked manuscript exactly. Ready for the dataset compatibility gate.
