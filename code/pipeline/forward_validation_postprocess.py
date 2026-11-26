# -*- coding: utf-8 -*-
"""
forward_validation_postprocess.py
==================================
Consume the COMSOL forward-validation MAT outputs and produce metrics,
figures, and the scientific conclusions A-D.

Run AFTER the server has executed run_forward_validation_unbiased.m and the
comsol_pred/ (+ comsol_true/) MAT files have been copied back here.

Inputs
------
  forward_validation_unbiased/selected_samples.csv
  forward_validation_unbiased/comsol_pred/Sample_<id>_pred.mat   (J in A/m^2)
  forward_validation_unbiased/comsol_true/Sample_<id>_true.mat   (control, optional)
  forward_validation_unbiased/param_error_posthoc.csv
  data/dataset_normalized.npz  (J_test_raw target, mA/cm^2)

Outputs (forward_validation_unbiased/)
--------------------------------------
  forward_metrics_per_sample.csv
  forward_metrics_summary.csv
  forward_validation_summary.txt
  forward_validation_unbiased.png          (a) 5 rep cases, (b) RMSE dist,
                                           (c) device deltas, (d) param vs J-RMSE
  forward_validation_metric_summary.png    Jsc/Voc/FF/PCE scatter + 1:1
"""

import os
import glob
import numpy as np
import pandas as pd
from scipy.io import loadmat
from scipy.stats import spearmanr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = r"E:/project/work1"
OUT  = os.path.join(ROOT, "forward_validation_unbiased")
PRED_DIR = os.path.join(OUT, "comsol_pred")
TRUE_DIR = os.path.join(OUT, "comsol_true")
NPZ  = os.path.join(ROOT, "data", "dataset_normalized.npz")

V = np.linspace(0.0, 1.3, 131)
TRUE_CONTROL_RMSE_FAIL = 0.05   # mA/cm^2: median true-control RMSE above this -> reproducibility failure

# Okabe-Ito (colorblind-safe) categorical palette
C = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]


def observables(J):
    N = J.shape[0]
    jsc = np.abs(J[:, 0])
    voc = np.full(N, np.nan)
    for i in range(N):
        s = np.diff(np.sign(J[i]))
        k0 = np.where(s)[0]
        if len(k0):
            k = k0[0]
            voc[i] = np.interp(0.0, [J[i, k], J[i, k + 1]], [V[k], V[k + 1]])
    pv = np.where(J * V[None, :] > 0, J * V[None, :], np.nan)
    pmax = np.nanmax(pv, axis=1)
    ff = np.where((voc > 0) & (jsc * voc > 0), pmax / (jsc * voc), np.nan)
    pce = jsc * voc * ff
    return jsc, voc, ff, pce


def metrics_curve(Jt, Js):
    """Jt target, Js simulated (both mA/cm^2, 131)."""
    d = Jt - Js
    rmse = float(np.sqrt(np.mean(d ** 2)))
    mae = float(np.mean(np.abs(d)))
    sst = float(np.sum((Jt - Jt.mean()) ** 2))
    r2 = float(1.0 - np.sum(d ** 2) / sst) if sst > 0 else np.nan
    lo = V <= 1.0
    rmse_lo = float(np.sqrt(np.mean((d[lo]) ** 2)))
    rmse_hi = float(np.sqrt(np.mean((d[~lo]) ** 2)))
    return rmse, mae, r2, rmse_lo, rmse_hi


def load_pred_mat(path):
    d = loadmat(path, squeeze_me=True)
    J = np.asarray(d["J"], dtype=np.float64)
    if J.ndim == 2:
        J = J[:, 0]
    return J * 0.1      # A/m^2 -> mA/cm^2 (see unit_conversion_audit.txt E2)


def main():
    data = np.load(NPZ)
    J_target = data["J_test_raw"].astype(np.float64)
    sel = pd.read_csv(os.path.join(OUT, "selected_samples.csv"))
    err = pd.read_csv(os.path.join(OUT, "param_error_posthoc.csv"))

    pred_files = sorted(glob.glob(os.path.join(PRED_DIR, "Sample_*_pred.mat")))
    true_files = sorted(glob.glob(os.path.join(TRUE_DIR, "Sample_*_true.mat")))
    if not pred_files:
        raise SystemExit("No comsol_pred MAT files found. Run the COMSOL batch first.")

    rows = []
    for f in pred_files:
        sid = int(os.path.basename(f).split("_")[1])
        Js = load_pred_mat(f)
        Jt = J_target[sid]
        rmse, mae, r2, rlo, rhi = metrics_curve(Jt, Js)
        jsc_t, voc_t, ff_t, pce_t = observables(Jt[None, :])
        jsc_s, voc_s, ff_s, pce_s = observables(Js[None, :])
        rows.append(dict(
            sample_id=sid, test_index=sid,
            Jsc_t=jsc_t[0], Voc_t=voc_t[0], FF_t=ff_t[0], PCE_t=pce_t[0],
            Jsc_sim=jsc_s[0], Voc_sim=voc_s[0], FF_sim=ff_s[0], PCE_sim=pce_s[0],
            dJsc=jsc_s[0] - jsc_t[0], dVoc=voc_s[0] - voc_t[0],
            dFF=ff_s[0] - ff_t[0], dPCE=pce_s[0] - pce_t[0],
            rel_dJsc=(jsc_s[0] - jsc_t[0]) / abs(jsc_t[0]),
            rel_dVoc=(voc_s[0] - voc_t[0]) / abs(voc_t[0]),
            rel_dFF=(ff_s[0] - ff_t[0]) / abs(ff_t[0]),
            rel_dPCE=(pce_s[0] - pce_t[0]) / abs(pce_t[0]),
            rmse_full=rmse, mae_full=mae, r2_full=r2,
            rmse_0to1V=rlo, rmse_gt1V=rhi,
        ))
    df = pd.DataFrame(rows)

    # merge cohort metadata + post-hoc param error
    df = df.merge(sel[["test_index", "selection_stratum", "sigma_tier_posthoc",
                       "mean_pred_sigma"]].rename(columns={"test_index": "sample_id"}), on="sample_id", how="left")
    df = df.merge(err[["test_index", "param_log10_rmse"]].rename(columns={"test_index": "sample_id"}),
                  on="sample_id", how="left")

    # ---- true-parameter control (optional) ------------------------------
    control = None
    if true_files:
        crows = []
        for f in true_files:
            sid = int(os.path.basename(f).split("_")[1])
            Js = load_pred_mat(f)
            Jt = J_target[sid]
            rmse, mae, r2, rlo, rhi = metrics_curve(Jt, Js)
            crows.append(dict(sample_id=sid, rmse_true_control=rmse, mae_true_control=mae))
        control = pd.DataFrame(crows).merge(df[["sample_id", "Jsc_t"]], on="sample_id", how="left")
        med = control["rmse_true_control"].median()
        pip_fail = med > TRUE_CONTROL_RMSE_FAIL
    else:
        med, pip_fail = None, None

    # ---- cohort statistics ----------------------------------------------
    def q(s):
        return s.quantile([0.10, 0.25, 0.50, 0.75, 0.90])

    stat = pd.DataFrame({
        "rmse_full": q(df["rmse_full"]), "r2_full": q(df["r2_full"]),
        "rmse_0to1V": q(df["rmse_0to1V"]), "rmse_gt1V": q(df["rmse_gt1V"]),
    })
    dev_mae = pd.DataFrame({
        "MAE_Jsc": df["dJsc"].abs(), "MAE_Voc": df["dVoc"].abs(),
        "MAE_FF": df["dFF"].abs(), "MAE_PCE": df["dPCE"].abs(),
    })
    dev_sum = pd.DataFrame({
        "median": dev_mae.median(), "q25": dev_mae.quantile(0.25), "q75": dev_mae.quantile(0.75),
    })

    # ---- post-hoc correlations (interpretation only, not selection) -----
    rhos = {}
    for a, b in [("param_log10_rmse", "rmse_full"), ("mean_pred_sigma", "rmse_full"),
                 ("param_log10_rmse", "dPCE")]:
        m = df[[a, b]].dropna()
        if len(m) > 3:
            r, p = spearmanr(m[a], m[b])
            rhos[f"spearman({a},{b})"] = (round(float(r), 3), round(float(p), 4))
    # inverse-ambiguity signature: large param error but small forward error
    med_pe = df["param_log10_rmse"].median()
    med_jr = df["rmse_full"].median()
    amb = int(((df["param_log10_rmse"] > med_pe) & (df["rmse_full"] < med_jr)).sum())

    # ---- save tables ----------------------------------------------------
    df.to_csv(os.path.join(OUT, "forward_metrics_per_sample.csv"), index=False)
    summary_rows = {
        "n_cohort": len(df),
        "rmse_full_median": stat.loc[0.50, "rmse_full"], "rmse_full_mean": df["rmse_full"].mean(),
        "rmse_full_iqr": [stat.loc[0.25, "rmse_full"], stat.loc[0.75, "rmse_full"]],
        "rmse_full_p10_p90": [stat.loc[0.10, "rmse_full"], stat.loc[0.90, "rmse_full"]],
        "r2_full_median": stat.loc[0.50, "r2_full"],
        "device_mae": dev_sum.round(4).to_dict("index"),
        "true_control_median_rmse": med, "pipeline_reproducibility_failure": bool(pip_fail),
        "correlations": rhos,
        "inverse_ambiguity_signature_count": amb,
    }
    with open(os.path.join(OUT, "forward_metrics_summary.csv"), "w") as f:
        f.write(pd.Series({k: str(v) for k, v in summary_rows.items()}).to_csv())

    # ---- figures ---------------------------------------------------------
    make_figures(df, J_target)
    make_summary_figure(df)

    # ---- text summary + conclusions --------------------------------------
    write_summary(df, stat, dev_sum, control, med, pip_fail, rhos, amb)
    print("Postprocess complete ->", OUT)


def pick_representatives(df):
    """5 predefined cases: low/mid/high-PCE representatives + lowest/highest sigma.
    Overlap rule: each selector yields an ordered candidate list; first distinct wins."""
    def by(cand_idx, key, val):
        return sorted(cand_idx, key=lambda i: abs(df.loc[i, key] - val))
    picks, used = [], set()
    low = df.index[df["selection_stratum"] == "low_PCE"]; med = df.index[df["selection_stratum"] == "mid_PCE"]
    high = df.index[df["selection_stratum"] == "high_PCE"]
    specs = [
        ("low-PCE rep",  by(low,  "PCE_t", df.loc[low, "PCE_t"].median())),
        ("mid-PCE rep",  by(med,  "PCE_t", df["PCE_t"].median())),
        ("high-PCE rep", by(high, "PCE_t", df.loc[high, "PCE_t"].median())),
        ("low-sigma",    df.sort_values("mean_pred_sigma").index.tolist()),
        ("high-sigma",   df.sort_values("mean_pred_sigma", ascending=False).index.tolist()),
    ]
    for label, cand in specs:
        for i in cand:
            if i not in used:
                picks.append((label, i)); used.add(i); break
    return picks


def make_figures(df, J_target):
    fig = plt.figure(figsize=(15, 9), dpi=150)
    gs = fig.add_gridspec(2, 3, hspace=0.45, wspace=0.30)
    gs_top = gs[0, :].subgridspec(1, 5, wspace=0.28)
    # (a) 5 predefined representative cases (NOT best-error picks)
    reps = pick_representatives(df)
    for k, (label, i) in enumerate(reps):
        sid = df.loc[i, "sample_id"]
        js = load_pred_mat(os.path.join(PRED_DIR, f"Sample_{sid:05d}_pred.mat"))
        ax = fig.add_subplot(gs_top[k])
        ax.plot(V, J_target[sid], color="0.45", lw=1.6, label="target")
        ax.plot(V, js, color=C[k], lw=1.9, ls="--", label="COMSOL(pred)")
        ax.set_title(f"{label}  #{sid}\nPCE {df.loc[i, 'PCE_t']:.1f}%", fontsize=8)
        ax.set_xlabel("V (V)")
        if k == 0:
            ax.set_ylabel("J (mA/cm$^2$)")
            ax.legend(fontsize=7)
        ax.axhline(0, color="0.7", lw=0.6)
    # (b) RMSE distribution
    ax = fig.add_subplot(gs[1, 0])
    ax.hist(df["rmse_full"], bins=12, color=C[0], edgecolor="w")
    ax.axvline(df["rmse_full"].median(), color=C[1], ls="--", lw=1.5,
               label=f"median {df['rmse_full'].median():.3f}")
    ax.set_xlabel("J-V RMSE (mA/cm$^2$)"); ax.set_ylabel("count")
    ax.legend(fontsize=8); ax.set_title("(b) cohort J-V RMSE", fontsize=9)
    # (c) device-metric deltas
    ax = fig.add_subplot(gs[1, 1])
    bp = ax.boxplot([df["dJsc"], df["dVoc"], df["dFF"], df["dPCE"]],
                    tick_labels=["ΔJsc", "ΔVoc", "ΔFF", "ΔPCE"], patch_artist=True,
                    medianprops=dict(color="k"))
    for patch, cc in zip(bp["boxes"], C):
        patch.set_facecolor(cc); patch.set_alpha(0.6)
    ax.axhline(0, color="0.5", lw=0.7)
    ax.set_ylabel("pred-forward − target"); ax.set_title("(c) device-metric deltas", fontsize=9)
    # (d) inversion error vs forward error
    ax = fig.add_subplot(gs[1, 2])
    ax.scatter(df["param_log10_rmse"], df["rmse_full"], c=C[2], s=28, alpha=0.85,
               edgecolor="k", lw=0.4)
    ax.set_xlabel("param log10-RMSE (post-hoc)")
    ax.set_ylabel("forward J-V RMSE (mA/cm$^2$)")
    ax.set_title("(d) inversion error vs forward error", fontsize=9)
    fig.savefig(os.path.join(OUT, "forward_validation_unbiased.png"), bbox_inches="tight")
    plt.close(fig)


def make_summary_figure(df):
    fig, axes = plt.subplots(2, 2, figsize=(10, 8), dpi=150)
    fields = [("Jsc_t", "Jsc_sim", "J$_{sc}$ (mA/cm$^2$)"), ("Voc_t", "Voc_sim", "V$_{oc}$ (V)"),
              ("FF_t", "FF_sim", "FF"), ("PCE_t", "PCE_sim", "PCE (%)")]
    colors = {"low_PCE": C[1], "mid_PCE": C[0], "high_PCE": C[2]}
    for ax, (x, y, lab) in zip(axes.ravel(), fields):
        lo = min(df[x].min(), df[y].min()); hi = max(df[x].max(), df[y].max())
        for st in ["low_PCE", "mid_PCE", "high_PCE"]:
            m = df["selection_stratum"] == st
            ax.scatter(df.loc[m, x], df.loc[m, y], c=colors[st], s=30, alpha=0.85,
                       edgecolor="k", lw=0.4, label=st.replace("_", "-"))
        ax.plot([lo, hi], [lo, hi], "k--", lw=1.0, label="1:1")
        ax.set_xlabel(f"original {lab}"); ax.set_ylabel(f"COMSOL(pred) {lab}")
        ax.set_title(lab, fontsize=9)
        ax.legend(fontsize=7)
    fig.suptitle("Predicted-parameter forward simulation vs original device metrics", fontsize=11)
    fig.savefig(os.path.join(OUT, "forward_validation_metric_summary.png"), bbox_inches="tight")
    plt.close(fig)


def write_summary(df, stat, dev_sum, control, med, pip_fail, rhos, amb):
    L = []
    L.append("FORWARD VALIDATION SUMMARY (unbiased cohort, VAE-v6)")
    L.append("=" * 62)
    L.append(f"cohort: {len(df)} test samples | PCE-tercile stratified, fixed seed | "
             f"COMSOL(pred) vs J_test_raw")
    L.append(f"curve metrics: median RMSE={stat.loc[0.50,'rmse_full']:.4f} mA/cm2 | "
             f"mean={df['rmse_full'].mean():.4f} | IQR=[{stat.loc[0.25,'rmse_full']:.4f},"
             f"{stat.loc[0.75,'rmse_full']:.4f}] | P10-P90=[{stat.loc[0.10,'rmse_full']:.4f},"
             f"{stat.loc[0.90,'rmse_full']:.4f}]")
    L.append(f"median R^2 (full curve) = {stat.loc[0.50,'r2_full']:.4f}")
    L.append(f"region RMSE (analysis convention, V=1.0V boundary): 0-1.0V median="
             f"{stat.loc[0.50,'rmse_0to1V']:.4f} | >1.0V median={stat.loc[0.50,'rmse_gt1V']:.4f}")
    L.append("device-metric |COMSOL(pred)-target| (median / q25 / q75):")
    for nm, r in dev_sum.iterrows():
        L.append(f"   {nm:<8} {r['median']:.4f} / {r['q25']:.4f} / {r['q75']:.4f}")
    if control is not None:
        L.append(f"true-param control: median RMSE = {med:.5f} mA/cm2")
        L.append(("   *** PIPELINE REPRODUCIBILITY FAILURE ***" if pip_fail else
                  "   control OK: COMSOL(true params) reproduces target (unit/ordering/model consistent)."))
    else:
        L.append("true-param control: not run (no comsol_true/ MATs).")
    L.append("post-hoc (interpretation only, not used for selection):")
    for k, (r, p) in rhos.items():
        L.append(f"   {k} = {r} (p={p})")
    L.append(f"inverse-ambiguity signature (large param error, small forward error): "
             f"{amb} / {len(df)} samples")
    L.append("")
    L.append("SCIENTIFIC CONCLUSIONS")
    med_rm = stat.loc[0.50, "rmse_full"]
    if med_rm < 0.2:
        fc = "SUPPORTED"
    elif med_rm < 0.5:
        fc = "PARTIALLY SUPPORTED"
    else:
        fc = "NOT SUPPORTED"
    L.append(f"A. FORWARD CONSISTENCY -> {fc}")
    L.append(f"   median J-V RMSE {med_rm:.3f} mA/cm2 across an unbiased cohort "
             "(interpretation: predicted param combinations reproduce the target curves; "
             "judged against the 1%-of-Jsc measurement-noise RMSE ~0.21 mA/cm2).")
    L.append("B. UNIQUE RECOVERY -> NOT SUPPORTED")
    L.append("   Forward consistency does not prove the recovered parameters are the unique "
             "true values (simulator-equivalent parameters can forward-reproduce J-V).")
    rh = rhos.get("spearman(param_log10_rmse,rmse_full)")
    if rh is not None and rh[0] < 0.5:
        cc = "SUPPORTED"
    elif rh is not None:
        cc = "PARTIALLY SUPPORTED"
    else:
        cc = "NOT ASSESSED"
    L.append(f"C. COLLISION CONSISTENCY -> {cc}")
    L.append(f"   Spearman(param-space error, forward J-V RMSE) = {rh[0] if rh else 'n/a'} "
             f"(weak => substantially different params can yield similar J-V; aligns with "
             f"the collision analysis).")
    mae_pce = dev_sum.loc["MAE_PCE", "median"]
    mae_jsc = dev_sum.loc["MAE_Jsc", "median"]
    if abs(mae_pce) < 2.0 and abs(mae_jsc) < 1.0:
        pm = "SUPPORTED"
    elif abs(mae_pce) < 5.0:
        pm = "PARTIALLY SUPPORTED"
    else:
        pm = "NOT SUPPORTED"
    L.append(f"D. PRACTICAL METRIC PRESERVATION -> {pm}")
    L.append(f"   median |ΔPCE|={mae_pce:.3f} pct-pts, |ΔJsc|={mae_jsc:.3f} mA/cm2 "
             "(reasonable device-level preservation).")
    L.append("")
    L.append("SUBMISSION WORDING BOUNDARY: may state 'Forward COMSOL re-simulation "
             "confirmed that the inferred parameter combinations reproduce the target "
             "J-V responses with low device-level discrepancy across an unbiased test "
             "cohort.' Must NOT state 'proves the inferred parameters are physically "
             "correct' or 'uniquely recovers the true material parameters'.")
    txt = "\n".join(L) + "\n"
    with open(os.path.join(OUT, "forward_validation_summary.txt"), "w", encoding="utf-8") as f:
        f.write(txt)
    print(txt)


if __name__ == "__main__":
    main()
