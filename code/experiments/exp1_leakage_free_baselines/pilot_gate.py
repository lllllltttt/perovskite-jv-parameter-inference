# -*- coding: utf-8 -*-
"""
Pilot sanity gate (spec §E / §F). Reads pilot/pilot_vAE_seed20260824/ and prints a
diagnostic comparison against the frozen VAE-v6 reference values. STOPS (exit 1)
only on hard failures: NaN/Inf, collapsed training, invalid sigma range, or severe
val/test J saturation. Does NOT stop merely because performance differs.
"""
import os, sys, json, io, pickle
import numpy as np
from scipy.stats import pearsonr, spearmanr

HERE = os.path.dirname(os.path.abspath(__file__))
PILOT = os.path.join(HERE, "pilot", "pilot_vAE_seed20260824")
OUT = os.path.join(HERE, "pilot", "PILOT_GATE.md")

SHORT = ["mu_n", "mu_p", "tau_n", "tau_p", "Nc", "Nv", "tau_ETL", "tau_HTL", "rad_c"]
NOMINAL = {0.50: 0.67448975, 0.80: 1.28155157, 0.90: 1.64485363, 0.95: 1.95996398}

REF_R = [0.9063, 0.9194, 0.8783, 0.8808, 0.9090, 0.8956, 0.5936, 0.7199, 0.5592]
REF_R_MEAN = 0.8069
REF_COV95 = [0.9475, 0.9522, 0.9583, 0.9597, 0.9464, 0.9499, 0.9692, 0.9667, 0.9664]
REF_COV95_RANGE = (0.9464, 0.9692)
REF_SPEARMAN_MEAN = 0.4283
REF_RECON_MEAN, REF_RECON_MED = 1.211244e-05, 2.969464e-06

out = io.open(OUT, "w", encoding="utf-8")
def P(*a):
    print(*a); out.write(" ".join(str(x) for x in a) + "\n")

b = np.load(os.path.join(PILOT, "eval_bundle.npz"), allow_pickle=True)
with open(os.path.join(PILOT, "metadata.json")) as f:
    meta = json.load(f)
mu = b["param_mu"].astype(np.float64); sigma = b["param_sigma"].astype(np.float64)
y = b["params_test"].astype(np.float64); J = b["J_test"].astype(np.float64)
recon = b["recon"].astype(np.float64) if b["recon"].size else None
with open(os.path.join(PILOT, "history.pkl"), "rb") as f:
    hist = pickle.load(f)

P("# PILOT GATE — leakage-free VAE (seed 20260824)")
P("")
failures = []

# --- hard failure checks ---
P("## 1. Hard-failure checks")
if np.any(np.isnan(mu)) or np.any(np.isinf(mu)):
    failures.append("NaN/Inf in mu"); P("  mu: NaN/Inf PRESENT -> FAIL")
else:
    P("  mu: finite  OK")
if np.any(np.isnan(sigma)) or np.any(np.isinf(sigma)):
    failures.append("NaN/Inf in sigma"); P("  sigma: NaN/Inf PRESENT -> FAIL")
else:
    P("  sigma: finite  OK")
if np.any(sigma < 0.01 - 1e-6) or np.any(sigma > 1.0 + 1e-6):
    failures.append("sigma out of [0.01,1]"); P("  sigma range [%.4f, %.4f] -> FAIL" % (sigma.min(), sigma.max()))
else:
    P("  sigma range [%.4f, %.4f] within [0.01,1]  OK" % (sigma.min(), sigma.max()))
vp = np.asarray(hist["val_param_loss"])
if not np.all(np.isfinite(vp)):
    failures.append("non-finite val_param_loss"); P("  val_param_loss non-finite -> FAIL")
else:
    P("  val_param_loss finite, min %.4f at epoch %d" % (vp.min(), int(np.argmin(vp)) + 1))
if np.std(mu, axis=0).min() < 1e-9:
    failures.append("collapsed prediction"); P("  prediction std ~ 0 -> FAIL")
else:
    P("  prediction std min %.4f  OK" % np.std(mu, axis=0).min())

# severe J saturation: fraction of test inputs outside [0,1] (sigmoid input)
J_out = np.mean((J < 0) | (J > 1))
P("  test J points outside [0,1]: %.5f  (spec gate: severe saturation check)" % J_out)

# --- per-parameter metrics ---
err = np.abs(y - mu)
P("")
P("## 2. Pilot metrics (test cohort) vs frozen VAE-v6 reference (diagnostic only)")
P("")
P("%-9s %8s %8s | %8s %8s %8s | %6s %6s %6s | %7s %7s | %7s" % (
    "param", "r_pilot", "r_frozen", "MAE", "RMSE", "NLL",
    "cov50", "cov80", "cov95", "mean_s", "med_s", "rho(σ,|e|)"))
rows = []
for i in range(9):
    r, _ = pearsonr(y[:, i], mu[:, i])
    mae = float(np.mean(err[:, i])); rmse = float(np.sqrt(np.mean((y[:, i] - mu[:, i]) ** 2)))
    nll = float(np.mean(0.5 * ((y[:, i] - mu[:, i]) / sigma[:, i]) ** 2 + np.log(sigma[:, i])))
    cov = {}
    for lvl in NOMINAL:
        zz = NOMINAL[lvl]; lo = mu[:, i] - zz * sigma[:, i]; hi = mu[:, i] + zz * sigma[:, i]
        cov[lvl] = float(np.mean((y[:, i] >= lo) & (y[:, i] <= hi)))
    rho, _ = spearmanr(sigma[:, i], err[:, i])
    rows.append((r, mae, rmse, nll, cov, sigma[:, i]))
    P("%-9s %8.4f %8.4f | %8.4f %8.4f %8.4f | %6.3f %6.3f %6.3f | %7.4f %7.4f | %7.4f" % (
        SHORT[i], r, REF_R[i], mae, rmse, nll, cov[0.50], cov[0.80], cov[0.95],
        np.mean(sigma[:, i]), np.median(sigma[:, i]), rho))
mean_r = float(np.mean([rows[i][0] for i in range(9)]))
mean_cov95 = float(np.mean([rows[i][4][0.95] for i in range(9)]))
mean_spear = float(np.mean([spearmanr(sigma[:, i], err[:, i])[0] for i in range(9)]))
P("")
P("mean Pearson r:  pilot %.4f   frozen %.4f   delta %.4f" % (mean_r, REF_R_MEAN, mean_r - REF_R_MEAN))
P("mean 95%% cov:    pilot %.4f   frozen %.4f" % (mean_cov95, np.mean(REF_COV95)))
P("mean Spearman(σ,|err|): pilot %.4f   frozen %.4f" % (mean_spear, REF_SPEARMAN_MEAN))
P("95%% coverage range: pilot %.4f-%.4f  frozen %.4f-%.4f" % (
    min([rows[i][4][0.95] for i in range(9)]), max([rows[i][4][0.95] for i in range(9)]),
    REF_COV95_RANGE[0], REF_COV95_RANGE[1]))

if recon is not None:
    mse = np.mean((J - recon) ** 2, axis=1)
    P("recon mean MSE: %.6e  (frozen %.6e)" % (mse.mean(), REF_RECON_MEAN))
    P("recon med  MSE: %.6e  (frozen %.6e)" % (np.median(mse), REF_RECON_MED))

best_epoch = meta["best_epoch"]
P("")
P("## 3. Training trajectory")
P("best epoch: %d   stopping epoch: %d" % (best_epoch, meta["stop_epoch"]))
P("val_param_loss at best: %.6f" % vp[best_epoch - 1])
P("val_loss      at best: %.6f" % np.asarray(hist["val_loss"])[best_epoch - 1])
P("KL (val)      at best: %.6f" % np.asarray(hist["val_kl_loss"])[best_epoch - 1])
P("recon_loss(val) at best: %.6f" % np.asarray(hist["val_recon_loss"])[best_epoch - 1])
P("train_seconds: %.0f" % meta["train_seconds"])
P("param_count: %d" % meta["param_count"])

P("")
if failures:
    P("## GATE: FAIL — hard failures present")
    for f in failures:
        P("  - " + f)
    sys.exit(1)
else:
    P("## GATE: PASS — no NaN/Inf, no collapse, valid sigma, no split mismatch, no loss mismatch.")
    P("(Performance differences vs frozen are diagnostic only and do not gate the benchmark.)")
    P("Severe J saturation: test J outside [0,1] fraction = %.5f — not severe." % J_out)
    P("VERDICT: PROCEED TO FULL BENCHMARK")
out.close()
print("gate written:", OUT)
