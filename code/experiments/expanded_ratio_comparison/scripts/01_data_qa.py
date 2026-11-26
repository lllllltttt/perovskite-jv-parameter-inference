# -*- coding: utf-8 -*-
"""Data acceptance (QA) for the expanded-ratio matched-comparison experiment.

Reads (read-only):
  E:/project/work1/20261021/JV_database_9D_interface_lifetimes-newratio.csv  (expanded)
  E:/project/work1/data/JV_database_9D_interface_lifetimes-2.csv             (original)

Writes under the experiment root:
  out/qa/*.csv, out/qa/qa_summary.json, docs/data_QA.md,
  figures/fig01_data_distributions.{png,pdf,svg}

No training, no COMSOL, no modification of any input file.
"""
import csv
import hashlib
import json
import os
import re

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out", "qa")
FIG = os.path.join(ROOT, "figures")
DOC = os.path.join(ROOT, "docs")
for d in (OUT, FIG, DOC):
    os.makedirs(d, exist_ok=True)

NEW_CSV = r"E:\project\work1\20261021\JV_database_9D_interface_lifetimes-newratio.csv"
OLD_CSV = r"E:\project\work1\data\JV_database_9D_interface_lifetimes-2.csv"

PARAM_COLS = ["mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk",
              "Nc_eff_pvk", "Nv_eff_pvk", "tau_ETL", "tau_HTL", "rad_c"]
J_COLS = ["J_%03d" % i for i in range(131)]

# Bounds used by the LHS generator (script/LHS.py) and by the expanded-ratio
# variant as declared in the task statement.
RATIO_OLD = (0.2, 5.0)
RATIO_NEW = (0.05, 20.0)
G_BOUNDS = {"g_mu": (1e-6, 1e-3), "g_tau": (1e-9, 1e-2), "g_D": (1e22, 1e26)}
INTERFACE_BOUNDS = {"tau_ETL": (1e-12, 1e-8), "tau_HTL": (1e-14, 1e-10)}
RAD_BOUNDS = (1e-12, 1e-9)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path):
    df = pd.read_csv(path)
    return df


def apply_filter(J):
    """The filter actually implemented in script/mat-csv.py, verbatim logic."""
    m1 = J[:, 0] > 0
    m2 = (np.diff(np.sign(J), axis=1) < 0).any(axis=1)
    m3 = np.all(np.isfinite(J), axis=1)
    m4 = np.all(np.diff(J, axis=1) <= 0.2, axis=1)
    return m1, m2, m3, m4


def reconstruct(P):
    mu_n, mu_p = P[:, 0], P[:, 1]
    tau_n, tau_p = P[:, 2], P[:, 3]
    Nc, Nv = P[:, 4], P[:, 5]
    g_mu = np.sqrt(mu_n * mu_p)
    g_tau = np.sqrt(tau_n * tau_p)
    g_D = np.sqrt(Nc * Nv)
    q_mu = mu_n / mu_p
    q_tau = tau_n / tau_p
    q_D = Nc / Nv
    return {"g_mu": g_mu, "g_tau": g_tau, "g_D": g_D,
            "q_mu": q_mu, "q_tau": q_tau, "q_D": q_D}


def lhs_unit(values, low, high, islog):
    if islog:
        return ((np.log10(values) - np.log10(low)) /
                (np.log10(high) - np.log10(low)))
    return (values - low) / (high - low)


def stratum_uniqueness(u, n):
    """Under a scrambled Latin hypercube with n strata each retained row falls in
    a different stratum, so floor(u*n) is unique (up to floating-point ties).
    Under i.i.d. uniform sampling many rows share a stratum.  The fraction of
    unique strata is therefore a direct test of the LHS stratum count n."""
    f = np.floor(u * n).astype(np.int64)
    return float(len(np.unique(f)) / f.size), f


def quantile_table(v, name):
    qs = [0, 1, 5, 25, 50, 75, 95, 99, 100]
    p = np.percentile(v, qs)
    return {"quantity": name, "n": int(v.size), "mean": float(np.mean(v)),
            "std": float(np.std(v, ddof=1)),
            **{"p%d" % q: float(x) for q, x in zip(qs, p)}}


def main():
    rows = []
    summary = {}

    print("hashing inputs ...")
    h_new, h_old = sha256(NEW_CSV), sha256(OLD_CSV)
    new, old = load(NEW_CSV), load(OLD_CSV)
    print("new", new.shape, "old", old.shape)

    checks = []

    def check(name, ok, detail=""):
        checks.append({"check": name, "status": "PASS" if ok else "FAIL",
                       "detail": detail})
        print(("PASS " if ok else "FAIL ") + name + ("  " + detail if detail else ""))

    # ---------------------------------------------------------------- schema
    check("column list identical between batches", list(new.columns) == list(old.columns))
    check("131 current columns in order J_000..J_130",
          [c for c in new.columns if c.startswith("J_")] == J_COLS and
          [c for c in old.columns if c.startswith("J_")] == J_COLS)
    check("9 parameter columns in canonical order",
          list(new.columns[1:10]) == PARAM_COLS)
    check("no duplicate column names", new.columns.is_unique and old.columns.is_unique)

    Pn = new[PARAM_COLS].to_numpy(float)
    Po = old[PARAM_COLS].to_numpy(float)
    Jn = new[J_COLS].to_numpy(float)
    Jo = old[J_COLS].to_numpy(float)

    check("new: all J finite", bool(np.isfinite(Jn).all()))
    check("new: all parameters finite", bool(np.isfinite(Pn).all()))
    check("new: all parameters positive", bool((Pn > 0).all()))
    check("old: all J finite", bool(np.isfinite(Jo).all()))
    check("old: all parameters finite", bool(np.isfinite(Po).all()))
    check("old: all parameters positive", bool((Po > 0).all()))

    # ------------------------------------------------------------- filter
    for nm, J in (("new", Jn), ("old", Jo)):
        m1, m2, m3, m4 = apply_filter(J)
        kept = m1 & m2 & m3 & m4
        detail = ("kept %d/%d; rejected by rule1=%d rule2=%d rule3=%d rule4=%d"
                  % (kept.sum(), len(J), (~m1).sum(), (~m2).sum(),
                     (~m3).sum(), (~m4).sum()))
        check("%s: delivered rows already satisfy the actual filter" % nm,
              bool(kept.all()), detail)
        summary.setdefault("filter", {})[nm] = {
            "n_rows": int(len(J)), "n_kept": int(kept.sum()),
            "rule1_first_current_gt0": int(m1.sum()),
            "rule2_any_negative_sign_change": int(m2.sum()),
            "rule3_all_finite": int(m3.sum()),
            "rule4_all_adjacent_steps_le_0p2": int(m4.sum()),
        }

    # ------------------------------------------------------------ identifier
    ids_new = new["Sample_ID"].to_numpy()
    ids_old = old["Sample_ID"].to_numpy()
    check("new: Sample_ID unique", bool(pd.Series(ids_new).is_unique),
          "n=%d range=%d..%d" % (len(ids_new), ids_new.min(), ids_new.max()))
    check("old: Sample_ID unique", bool(pd.Series(ids_old).is_unique),
          "n=%d range=%d..%d" % (len(ids_old), ids_old.min(), ids_old.max()))
    check("new: Sample_ID within declared 1..50000",
          bool(ids_new.min() >= 1 and ids_new.max() <= 50000))
    check("old: Sample_ID within declared 1..200000",
          bool(ids_old.min() >= 1 and ids_old.max() <= 200000))
    summary["ids"] = {
        "expanded": {"n": int(len(ids_new)), "min": int(ids_new.min()),
                     "max": int(ids_new.max()), "unique": int(len(np.unique(ids_new))),
                     "declared_submitted": 50000, "declared_mat_files": 49999,
                     "absent_ids": int(50000 - len(np.unique(ids_new)))},
        "original": {"n": int(len(ids_old)), "min": int(ids_old.min()),
                     "max": int(ids_old.max()), "unique": int(len(np.unique(ids_old))),
                     "declared_submitted": 200000,
                     "absent_ids": int(200000 - len(np.unique(ids_old)))},
    }

    # ------------------------------------------------------- duplicates
    def dup_report(P, J, label):
        from collections import Counter
        pv = Counter(map(tuple, P))
        dup_param_rows = int(sum(v - 1 for v in pv.values() if v > 1))
        jh = [hashlib.md5(np.ascontiguousarray(r).tobytes()).hexdigest() for r in J]
        jc = Counter(jh)
        dup_j_rows = int(sum(v - 1 for v in jc.values() if v > 1))
        check("%s: no exact duplicate parameter vectors" % label, dup_param_rows == 0,
              "%d duplicate rows" % dup_param_rows)
        check("%s: no byte-identical current curves" % label, dup_j_rows == 0,
              "%d duplicate rows" % dup_j_rows)
        return {"duplicate_parameter_rows": dup_param_rows,
                "duplicate_curve_rows": dup_j_rows}

    summary["duplicates"] = {
        "expanded": dup_report(Pn, Jn, "new"),
        "original": dup_report(Po, Jo, "old"),
    }

    # cross-batch duplicate parameter vectors (rounded to 8 significant digits,
    # because the two files were written with different numeric precision)
    def sigkey(P, sig=8):
        out = []
        for r in P:
            out.append(tuple(float("%.*e" % (sig - 1, v)) for v in r))
        return out
    inter = set(sigkey(Pn)) & set(sigkey(Po))
    summary["duplicates"]["cross_batch_parameter_vectors_8sig"] = int(len(inter))
    check("no cross-batch duplicate parameter vectors (8 s.f.)", len(inter) == 0,
          "%d shared vectors" % len(inter))

    # ------------------------------------------------------- reconstruction
    Rn, Ro = reconstruct(Pn), reconstruct(Po)
    dist_rows = []
    for k in ("g_mu", "g_tau", "g_D", "q_mu", "q_tau", "q_D"):
        for arm, R in (("expanded", Rn), ("original", Ro)):
            row = quantile_table(R[k], k)
            row["arm"] = arm
            row["dataset_id"] = "exp50k" if arm == "expanded" else "orig200k"
            dist_rows.append(row)
    for col, arr_n, arr_o, name in (
            ("tau_ETL", Pn[:, 6], Po[:, 6], "tau_ETL"),
            ("tau_HTL", Pn[:, 7], Po[:, 7], "tau_HTL"),
            ("rad_c", Pn[:, 8], Po[:, 8], "rad_c")):
        dist_rows.append({**quantile_table(arr_n, name), "arm": "expanded",
                          "dataset_id": "exp50k"})
        dist_rows.append({**quantile_table(arr_o, name), "arm": "original",
                          "dataset_id": "orig200k"})
    ddf = pd.DataFrame(dist_rows)[
        ["dataset_id", "arm", "quantity", "n", "mean", "std",
         "p0", "p1", "p5", "p25", "p50", "p75", "p95", "p99", "p100"]]
    ddf.to_csv(os.path.join(OUT, "distribution_quantiles.csv"), index=False)

    # ------------------------------------------------------- q-bin shares
    bin_rows = []
    for k in ("q_mu", "q_tau", "q_D"):
        for arm, R in (("expanded", Rn), ("original", Ro)):
            q = R[k]
            bin_rows.append({
                "arm": arm, "quantity": k, "n": int(q.size),
                "share_lt_0.2": float(np.mean(q < 0.2)),
                "share_0.2_to_5": float(np.mean((q >= 0.2) & (q <= 5.0))),
                "share_gt_5": float(np.mean(q > 5.0)),
                "share_lt_0.05": float(np.mean(q < 0.05)),
                "share_gt_20": float(np.mean(q > 20.0)),
            })
    bdf = pd.DataFrame(bin_rows)
    bdf.to_csv(os.path.join(OUT, "ratio_bin_shares.csv"), index=False)

    all_old_range = {}
    for arm, R in (("expanded", Rn), ("original", Ro)):
        inr = ((R["q_mu"] >= 0.2) & (R["q_mu"] <= 5) &
               (R["q_tau"] >= 0.2) & (R["q_tau"] <= 5) &
               (R["q_D"] >= 0.2) & (R["q_D"] <= 5))
        all_old_range[arm] = {"n_all_three_in_old_range": int(inr.sum()),
                              "share": float(np.mean(inr))}
    summary["all_three_ratios_in_old_range"] = all_old_range

    # ------------------------------------------------------- LHS grid test
    grid_rows = []
    n_lhs = 50000
    tests = [
        ("q_mu", Rn["q_mu"], RATIO_NEW[0], RATIO_NEW[1], False),
        ("q_tau", Rn["q_tau"], RATIO_NEW[0], RATIO_NEW[1], False),
        ("q_D", Rn["q_D"], RATIO_NEW[0], RATIO_NEW[1], False),
        ("tau_ETL", Pn[:, 6], INTERFACE_BOUNDS["tau_ETL"][0], INTERFACE_BOUNDS["tau_ETL"][1], True),
        ("tau_HTL", Pn[:, 7], INTERFACE_BOUNDS["tau_HTL"][0], INTERFACE_BOUNDS["tau_HTL"][1], True),
        ("rad_c", Pn[:, 8], RAD_BOUNDS[0], RAD_BOUNDS[1], True),
        ("g_mu", Rn["g_mu"], *G_BOUNDS["g_mu"], True),
        ("g_tau", Rn["g_tau"], *G_BOUNDS["g_tau"], True),
        ("g_D", Rn["g_D"], *G_BOUNDS["g_D"], True),
    ]
    # stratum-count discrimination: the true LHS size must maximise uniqueness
    cand_n = [10000, 20000, 25000, 30000, 40000, 45000, 50000, 55000, 60000, 100000]
    disc_rows = []
    for name, v, lo, hi, islog in tests:
        u = lhs_unit(v, lo, hi, islog)
        row = {"dimension": name, "bounds": "[%g, %g]" % (lo, hi)}
        for n in cand_n:
            row["uniq_%d" % n] = stratum_uniqueness(u, n)[0]
        disc_rows.append(row)
    pd.DataFrame(disc_rows).to_csv(
        os.path.join(OUT, "lhs_stratum_count_discrimination.csv"), index=False)

    for name, v, lo, hi, islog in tests:
        u = lhs_unit(v, lo, hi, islog)
        frac, f = stratum_uniqueness(u, n_lhs)
        grid_rows.append({
            "dimension": name, "n": int(v.size), "bounds": "[%g, %g]" % (lo, hi),
            "u_min": float(u.min()), "u_max": float(u.max()),
            "unique_strata_at_50000": int(len(np.unique(f))),
            "fraction_unique_at_50000": frac,
            "expected_fraction_if_iid_uniform": float(
                1.0 - (1.0 - 1.0 / n_lhs) ** v.size),
            "median_within_stratum_offset": float(
                np.median(u * n_lhs - np.floor(u * n_lhs))),
            "bounds_respected": bool(u.min() >= -1e-9 and u.max() <= 1.0 + 1e-9),
        })
    gdf = pd.DataFrame(grid_rows)
    gdf.to_csv(os.path.join(OUT, "lhs_grid_recovery.csv"), index=False)
    summary["lhs_stratum_test"] = gdf.to_dict(orient="records")

    # ------------------------------------------------------- unit checks
    unit = {
        "new_rad_c_min": float(Pn[:, 8].min()), "new_rad_c_max": float(Pn[:, 8].max()),
        "old_rad_c_min": float(Po[:, 8].min()), "old_rad_c_max": float(Po[:, 8].max()),
        "rad_c_within_sampling_range": bool(
            (Pn[:, 8].min() >= 1e-12) and (Pn[:, 8].max() <= 1e-9)),
        "rad_c_would_be_1e-18_if_extra_1e-6_applied": bool(
            Pn[:, 8].max() < 1e-15),
        "new_Jsc_range_mA_cm2": [float(Jn[:, 0].min()), float(Jn[:, 0].max())],
        "old_Jsc_range_mA_cm2": [float(Jo[:, 0].min()), float(Jo[:, 0].max())],
        "new_J_global": [float(Jn.min()), float(Jn.max())],
        "old_J_global": [float(Jo.min()), float(Jo.max())],
        "n_voltage_points": int(len(J_COLS)),
    }
    check("rad_c stored as pre-MATLAB raw value (inside 1e-12..1e-9)",
          unit["rad_c_within_sampling_range"],
          "[%.3e, %.3e]" % (unit["new_rad_c_min"], unit["new_rad_c_max"]))
    check("current magnitudes consistent with mA/cm2 after x0.1 conversion",
          bool(Jn[:, 0].max() < 100 and Jo[:, 0].max() < 100),
          "Jsc max new=%.3f old=%.3f" % (Jn[:, 0].max(), Jo[:, 0].max()))
    summary["units"] = unit

    # --------------------------------------------------- parameter precision
    def decimals(P):
        # count significant digits actually stored, by round-tripping the text
        return None
    # numeric precision comparison (recorded, not a failure)
    def max_sig(v):
        s = ["%.17g" % x for x in v[:1000]]
        return max(len(re.sub(r"[^0-9]", "", t.split("e")[0]).lstrip("0")) for t in s)
    summary["stored_precision"] = {"new": max_sig(Pn[:, 0]),
                                   "old": max_sig(Po[:, 0])}

    # ------------------------------------------------------------ figures
    Ok = ["#0072B2", "#D55E00"]
    fig, axes = plt.subplots(2, 3, figsize=(11.0, 6.2))
    gkeys = ["g_mu", "g_tau", "g_D"]
    glab = {"g_mu": "log$_{10}$ $g_\\mu$  (m$^2$ V$^{-1}$ s$^{-1}$)",
            "g_tau": "log$_{10}$ $g_\\tau$  (s)",
            "g_D": "log$_{10}$ $g_D$  (m$^{-3}$)"}
    qlab = {"q_mu": "mobility ratio  $q_\\mu$",
            "q_tau": "lifetime ratio  $q_\\tau$",
            "q_D": "DOS ratio  $q_D$"}
    for j, k in enumerate(gkeys):
        ax = axes[0, j]
        lo = np.log10(min(Ro[k].min(), Rn[k].min()))
        hi = np.log10(max(Ro[k].max(), Rn[k].max()))
        bins = np.linspace(lo, hi, 60)
        ax.hist(np.log10(Ro[k]), bins=bins, density=True, histtype="step",
                lw=1.6, color=Ok[0],
                label="original 0.2–5 (n=%d)" % Po.shape[0])
        ax.hist(np.log10(Rn[k]), bins=bins, density=True, histtype="step",
                lw=1.6, color=Ok[1],
                label="expanded 0.05–20 (n=%d)" % Pn.shape[0])
        ax.set_xlabel(glab[k])
        ax.set_ylabel("probability density (per decade)")
        ax.tick_params(labelsize=8)
        if j == 0:
            ax.legend(fontsize=7, frameon=False)
    from matplotlib.patches import Patch
    for j, k in enumerate(["q_mu", "q_tau", "q_D"]):
        ax = axes[1, j]
        bins = np.linspace(0.0, 21.0, 85)
        ax.hist(Ro[k], bins=bins, density=True, histtype="step", lw=1.6,
                color=Ok[0], label="original 0.2–5")
        ax.hist(Rn[k], bins=bins, density=True, histtype="step", lw=1.6,
                color=Ok[1], label="expanded 0.05–20")
        ax.axvspan(0.2, 5.0, color="#999999", alpha=0.12, lw=0)
        ax.set_xlim(0, 21)
        ax.set_ylim(0, 0.24)
        ax.set_xlabel(qlab[k])
        ax.set_ylabel("probability density")
        ax.tick_params(labelsize=8)
        if j == 0:
            ax.legend(handles=[Patch(color="#999999", alpha=0.35,
                                     label="old ratio range 0.2–5")],
                      fontsize=7, frameon=False, loc="upper right")
    fig.tight_layout()
    for ext in ("png", "pdf", "svg"):
        fig.savefig(os.path.join(FIG, "fig01_data_distributions." + ext),
                    dpi=300, facecolor="white")
    plt.close(fig)

    # ------------------------------------------------------------ summary
    summary["inputs"] = {
        "expanded_csv": {"path": NEW_CSV, "sha256": h_new, "shape": list(new.shape)},
        "original_csv": {"path": OLD_CSV, "sha256": h_old, "shape": list(old.shape)},
        "dataset_id": {"expanded": "exp50k", "original": "orig200k"},
    }
    summary["checks"] = checks
    summary["n_fail"] = int(sum(c["status"] == "FAIL" for c in checks))
    with open(os.path.join(OUT, "qa_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    with open(os.path.join(OUT, "qa_checks.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["check", "status", "detail"])
        w.writeheader()
        w.writerows(checks)

    print("\nFAILURES:", summary["n_fail"])
    return summary


if __name__ == "__main__":
    main()
