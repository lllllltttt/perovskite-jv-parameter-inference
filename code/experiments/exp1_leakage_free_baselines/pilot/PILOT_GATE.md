# PILOT GATE — leakage-free VAE (seed 20260824)

## 1. Hard-failure checks
  mu: finite  OK
  sigma: finite  OK
  sigma range [0.0121, 0.6584] within [0.01,1]  OK
  val_param_loss finite, min -14.5528 at epoch 1000
  prediction std min 0.1550  OK
  test J points outside [0,1]: 0.00006  (spec gate: severe saturation check)

## 2. Pilot metrics (test cohort) vs frozen VAE-v6 reference (diagnostic only)

param      r_pilot r_frozen |      MAE     RMSE      NLL |  cov50  cov80  cov95 |  mean_s   med_s | rho(σ,|e|)
mu_n        0.8775   0.9063 |   0.0845   0.1152  -1.8452 |  0.494  0.805  0.952 |  0.1050  0.0959 |  0.4481
mu_p        0.8927   0.9194 |   0.0805   0.1091  -1.8979 |  0.478  0.799  0.958 |  0.0983  0.0894 |  0.4175
tau_n       0.8598   0.8783 |   0.0998   0.1373  -1.8720 |  0.459  0.793  0.964 |  0.1185  0.1468 |  0.6276
tau_p       0.8615   0.8808 |   0.1009   0.1363  -1.8240 |  0.447  0.792  0.964 |  0.1187  0.1475 |  0.6036
Nc          0.8868   0.9090 |   0.0676   0.0906  -2.0190 |  0.517  0.816  0.952 |  0.0861  0.0829 |  0.3674
Nv          0.8787   0.8956 |   0.0701   0.0902  -1.9692 |  0.498  0.805  0.953 |  0.0879  0.0861 |  0.2887
tau_ETL     0.5667   0.5936 |   0.1934   0.2399  -1.0065 |  0.453  0.794  0.971 |  0.2331  0.2378 |  0.3838
tau_HTL     0.6885   0.7199 |   0.1683   0.2111  -1.1850 |  0.436  0.798  0.970 |  0.2024  0.2142 |  0.4422
rad_c       0.5288   0.5592 |   0.1980   0.2460  -0.9855 |  0.450  0.782  0.969 |  0.2376  0.2496 |  0.3599

mean Pearson r:  pilot 0.7823   frozen 0.8069   delta -0.0246
mean 95% cov:    pilot 0.9615   frozen 0.9574
mean Spearman(σ,|err|): pilot 0.4377   frozen 0.4283
95% coverage range: pilot 0.9518-0.9714  frozen 0.9464-0.9692
recon mean MSE: 1.148895e-05  (frozen 1.211244e-05)
recon med  MSE: 2.485213e-06  (frozen 2.969464e-06)

## 3. Training trajectory
best epoch: 1000   stopping epoch: 1000
val_param_loss at best: -14.552773
val_loss      at best: -14.498556
KL (val)      at best: 52.810223
recon_loss(val) at best: 0.001406
train_seconds: 4473
param_count: 55495

## GATE: PASS — no NaN/Inf, no collapse, valid sigma, no split mismatch, no loss mismatch.
(Performance differences vs frozen are diagnostic only and do not gate the benchmark.)
Severe J saturation: test J outside [0,1] fraction = 0.00006 — not severe.
VERDICT: PROCEED TO FULL BENCHMARK
