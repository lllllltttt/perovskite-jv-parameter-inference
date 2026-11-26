# -*- coding: utf-8 -*-
"""
figS6_nineparam.py — supplementary figure S6: nine single-parameter parities.
=============================================================================
The nine individual-parameter scatter plots were panel (a) of the SUBMITTED
main Figure 2 (the 3 x 3 grid followed by two comparison panels). The
reassembled main Figure 2 is the paired-coordinate figure — shared scale
against electron-hole log-ratio — so the per-parameter grid moves here, to the
supplementary information, where it supports the same statement at the level of
the nine raw parameters.

Nothing is recomputed. The truth and prediction arrays are the frozen ones
(`_frozen_preds.npz`: `params_test`, `param_mu`), all 15,307 test curves are
drawn in every cell, and the nine Pearson coefficients are asserted against
`evaluation_fixed/parameter_metrics.csv` before the figure is built, so a
layout change can never move a number.

Coordinates are the NORMALIZED log10 parameters — the space the model and its
scaler work in (Methods, "Partitioning and preprocessing") — not physical
log10. The physical-coordinate statement is the main Figure 2; this grid is
the per-parameter companion to it.

Outputs: figures/FigureS6_nineparam{,_large}.{png,pdf,svg}
         data_used/FigureS6_nineparam_values.csv
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

METRICS_CSV = os.path.join(st.BASE, "evaluation_fixed", "parameter_metrics.csv")

R_EXPECT = {                       # evaluation_fixed/parameter_metrics.csv
    "mu_n_pvk": 0.906268, "mu_p_pvk": 0.919434, "tau_n_pvk": 0.878266,
    "tau_p_pvk": 0.880803, "Nc_eff_pvk": 0.909047, "Nv_eff_pvk": 0.895604,
    "tau_ETL": 0.593605, "tau_HTL": 0.719923, "rad_c": 0.559174,
}
N_TEST = 15307

XTICKS = [0.0, 0.5, 1.0]
X_LABELS = {(2, 0): ["0.0", "0.5", ""], (2, 1): ["", "0.5", ""],
            (2, 2): ["", "0.5", "1.0"]}
Y_LABELS = {(0, 0): ["", "0.5", "1.0"], (1, 0): ["", "0.5", ""],
            (2, 0): ["0.0", "0.5", ""]}


def load():
    d = np.load(st.NPZ)
    y_true, y_pred = d["params_test"], d["param_mu"]
    assert y_true.shape == (N_TEST, 9), y_true.shape
    assert y_pred.shape == (N_TEST, 9), y_pred.shape
    metr = pd.read_csv(METRICS_CSV).set_index("parameter")
    for nm, exp in R_EXPECT.items():
        got = float(metr.loc[nm, "pearson_r"])
        assert abs(got - exp) < 5e-7, (nm, got, exp)
    return y_true, y_pred, metr


def build(size):
    y_true, y_pred, metr = load()
    w = st.set_fig_width(size)
    fig = plt.figure(figsize=(w, w * 0.960))
    gs = fig.add_gridspec(1, 1, left=0.098, right=0.988, top=0.946,
                          bottom=0.088)
    gsa = GridSpecFromSubplotSpec(3, 3, subplot_spec=gs[0, 0],
                                  wspace=0.16, hspace=0.16)
    for k in range(9):
        row, col = divmod(k, 3)
        ax = fig.add_subplot(gsa[row, col])
        ax.scatter(y_true[:, k], y_pred[:, k], s=2.0, alpha=0.10,
                   color=st.OKABE_ITO[0], linewidths=0, rasterized=True)
        ax.plot([0, 1], [0, 1], ls="--", color="#555555", lw=0.8, zorder=3)
        ax.text(0.06, 0.94, st.PARAM_LABELS[k], fontsize=st.FS_ANNOT,
                fontweight="bold", color=st.INK, transform=ax.transAxes,
                va="top", ha="left")
        # rho, not r: r is the electron-hole log-ratio coordinate of the main
        # Figure 2 and r_rad is the radiative coefficient. Three different r's
        # would otherwise share one figure.
        ax.text(0.97, 0.06, r"$\rho$ = %.3f" % R_EXPECT[st.PARAM_NAMES[k]],
                fontsize=st.FS_ANNOT, color=st.INK,
                transform=ax.transAxes, va="bottom", ha="right")
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)
        ax.set_xticks(XTICKS); ax.set_yticks(XTICKS)
        ax.set_xticklabels(X_LABELS.get((row, col), ["", "", ""]))
        ax.set_yticklabels(Y_LABELS.get((row, col), ["", "", ""]))
        ax.tick_params(labelsize=st.FS_TICK - 1.0)
        st.configure_axes(ax)

    pos = gs[0, 0].get_position(fig).bounds
    axg = fig.add_axes(pos)
    axg.axis("off"); axg.patch.set_visible(False)
    axg.set_xlim(0, 1); axg.set_ylim(0, 1)
    axg.text(0.5, -0.062, r"True normalized log$_{10}$ parameter",
             fontsize=st.FS_TITLE, ha="center", va="top", color=st.INK)
    axg.text(-0.058, 0.5, r"Predicted normalized log$_{10}$ parameter",
             fontsize=st.FS_TITLE, rotation=90, ha="center", va="center",
             color=st.INK)
    axg.text(0.5, 1.020,
             r"$n$ = 15,307 test curves   $\cdot$   dashed line is the "
             r"identity   $\cdot$   $\rho$ is the Pearson correlation",
             fontsize=st.FS_ANNOT, ha="center", va="bottom", color=st.MUTED)

    stem = os.path.join(st.FIGDIR, "FigureS6_nineparam"
                        + ("_large" if size == "large" else ""))
    st.save_fig(fig, stem)
    print("wrote:", stem)


def main():
    for sz in ("journal", "large"):
        build(sz)
    y_true, y_pred, metr = load()
    rows = []
    for k, nm in enumerate(st.PARAM_NAMES):
        rows.append(dict(parameter=nm, unit=st.PARAM_LABELS[k],
                         pearson_r=R_EXPECT[nm],
                         n_test=int(y_true.shape[0]),
                         space="normalized log10 (model space)",
                         source="final_figures/scripts/_frozen_preds.npz "
                                "(params_test, param_mu); rho cross-checked "
                                "against evaluation_fixed/parameter_metrics.csv"))
    pd.DataFrame(rows).to_csv(
        os.path.join(st.DATADIR, "FigureS6_nineparam_values.csv"), index=False)
    print("wrote FigureS6_nineparam_values.csv")


if __name__ == "__main__":
    main()
