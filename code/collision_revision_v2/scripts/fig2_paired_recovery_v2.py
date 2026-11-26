# -*- coding: utf-8 -*-
"""
fig2_paired_recovery_v2.py — Figure 2 layout, v2 refinement.
============================================================
Structure is unchanged from phase 1: the same a-h layout and the same complete
sample (all 15,307 test curves in every panel). Changes made this round:

  1. the bottom two panels (g) and (h) are now EQUAL WIDTH, which relieves the
     crowding in (h);
  2. the coordinates are labelled in log10 units, with the physical unit basis
     stated per panel: the shared-scale coordinate is a = log10(g) with g the
     geometric mean of the pair, so its numeric value depends on the unit the
     parameter was sampled in (m^2 V^-1 s^-1, s, m^-3 for the three families);
     the log-ratio r is dimensionless and unit-invariant;
  3. the correlation is named "Pearson correlation rho" in the axis label, so
     it cannot be confused with the log-ratio coordinate r or with a Spearman
     statistic;
  4. per-panel x and y limits remain identical to each other, and the three
     ratio panels keep one common limit, covering every true and predicted
     value.

The correlation values, the MAE reductions and the training-coordinate medians
are NOT touched: they are recomputed from the same frozen sources and asserted
against the phase-1 numbers before the figure is drawn.

Read-only on the frozen project; writes only inside this v2 directory.
"""
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import pearsonr

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lib_v2 as L
import figstyle_v2 as st

OUT = os.path.dirname(HERE)
DATADIR = os.path.join(OUT, "source_data")
FIGDIR = os.path.join(OUT, "preview")
os.makedirs(DATADIR, exist_ok=True)
os.makedirs(FIGDIR, exist_ok=True)

C_SHARED = st.OKABE_ITO[0]
C_RATIO = st.OKABE_ITO[3]

FAMILIES = [("mobility", 0, 1, "Mobility"),
            ("lifetime", 2, 3, "Bulk lifetime"),
            ("DOS", 4, 5, "Density of states")]

# phase-1 values, asserted below so a layout edit can never move a number
V1 = {("a", "mobility"): (0.925047, 0.680984), ("r", "mobility"): (0.428887, 0.083636),
      ("a", "lifetime"): (0.881870, 0.612916), ("r", "lifetime"): (0.351667, 0.027472),
      ("a", "DOS"): (0.924758, 0.662630), ("r", "DOS"): (0.266298, 0.008322)}

A_LIMITS = {"mobility": (-6.6, -1.4), "lifetime": (-9.9, -1.6),
            "DOS": (22.5, 26.8)}
A_TICKS = {"mobility": [-6, -5, -4, -3, -2],
           "lifetime": [-9, -8, -7, -6, -5, -4, -3, -2],
           "DOS": [23, 24, 25, 26]}
R_LIMIT = (-0.95, 1.30)
R_TICKS = [-0.5, 0.0, 0.5, 1.0]

UNIT_TEX = {"mobility": r"m$^2$ V$^{-1}$ s$^{-1}$",
            "lifetime": r"s", "DOS": r"m$^{-3}$"}


def load():
    """Truth/prediction/train coordinates, physical log10, plus per-sample table."""
    f = np.load(L.FROZEN_NPZ)
    d = np.load(L.DATA_NPZ)
    with open(L.SCALER_PKL, "rb") as fh:
        import pickle
        sc = pickle.load(fh)["scaler"]
    L_true = np.log10(f["params_test_raw"].astype(np.float64))
    L_pred = np.log10(f["params_pred_phys"].astype(np.float64))
    L_train = d["params_train"].astype(np.float64) * sc.data_range_ + sc.data_min_
    assert np.max(np.abs(
        L_true - (f["params_test"] * sc.data_range_ + sc.data_min_))) < 1e-12
    assert np.max(np.abs(
        L_pred - (f["param_mu"] * sc.data_range_ + sc.data_min_))) < 1e-12

    coords, rows = {}, {}
    for lab, p, q, _t in FAMILIES:
        coords[("a", lab)] = (0.5 * (L_true[:, p] + L_true[:, q]),
                              0.5 * (L_pred[:, p] + L_pred[:, q]),
                              0.5 * (L_train[:, p] + L_train[:, q]))
        coords[("r", lab)] = (L_true[:, p] - L_true[:, q],
                              L_pred[:, p] - L_pred[:, q],
                              L_train[:, p] - L_train[:, q])
        rows["a_" + lab] = coords[("a", lab)]
        rows["r_" + lab] = coords[("r", lab)]

    n = L_true.shape[0]
    per = pd.DataFrame({"test_index": np.arange(n)})
    for lab, p, q, _t in FAMILIES:
        ta, pa, _ = coords[("a", lab)]
        tr, pr, _ = coords[("r", lab)]
        tag = {"mobility": "mu", "lifetime": "tau", "DOS": "D"}[lab]
        per["a_%s_true" % tag] = ta
        per["a_%s_pred" % tag] = pa
        per["r_%s_true" % tag] = tr
        per["r_%s_pred" % tag] = pr
    return coords, per


def panel_parity(ax, t, p, color, lim, ticks, tag, title, show_xlab,
                 show_ylab, xlabel, ylabel):
    ax.scatter(t, p, s=1.6, alpha=0.10, color=color, linewidths=0,
               rasterized=True, zorder=2)
    ax.plot(list(lim), list(lim), ls="--", color="#555555", lw=0.8, zorder=3)
    ax.set_xlim(*lim)
    ax.set_ylim(*lim)                      # identical x and y limits per panel
    ax.set_xticks(ticks)
    ax.set_yticks(ticks)
    rho = float(pearsonr(t, p)[0])
    ax.text(0.045, 0.955, tag, transform=ax.transAxes, fontsize=st.FS_TITLE,
            fontweight="bold", color=st.INK, va="top", ha="left")
    ax.text(0.955, 0.055, r"$\rho$ = %.3f" % rho, transform=ax.transAxes,
            fontsize=st.FS_ANNOT, color=st.INK, va="bottom", ha="right")
    ax.set_title(title, fontsize=st.FS_AXIS, color=st.INK, pad=3.0)
    if show_xlab:
        ax.set_xlabel(xlabel, fontsize=st.FS_ANNOT - 0.4)
    if show_ylab:
        ax.set_ylabel(ylabel, fontsize=st.FS_ANNOT - 0.4)
    ax.tick_params(labelsize=st.FS_TICK - 0.5)
    st.configure_axes(ax)
    return rho


def build(size, coords):
    w = st.set_fig_width(size)
    fig = plt.figure(figsize=(w, w * 1.10))
    # 3 rows x 6 columns so that (g) and (h) can each take exactly half of the
    # bottom row and therefore have equal width.
    gs = fig.add_gridspec(3, 6, left=0.078, right=0.988, top=0.892,
                          bottom=0.135, wspace=1.15, hspace=0.50,
                          height_ratios=[1.0, 1.0, 1.08])

    rho = {}
    for col, (lab, p, q, title) in enumerate(FAMILIES):
        for row, fam in ((0, "a"), (1, "r")):
            ax = fig.add_subplot(gs[row, col * 2:col * 2 + 2])
            t, pr, _ = coords[(fam, lab)]
            lim = A_LIMITS[lab] if fam == "a" else R_LIMIT
            tks = A_TICKS[lab] if fam == "a" else R_TICKS
            color = C_SHARED if fam == "a" else C_RATIO
            if fam == "a":
                xlab = r"True  $\log_{10} g$  (%s)" % UNIT_TEX[lab]
                ylab = r"Predicted  $\log_{10} g$  (%s)" % UNIT_TEX[lab]
            else:
                xlab = r"True  $\log_{10}(p_n/p_p)$"
                ylab = r"Predicted  $\log_{10}(p_n/p_p)$"
            rho[(fam, lab)] = panel_parity(
                ax, t, pr, color, lim, tks, "(%s)" % "abcdef"[row * 3 + col],
                title if row == 0 else "", True, col == 0, xlab, ylab)

    # row headers naming the two coordinate families
    pos = gs[0, :].get_position(fig)
    axg = fig.add_axes(pos); axg.axis("off"); axg.patch.set_visible(False)
    axg.text(0.0, 1.09,
             r"Shared scale  $a=(\log_{10}p_n+\log_{10}p_p)/2$   "
             r"(blue; panels a-c)",
             transform=axg.transAxes, fontsize=st.FS_ANNOT, color=C_SHARED,
             va="bottom", ha="left")
    pos2 = gs[1, :].get_position(fig)
    axg2 = fig.add_axes(pos2); axg2.axis("off"); axg2.patch.set_visible(False)
    axg2.text(0.0, 1.09,
              r"Electron-hole log-ratio  $r=\log_{10}(p_n/p_p)$   "
              r"(orange; panels d-f)",
              transform=axg2.transAxes, fontsize=st.FS_ANNOT, color=C_RATIO,
              va="bottom", ha="left")

    x = np.arange(3); bw = 0.36

    # ---------------- (g) Pearson correlation comparison, half width --------
    axg_ = fig.add_subplot(gs[2, 0:3])
    a_vals = [rho[("a", lab)] for lab, _, _, _ in FAMILIES]
    r_vals = [rho[("r", lab)] for lab, _, _, _ in FAMILIES]
    b1 = axg_.bar(x - bw / 2, a_vals, bw, color=C_SHARED, edgecolor="white",
                  linewidth=0.5, zorder=3, label="Shared scale $a$")
    b2 = axg_.bar(x + bw / 2, r_vals, bw, color=C_RATIO, edgecolor="white",
                  linewidth=0.5, zorder=3,
                  label="Electron–hole log-ratio $r$")
    for bars, vals in ((b1, a_vals), (b2, r_vals)):
        for rect, v in zip(bars, vals):
            axg_.text(rect.get_x() + rect.get_width() / 2, v + 0.022,
                      "%.3f" % v, ha="center", va="bottom",
                      fontsize=st.FS_ANNOT - 0.5, color=st.INK, zorder=4)
    axg_.set_xticks(x)
    axg_.set_xticklabels([t for _, _, _, t in FAMILIES],
                         fontsize=st.FS_ANNOT - 0.5)
    axg_.set_xlim(-0.62, 2.62); axg_.set_ylim(0, 1.10)
    axg_.set_yticks([0.0, 0.25, 0.5, 0.75, 1.0])
    axg_.set_ylabel("Pearson correlation $\\rho$\n(true vs predicted)",
                    fontsize=st.FS_ANNOT)
    # no in-panel legend: the blue/orange encoding is carried by the row headers
    # above and by the single figure-level legend at the foot of the figure
    st.configure_axes(axg_)
    st.panel_label(axg_, "(g)", dx=-0.085, dy=1.03)

    # ---------------- (h) MAE reduction, equal width -----------------------
    axh = fig.add_subplot(gs[2, 3:6])
    a_red, r_red, red = [], [], {}
    for lab, _, _, _ in FAMILIES:
        for fam, sink in (("a", a_red), ("r", r_red)):
            t, pr, tr = coords[(fam, lab)]
            base = float(np.median(tr))
            v = 1.0 - np.mean(np.abs(t - pr)) / np.mean(np.abs(t - base))
            sink.append(100.0 * v)
            red[(fam, lab)] = v
    b1 = axh.bar(x - bw / 2, a_red, bw, color=C_SHARED, edgecolor="white",
                 linewidth=0.5, zorder=3, label="Shared scale $a$")
    b2 = axh.bar(x + bw / 2, r_red, bw, color=C_RATIO, edgecolor="white",
                 linewidth=0.5, zorder=3, label="Log-ratio $r$")
    for bars, vals in ((b1, a_red), (b2, r_red)):
        for rect, v in zip(bars, vals):
            axh.text(rect.get_x() + rect.get_width() / 2, v + 2.2,
                     "%.1f%%" % v, ha="center", va="bottom",
                     fontsize=st.FS_ANNOT - 0.5, color=st.INK, zorder=4)
    axh.axhline(0.0, color=st.MUTED, lw=0.9, zorder=4)
    axh.set_xticks(x)
    axh.set_xticklabels([t for _, _, _, t in FAMILIES],
                        fontsize=st.FS_ANNOT - 0.5)
    axh.set_xlim(-0.62, 2.62); axh.set_ylim(-9.0, 84.0)
    axh.set_yticks([0, 20, 40, 60, 80])
    axh.set_ylabel("MAE reduction vs\ntraining-median baseline (%)",
                   fontsize=st.FS_ANNOT)
    st.configure_axes(axh)
    st.panel_label(axh, "(h)", dx=-0.085, dy=1.03)

    fig.legend([b1[0], b2[0]], ["Shared scale $a$", "Electron–hole log-ratio $r$"],
               loc="lower center", ncol=2, frameon=False,
               fontsize=st.FS_LEGEND, handlelength=1.4, handletextpad=0.6,
               columnspacing=2.6, bbox_to_anchor=(0.5, 0.010))

    fig.suptitle("Figure 2 — paired-coordinate recovery, frozen VAE-v6, "
                 "$n$ = 15,307 test samples\n"
                 "coordinates are in physical log$_{10}$ units; shared-scale "
                 "panels are $\\log_{10}$ of the geometric mean in the stated unit",
                 fontsize=st.FS_AXIS - 0.8, color=st.INK, y=0.988)
    stem = os.path.join(FIGDIR, "Figure2_paired_recovery"
                        + ("_large" if size == "large" else ""))
    st.save_fig(fig, stem, dpi=200)
    print("wrote:", stem)
    return rho, red


def main():
    coords, per = load()

    # the layout must not move any number
    for (fam, lab), (rho_v1, red_v1) in V1.items():
        t, pr, tr = coords[(fam, lab)]
        rho_now = float(pearsonr(t, pr)[0])
        base = float(np.median(tr))
        red_now = 1.0 - np.mean(np.abs(t - pr)) / np.mean(np.abs(t - base))
        assert abs(rho_now - rho_v1) < 5e-7, (fam, lab, rho_now, rho_v1)
        assert abs(red_now - red_v1) < 5e-7, (fam, lab, red_now, red_v1)
    print("[check] all six correlations and MAE reductions match phase 1")

    rho, red = build("journal", coords)
    build("large", coords)
    per.to_csv(os.path.join(DATADIR, "fig2_coordinates_per_sample.csv"),
               index=False)

    rows = []
    for lab, _p, _q, _t in FAMILIES:
        for fam in ("a", "r"):
            t, pr, tr = coords[(fam, lab)]
            base = float(np.median(tr))
            tag = {"mobility": "mu", "lifetime": "tau", "DOS": "D"}[lab]
            rows.append(dict(
                pair=lab, coordinate=("%s_%s" % (fam, tag)),
                unit=(L.PARAM_UNITS_PLAIN[0] if fam == "a" and lab == "mobility"
                      else L.PARAM_UNITS_PLAIN[2] if fam == "a" and lab == "lifetime"
                      else L.PARAM_UNITS_PLAIN[4] if fam == "a"
                      else "dimensionless log10 ratio"),
                pearson_r=rho[(fam, lab)],
                mae_model=float(np.mean(np.abs(t - pr))),
                mae_training_median_baseline=float(np.mean(np.abs(t - base))),
                mae_reduction=red[(fam, lab)],
                train_median=base, n_test=int(len(t))))
    pd.DataFrame(rows).to_csv(
        os.path.join(DATADIR, "Figure2_paired_values_v2.csv"), index=False)
    print("wrote fig2_coordinates_per_sample.csv, Figure2_paired_values_v2.csv")
    for r in rows:
        print("  %-8s %-6s rho=%.6f  MAEred=%.6f  unit=%s"
              % (r["pair"], r["coordinate"], r["pearson_r"],
                 r["mae_reduction"], r["unit"]))


if __name__ == "__main__":
    main()
