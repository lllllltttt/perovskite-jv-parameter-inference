# -*- coding: utf-8 -*-
"""
Full-test decomposition (EXP2 spec §3, §4, §6, §7, §8, §10, §14).

Runs the selected M = 500 over all 15,307 test samples in chunks (no giant
tensor). For every sample/parameter stores:
  mu_current, sigma_current (z_mean evaluation)
  mu_total, sigma_total, V_head, V_latent, V_total, f_head, f_latent
  delta_mu, ratio_sigma, sigma_head, sigma_latent
  abs_err_current, abs_err_latent
  mixture predictive interval endpoints (K theta-samples per latent draw,
    1000 predictive samples per (sample,param); levels 50/80/90/95)
  latent-induced 9x9 covariance C_latent (ddof=0)

Writes:
  results/sample_level_decomposition.npz
  results/decomposition_meta.json
  results/variance_decomposition_by_parameter.csv
"""
import os, sys, json, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exp2_lib import (EXP2, load_frozen_submodels, load_frozen_test,
                      encode_zstats, param_head_batch, sigma_fixed_np,
                      N_PARAM, PARAM_SHORT, PARAM_FULL, PARAM_LOG_RANGE, NOMINAL)

RES = os.path.join(EXP2, "results")
M = 500
EPS_SEED = 20260825
CHUNK = 256
K_MIX = 2  # theta samples per latent draw -> M*K = 1000 predictive samples
LEVELS = sorted(NOMINAL.keys())
Q_FRAC = [0.025, 0.05, 0.10, 0.25, 0.75, 0.90, 0.95, 0.975]
# level -> (lo-quantile fraction index, hi-quantile fraction index)
LVL_QI = {0.50: (3, 4), 0.80: (2, 5), 0.90: (1, 6), 0.95: (0, 7)}

rng = np.random.default_rng(EPS_SEED)  # sequential per-chunk stream (reproducible)

encoder, param_head = load_frozen_submodels()
J_test, params_test = load_frozen_test()
N = J_test.shape[0]
t0 = time.time()

z_mean, z_log_var = encode_zstats(encoder, J_test)

# accumulators
A = {k: np.zeros((N, 9), np.float32) for k in
     ["mu_current", "sigma_current", "mu_total", "sigma_total",
      "V_head", "V_latent", "V_total", "f_head", "f_latent",
      "delta_mu", "ratio_sigma", "sigma_head", "sigma_latent",
      "abs_err_current", "abs_err_latent"]}
mi_lo = np.zeros((N, 9, len(LEVELS)), np.float32)
mi_hi = np.zeros((N, 9, len(LEVELS)), np.float32)
C_latent = np.zeros((N, 9, 9), np.float32)

n_chunk = (N + CHUNK - 1) // CHUNK
for c in range(n_chunk):
    s, e = c * CHUNK, min((c + 1) * CHUNK, N)
    S = e - s
    zm_c = z_mean[s:e]
    zl_c = z_log_var[s:e]

    eps = rng.standard_normal((S, M, N_PARAM)).astype(np.float32)
    z = zm_c[:, None, :] + np.exp(0.5 * zl_c)[:, None, :] * eps          # (S,M,9)
    mu_d, sig_d = param_head_batch(param_head, z.reshape(-1, 9))          # (S*M,9)
    mu_d = mu_d.reshape(S, M, 9)
    sig_d = sig_d.reshape(S, M, 9)

    mu_total = mu_d.mean(axis=1)
    V_head = (sig_d ** 2).mean(axis=1)
    V_latent = mu_d.var(axis=1)                                           # ddof=0
    V_total = V_head + V_latent
    f_latent = np.zeros_like(V_total)
    nz = V_total > 1e-12
    f_latent[nz] = V_latent[nz] / V_total[nz]
    sigma_total = np.sqrt(V_total)
    sigma_head = np.sqrt(V_head)
    sigma_latent = np.sqrt(V_latent)

    mu_zm, sig_zm = param_head_batch(param_head, zm_c)
    sigma_current = np.asarray(sig_zm, np.float32)

    err_cur = np.abs(params_test[s:e] - mu_zm)
    err_lat = np.abs(params_test[s:e] - mu_total)

    A["mu_current"][s:e] = mu_zm
    A["sigma_current"][s:e] = sigma_current
    A["mu_total"][s:e] = mu_total
    A["sigma_total"][s:e] = sigma_total
    A["V_head"][s:e] = V_head
    A["V_latent"][s:e] = V_latent
    A["V_total"][s:e] = V_total
    A["f_head"][s:e] = 1.0 - f_latent
    A["f_latent"][s:e] = f_latent
    A["delta_mu"][s:e] = mu_total - mu_zm
    A["ratio_sigma"][s:e] = sigma_total / np.maximum(sigma_current, 1e-12)
    A["sigma_head"][s:e] = sigma_head
    A["sigma_latent"][s:e] = sigma_latent
    A["abs_err_current"][s:e] = err_cur
    A["abs_err_latent"][s:e] = err_lat

    # mixture predictive quantiles (1000 predictive samples per (sample,param))
    th_eps = rng.standard_normal((S, M, K_MIX, N_PARAM)).astype(np.float32)
    th = (mu_d[:, :, None, :] + sig_d[:, :, None, :] * th_eps).reshape(S, M * K_MIX, 9)
    q = np.quantile(th, Q_FRAC, axis=1).astype(np.float32)                # (8,S,9)
    for j, lvl in enumerate(LEVELS):
        li, hi_i = LVL_QI[lvl]
        mi_lo[s:e, :, j] = q[li]
        mi_hi[s:e, :, j] = q[hi_i]

    # latent-induced covariance (ddof=0), per sample
    dc = mu_d - mu_d.mean(axis=1, keepdims=True)                          # (S,M,9)
    C = np.einsum("sij,sik->sjk", dc, dc) / M                             # (S,9,9)
    C_latent[s:e] = C.astype(np.float32)

    if (c + 1) % 10 == 0 or c == n_chunk - 1:
        print("chunk %d/%d  (%.1f min)" % (c + 1, n_chunk, (time.time() - t0) / 60))

# ---------------- save sample-level npz ----------------
np.savez(os.path.join(RES, "sample_level_decomposition.npz"),
         sample_id=np.arange(N),
         params_test=params_test.astype(np.float32),
         **A,
         mi_lo=mi_lo, mi_hi=mi_hi, C_latent=C_latent,
         param_names=np.array(PARAM_FULL),
         levels=np.array(LEVELS), M=np.int32(M), K_mix=np.int32(K_MIX))
print("saved sample_level_decomposition.npz")

meta = dict(M=M, eps_seed=EPS_SEED, chunk=CHUNK, K_mix=K_MIX,
            predictive_samples_per_sample_param=M * K_MIX,
            levels=LEVELS, quantile_fractions=Q_FRAC,
            ddof_convention="population (ddof=0) for latent variance/covariance",
            frozen_test_N=N)
with open(os.path.join(RES, "decomposition_meta.json"), "w") as f:
    json.dump(meta, f, indent=2)

# ---------------- variance_decomposition_by_parameter.csv ----------------
def pct(x, q):
    return np.percentile(x, q)

rows = []
for j in range(9):
    vh = A["V_head"][:, j]; vl = A["V_latent"][:, j]; vt = A["V_total"][:, j]
    fl = A["f_latent"][:, j]
    lg = PARAM_LOG_RANGE[j]
    rows.append([PARAM_SHORT[j],
                 float(vh.mean()), float(np.median(vh)),
                 float(vl.mean()), float(np.median(vl)),
                 float(vt.mean()), float(np.median(vt)),
                 float(fl.mean()), float(np.median(fl)),
                 float(pct(fl, 25)), float(pct(fl, 75)),
                 float(pct(fl, 90)), float(pct(fl, 95)),
                 float(np.median(np.sqrt(vh) * lg)),
                 float(np.median(np.sqrt(vl) * lg)),
                 float(np.median(np.sqrt(vt) * lg))])
import csv
with open(os.path.join(RES, "variance_decomposition_by_parameter.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["parameter", "mean_V_head", "median_V_head", "mean_V_latent",
                "median_V_latent", "mean_V_total", "median_V_total",
                "mean_f_latent", "median_f_latent", "q25_f_latent", "q75_f_latent",
                "q90_f_latent", "q95_f_latent",
                "median_sigma_head_decades", "median_sigma_latent_decades",
                "median_sigma_total_decades"])
    w.writerows([[r[0]] + ["%.6g" % v for v in r[1:]] for r in rows])
print("saved variance_decomposition_by_parameter.csv")

# quick summary print
print("\nper-param median f_latent / sigma_total_decades:")
for r in rows:
    print("  %-8s  med_f_latent=%.4f  med_sigma_total_decades=%.4f"
          % (r[0], r[8], r[15]))
