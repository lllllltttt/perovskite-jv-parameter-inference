# -*- coding: utf-8 -*-
"""
Phase 0 — FROZEN MODEL REPRODUCTION CHECK (EXP2 spec §2).

Inference only. Loads the frozen Stage-I VAE-v6 and verifies that evaluating
at z = z_mean with the frozen sigma convention reproduces the manuscript /
frozen-evaluation numbers:

  test N = 15,307
  Pearson r : mu_n 0.906 / mu_p 0.919 / tau_n 0.878 / tau_p 0.881 / Nc 0.909 /
              Nv 0.896 / tau_ETL 0.594 / tau_HTL 0.720 / rad_c 0.559 / mean 0.807
  95% coverage : 0.946 - 0.969
  Spearman(sigma, |err|) : mu_n 0.398 / mu_p 0.334 / tau_n 0.646 / tau_p 0.622 /
              Nc 0.353 / Nv 0.244 / tau_ETL 0.377 / tau_HTL 0.465 / rad_c 0.415 /
              mean 0.428

If any check fails -> STOP (per spec §2).
Writes FROZEN_MODEL_REPRODUCTION_CHECK.md into the EXP2 directory.
"""
import os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exp2_lib import (EXP2, load_frozen_submodels, load_frozen_test,
                      encode_zstats, param_head_batch, sigma_fixed_np,
                      per_param_pearson, per_param_spearman,
                      coverage_at_levels, gaussian_intervals,
                      NOMINAL, PARAM_FULL, PARAM_SHORT)

OUT = os.path.join(EXP2, "FROZEN_MODEL_REPRODUCTION_CHECK.md")

# reference values (frozen evaluation_fixed / manuscript)
REF_R = np.array([0.9063, 0.9194, 0.8783, 0.8808, 0.9090, 0.8956, 0.5936, 0.7199, 0.5592])
REF_SP = np.array([0.398191, 0.334319, 0.645906, 0.621839, 0.353014,
                   0.244391, 0.377232, 0.464704, 0.414716])
REF_COV95 = np.array([0.9475, 0.9522, 0.9583, 0.9597, 0.9464,
                      0.9499, 0.9692, 0.9667, 0.9664])
REF_R_MEAN = 0.8069
REF_SP_MEAN = 0.4283

TOL = 0.0015
TOL_SP = 0.0015
TOL_COV = 0.0015

lines = []
def P(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    lines.append(s)

# ---------------- run ----------------
encoder, param_head = load_frozen_submodels()
J_test, params_test = load_frozen_test()
N = J_test.shape[0]
P("# FROZEN MODEL REPRODUCTION CHECK")
P("")
P("EXP2 Phase 0 · inference-only · frozen Stage-I VAE-v6 `data/vae-v6/vae-v6/`")
P("sigma convention: `clip(softplus(raw)+0.01, 0.01, 1.0)` · point evaluation at `z = z_mean`")
P("")
P("## Test-set identity")
P("")
P("- test J: `%s`  test params: `%s`" % (J_test.shape, params_test.shape))
P("- **test N = %d** -> %s" % (N, "PASS" if N == 15307 else "FAIL"))
P("")

z_mean, z_log_var = encode_zstats(encoder, J_test)
mu_current, sig_cur = param_head_batch(param_head, z_mean)
sigma_current = np.asarray(sig_cur)

P("## NaN/Inf / sigma-bounds check")
P("")
P("- any NaN/Inf in mu/sigma/z_mean/z_log_var:",
  bool(np.isnan(mu_current).any() or np.isinf(mu_current).any()
       or np.isnan(sigma_current).any() or np.isinf(sigma_current).any()
       or np.isnan(z_mean).any() or np.isnan(z_log_var).any()), "(must be False)")
P("- sigma range on test: [%.6f, %.6f]  inside [0.01, 1.0]: %s"
  % (sigma_current.min(), sigma_current.max(),
     "PASS" if (sigma_current.min() >= 0.01 - 1e-6 and sigma_current.max() <= 1.0 + 1e-6) else "FAIL"))
P("")

# ---- Pearson ----
err = np.abs(params_test - mu_current)
pearson = per_param_pearson(params_test, mu_current)
P("## Point recovery (Pearson r, normalized log-param space)")
P("")
P("| param | frozen reference | reproduced | diff |")
P("|---|---|---|---|")
ok = True
for i in range(9):
    d = pearson[i] - REF_R[i]
    p = "PASS" if abs(d) <= TOL else "FAIL"
    if p == "FAIL":
        ok = False
    P("| %-10s | %.4f | %.4f | %+.4f | %s |" % (PARAM_SHORT[i], REF_R[i], pearson[i], d, p))
P("| **mean** | **%.4f** | **%.4f** | %+.4f | %s |"
  % (REF_R_MEAN, pearson.mean(), pearson.mean() - REF_R_MEAN,
     "PASS" if abs(pearson.mean() - REF_R_MEAN) <= TOL else "FAIL"))
P("")

# ---- Spearman ----
spearman = per_param_spearman(sigma_current, err)
P("## Spearman(sigma, |error|)")
P("")
P("| param | frozen reference | reproduced | diff |")
P("|---|---|---|---|")
for i in range(9):
    d = spearman[i] - REF_SP[i]
    p = "PASS" if abs(d) <= TOL_SP else "FAIL"
    if p == "FAIL":
        ok = False
    P("| %-10s | %.4f | %.4f | %+.4f | %s |" % (PARAM_SHORT[i], REF_SP[i], spearman[i], d, p))
P("| **mean** | **%.4f** | **%.4f** | %+.4f | %s |"
  % (REF_SP_MEAN, spearman.mean(), spearman.mean() - REF_SP_MEAN,
     "PASS" if abs(spearman.mean() - REF_SP_MEAN) <= TOL_SP else "FAIL"))
P("")

# ---- Coverage ----
levels = sorted(NOMINAL.keys())
lo, hi = gaussian_intervals(mu_current, sigma_current)
cov = coverage_at_levels(params_test, lo, hi)
P("## Empirical coverage (z_mean Gaussian intervals)")
P("")
P("| param | 50%% | 80%% | 90%% | 95%% |")
P("|---|---|---|---|---|")
for i in range(9):
    P("| %-10s | %.4f | %.4f | %.4f | %.4f |" % (PARAM_SHORT[i], cov[i, 0], cov[i, 1], cov[i, 2], cov[i, 3]))
P("")
P("95%% coverage range reproduced: [%.4f, %.4f] (reference [0.9464, 0.9692])"
  % (cov[:, -1].min(), cov[:, -1].max()))
cov_ok = all(abs(cov[i, -1] - REF_COV95[i]) <= TOL_COV for i in range(9))
P("95%% coverage per-parameter match: %s" % ("PASS" if cov_ok else "FAIL"))
if not cov_ok:
    ok = False
P("")

# ---- KL consistency ----
per_dim_kl = 0.5 * (z_mean ** 2 + np.exp(z_log_var) - 1 - z_log_var)
total_kl = per_dim_kl.sum(axis=1)
P("## Encoder KL (test set)")
P("")
P("- mean per-sample total KL over test: **%.3f nats** (frozen training history final: 51.40)" % total_kl.mean())
P("- per-dim mean KL: " + "  ".join("%.3f" % v for v in per_dim_kl.mean(axis=0)))
P("")

P("## Verdict")
P("")
if ok and cov_ok:
    P("**PASS — frozen model reproduces all reference numbers (|Δ| ≤ %.4f).**" % TOL)
    P("Proceed to the Monte-Carlo convergence gate.")
else:
    P("**FAIL — STOP.** A discrepancy exists; do not proceed until resolved.")
    sys.exit(1)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print("\nsaved:", OUT)
