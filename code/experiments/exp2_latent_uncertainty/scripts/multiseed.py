# -*- coding: utf-8 -*-
"""
EXP1 cross-seed robustness (EXP2 spec §16).

Runs the reduced decomposition on the FIVE leakage-free VAE checkpoints from
Experiment 1 (never retrained). Same selected M = 500. For each seed on the
leakage-free test set:
  median f_latent per parameter
  median sigma_total / sigma_current
  95% moment-matched coverage
  rho_total, rho_current (Spearman with |error|)
  delta point Pearson under latent averaging

Summarized as mean ± SD across the 5 seeds. The frozen model remains the
manuscript reference; these seeds are a robustness check only.

Writes results/exp1_multiseed_decomposition_summary.csv
"""
import os, sys, json, time
import numpy as np
from scipy.stats import spearmanr, pearsonr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exp2_lib import (EXP1, load_lf_test, param_head_batch, NOMINAL,
                      PARAM_SHORT, N_PARAM)
from tensorflow import keras
from exp2_lib import _Sampling

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
SEEDS = [20260824, 20260825, 20260826, 20260827, 20260828]
M = 500
EPS_SEED = 20260825
CHUNK = 256

def load_seed(seed):
    d = os.path.join(EXP1, "models", "vae", "seed%d" % seed)
    enc = keras.models.load_model(os.path.join(d, "encoder.h5"),
                                  custom_objects={"Sampling": _Sampling, "_Sampling": _Sampling})
    ph = keras.models.load_model(os.path.join(d, "param_head.h5"))
    return enc, ph

J_test, params_test = load_lf_test()
N = J_test.shape[0]

# fixed master eps shared across seeds (isolates seed differences from MC noise)
rng = np.random.default_rng(EPS_SEED)

results = []
for si, seed in enumerate(SEEDS):
    t0 = time.time()
    enc, ph = load_seed(seed)
    z_mean, z_log_var, _ = enc.predict(J_test, verbose=0)
    z_mean = z_mean.astype(np.float32); z_log_var = z_log_var.astype(np.float32)

    # accumulators
    f_lat = np.zeros((N, 9), np.float32)
    ratio = np.zeros((N, 9), np.float32)
    sigma_tot = np.zeros((N, 9), np.float32)
    mu_tot = np.zeros((N, 9), np.float32)
    mu_cur = np.zeros((N, 9), np.float32)
    sig_cur = np.zeros((N, 9), np.float32)

    for c in range((N + CHUNK - 1) // CHUNK):
        s, e = c * CHUNK, min((c + 1) * CHUNK, N)
        S = e - s
        eps = rng.standard_normal((S, M, N_PARAM)).astype(np.float32)
        z = z_mean[s:e][:, None, :] + np.exp(0.5 * z_log_var[s:e])[:, None, :] * eps
        mu_d, sig_d = param_head_batch(ph, z.reshape(-1, 9))
        mu_d = mu_d.reshape(S, M, 9); sig_d = sig_d.reshape(S, M, 9)
        vh = (sig_d ** 2).mean(axis=1)
        vl = mu_d.var(axis=1)
        vt = vh + vl
        fl = np.zeros_like(vt); nz = vt > 1e-12; fl[nz] = vl[nz] / vt[nz]
        mt = mu_d.mean(axis=1)
        mz, sz = param_head_batch(ph, z_mean[s:e])
        mu_cur[s:e] = mz; sig_cur[s:e] = sz
        f_lat[s:e] = fl; ratio[s:e] = np.sqrt(vt) / np.maximum(sz, 1e-12)
        sigma_tot[s:e] = np.sqrt(vt); mu_tot[s:e] = mt

    # metrics per param
    err_cur = np.abs(params_test - mu_cur)
    err_lat = np.abs(params_test - mu_tot)
    rho_cur = np.array([spearmanr(sig_cur[:, j], err_cur[:, j])[0] for j in range(9)])
    rho_tot = np.array([spearmanr(sigma_tot[:, j], err_lat[:, j])[0] for j in range(9)])
    # 95% moment-matched coverage
    zz = NOMINAL[0.95]
    lo = mu_tot - zz * sigma_tot; hi = mu_tot + zz * sigma_tot
    cov95 = np.mean((params_test >= lo) & (params_test <= hi), axis=0)
    # point Pearson delta
    r_cur = np.array([pearsonr(params_test[:, j], mu_cur[:, j])[0] for j in range(9)])
    r_lat = np.array([pearsonr(params_test[:, j], mu_tot[:, j])[0] for j in range(9)])
    d_pear = r_lat.mean() - r_cur.mean()

    for j in range(9):
        results.append(dict(seed=seed, parameter=PARAM_SHORT[j],
                            median_f_latent=float(np.median(f_lat[:, j])),
                            median_ratio_sigma=float(np.median(ratio[:, j])),
                            cov95_moment=float(cov95[j]),
                            rho_current=float(rho_cur[j]),
                            rho_total=float(rho_tot[j])))
    results.append(dict(seed=seed, parameter="ALL",
                        median_f_latent=float(np.median(f_lat)),
                        median_ratio_sigma=float(np.median(ratio)),
                        cov95_moment=float(np.mean(cov95)),
                        rho_current=float(rho_cur.mean()),
                        rho_total=float(rho_tot.mean()),
                        delta_pearson=float(d_pear)))
    print("seed %d done (%.1f min)" % (seed, (time.time() - t0) / 60))

# ---- summary across seeds ----
import csv
with open(os.path.join(RES, "exp1_multiseed_decomposition_summary.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["seed", "parameter", "median_f_latent", "median_ratio_sigma",
                "cov95_moment", "rho_current", "rho_total", "delta_pearson_ALL"])
    for r in results:
        dp = r.get("delta_pearson")
        w.writerow([r["seed"], r["parameter"], "%.6f" % r["median_f_latent"],
                    "%.6f" % r["median_ratio_sigma"], "%.6f" % r["cov95_moment"],
                    "%.6f" % r["rho_current"], "%.6f" % r["rho_total"],
                    "%.6f" % dp if dp is not None else ""])
print("saved exp1_multiseed_decomposition_summary.csv")

# ---- per-param mean +/- SD across the 5 seeds ----
print("\nper-param mean +/- SD across 5 seeds:")
all_rows = [r for r in results if r["parameter"] == "ALL"]
print("  ALL: med_f_latent %.4f ± %.4f | med_ratio %.6f ± %.6f | cov95 %.4f ± %.4f | "
      "rho_cur %.4f ± %.4f | rho_tot %.4f ± %.4f | dPear %.6f ± %.6f"
      % (np.mean([r["median_f_latent"] for r in all_rows]), np.std([r["median_f_latent"] for r in all_rows]),
         np.mean([r["median_ratio_sigma"] for r in all_rows]), np.std([r["median_ratio_sigma"] for r in all_rows]),
         np.mean([r["cov95_moment"] for r in all_rows]), np.std([r["cov95_moment"] for r in all_rows]),
         np.mean([r["rho_current"] for r in all_rows]), np.std([r["rho_current"] for r in all_rows]),
         np.mean([r["rho_total"] for r in all_rows]), np.std([r["rho_total"] for r in all_rows]),
         np.mean([r["delta_pearson"] for r in all_rows]), np.std([r["delta_pearson"] for r in all_rows])))
for j in range(9):
    pr = [r for r in results if r["parameter"] == PARAM_SHORT[j]]
    print("  %-8s med_f_latent %.5f ± %.5f | cov95 %.4f ± %.4f | rho_tot %.4f ± %.4f"
          % (PARAM_SHORT[j], np.mean([r["median_f_latent"] for r in pr]),
             np.std([r["median_f_latent"] for r in pr]),
             np.mean([r["cov95_moment"] for r in pr]), np.std([r["cov95_moment"] for r in pr]),
             np.mean([r["rho_total"] for r in pr]), np.std([r["rho_total"] for r in pr])))
