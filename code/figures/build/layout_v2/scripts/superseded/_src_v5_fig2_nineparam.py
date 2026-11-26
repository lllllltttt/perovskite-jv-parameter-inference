# -*- coding: utf-8 -*-
"""
fig2_recovery.py — reassembled main Figure 2 (v3).
==================================================
"Recovery of individual parameters and shared-scale and ratio coordinates"

v3 RESTRUCTURE (supervisor layout)
----------------------------------
The submitted arrangement gave the nine parity sub-plots most of the area and
the two comparison panels the remainder. The plan requires the opposite
balance:

    +-----------------------------------------------------+
    | (a) nine-parameter parity, 3 x 3, spans the row     |
    +--------------------------+--------------------------+
    | (b) shared-scale / ratio | (c) MAE reduction vs the |
    |     prediction           |     training-median      |
    |     correlation          |     baseline             |
    +--------------------------+--------------------------+

(b) and (c) are given comparable visual weight and are the point of the
figure; (a) is the supporting panel. Three further changes are required by the
plan and are implemented here:

  * the correlation statistic is written as an explicitly defined symbol
    (Pearson rho), so it cannot be confused with the ratio coordinate r or
    with the radiative coefficient r_rad; the panel says so in words;
  * the zero line of (c) is labelled "no improvement over baseline";
  * the axis range of (c) admits negative values, so a future recomputation
    that produced a negative improvement would be shown rather than clipped.

Nothing is retrained or re-predicted. Every number is read from the frozen
sources below and asserted against its archived value before the figure is
written.

Panel sources (all frozen):
  (a) final_figures/scripts/_frozen_preds.npz          (frozen VAE-v6 chain)
      evaluation_fixed/parameter_metrics.csv           (Pearson r, per param)
  (b) reviewer_experiments/exp3_prior_coordinate_recoverability/
      results/frozen_coordinate_recoverability.csv
  (c) same file — the quantity the manuscript's Table S11 tabulates

Coordinate definitions, in the physical log10 space (predictions are taken
back out of the per-parameter min-max normalisation before the coordinates
are formed):
    a = (log10 p_n + log10 p_p) / 2        shared scale
    r = log10 p_n - log10 p_p = log10 q    electron-hole ratio

Outputs: figures/Figure2{,_large}.{png,pdf,svg}
         data_used/Figure2_plotting_values.csv
"""

import os
import sys

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpecFromSubplotSpec

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import figstyle as st

BASE = st.BASE
NPZ = st.NPZ
METRICS_CSV = os.path.join(BASE, "evaluation_fixed", "parameter_metrics.csv")
COORD_CSV = os.path.join(
    BASE, "reviewer_experiments", "exp3_prior_coordinate_recoverability",
    "results", "frozen_coordinate_recoverability.csv")

# ------------------------------------------------------------- frozen pins --
R_EXPECT = {                       # evaluation_fixed/parameter_metrics.csv
    "mu_n_pvk": 0.906268, "mu_p_pvk": 0.919434, "tau_n_pvk": 0.878266,
    "tau_p_pvk": 0.880803, "Nc_eff_pvk": 0.909047, "Nv_eff_pvk": 0.895604,
    "tau_ETL": 0.593605, "tau_HTL": 0.719923, "rad_c": 0.559174,
}
COORD_EXPECT = {                   # frozen_coordinate_recoverability.csv
    "a_mu": (0.925047, 0.680984), "r_mu": (0.428887, 0.083636),
    "a_tau": (0.881870, 0.612916), "r_tau": (0.351667, 0.027472),
    "a_D": (0.924758, 0.662630), "r_D": (0.266298, 0.008322),
}
N_TEST = 15307

PAIR_KEYS = [("a_mu", "r_mu"), ("a_tau", "r_tau"), ("a_D", "r_D")]
PAIR_TICK = ["Mobility\n$\\mu_n,\\mu_p$",
             "Bulk lifetime\n$\\tau_n,\\tau_p$",
             "Density of states\n$N_c,N_v$"]

C_SHARED = st.OKABE_ITO[0]     # shared scale  a
C_RATIO = st.OKABE_ITO[3]      # log-ratio     r

XTICKS = [0.0, 0.5, 1.0]
YTICKS = [0.0, 0.5, 1.0]
X_LABELS = {(2, 0): ["0.0", "0.5", ""], (2, 1): ["", "0.5", ""],
            (2, 2): ["", "0.5", "1.0"]}
Y_LABELS = {(0, 0): ["", "0.5", "1.0"], (1, 0): ["", "0.5", ""],
            (2, 0): ["0.0", "0.5", ""]}


def load():
    d = np.load(NPZ)
    y_true, y_pred = d["params_test"], d["param_mu"]
    metr = pd.read_csv(METRICS_CSV).set_index("parameter")
    co = pd.read_csv(COORD_CSV).set_index("coordinate")

    for nm, exp in R_EXPECT.items():
        got = float(metr.loc[nm, "pearson_r"])
        assert abs(got - exp) < 5e-7, (nm, got, exp)
    for nm, (pr, mr) in COORD_EXPECT.items():
        gotpr = float(co.loc[nm, "pearson_r"])
        gotmr = float(co.loc[nm, "mae_reduction"])
        assert abs(gotpr - pr) < 5e-7, (nm, gotpr, pr)
        assert abs(gotmr - mr) < 5e-7, (nm, gotmr, mr)
    assert y_true.shape == (N_TEST, 9), y_true.shape
    assert y_pred.shape == (N_TEST, 9), y_pred.shape
    return d, y_true, y_pred, metr, co


def build(size):
    d, y_true, y_pred, metr, co = load()
    r_par = {n: float(metr.loc[n, "pearson_r"]) for n in st.PARAM_NAMES}

    w = st.set_fig_width(size)
    # The 3 x 3 grid spans the full row, so the canvas has to be tall enough
    # that its cells are not slivers; the bottom row then keeps a weight
    # comparable to it, as the plan requires.
    # Margins are set by measurement, not by eye: the left edge has to clear
    # the two-line y-axis label of (b) AND the rotated (a) axis title, and the
    # bottom has to clear the two-line footnotes under (b) and (c).
    fig = plt.figure(figsize=(w, w * 1.130))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.34, 1.0],
                          left=0.095, right=0.988, top=0.955, bottom=0.090,
                          wspace=0.30, hspace=0.36)

    # ---------------- (a) 3 x 3 parity, normalized log10 -------------------
    gsa = GridSpecFromSubplotSpec(3, 3, subplot_spec=gs[0, :],
                                  wspace=0.14, hspace=0.14)
    for k in range(9):
        row, col = divmod(k, 3)
        ax = fig.add_subplot(gsa[row, col])
        ax.scatter(y_true[:, k], y_pred[:, k], s=2.0, alpha=0.10,
                   color=st.OKABE_ITO[0], linewidths=0, rasterized=True)
        ax.plot([0, 1], [0, 1], ls="--", color="#555555", lw=0.8, zorder=3)
        ax.text(0.06, 0.94, st.PARAM_LABELS[k], fontsize=st.FS_ANNOT,
                fontweight="bold", color=st.INK, transform=ax.transAxes,
                va="top", ha="left")
        # rho, not r: r is the log-ratio COORDINATE plotted in panel (b) and
        # r_rad is the radiative coefficient. Three different r's would
        # otherwise sit in one figure.
        ax.text(0.97, 0.06, r"$\rho$ = %.3f" % r_par[st.PARAM_NAMES[k]],
                fontsize=st.FS_ANNOT, color=st.INK,
                transform=ax.transAxes, va="bottom", ha="right")
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)
        ax.set_xticks(XTICKS); ax.set_yticks(YTICKS)
        ax.set_xticklabels(X_LABELS.get((row, col), ["", "", ""]))
        ax.set_yticklabels(Y_LABELS.get((row, col), ["", "", ""]))
        ax.tick_params(labelsize=st.FS_TICK - 1.0)
        st.configure_axes(ax)

    pos = gs[0, :].get_position(fig).bounds
    axg = fig.add_axes(pos)
    axg.axis("off"); axg.patch.set_visible(False)
    axg.set_xlim(0, 1); axg.set_ylim(0, 1)
    axg.text(-0.052, 1.058, "(a)", fontsize=st.FS_PANEL, fontweight="bold",
             va="top", color=st.INK)
    axg.text(0.5, -0.098, r"True normalized log$_{10}$ parameter",
             fontsize=st.FS_TITLE, ha="center", va="top", color=st.INK)
    axg.text(-0.058, 0.5, r"Predicted normalized log$_{10}$ parameter",
             fontsize=st.FS_TITLE, rotation=90, ha="center", va="center",
             color=st.INK)
    # The provenance note sits above the grid, not below it: below, the
    # centred x-axis title runs into it at journal width.
    axg.text(1.0, 1.040,
             r"$n$ = 15,307   $\cdot$   dashed line is identity   "
             r"$\cdot$   $\rho$ = Pearson correlation",
             fontsize=st.FS_ANNOT, ha="right", va="bottom", color=st.MUTED)

    # ---------------- (b) shared scale vs log-ratio ------------------------
    axb = fig.add_subplot(gs[1, 0])
    x = np.arange(3)
    bw = 0.36
    a_vals = [float(co.loc[a, "pearson_r"]) for a, _ in PAIR_KEYS]
    r_vals = [float(co.loc[r, "pearson_r"]) for _, r in PAIR_KEYS]
    b1 = axb.bar(x - bw / 2, a_vals, bw, color=C_SHARED,
                 edgecolor="white", linewidth=0.5, zorder=3,
                 label="Shared scale $a$")
    b2 = axb.bar(x + bw / 2, r_vals, bw, color=C_RATIO,
                 edgecolor="white", linewidth=0.5, zorder=3,
                 label="Electron–hole ratio $r$")
    for bars, vals in ((b1, a_vals), (b2, r_vals)):
        for rect, v in zip(bars, vals):
            axb.text(rect.get_x() + rect.get_width() / 2, v + 0.020,
                     "%.3f" % v, ha="center", va="bottom",
                     fontsize=st.FS_ANNOT, color=st.INK, zorder=4)
    axb.set_xticks(x)
    axb.set_xticklabels(PAIR_TICK, fontsize=st.FS_ANNOT)
    axb.set_xlim(-0.62, 2.62)
    axb.set_ylim(0, 1.06)
    axb.set_yticks([0.0, 0.25, 0.5, 0.75, 1.0])
    axb.set_ylabel(r"Prediction correlation, Pearson $\rho$")
    axb.legend(loc="lower right", bbox_to_anchor=(1.0, 1.005),
               ncol=1, frameon=False, fontsize=st.FS_LEGEND,
               handlelength=1.2, handletextpad=0.5, borderpad=0.1)
    st.configure_axes(axb)
    st.panel_label(axb, "(b)", dx=-0.16, dy=1.10)
    # Below the axes, not beside the legend: at journal width the legend and a
    # top-anchored note overlap by more than 80 pt horizontally.
    axb.text(1.0, -0.150,
             "$\\rho$ is a Pearson correlation;\n"
             r"$r$ is the log-ratio $\log_{10}(p_n/p_p)$",
             transform=axb.transAxes, fontsize=st.FS_ANNOT - 0.6,
             color=st.MUTED, va="top", ha="right", linespacing=1.25)

    # ---------------- (c) MAE reduction vs training median -----------------
    axc = fig.add_subplot(gs[1, 1])
    a_red = [100.0 * float(co.loc[a, "mae_reduction"]) for a, _ in PAIR_KEYS]
    r_red = [100.0 * float(co.loc[r, "mae_reduction"]) for _, r in PAIR_KEYS]
    b1 = axc.bar(x - bw / 2, a_red, bw, color=C_SHARED,
                 edgecolor="white", linewidth=0.5, zorder=3,
                 label="Shared scale $a$")
    b2 = axc.bar(x + bw / 2, r_red, bw, color=C_RATIO,
                 edgecolor="white", linewidth=0.5, zorder=3,
                 label="Electron–hole ratio $r$")
    for bars, vals in ((b1, a_red), (b2, r_red)):
        for rect, v in zip(bars, vals):
            axc.text(rect.get_x() + rect.get_width() / 2, v + 1.8,
                     "%.1f%%" % v, ha="center", va="bottom",
                     fontsize=st.FS_ANNOT, color=st.INK, zorder=4)
    axc.axhline(0.0, color=st.MUTED, lw=0.9, zorder=4)
    axc.set_xticks(x)
    axc.set_xticklabels(PAIR_TICK, fontsize=st.FS_ANNOT)
    axc.set_xlim(-0.62, 2.62)
    # the range admits negatives on purpose: if a future recomputation gave a
    # negative improvement it must be drawn, not clipped
    axc.set_ylim(-8.0, 80.0)
    axc.set_yticks([0, 20, 40, 60, 80])
    axc.set_ylabel("MAE reduction vs\ntraining median (%)")
    axc.legend(loc="lower right", bbox_to_anchor=(1.0, 1.005),
               ncol=1, frameon=False, fontsize=st.FS_LEGEND,
               handlelength=1.2, handletextpad=0.5, borderpad=0.1)
    st.configure_axes(axc)
    st.panel_label(axc, "(c)", dx=-0.16, dy=1.10)
    axc.text(0.0, 1.005,
             "0% line = no improvement over baseline",
             transform=axc.transAxes, fontsize=st.FS_ANNOT - 0.6,
             color=st.MUTED, va="bottom", ha="left")
    axc.text(0.985, -0.150,
             r"$100\,(1-\mathrm{MAE_{model}}/\mathrm{MAE_{baseline}})$" "\n"
             r"baseline = training median, physical log$_{10}$ coords",
             transform=axc.transAxes, fontsize=st.FS_ANNOT - 0.6,
             color=st.MUTED, va="top", ha="right", linespacing=1.25)

    stem = os.path.join(st.FIGDIR, "Figure2"
                        + ("_large" if size == "large" else ""))
    st.save_fig(fig, stem)
    print("wrote:", stem)
    return fig


def main():
    for size in ("journal", "large"):
        build(size)

    # ---- light plotting table actually used (for the source record) ----
    co = pd.read_csv(COORD_CSV).set_index("coordinate")
    metr = pd.read_csv(METRICS_CSV).set_index("parameter")
    rows = []
    for (a, r), lab in zip(PAIR_KEYS, ["mobility", "bulk_lifetime", "dos"]):
        rows.append(dict(pair=lab, coordinate="a_shared_scale",
                         pearson_r=float(co.loc[a, "pearson_r"]),
                         mae_reduction=float(co.loc[a, "mae_reduction"]),
                         source=os.path.relpath(COORD_CSV, BASE)))
        rows.append(dict(pair=lab, coordinate="r_log_ratio",
                         pearson_r=float(co.loc[r, "pearson_r"]),
                         mae_reduction=float(co.loc[r, "mae_reduction"]),
                         source=os.path.relpath(COORD_CSV, BASE)))
    for k, n in enumerate(st.PARAM_NAMES):
        rows.append(dict(pair="nine_parameter", coordinate=n,
                         pearson_r=float(metr.loc[n, "pearson_r"]),
                         mae_reduction=np.nan,
                         source="evaluation_fixed/parameter_metrics.csv"))
    pd.DataFrame(rows).to_csv(
        os.path.join(st.DATADIR, "Figure2_plotting_values.csv"), index=False)
    print("wrote plotting table")


if __name__ == "__main__":
    main()
