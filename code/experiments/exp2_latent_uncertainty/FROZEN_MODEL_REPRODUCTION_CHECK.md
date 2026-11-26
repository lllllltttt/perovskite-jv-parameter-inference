# FROZEN MODEL REPRODUCTION CHECK

EXP2 Phase 0 · inference-only · frozen Stage-I VAE-v6 `data/vae-v6/vae-v6/`
sigma convention: `clip(softplus(raw)+0.01, 0.01, 1.0)` · point evaluation at `z = z_mean`

## Test-set identity

- test J: `(15307, 131)`  test params: `(15307, 9)`
- **test N = 15307** -> PASS

## NaN/Inf / sigma-bounds check

- any NaN/Inf in mu/sigma/z_mean/z_log_var: False (must be False)
- sigma range on test: [0.011165, 0.792324]  inside [0.01, 1.0]: PASS

## Point recovery (Pearson r, normalized log-param space)

| param | frozen reference | reproduced | diff |
|---|---|---|---|
| mu_n       | 0.9063 | 0.9063 | -0.0000 | PASS |
| mu_p       | 0.9194 | 0.9194 | +0.0000 | PASS |
| tau_n      | 0.8783 | 0.8783 | -0.0000 | PASS |
| tau_p      | 0.8808 | 0.8808 | +0.0000 | PASS |
| Nc         | 0.9090 | 0.9090 | +0.0000 | PASS |
| Nv         | 0.8956 | 0.8956 | +0.0000 | PASS |
| tau_ETL    | 0.5936 | 0.5936 | +0.0000 | PASS |
| tau_HTL    | 0.7199 | 0.7199 | +0.0000 | PASS |
| rad_c      | 0.5592 | 0.5592 | -0.0000 | PASS |
| **mean** | **0.8069** | **0.8069** | +0.0000 | PASS |

## Spearman(sigma, |error|)

| param | frozen reference | reproduced | diff |
|---|---|---|---|
| mu_n       | 0.3982 | 0.3982 | +0.0000 | PASS |
| mu_p       | 0.3343 | 0.3343 | +0.0000 | PASS |
| tau_n      | 0.6459 | 0.6459 | +0.0000 | PASS |
| tau_p      | 0.6218 | 0.6218 | +0.0000 | PASS |
| Nc         | 0.3530 | 0.3530 | -0.0000 | PASS |
| Nv         | 0.2444 | 0.2444 | -0.0000 | PASS |
| tau_ETL    | 0.3772 | 0.3772 | -0.0000 | PASS |
| tau_HTL    | 0.4647 | 0.4647 | -0.0000 | PASS |
| rad_c      | 0.4147 | 0.4147 | +0.0000 | PASS |
| **mean** | **0.4283** | **0.4283** | -0.0000 | PASS |

## Empirical coverage (z_mean Gaussian intervals)

| param | 50%% | 80%% | 90%% | 95%% |
|---|---|---|---|---|
| mu_n       | 0.5005 | 0.8021 | 0.8980 | 0.9475 |
| mu_p       | 0.4965 | 0.8029 | 0.9039 | 0.9522 |
| tau_n      | 0.4738 | 0.7940 | 0.9070 | 0.9583 |
| tau_p      | 0.4590 | 0.7904 | 0.9100 | 0.9597 |
| Nc         | 0.5226 | 0.8098 | 0.9032 | 0.9464 |
| Nv         | 0.4985 | 0.8037 | 0.9014 | 0.9499 |
| tau_ETL    | 0.4592 | 0.7971 | 0.9197 | 0.9692 |
| tau_HTL    | 0.4556 | 0.7955 | 0.9164 | 0.9667 |
| rad_c      | 0.4483 | 0.7796 | 0.9089 | 0.9664 |

95% coverage range reproduced: [0.9464, 0.9692] (reference [0.9464, 0.9692])
95% coverage per-parameter match: PASS

## Encoder KL (test set)

- mean per-sample total KL over test: **51.356 nats** (frozen training history final: 51.40)
- per-dim mean KL: 5.583  6.141  5.221  5.689  5.744  5.817  6.073  5.296  5.791

## Verdict

**PASS — frozen model reproduces all reference numbers (|Δ| ≤ 0.0015).**
Proceed to the Monte-Carlo convergence gate.
