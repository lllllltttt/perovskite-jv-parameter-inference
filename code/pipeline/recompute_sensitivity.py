"""
FINAL_PRECISION_FIX — TASK 1 / TASK 9
Recompute the parameter->J-V sensitivity index from the REAL test set.

Definition (both versions share the same linear, voltage-averaged, absolute Pearson form):

  S_i  = (1/N_V) * sum_{V} | Pearson(theta_i , J(V)) |

Two parameter-space versions are computed on the SAME test set (N=15,307):
  S_raw : theta_i in raw physical units (mA/cm2 for J, physical units for theta)
  S_log : theta_i in log10 space (log10 of raw physical values)

Notes
-----
* Pearson correlation is invariant to per-column affine transforms, so computing J(V)
  in raw (mA/cm2) or in normalized [0,1] columns gives IDENTICAL S values. We compute
  on the raw physical J (J_test_raw) and verify the invariance numerically.
* The normalized-log parameter matrix params_test IS an affine transform of log10(theta_raw)
  (log10 -> per-parameter MinMax, fitted on all 102,046 retained samples), so
  Pearson(log10 theta, J) == Pearson(normalized-log theta, J) exactly. We use log10(theta_raw).
* The old hardcoded array in script/uncertain_predict.py (0.015-0.259) came from
  JV-sensitive-score.py run on the FULL retained CSV in RAW physical space (Linux path
  /home/student2/result-csv/JV_database_9D_interface_lifetimes-2.csv, not available on this
  machine). It is superseded by this test-set recomputation. Raw-space values are reported
  here for continuity; the manuscript adopts the log-space version (see summary).
"""

import os
import numpy as np
import pandas as pd
from scipy import stats

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NPZ = os.path.join(BASE, "data", "dataset_normalized.npz")
OUTDIR = os.path.join(BASE, "sensitivity_recomputed")
os.makedirs(OUTDIR, exist_ok=True)

npz = np.load(NPZ, allow_pickle=True)
param_names = [str(n) for n in npz["param_names"]]          # canonical order
J_test_raw  = npz["J_test_raw"].astype(float)               # (15307, 131) mA/cm2
P_raw       = npz["params_test_raw"].astype(float)          # (15307, 9) physical units
P_log       = np.log10(P_raw)                               # log10 space
J_test_norm = npz["J_test"].astype(float)                   # normalized J (for invariance check)

N, N_V = J_test_raw.shape
assert P_raw.shape[0] == N and P_raw.shape[1] == 9


def sensitivity(P, J):
    """S_i = (1/N_V) * sum_V |Pearson(theta_i, J(V))|  over the given samples."""
    corr = np.empty((J.shape[1], P.shape[1]))
    for v in range(J.shape[1]):
        jv = J[:, v]
        for i in range(P.shape[1]):
            corr[v, i] = np.corrcoef(P[:, i], jv)[0, 1]
    return np.mean(np.abs(corr), axis=0)


def pearson_matrix(P, J):
    """Full |Pearson| matrix, voltage x parameter (for the traceability record)."""
    corr = np.empty((J.shape[1], P.shape[1]))
    for v in range(J.shape[1]):
        jv = J[:, v]
        for i in range(P.shape[1]):
            corr[v, i] = np.corrcoef(P[:, i], jv)[0, 1]
    return np.abs(corr)


# ---- main recomputation on the test set ----
S_raw = sensitivity(P_raw, J_test_raw)
S_log = sensitivity(P_log, J_test_raw)

# ---- verify affine invariance of the J representation ----
S_log_normJ = sensitivity(P_log, J_test_norm)
S_raw_normJ = sensitivity(P_raw, J_test_norm)
aff_err_log = float(np.max(np.abs(S_log - S_log_normJ)))
aff_err_raw = float(np.max(np.abs(S_raw - S_raw_normJ)))
assert aff_err_log < 1e-12 and aff_err_raw < 1e-12, "affine invariance violated"

# ---- ranks (1 = most sensitive) ----
rank_raw = stats.rankdata(-S_raw).astype(int)
rank_log = stats.rankdata(-S_log).astype(int)

# ---- recoverability (Pearson r, test set, normalized log space) - Eval Table 2 ----
r_rec = np.array([0.9063, 0.9194, 0.8783, 0.8808, 0.9090,
                  0.8956, 0.5936, 0.7199, 0.5592])  # canonical order (mu_n, mu_p, tau_n, tau_p, Nc, Nv, tau_ETL, tau_HTL, rad_c)

rho_raw, p_raw = stats.spearmanr(S_raw, r_rec)
rho_log, p_log = stats.spearmanr(S_log, r_rec)

# ---- CSV ----
df = pd.DataFrame({
    "parameter": param_names,
    "S_raw": S_raw,
    "S_log": S_log,
    "rank_raw": rank_raw,
    "rank_log": rank_log,
    "r_recoverability": r_rec,
})
csv_path = os.path.join(OUTDIR, "sensitivity_recomputed.csv")
df.to_csv(csv_path, index=False, float_format="%.6f")

# ---- old hardcoded values (from uncertain_predict.py; note tau_p BEFORE tau_n there) ----
# order in the old array: mu_n, mu_p, tau_p, tau_n, Nc, Nv, tau_ETL, tau_HTL, rad_c
old = {
    "mu_n_pvk": 0.259256, "mu_p_pvk": 0.258027, "tau_p_pvk": 0.146627,
    "tau_n_pvk": 0.139511, "Nc_eff_pvk": 0.125126, "Nv_eff_pvk": 0.136556,
    "tau_ETL": 0.015462, "tau_HTL": 0.026015, "rad_c": 0.032587,
}
old_arr = np.array([old[n] for n in param_names])

# ---- summary text ----
lines = []
lines.append("SENSITIVITY RECOMPUTATION  (FINAL_PRECISION_FIX TASK 1/9)")
lines.append("=" * 72)
lines.append("")
lines.append("Data:        data/dataset_normalized.npz")
lines.append("Split:       TEST SET ONLY (N = 15,307)  -- consistent with recoverability metrics")
lines.append("             (old values came from the FULL 102,046 retained dataset; the full raw CSV")
lines.append("              lives at a Linux path and is not reproducible on this machine)")
lines.append("Voltages:    131 points, V = {0, 0.01, ..., 1.3} V")
lines.append("J resp.:     J_test_raw, physical mA/cm2 (Pearson is invariant to the per-column")
lines.append("             MinMax normalization; verified numerically, max |delta| = %.1e)" % aff_err_log)
lines.append("")
lines.append("Definitions:")
lines.append("  S_raw  = (1/131) * sum_V | Pearson(theta_raw_i, J(V)) |")
lines.append("  S_log  = (1/131) * sum_V | Pearson(log10(theta_raw_i), J(V)) |")
lines.append("  Pearson via numpy corrcoef; |.| then mean over V. Both on the SAME test set.")
lines.append("  Note: params_test (normalized-log) is an affine transform of log10(theta_raw);")
lines.append("  Pearson is affine-invariant, so Pearson(normalized-log theta, J) == Pearson(log10 theta, J).")
lines.append("")
lines.append(f"{'parameter':<14}{'S_raw':>10}{'S_log':>10}{'rank_raw':>9}{'rank_log':>9}{'r_rec':>9}{'S_old(full,raw)':>16}")
lines.append("-" * 72)
for i, n in enumerate(param_names):
    lines.append(f"{n:<14}{S_raw[i]:>10.4f}{S_log[i]:>10.4f}{rank_raw[i]:>9d}{rank_log[i]:>9d}{r_rec[i]:>9.4f}{old_arr[i]:>16.4f}")
lines.append("")
lines.append("OLD vs NEW (raw-space) comparison on shared params:")
lines.append("  old (full dataset, raw)  vs new (test set, raw):")
lines.append("  correlation across the 9 params: r = %.4f" % np.corrcoef(old_arr, S_raw)[0, 1])
lines.append("")
lines.append("Spearman(S, recoverability r)  -- 9 params, test set:")
lines.append("  S_raw  vs r_rec:  rho = %.3f, p = %.4f" % (rho_raw, p_raw))
lines.append("  S_log  vs r_rec:  rho = %.3f, p = %.4f" % (rho_log, p_log))
lines.append("")
lines.append("ADOPTED VERSION:  S_log (log10 parameter space).")
lines.append("  Rationale: the model is trained and evaluated in normalized-log10 parameter space")
lines.append("  (log_transform_mask all True; pre-processing applies log10 before MinMax); the latent")
lines.append("  parameters span decades (mu_n 4.9e-7..2.2e-3, tau 4.5e-10..2e-2, N 4.5e22..2.2e26);")
lines.append("  a correlation in log space therefore measures sensitivity on the scale the network")
lines.append("  actually uses, whereas S_raw is dominated by the largest absolute parameter.")
lines.append("  Ranks largely agree between the two versions (see CSV); the log-space version is the")
lines.append("  scientifically meaningful one and is reported in the manuscript.")

with open(os.path.join(OUTDIR, "sensitivity_recomputed_summary.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

# ---- also write the full |Pearson| matrix (V x param) for traceability ----
mat = pearson_matrix(P_log, J_test_raw)
np.savetxt(os.path.join(OUTDIR, "pearson_abs_matrix_log.csv"), mat, delimiter=",",
           header="V_rows," + ",".join(param_names), comments="", fmt="%.6f")

print("\n".join(lines))
