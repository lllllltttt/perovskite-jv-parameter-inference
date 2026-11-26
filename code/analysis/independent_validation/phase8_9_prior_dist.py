# -*- coding: utf-8 -*-
"""
Phase 8 + 9 — PRIOR-COORDINATE REPLICATION + DISTRIBUTION COMPARISON
Independent dataset validation of frozen VAE-v6.

Phase 8: reproduce the Exp3 coordinate decomposition on the independent
predictions (same formulas, same log10-physical space, frozen scaler inversion).
  a = 0.5*(log10 p_n + log10 p_p);  r = log10 p_n - log10 p_p
Reference (Exp3, frozen test N=15307): a_mu 0.9250, a_tau 0.8819, a_D 0.9248,
r_mu 0.4289, r_tau 0.3517, r_D 0.2663.

Phase 9: distribution comparison old retained vs new independent (no COMSOL).

Outputs:
  independent_validation/independent_prior_coordinate_recovery.csv
  independent_validation/original_vs_independent_summary.csv
"""
import os, csv, pickle
import numpy as np
import pandas as pd
from scipy.stats import pearsonr

BASE = r"E:\project\work1"
OUT = os.path.join(BASE, "independent_validation")
OLD = os.path.join(BASE, "data", "JV_database_9D_interface_lifetimes-2.csv")
NEW = os.path.join(BASE, "data", "JV_database_9D_interface_lifetimes-3.csv")

PARAM_NAMES = ["mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk",
               "Nc_eff_pvk", "Nv_eff_pvk", "tau_ETL", "tau_HTL", "rad_c"]
SHORT = ["mu_n", "mu_p", "tau_n", "tau_p", "Nc", "Nv", "tau_ETL", "tau_HTL", "rad_c"]
COORDS = ["a_mu", "r_mu", "a_tau", "r_tau", "a_D", "r_D"]
ORIG_COORD = {"a_mu": 0.9250, "r_mu": 0.4289,
              "a_tau": 0.8819, "r_tau": 0.3517,
              "a_D": 0.9248, "r_D": 0.2663}

# ----------------------------------------------------------------------
# Phase 8 — coordinate recovery
# ----------------------------------------------------------------------
d = np.load(os.path.join(OUT, "preprocessed_independent.npz"))
P_norm = d["P_norm"].astype(np.float64)

pred_df = pd.read_csv(os.path.join(OUT, "independent_predictions.csv"))
mu_norm = pred_df[[("pred_norm_%s" % c) for c in PARAM_NAMES]].values.astype(np.float64)

with open(os.path.join(BASE, "data", "param_scaler.pkl"), "rb") as f:
    psc = pickle.load(f)["scaler"]

def norm_to_log10(norm):
    return np.asarray(norm, np.float64) * psc.data_range_ + psc.data_min_

true_L = norm_to_log10(P_norm)
pred_L = norm_to_log10(mu_norm)

def coords(L):
    return np.column_stack([
        0.5 * (L[:, 0] + L[:, 1]), L[:, 0] - L[:, 1],
        0.5 * (L[:, 2] + L[:, 3]), L[:, 2] - L[:, 3],
        0.5 * (L[:, 4] + L[:, 5]), L[:, 4] - L[:, 5],
    ])

C_true = coords(true_L)
C_pred = coords(pred_L)

print("===== PHASE 8 — PRIOR-COORDINATE RECOVERABILITY =====")
print("%-6s %10s %10s %10s" % ("coord", "orig r", "indep r", "delta"))
rows = []
for i, c in enumerate(COORDS):
    r, _ = pearsonr(C_true[:, i], C_pred[:, i])
    orig = ORIG_COORD[c]
    delta = r - orig
    rows.append((c, orig, float(r), delta))
    print("%-6s %10.4f %10.4f %+10.4f" % (c, orig, r, delta))

with open(os.path.join(OUT, "independent_prior_coordinate_recovery.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["coordinate", "type", "original_pearson", "independent_pearson",
                "delta_pearson"])
    for c, orig, r, delta in rows:
        w.writerow([c, "shared_scale" if c.startswith("a_") else "ratio",
                    "%.4f" % orig, "%.4f" % r, "%+.4f" % delta])

print("\nShared-scale recovery: mean orig=%.4f indep=%.4f" %
      (np.mean([ORIG_COORD[c] for c in COORDS if c.startswith("a_")]),
       np.mean([r for c, _, r, _ in rows if c.startswith("a_")])))
print("Ratio recovery       : mean orig=%.4f indep=%.4f" %
      (np.mean([ORIG_COORD[c] for c in COORDS if c.startswith("r_")]),
       np.mean([r for c, _, r, _ in rows if c.startswith("r_")])))
gap_orig = np.mean([ORIG_COORD[c] for c in COORDS if c.startswith("a_")]) - \
           np.mean([ORIG_COORD[c] for c in COORDS if c.startswith("r_")])
gap_ind = np.mean([r for c, _, r, _ in rows if c.startswith("a_")]) - \
          np.mean([r for c, _, r, _ in rows if c.startswith("r_")])
print("shared-minus-ratio gap: orig=%.4f  indep=%.4f" % (gap_orig, gap_ind))

# ----------------------------------------------------------------------
# Phase 9 — distribution comparison (old retained vs new)
# ----------------------------------------------------------------------
print("\n===== PHASE 9 — DISTRIBUTION COMPARISON (old retained vs new) =====")

def load_raw(path):
    return pd.read_csv(path)

old = load_raw(OLD)
new = load_raw(NEW)
J_old = old[[c for c in old.columns if c.startswith("J_")]].values.astype(np.float64)
J_new = new[[c for c in new.columns if c.startswith("J_")]].values.astype(np.float64)
P_old = old[PARAM_NAMES].values.astype(np.float64)
P_new = new[PARAM_NAMES].values.astype(np.float64)

print("\nParameter log10 distributions (median / IQR / min / max):")
sum_rows = []
for i, c in enumerate(PARAM_NAMES):
    lo = np.log10(P_old[:, i]); ln = np.log10(P_new[:, i])
    def stats(x):
        return (np.median(x), np.percentile(x, 25), np.percentile(x, 75),
                x.min(), x.max())
    so, sn = stats(lo), stats(ln)
    sum_rows.append(dict(kind="param", name=c,
                         old_median=so[0], old_q25=so[1], old_q75=so[2], old_min=so[3], old_max=so[4],
                         new_median=sn[0], new_q25=sn[1], new_q75=sn[2], new_min=sn[3], new_max=sn[4]))
    print("  %-10s old med=%.3f IQR=[%.3f,%.3f] min=%.3f max=%.3f"
          % (c, so[0], so[1], so[2], so[3], so[4]))
    print("  %-10s new med=%.3f IQR=[%.3f,%.3f] min=%.3f max=%.3f"
          % ("", sn[0], sn[1], sn[2], sn[3], sn[4]))
    print("  %-10s med shift=%+.3f  IQR shift=%+.3f/%+.3f"
          % ("", sn[0] - so[0], sn[1] - so[1], sn[2] - so[2]))
    print()

# J-V observables
def voc(J):
    V = np.linspace(0, 1.3, 131)
    out = np.full(J.shape[0], np.nan)
    for n in range(J.shape[0]):
        idx = np.where(np.diff(np.sign(J[n])))[0]
        if len(idx) == 0:
            continue
        i = idx[0]
        out[n] = np.interp(0, [J[n, i], J[n, i + 1]], [V[i], V[i + 1]])
    return out

V = np.linspace(0, 1.3, 131)
Jsc_o = J_old[:, 0]; Jsc_n = J_new[:, 0]
Voc_o = voc(J_old);  Voc_n = voc(J_new)

def brief(name, a, b):
    print("  %-12s old: median=%.3f  [%.3f, %.3f]    new: median=%.3f  [%.3f, %.3f]"
          % (name, np.nanmedian(a), np.nanpercentile(a, 5), np.nanpercentile(a, 95),
             np.nanmedian(b), np.nanpercentile(b, 5), np.nanpercentile(b, 95)))

print("\nJ-V observables:")
brief("Jsc (mA/cm2)", Jsc_o, Jsc_n)
brief("Voc (V)", Voc_o, Voc_n)
brief("J min (mA/cm2)", J_old.min(axis=1), J_new.min(axis=1))
brief("J max (mA/cm2)", J_old.max(axis=1), J_new.max(axis=1))
print("\n  (no PCE column present in either CSV; PCE comparison not applicable)")

for lbl, a, b in (("Jsc", Jsc_o, Jsc_n), ("Voc", Voc_o, Voc_n),
                  ("Jmin", J_old.min(axis=1), J_new.min(axis=1)),
                  ("Jmax", J_old.max(axis=1), J_new.max(axis=1))):
    sum_rows.append(dict(kind="J_observable", name=lbl,
                         old_median=float(np.nanmedian(a)),
                         old_q25=float(np.nanpercentile(a, 25)),
                         old_q75=float(np.nanpercentile(a, 75)),
                         old_min=float(np.nanpercentile(a, 0)),
                         old_max=float(np.nanpercentile(a, 100)),
                         new_median=float(np.nanmedian(b)),
                         new_q25=float(np.nanpercentile(b, 25)),
                         new_q75=float(np.nanpercentile(b, 75)),
                         new_min=float(np.nanpercentile(b, 0)),
                         new_max=float(np.nanpercentile(b, 100))))

with open(os.path.join(OUT, "original_vs_independent_summary.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["kind", "name", "old_median", "old_q25", "old_q75", "old_min", "old_max",
                "new_median", "new_q25", "new_q75", "new_min", "new_max",
                "delta_median", "delta_q25", "delta_q75"])
    for r in sum_rows:
        w.writerow([r["kind"], r["name"],
                    "%.6f" % r["old_median"], "%.6f" % r["old_q25"], "%.6f" % r["old_q75"],
                    "%.6f" % r["old_min"], "%.6f" % r["old_max"],
                    "%.6f" % r["new_median"], "%.6f" % r["new_q25"], "%.6f" % r["new_q75"],
                    "%.6f" % r["new_min"], "%.6f" % r["new_max"],
                    "%+.6f" % (r["new_median"] - r["old_median"]),
                    "%+.6f" % (r["new_q25"] - r["old_q25"]),
                    "%+.6f" % (r["new_q75"] - r["old_q75"])])

print("\nPhase 8+9 complete.")
