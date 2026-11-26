"""
plot_Fig3_recoverability_micropatch.py — Fig. 3 minimal finishing micro-patch.
===============================================================================
This variant is IDENTICAL to Fig3_recoverability_labeltune_bonly EXCEPT three
micro-patches (and nothing else):

  1) panel (b) top-right four parameter-label offsets nudged for a clearer
     hierarchy (mu_p slightly left, mu_n slightly right, tau_p slightly
     upper-left, tau_n slightly lower-left).  The other five labels
     (N_c, N_v, tau_ETL, tau_HTL, r_rad) are UNCHANGED from labeltune_bonly.
  2) panel (b) Spearman note moved a little left and slightly up
     (axes-fraction (0.97, 0.04) -> (0.94, 0.06)); text content unchanged.
  3) panel (a) shared axis titles typeset log10 as mathtext:
       "True normalized log10 parameter"      -> "True normalized log$_{10}$ parameter"
       "Predicted normalized log10 parameter" -> "Predicted normalized log$_{10}$ parameter"
     (position / font-size / weight / color unchanged; no subplot text touched).

STRICTLY unchanged: data, scatter coordinates, axes ranges, font-size system,
colors, line styles, panel layout, figure size, export formats, panel (a)
9-panel content, r values, Spearman statistic, (a)/(b) tags, tick labels.

Frozen sources: sensitivity_recomputed/sensitivity_recomputed.csv (S_log,
authoritative), evaluation_fixed/parameter_metrics.csv (Pearson r,
authoritative), final_figures/scripts/_frozen_preds.npz (per-sample
predictions). No data is altered or recomputed.

Outputs:
  final_figures/Fig3/Fig3_recoverability_micropatch.png / .pdf / .svg
  final_figures/Fig3/Fig3_recoverability_micropatch_large.png/.pdf/.svg
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

# Panel (b) parameter order (unchanged).
PARAM_ORDER = ["mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk",
               "Nc_eff_pvk", "Nv_eff_pvk", "tau_ETL", "tau_HTL", "rad_c"]
# [micropatch] 2026-08-28 top-right four nudged vs labeltune_bonly
#   (mu_p was (-15,4), mu_n (15,3), tau_p (-18,2), tau_n (-18,-12));
#   other five offsets byte-identical to labeltune_bonly.
# Each entry: (dx, dy, ha, va, shrinkA).
LABEL_OFFSETS = [
    (18, 3, "left", "bottom", 2),     #  mu_n    slightly right
    (-18, 4, "right", "top", 2),      #  mu_p    slightly left
    (-20, -14, "right", "top", 2),    #  tau_n   slightly lower-left
    (-20, 3, "right", "bottom", 2),   #  tau_p   slightly upper-left
    (-12, 2, "right", "bottom", 2),   #  N_c     UNCHANGED
    (-12, -14, "right", "top", 2),    #  N_v     UNCHANGED
    (16, -4, "left", "top", 7),       #  tau_ETL UNCHANGED
    (12, -15, "left", "top", 4),      #  tau_HTL UNCHANGED
    (18, 3, "left", "top", 7),        #  r_rad   UNCHANGED
]
LEAD_COLOR = "0.65"

# [micropatch] Spearman note: moved a little left and slightly up
# (was (0.97, 0.04)) to sit more calmly, away from the corner.
SPEARMAN_XY = (0.94, 0.06)

# [annotfix6, frozen] edge-label subsetting on panel (a). UNCHANGED.
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
        # [frozen] identical block from annotfix6 / labeltune_bonly -- do not touch.
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
        # [micropatch] ONLY the mathtext typesetting changed ("log10" -> "log$_{10}$");
        # frac / size / weight / color identical to labeltune_bonly.
        axg.text(0.5, -0.088, r"True normalized log$_{10}$ parameter",
                 fontsize=st.FS_TITLE, ha="center", va="top", color=INK)
        axg.text(-0.098, 0.5, r"Predicted normalized log$_{10}$ parameter",
                 fontsize=st.FS_TITLE, rotation=90, ha="center", va="center",
                 color=INK)

        # ---------------- (b) S_log vs recoverability ----------------
        # [micropatch] data / axes / markers / Spearman text IDENTICAL to
        # labeltune_bonly; only LABEL_OFFSETS + SPEARMAN_XY above changed.
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
        axb.text(SPEARMAN_XY[0], SPEARMAN_XY[1],
                 r"Spearman $\rho_s$ = 0.533,  $p$ = 0.139"
                 "\n(non-significant)",
                 transform=axb.transAxes, fontsize=st.FS_ANNOT, va="bottom",
                 ha="right", color=INK, linespacing=1.35)
        axb.text(0.0, 1.06, "(b)", fontsize=st.FS_PANEL, fontweight="bold",
                 va="top", transform=axb.transAxes, color=INK)

        stem = os.path.join(OUT_DIR, "Fig3_recoverability_micropatch"
                            + ("_large" if size == "large" else ""))
        st.save_fig(fig, stem, svg=True)
        print("wrote:", stem)


if __name__ == "__main__":
    main()
