# LOSS_REDUCTION_VERIFICATION — EXP1

Date: 2026-08-24
Authority: `script/VAE-v6.py` (frozen training code) and `script/VAE_v6_eval_fixed.py` (frozen eval code).
All reductions below were read directly from the frozen executable code; the benchmark
implementations in `exp1_lib.py` reproduce them line-for-line in formula form.

## 1. Gaussian parameter NLL (monitored as `param_loss`)

Frozen code (`VAE-v6.py` `gaussian_nll`):

```
loss = 0.5 * ( (y - mu)^2 / sigma^2  +  2 * log(sigma) )
param_loss = reduce_mean( reduce_sum(loss, axis=1) )
```

Equivalently, per sample:

```
sum_{p=1..9} [ 0.5 * ((y_p - mu_p)/sigma_p)^2  +  log(sigma_p) ]
```

then **mean over the batch**. The 0.5·log(2π) constant of a standard Gaussian log-density
is omitted (as it would not affect gradients within an architecture). This matches the
form in the experiment specification §H. Benchmark implementation: `gaussian_nll` in
`exp1_lib.py` — identical formula, `reduce_mean(reduce_sum(..., axis=1))`.

**Reduction convention: SUM over the 9 parameters per sample, then MEAN over the batch.**

## 2. Reconstruction loss

Frozen code (`VAE-v6.py` `train_step`):

```
recon_loss = reduce_mean( reduce_sum( (x - recon)^2, axis=1 ) )
```

Per sample: **sum** of squared error over all 131 J-V points; then **mean over batch**.
This is NOT `mean over all 131 elements and batch`; it is a per-sample sum.
Equivalently: `recon_loss = (1/B) * Σ_b Σ_j (x_{b,j} - recon_{b,j})^2`.
Benchmark implementation: `recon_loss` in `exp1_lib.py` — identical.

**Reduction convention: SUM over the 131 points per sample, then MEAN over batch.**

## 3. KL divergence (VAE only)

Frozen code (`VAE-v6.py` `train_step`):

```
kl = -0.5 * reduce_mean( reduce_sum( 1 + z_log_var - z_mean^2 - exp(z_log_var), axis=1 ) )
```

Standard unit-Gaussian KL in the `exp(z_log_var)` parameterization. Per sample sum over the
9 latent dims, then mean over batch. Benchmark implementation: `kl_divergence` in `exp1_lib.py`.

## 4. Total objective

Frozen code:

```
loss = recon_loss  +  BETA * kl  +  LAMBDA * param_loss
BETA  = 1e-3
LAMBDA = 1.0
```

Benchmark keeps BETA=1e-3, LAMBDA=1.0 for the VAE. Deterministic-AE drops only the KL term
(BETA·kl = 0); reconstruction and NLL weights stay 1.0 and 1.0. MLP drops reconstruction and
KL entirely; the objective is `LAMBDA * param_loss` with LAMBDA=1.0.

## 5. Sigma transform (training AND evaluation)

Frozen code (`sigma_transform`):

```
sigma = clip( softplus(raw) + SIGMA_MIN, SIGMA_MIN, SIGMA_MAX ),  SIGMA_MIN=0.01, SIGMA_MAX=1.0
```

Identical in benchmark (`sigma_transform`, `exp1_lib.py`). The sigma_raw head bias is
initialized to Constant(-3.0) in both. Point evaluation uses the deterministic path:
VAE → ParamHead(z_mean) and decoder(z_mean); Det-AE → ParamHead(z) and decoder(z); MLP → trunk.

## 6. Callbacks / training loop (all three models)

| Setting | Value (frozen) | Benchmark |
|---|---|---|
| Optimizer | Adam(1e-3) | Adam(1e-3) |
| Batch size | 64 | 64 |
| Max epochs | 1000 | 1000 |
| EarlyStopping | monitor=val_param_loss, patience=50, restore_best_weights=True | same |
| ReduceLROnPlateau | monitor=val_loss, factor=0.5, patience=15, min_lr=1e-6 | same |
| ModelCheckpoint | monitor=val_loss, save_best_only, weights only | same (saved as `best_val_loss.weights.h5`) |
| Data shuffle | full-buffer shuffle | full-buffer shuffle, buffer seed = run seed (per spec §I) |

## 7. Cross-check with the frozen run

`history.pkl` of the frozen VAE-v6 confirms: best val_param_loss at epoch 638,
KL ≈ 51.36, 688 epochs total, final lr = 1e-6 — consistent with the above monitors.
A fresh run of the frozen model (unchanged) reproduces the manuscript's Table-2 recovery
values (mean r = 0.807), coverage 0.9464–0.9692, and mean Spearman(σ, |err|) = 0.4283
(`phase0_frozen_eval_repro.txt`), confirming the reductions and the environment.
