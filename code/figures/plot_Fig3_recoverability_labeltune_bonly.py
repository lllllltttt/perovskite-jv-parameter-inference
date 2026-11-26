"""
plot_Fig3_recoverability_labeltune_bonly.py — Fig. 3 panel-(b)-labels-only micro-tune.
===============================================================================
This variant is IDENTICAL to Fig3_recoverability_annotfix6 EXCEPT for the nine
panel-(b) parameter-label OFFSETS (and their leader lines). Everything else is
frozen and byte-identical to annotfix6:

  * panel (a) 3x3 parity grid: same nested GridSpecFromSubplotSpec(3,3,
    wspace=hspace=0.10), same scatter data/alpha/marker, same identity line,
    same parameter labels, same frozen Pearson r, same edge-label tick
    subsetting, same shared axis labels -- NOT touched.
  * panel (b) scatter data (S_log vs Pearson r), axes limits, point markers,
    colors, Spearman annotation, (b) tag, figure size and export formats --
    NOT touched.
  * ONLY the 9 annotation (label position + ha/va + leader line) offsets below
    changed, to de-crowd the top-right cluster (mu_n/mu_p/tau_n/tau_p), stagger
    the bottom-left pair (tau_ETL / r_rad), open the top-left pair (N_c / N_v),
    and give tau_HTL a little more air.

Frozen sources: sensitivity_recomputed/sensitivity_recomputed.csv (S_log,
authoritative), evaluation_fixed/parameter_metrics.csv (Pearson r,
authoritative), final_figures/scripts/_frozen_preds.npz (per-sample
predictions). No data is altered or recomputed.

Outputs:
  final_figures/Fig3/Fig3_recoverability_labeltune_bonly.png / .pdf / .svg
  final_figures/Fig3/Fig3_recoverability_labeltune_bonly_large.png/.pdf/.svg
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpecFromSubplotSpec
from scipy.stats import spearmanr

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import figure_style as st

BASE = os.path.dirname(os.path.dirname(HERE))
OUT_DIR = os.path.join(BASE, "final_figures", "Fig3")
os.makedirs(OUT_DIR, exist_ok=True)

NPZ = os.path.join(HERE, "_frozen_preds.npz")
SENS_CSV = os.path.join(BASE, "sensitivity_recomputed", "sensitivity_recomputed.csv")
METRICS_CSV = os.path.join(BASE, "evaluation_fixed", "parameter_metrics.csv")

SLOG_EXPECTED = {
    "mu_n_pvk": 0.371, "mu_p_pvk": 0.374, "tau_n_pvk": 0.499,
    "tau_p_pvk": 0.498, "Nc_eff_pvk": 0.107, "Nv_eff_pvk": 0.113,
    "tau_ETL": 0.039, "tau_HTL": 0.061, "rad_c": 0.035,
}

INK = "#22262b"

# 2026-08-28 notation fix (Fig.3 ONLY): r_ad -> r_rad.
PARAM_LABELS = list(st.PARAM_LABELS)
PARAM_LABELS[8] = r"$r_\mathrm{rad}$"

# Panel (b) parameter order (unchanged from annotfix6).
PARAM_ORDER = ["mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk",
               "Nc_eff_pvk", "Nv_eff_pvk", "tau_ETL", "tau_HTL", "rad_c"]
# [labeltune_bonly] 2026-08-28 de-crowded offsets (was annotfix5/6 frozen set).
#   top-right cluster:  mu_p upper-left, mu_n upper-right,
#                       tau_p upper-left, tau_n lower-left  (clear of each other)
#   bottom-left pair:   tau_ETL right/slightly-below, r_rad right (staggered)
#   top-left pair:      N_c upper-left, N_v lower-left (opened gap)
#   middle-left:        tau_HTL bottom-right, a little farther from its point
# Each entry: (dx, dy, ha, va, shrinkA).  shrinkA is the leader's gap at the
# TEXT end (FancyArrowPatch "A" = xytext): tau_ETL / tau_HTL / r_rad get a
# larger gap because their mathtext glyphs overhang the anchor box (tau has a
# ~6 pt negative left bearing, subscripts hang below), so without it the leader
# line pierces the drawn glyphs. Verified in the PDF glyph spans.
LABEL_OFFSETS = [
    (15, 3, "left", "bottom", 2),     #  mu_n    upper-right of its point
    (-15, 4, "right", "top", 2),      #  mu_p    upper-left of its point
    (-18, -12, "right", "top", 2),    #  tau_n   lower-left of its point
    (-18, 2, "right", "bottom", 2),   #  tau_p   upper-left of its point
    (-12, 2, "right", "bottom", 2),   #  N_c     upper-left of its point
    (-12, -14, "right", "top", 2),    #  N_v     lower-left of its point
    (16, -4, "left", "top", 7),       #  tau_ETL right, slightly below
    (12, -15, "left", "top", 4),      #  tau_HTL bottom-right, farther out
    (18, 3, "left", "top", 7),        #  r_rad   right of its point
]
LEAD_COLOR = "0.65"

# [annotfix6, frozen] edge-label subsetting on panel (a): numeric x labels only
# on the bottom row, numeric y labels only on the left column, with
# boundary-crossing labels suppressed. UNCHANGED here.
XTICKS = [0.0, 0.5, 1.0]
YTICKS = [0.0, 0.5, 1.0]
X_LABELS = {
    (2, 0): ["0.0", "0.5", ""],          # bottom-left  : 0.0, 0.5 (1.0 out)
    (2, 1): ["", "0.5", ""],             # bottom-middle: only 0.5
    (2, 2): ["", "0.5", "1.0"],          # bottom-right : 0.5, 1.0 (0.0 out)
}
Y_LABELS = {
    (0, 0): ["", "0.5", "1.0"],          # top-left    : 0.5, 1.0 (0.0 out)
    (1, 0): ["", "0.5", ""],             # middle-left : only 0.5
    (2, 0): ["0.0", "0.5", ""],          # bottom-left : 0.0, 0.5 (1.0 out)
}


def main():
    d = np.load(NPZ)
    y_true = d["params_test"]          # normalized log10, 15,307 rows
    y_pred = d["param_mu"]

    sens = pd.read_csv(SENS_CSV).sort_values("parameter")
    metr = pd.read_csv(METRICS_CSV).sort_values("parameter")
    Slog = sens["S_log"].values
    r_recover = metr["pearson_r"].values
    pnames = sens["parameter"].values

    for nm, exp in SLOG_EXPECTED.items():
        got = float(sens.loc[sens["parameter"] == nm, "S_log"].iloc[0])
        assert abs(got - exp) < 1e-3, (nm, got, exp)
    rho, pval = spearmanr(Slog, r_recover)
    print("Spearman(S_log, r) = %.4f  p = %.4f" % (rho, pval))
    assert abs(rho - 0.533) < 1e-3 and abs(pval - 0.139) < 1e-2, "Spearman mismatch!"
    r_par = dict(zip(pnames, r_recover))

    for size in ("journal", "large"):
        w = st.set_fig_width(size)
        fig = plt.figure(figsize=(w, w * 0.54))
        gs = fig.add_gridspec(1, 2, width_ratios=[1.7, 1.0],
                              left=0.085, right=0.99, top=0.90, bottom=0.10,
                              wspace=0.17)

        # ---------------- (a) 3x3 parity, REAL-spacing nested grid ----------------
        # [annotfix6, frozen] identical block -- do not touch.
        gsa = GridSpecFromSubplotSpec(3, 3, subplot_spec=gs[0, 0],
                                      wspace=0.10, hspace=0.10)
        for k in range(9):
            row, col = divmod(k, 3)            # row 0 top .. row 2 bottom
            ax = fig.add_subplot(gsa[row, col])
            ax.scatter(y_true[:, k], y_pred[:, k], s=3, alpha=0.12,
                       color=st.OKABE_ITO[0], linewidths=0, rasterized=True)
            ax.plot([0, 1], [0, 1], ls="--", color="#555555", lw=0.8)
            ax.text(0.06, 0.94, PARAM_LABELS[k], fontsize=st.FS_ANNOT,
                    fontweight="bold", color=INK, transform=ax.transAxes,
                    va="top", ha="left")
            ax.text(0.97, 0.06, r"$r$ = %.3f" % r_par[st.PARAM_NAMES[k]],
                    fontsize=st.FS_ANNOT, color=INK, transform=ax.transAxes,
                    va="bottom", ha="right")
            ax.set_xlim(0, 1); ax.set_ylim(0, 1)
            ax.set_xticks(XTICKS); ax.set_yticks(YTICKS)
            ax.set_xticklabels(X_LABELS.get((row, col), ["", "", ""]))
            ax.set_yticklabels(Y_LABELS.get((row, col), ["", "", ""]))
            st.configure_axes(ax)

        pos = gs[0, 0].get_position(fig).bounds
        axg = fig.add_axes(pos)
        axg.axis("off"); axg.patch.set_visible(False)
        axg.set_xlim(0, 1); axg.set_ylim(0, 1)
        axg.text(0.0, 1.06, "(a)", fontsize=st.FS_PANEL, fontweight="bold",
                 va="top", color=INK)
        axg.text(0.5, -0.088, "True normalized log10 parameter",
                 fontsize=st.FS_TITLE, ha="center", va="top", color=INK)
        axg.text(-0.098, 0.5, "Predicted normalized log10 parameter",
                 fontsize=st.FS_TITLE, rotation=90, ha="center", va="center",
                 color=INK)

        # ---------------- (b) S_log vs recoverability ----------------
        # [labeltune_bonly] data / axes / markers / Spearman text IDENTICAL to
        # annotfix6; only the LABEL_OFFSETS above changed.
        axb = fig.add_subplot(gs[0, 1])
        axb.scatter(Slog, r_recover, s=46, color=st.OKABE_ITO[2], alpha=0.92,
                    edgecolor="white", linewidth=0.6, zorder=3)
        Slog_by = dict(zip(sens["parameter"], Slog))
        r_by = dict(zip(metr["parameter"], r_recover))
        xb = [Slog_by[p] for p in PARAM_ORDER]
        yb = [r_by[p] for p in PARAM_ORDER]
        for i, (dx, dy, ha, va, sA) in enumerate(LABEL_OFFSETS):
            axb.annotate(PARAM_LABELS[i], xy=(xb[i], yb[i]),
                         xytext=(dx, dy), textcoords="offset points",
                         ha=ha, va=va,
                         fontsize=st.FS_ANNOT, color=INK,
                         arrowprops=dict(arrowstyle="-", color=LEAD_COLOR,
                                         lw=0.8, shrinkA=sA),
                         annotation_clip=True,
                         zorder=6)
        axb.set_xlabel(r"Correlation-based J–V sensitivity, $S_{\log}$")
        axb.set_ylabel(r"Parameter recoverability, Pearson $r$")
        axb.yaxis.set_label_coords(-0.12, 0.5)
        st.configure_axes(axb)
        axb.text(0.97, 0.04,
                 r"Spearman $\rho_s$ = 0.533,  $p$ = 0.139"
                 "\n(non-significant)",
                 transform=axb.transAxes, fontsize=st.FS_ANNOT, va="bottom",
                 ha="right", color=INK, linespacing=1.35)
        axb.text(0.0, 1.06, "(b)", fontsize=st.FS_PANEL, fontweight="bold",
                 va="top", transform=axb.transAxes, color=INK)

        stem = os.path.join(OUT_DIR, "Fig3_recoverability_labeltune_bonly"
                            + ("_large" if size == "large" else ""))
        st.save_fig(fig, stem, svg=True)
        print("wrote:", stem)


if __name__ == "__main__":
    main()
