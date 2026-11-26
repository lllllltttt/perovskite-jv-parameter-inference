# -*- coding: utf-8 -*-
"""
Encoder latent diagnostics + latent-induced joint structure
(EXP2 spec §13, §14).

Encoder: per latent dimension report
  mean(z_mean), SD(z_mean) over the test set,
  mean/median posterior latent std = exp(0.5 * z_log_var),
  mean per-dimension KL contribution, total mean KL.

Joint: per-sample latent-induced 9x9 covariance Cov_z[mu_theta(z)] (already
stored as C_latent, ddof=0); derived per-pair correlation summarized across
samples (median, IQR, fraction positive/negative).

Writes results/encoder_latent_diagnostics.csv
       results/latent_induced_pairwise_covariance.csv
"""
import os, sys, csv
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exp2_lib import (EXP2, load_frozen_submodels, load_frozen_test,
                      encode_zstats, PARAM_SHORT)

RES = os.path.join(EXP2, "results")

# ---- encoder diagnostics ----
encoder, _ = load_frozen_submodels()
J_test, _ = load_frozen_test()
z_mean, z_log_var = encode_zstats(encoder, J_test)
post_std = np.exp(0.5 * z_log_var)
per_dim_kl = 0.5 * (z_mean ** 2 + np.exp(z_log_var) - 1 - z_log_var)
total_kl = per_dim_kl.sum(axis=1).mean()

with open(os.path.join(RES, "encoder_latent_diagnostics.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["latent_dim", "mean_z_mean", "sd_z_mean", "mean_post_std",
                "median_post_std", "mean_kl_per_dim"])
    for j in range(9):
        w.writerow([j, round(float(z_mean[:, j].mean()), 6),
                    round(float(z_mean[:, j].std()), 6),
                    round(float(post_std[:, j].mean()), 6),
                    round(float(np.median(post_std[:, j])), 6),
                    round(float(per_dim_kl[:, j].mean()), 6)])
print("saved encoder_latent_diagnostics.csv")
print("total mean KL (test): %.3f nats" % total_kl)

# ---- latent-induced pairwise covariance summary ----
C = np.load(os.path.join(RES, "sample_level_decomposition.npz"))["C_latent"]
S, _, _ = C.shape
# per-sample correlation matrix with zero-variance guard
v = np.sqrt(np.einsum("sii->si", C))                     # (S,9) latent std per dim
corr = np.zeros((S, 9, 9))
for i in range(9):
    for k in range(9):
        denom = v[:, i] * v[:, k]
        safe = denom > 1e-16
        corr[safe, i, k] = C[safe, i, k] / denom[safe]
        corr[~safe, i, k] = np.nan

pairs = [(i, k) for i in range(9) for k in range(i + 1, 9)]
rows = []
for (i, k) in pairs:
    c = corr[:, i, k]
    valid = c[~np.isnan(c)]
    pos = np.mean(valid > 0)
    neg = np.mean(valid < 0)
    if len(valid) == 0:
        rows.append([PARAM_SHORT[i], PARAM_SHORT[k], "nan", "nan", "nan", "nan", "nan"])
        continue
    rows.append([PARAM_SHORT[i], PARAM_SHORT[k],
                 float(np.median(valid)),
                 float(np.percentile(valid, 25)), float(np.percentile(valid, 75)),
                 float(pos), float(neg)])

with open(os.path.join(RES, "latent_induced_pairwise_covariance.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["param_i", "param_j", "median_corr", "q25_corr", "q75_corr",
                "frac_positive", "frac_negative"])
    for r in rows:
        w.writerow([r[0], r[1]] + ["%.6f" % x for x in r[2:]])
print("saved latent_induced_pairwise_covariance.csv")

# focus pairs (collision-related)
focus = [("tau_n", "tau_ETL"), ("tau_n", "tau_HTL"), ("rad_c", "tau_n"), ("rad_c", "tau_ETL")]
print("\nfocus pairs (median corr | frac>0):")
for r in rows:
    if (r[0], r[1]) in focus or (r[1], r[0]) in focus:
        print("  %-8s %-8s  med=%.4f  frac_pos=%.3f" % (r[0], r[1], r[2], r[5]))
# global magnitude
meds = [r[2] for r in rows if not isinstance(r[2], str)]
print("\noverall median |latent corr| across all 36 pairs: %.4f" % np.median(np.abs(meds)))
