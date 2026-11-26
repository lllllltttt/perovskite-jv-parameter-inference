"""
plot_SI_S3_cycle_audit.py — SI Figure S3 (Decoder-COMSOL cycle-consistency
audit), re-rendered in the unified FINAL package style from the SAME frozen
local data the audit used (decoder_comsol_audit/, forward_validation_unbiased/
comsol_pred & comsol_true .mat files, _frozen_preds.npz). No new analysis.

  FigS3_cycle_cases.png   (a-f) 5 representative cases by cycle-gap percentile
                                (lowest/Q25/median/Q75/highest) + true-param
                                COMSOL control panel.
  FigS3_cycle_voltage.png  voltage-resolved RMSE across the 45-sample cohort:
                                decoder vs target, COMSOL(pred) vs target,
                                decoder vs COMSOL(pred); 1%-of-Jsc noise floor.
  FigS3_cycle_gap.png      (a-d) full-gap histogram; 0-1.0V vs >1.0V paired
                                boxplot; param-error vs gap; sigma vs gap.

Outputs under final_figures/SI/ (PNG 600dpi + vector PDF) by default; use
--cases-only to render ONLY FigS3_cycle_cases into final_figures/SI_final_review/
(the review copy: PNG@600 + PDF + SVG) without touching voltage/gap or SI/.

2026-08-28 surgical layout cleanup of the cycle-cases figure only (layout-only):
bigger canvas, two-line title hierarchy, uniform (a)-(f) panel labels, a single
shared figure-level legend, cleaner axes/tick labels, lighter 0-current line,
uniform linewidths. No data / sample selection / displayed numbers / panel
order / curve colors or styles changed.

2026-08-28 final micro-polish (3 layout-only tweaks, --cases-only review copy):
(1) panel labels (a)-(f) moved right+down onto the line-1 baseline, forming ONE
left-aligned title block "(a) cycle-gap lowest #12058" / "cg = ..."; (2) two-line
title gap tightened ~12% (1.154 -> 1.04 baselines); (3) shared legend moved down
(anchor y 0.052 -> 0.030) for more clearance under the bottom-row x labels.
Data / samples / numbers / curves / colors / 2x3 structure unchanged.
"""

import os
import argparse
import sys
import numpy as np
import pandas as pd
import pickle
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.io import loadmat
from scipy.stats import spearmanr

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import figure_style as st

BASE = os.path.dirname(os.path.dirname(HERE))
SI_DIR = os.path.join(BASE, "final_figures", "SI")
os.makedirs(SI_DIR, exist_ok=True)

NPZ = os.path.join(HERE, "_frozen_preds.npz")
J_SCALER = os.path.join(BASE, "data", "J_scaler.pkl")
DC_CSV = os.path.join(BASE, "decoder_comsol_audit", "decoder_comsol_metrics_per_sample.csv")
VR_CSV = os.path.join(BASE, "decoder_comsol_audit", "voltage_resolved_consistency.csv")
FW_PRED = os.path.join(BASE, "forward_validation_unbiased", "comsol_pred")
FW_TRUE = os.path.join(BASE, "forward_validation_unbiased", "comsol_true")

NOISE_RMSE = 0.21     # 1%-of-Jsc measurement-noise floor (frozen audit value)
INK = "#22262b"
GRAY = "#5a6470"


def load_mat_J(path):
    """A/m^2 -> mA/cm^2 (frozen unit convention of the audit)."""
    d = loadmat(path, squeeze_me=True)
    J = np.asarray(d["J"], dtype=np.float64)
    if J.ndim == 2:
        J = J[:, 0]
    return J * 0.1


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cases-only", action="store_true",
                    help="render ONLY FigS3_cycle_cases to the SI_final_review "
                         "folder (layout-cleanup review copy); skip voltage & gap")
    args = ap.parse_args()
    out_cases_dir = SI_DIR
    svg_cases = False
    if args.cases_only:
        out_cases_dir = os.path.join(BASE, "final_figures", "SI_final_review")
        svg_cases = True

    d = np.load(NPZ, allow_pickle=True)
    V = d["V_GRID"]
    Jraw = d["J_test_raw"]
    with open(J_SCALER, "rb") as f:
        js = pickle.load(f)
    recon_phys = js.inverse_transform(d["recon_test"])

    df = pd.read_csv(DC_CSV)
    assert len(df) == 45
    vres = pd.read_csv(VR_CSV)

    # ---- frozen-number sanity: medians + control must match the audit ----
    med_cg = float(df["cycle_gap"].median())
    med_dt = float(df["rmse_decoder"].median())
    med_ct = float(df["rmse_comsol"].median())
    print("medians: cycle_gap=%.4f decoder=%.4f comsol=%.4f"
          % (med_cg, med_dt, med_ct))
    assert abs(med_cg - 2.5627) < 1e-3
    assert abs(med_dt - 1.88597) < 1e-3
    assert abs(med_ct - 2.69263) < 1e-3

    # per-sample decoder/comsol/cycle-gap from raw curves must match CSV rows
    for sid in df["sample_id"].values[[0, 10, 22, 44]]:
        Jc_pred = load_mat_J(os.path.join(FW_PRED, "Sample_%05d_pred.mat" % sid))
        row = df[df.sample_id == sid].iloc[0]
        rmse_c = np.sqrt(np.mean((Jc_pred - Jraw[sid]) ** 2))
        rmse_d = np.sqrt(np.mean((recon_phys[sid] - Jraw[sid]) ** 2))
        cg = np.sqrt(np.mean((Jc_pred - recon_phys[sid]) ** 2))
        assert abs(rmse_c - row["rmse_comsol"]) < 1e-3, (sid, rmse_c)
        assert abs(rmse_d - row["rmse_decoder"]) < 1e-3, (sid, rmse_d)
        assert abs(cg - row["cycle_gap"]) < 1e-3, (sid, cg)
    print("per-sample curve RMSEs match frozen CSV rows. OK")

    # ---------- (1) representative cases (2 x 3) ----------
    # (2026-08-28 surgical layout cleanup — layout only; data/selection unchanged)
    w = st.set_fig_width("journal", 1.0)
    # local style constants for this figure (per the layout-cleanup spec)
    FS_LABEL, FS_T1, FS_T2 = 17.0, 13.0, 11.5     # (a)-(f) / title line1 / line2
    FS_TICK, FS_AXIS, FS_LEG = 10.5, 12.5, 10.5    # ticks / axis labels / legend
    L1_Y, L2_Y = 1.154, 1.04                      # title line1 / line2 baselines
    LB_Y = 1.154                                  # panel label shares the line1 band
    LABEL_X, TITLE_X = 0.02, 0.19                 # label x / left-aligned title block x
    fig = plt.figure(figsize=(11.5, 7.4))
    gs = fig.add_gridspec(2, 3, left=0.095, right=0.985, top=0.870, bottom=0.130,
                          wspace=0.48, hspace=0.60)
    order = np.argsort(df["cycle_gap"].values)
    qs = [0.0, 0.25, 0.5, 0.75, 1.0]
    idx = [order[int(q * (len(df) - 1))] for q in qs]
    labels = ["lowest", "Q25", "median", "Q75", "highest"]
    axs = [fig.add_subplot(gs[r, c]) for r in range(2) for c in range(3)]

    def style_case_ax(ax, show_x, show_y):
        """Uniform outward ticks + spines; only outer edges carry tick labels."""
        ax.tick_params(axis="both", which="major", direction="out", length=3.0,
                       width=0.8, labelsize=FS_TICK, colors=INK, top=False,
                       right=False, pad=2.5)
        if not show_x:
            ax.tick_params(labelbottom=False)
        if not show_y:
            ax.tick_params(labelleft=False)
        for sp in ax.spines.values():
            sp.set_color(INK)
            sp.set_linewidth(1.1)

    label_txts, l1_txts, l2_txts = [], [], []
    for k, (i, lab) in enumerate(zip(idx, labels)):
        ax = axs[k]
        sid = df.loc[i, "sample_id"]
        Jc_pred = load_mat_J(os.path.join(FW_PRED, "Sample_%05d_pred.mat" % sid))
        ax.plot(V, Jraw[sid], color=INK, lw=2.2, label="target")
        ax.plot(V, recon_phys[sid], color=st.OKABE_ITO[0], lw=2.0, label="decoder")
        ax.plot(V, Jc_pred, color=st.OKABE_ITO[3], lw=2.0, ls="--",
                label=r"COMSOL(pred $\theta$)")
        ax.axhline(0, color="#cccccc", lw=0.6, zorder=1)   # lighter 0-current line
        style_case_ax(ax, show_x=(k // 3 == 1), show_y=(k % 3 == 0))
        if k // 3 == 1:
            ax.set_xlabel("V (V)", fontsize=FS_AXIS, labelpad=3.0)
        if k % 3 == 0:
            ax.set_ylabel(r"J (mA cm$^{-2}$)", fontsize=FS_AXIS, labelpad=3.0)
        lt = ax.text(LABEL_X, LB_Y, "(%s)" % "abcdef"[k], transform=ax.transAxes,
                     fontsize=FS_LABEL, fontweight="bold", ha="left", va="bottom",
                     color=INK)
        t1 = ax.text(TITLE_X, L1_Y, "cycle-gap %s # %d" % (lab, sid),
                     transform=ax.transAxes, fontsize=FS_T1, ha="left",
                     va="bottom", color=INK)
        t2 = ax.text(TITLE_X, L2_Y, "cg = %.2f mA cm$^{-2}$" % df.loc[i, "cycle_gap"],
                     transform=ax.transAxes, fontsize=FS_T2, ha="left",
                     va="bottom", color=INK)
        label_txts.append(lt); l1_txts.append(t1); l2_txts.append(t2)
    # control panel (f)
    ax = axs[5]
    mid = order[len(df) // 2]
    sid = df.loc[mid, "sample_id"]
    Jc_true = load_mat_J(os.path.join(FW_TRUE, "Sample_%05d_true.mat" % sid))
    ax.plot(V, Jraw[sid], color=INK, lw=2.2, label="target")
    ax.plot(V, Jc_true, color=st.OKABE_ITO[2], lw=2.0, ls=":", label=r"COMSOL(true $\theta$)")
    ax.axhline(0, color="#cccccc", lw=0.6, zorder=1)
    style_case_ax(ax, show_x=True, show_y=True)
    ax.set_xlabel("V (V)", fontsize=FS_AXIS, labelpad=3.0)
    ax.set_ylabel(r"J (mA cm$^{-2}$)", fontsize=FS_AXIS, labelpad=3.0)
    lt = ax.text(LABEL_X, LB_Y, "(f)", transform=ax.transAxes, fontsize=FS_LABEL,
                 fontweight="bold", ha="left", va="bottom", color=INK)
    t1 = ax.text(TITLE_X, L1_Y, "true-param control # %d" % sid,
                 transform=ax.transAxes, fontsize=FS_T1, ha="left",
                 va="bottom", color=INK)
    t2 = ax.text(TITLE_X, L2_Y, r"rRMSE = %.2e mA cm$^{-2}$" % df.loc[mid, "rmse_true_control"],
                 transform=ax.transAxes, fontsize=FS_T2, ha="left",
                 va="bottom", color=INK)
    label_txts.append(lt); l1_txts.append(t1); l2_txts.append(t2)

    # single figure-level shared legend (all four entries), below the panels
    leg = fig.legend(
        handles=[
            plt.Line2D([0], [0], color=INK, lw=2.2, label="target"),
            plt.Line2D([0], [0], color=st.OKABE_ITO[0], lw=2.0, label="decoder"),
            plt.Line2D([0], [0], color=st.OKABE_ITO[3], lw=2.0, ls="--",
                       label=r"COMSOL(pred $\theta$)"),
            plt.Line2D([0], [0], color=st.OKABE_ITO[2], lw=2.0, ls=":",
                       label=r"COMSOL(true $\theta$)"),
        ],
        loc="lower center", bbox_to_anchor=(0.5, 0.030), ncol=4, frameon=False,
        fontsize=FS_LEG, handlelength=2.2, columnspacing=1.6,
        handletextpad=0.7, borderaxespad=0.0)

    # ---- layout-only QC ----
    fig.canvas.draw()
    ren = fig.canvas.get_renderer()
    qc = []

    def chk(name, cond, note=""):
        qc.append(bool(cond))
        print("[%s] %s  %s" % ("PASS" if cond else "FAIL", name, note))

    sid_list = [int(df.loc[i, "sample_id"]) for i in idx] + [int(sid)]
    cg_list = ["%.2f" % df.loc[i, "cycle_gap"] for i in idx]
    chk("sample IDs", sid_list == [12058, 4077, 595, 695, 14499, 595], str(sid_list))
    chk("cg values", cg_list == ["0.27", "1.68", "2.56", "5.64", "54.10"], str(cg_list))
    chk("rRMSE", "%.2e" % df.loc[mid, "rmse_true_control"] == "1.23e-07", "")

    ok_data = True
    for k, (i, _) in enumerate(zip(idx, labels)):
        sidk = int(df.loc[i, "sample_id"])
        L = axs[k].lines
        if not (np.array_equal(L[0].get_ydata(), Jraw[sidk])
                and np.array_equal(L[1].get_ydata(), recon_phys[sidk])
                and np.array_equal(L[2].get_ydata(), load_mat_J(os.path.join(
                    FW_PRED, "Sample_%05d_pred.mat" % sidk)))):
            ok_data = False
    L = axs[5].lines
    if not (np.array_equal(L[0].get_ydata(), Jraw[sid])
            and np.array_equal(L[1].get_ydata(), Jc_true)):
        ok_data = False
    chk("curve data", ok_data, "target/decoder/comsol(pred)/comsol(true) == frozen arrays")

    ok_uniform = True
    for lt in label_txts:
        if not (abs(lt.get_position()[0] - LABEL_X) < 1e-9
                and abs(lt.get_fontsize() - FS_LABEL) < 1e-6
                and lt.get_fontweight() == "bold"):
            ok_uniform = False
    for t1, t2 in zip(l1_txts, l2_txts):
        if not (abs(t1.get_position()[0] - TITLE_X) < 1e-9
                and abs(t2.get_position()[0] - TITLE_X) < 1e-9
                and t1.get_fontsize() > t2.get_fontsize()):
            ok_uniform = False
    chk("uniform labels", ok_uniform,
        "labels identical x=%.2f, bold fs=%.0f, on line1 band y=%.3f; titles left-aligned x=%.2f"
        % (LABEL_X, FS_LABEL, LB_Y, TITLE_X))

    ok_in = True
    for k in range(6):
        for t in (label_txts[k], l1_txts[k], l2_txts[k]):
            e = t.get_window_extent(ren)
            if not (e.x0 >= 0 and e.y0 >= 0 and e.x1 <= fig.bbox.width and e.y1 <= fig.bbox.height):
                ok_in = False
    le = leg.get_window_extent(ren)
    if not (le.x0 >= 0 and le.x1 <= fig.bbox.width):
        ok_in = False
    chk("no clipping", ok_in, "all titles/labels/legend inside figure")

    ok_ov = True
    for k in range(6):
        el = label_txts[k].get_window_extent(ren)
        e1 = l1_txts[k].get_window_extent(ren)
        e2 = l2_txts[k].get_window_extent(ren)
        if el.overlaps(e1) or e1.overlaps(e2) or el.overlaps(e2):
            ok_ov = False
    for r in range(2):
        row = [l1_txts[r * 3 + c].get_window_extent(ren) for c in range(3)]
        if row[0].x1 > row[1].x0 or row[1].x1 > row[2].x0:
            ok_ov = False
    bottom_ax = axs[3].get_window_extent(ren)
    if not le.y1 < bottom_ax.y0:
        ok_ov = False
    # legend must also clear the bottom-row x tick labels (not just the axes box)
    xtl = [t.get_window_extent(ren).y0 for t in axs[3].get_xticklabels()]
    if xtl and not le.y1 < min(xtl):
        ok_ov = False
    chk("no overlap", ok_ov,
        "label/title stacks separated; titles not colliding; legend below axes and x tick labels")

    st.save_fig(fig, os.path.join(out_cases_dir, "FigS3_cycle_cases"), svg=svg_cases)

    from PIL import Image as _PIL
    _im = _PIL.open(os.path.join(out_cases_dir, "FigS3_cycle_cases.png"))
    dpi = _im.info.get("dpi", (0, 0))[0]
    chk("PNG 600dpi", abs(dpi - 600) < 1.0, "%dx%d @%.0f" % (_im.size[0], _im.size[1], dpi))
    chk("PDF/SVG", os.path.exists(os.path.join(out_cases_dir, "FigS3_cycle_cases.pdf"))
        and os.path.exists(os.path.join(out_cases_dir, "FigS3_cycle_cases.svg")),
        "PDF + SVG emitted")
    print("CASES QC: %d/%d PASS" % (sum(qc), len(qc)))

    if args.cases_only:
        print("cases-only: wrote FigS3_cycle_cases to", out_cases_dir, "(review copy)")
        return

    # ---------- (2) voltage-resolved consistency ----------
    fig, ax = plt.subplots(figsize=(st.set_fig_width("journal"), w * 0.36))
    ax.plot(vres["voltage"], vres["decoder_target_rmse"], color=st.OKABE_ITO[0],
            lw=1.6, label="decoder vs target")
    ax.plot(vres["voltage"], vres["comsol_target_rmse"], color=st.OKABE_ITO[3],
            lw=1.6, ls="--", label="COMSOL(pred) vs target")
    ax.plot(vres["voltage"], vres["decoder_comsol_rmse"], color=st.OKABE_ITO[2],
            lw=1.6, ls=":", label="decoder vs COMSOL(pred)")
    ax.axvline(1.0, color="#999999", lw=0.8, ls="-.")
    ax.axhline(NOISE_RMSE, color="#888888", lw=0.7, ls="--")
    ax.text(0.02, NOISE_RMSE * 1.12, "noise floor 0.21", fontsize=st.FS_ANNOT,
            color=GRAY)
    ax.set_xlabel("Voltage (V)")
    ax.set_ylabel(r"RMSE across 45 samples (mA cm$^{-2}$)")
    st.configure_axes(ax)
    ax.legend(fontsize=st.FS_LEGEND, frameon=False, loc="upper left",
              handlelength=1.6)
    st.save_fig(fig, os.path.join(SI_DIR, "FigS3_cycle_voltage"))

    # ---------- (3) cycle-gap distributions (2 x 2) ----------
    fig = plt.figure(figsize=(w, w * 0.62))
    gs = fig.add_gridspec(2, 2, left=0.09, right=0.99, top=0.90, bottom=0.11,
                          wspace=0.42, hspace=0.55)
    # (a) full-gap histogram
    axa = fig.add_subplot(gs[0, 0])
    axa.hist(df["cycle_gap"], bins=14, color=st.OKABE_ITO[0],
             edgecolor="white", linewidth=0.4)
    axa.axvline(med_cg, color=st.OKABE_ITO[3], ls="--", lw=1.4)
    axa.text(med_cg, axa.get_ylim()[1] * 0.95, "median %.2f" % med_cg,
             fontsize=st.FS_ANNOT, color=INK, va="top")
    axa.set_xlabel(r"cycle gap, full 0–1.3 V (mA cm$^{-2}$)")
    axa.set_ylabel("count")
    st.configure_axes(axa)
    axa.text(0.0, 1.16, "(a)", fontsize=st.FS_PANEL, fontweight="bold",
             va="top", transform=axa.transAxes, color=INK)
    # (b) region paired boxplot
    axb = fig.add_subplot(gs[0, 1])
    x0, x1 = df["cycle_gap_0to1V"].values, df["cycle_gap_gt1V"].values
    bp = axb.boxplot([x0, x1], positions=[0, 1], widths=0.5, patch_artist=True,
                     medianprops=dict(color="black", lw=1.2),
                     flierprops=dict(marker="o", ms=2.5, alpha=0.4,
                                     markeredgecolor="none"))
    for patch, cc in zip(bp["boxes"], [st.OKABE_ITO[0], st.OKABE_ITO[3]]):
        patch.set_facecolor(cc); patch.set_alpha(0.65)
    for i in range(len(x0)):
        axb.plot([0, 1], [x0[i], x1[i]], color="#999999", lw=0.5, alpha=0.45)
    for i, m in enumerate([np.median(x0), np.median(x1)]):
        axb.text(i, m, "%.2f" % m, ha="center", va="bottom",
                 fontsize=st.FS_ANNOT, color=INK)
    axb.set_xticks([0, 1])
    axb.set_xticklabels(["0–1.0 V", ">1.0 V"], fontsize=st.FS_TICK)
    axb.set_ylabel(r"cycle gap (mA cm$^{-2}$)")
    st.configure_axes(axb)
    axb.text(0.0, 1.16, "(b)", fontsize=st.FS_PANEL, fontweight="bold",
             va="top", transform=axb.transAxes, color=INK)
    # (c) param error vs gap
    axc = fig.add_subplot(gs[1, 0])
    axc.scatter(df["param_log10_rmse"], df["cycle_gap"], s=26,
                color=st.OKABE_ITO[2], alpha=0.85, edgecolor="white",
                linewidth=0.4, zorder=3)
    r, p = spearmanr(df["param_log10_rmse"], df["cycle_gap"])
    axc.set_xlabel("param $\\log_{10}$-RMSE (post-hoc)")
    axc.set_ylabel(r"cycle gap (mA cm$^{-2}$)")
    st.configure_axes(axc)
    axc.text(0.97, 0.05, r"$\rho$ = %.2f (p = %.2f)" % (r, p),
             transform=axc.transAxes, fontsize=st.FS_ANNOT, va="bottom",
             ha="right", color=INK)
    axc.text(0.0, 1.16, "(c)", fontsize=st.FS_PANEL, fontweight="bold",
             va="top", transform=axc.transAxes, color=INK)
    # (d) predicted sigma vs gap
    axd = fig.add_subplot(gs[1, 1])
    axd.scatter(df["mean_pred_sigma"], df["cycle_gap"], s=26,
                color=st.OKABE_ITO[4], alpha=0.85, edgecolor="white",
                linewidth=0.4, zorder=3)
    r, p = spearmanr(df["mean_pred_sigma"], df["cycle_gap"])
    axd.set_xlabel(r"mean predicted $\sigma$")
    axd.set_ylabel(r"cycle gap (mA cm$^{-2}$)")
    st.configure_axes(axd)
    axd.text(0.97, 0.05, r"$\rho$ = %.2f (p = %.2f)" % (r, p),
             transform=axd.transAxes, fontsize=st.FS_ANNOT, va="bottom",
             ha="right", color=INK)
    axd.text(0.0, 1.16, "(d)", fontsize=st.FS_PANEL, fontweight="bold",
             va="top", transform=axd.transAxes, color=INK)
    st.save_fig(fig, os.path.join(SI_DIR, "FigS3_cycle_gap"))

    print("SI S3 cycle-audit figures written to", SI_DIR)


if __name__ == "__main__":
    main()
