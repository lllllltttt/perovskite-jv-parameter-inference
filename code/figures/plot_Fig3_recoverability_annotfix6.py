"""
plot_Fig3_recoverability_annotfix6.py — Fig. 3 of the FINAL figure package.
===========================================================================
(a) 3x3 parity plots: true vs predicted parameters, normalized log10 space
    (shared [0,1] axes, y = x, Pearson r per parameter). All 15,307 test
    points preserved; each panel carries its mathematical parameter label and
    the frozen Pearson r.
(b) Correlation-based J-V linear sensitivity S_log (recomputed, log10
    parameter space, test set) vs parameter recoverability (Pearson r).

2026-08-28 REDESIGN (annotfix6) — layout reference: legacy
    9D-HTL-new/fig_parameter_scatter_all9.png (3600x3600, 9 LARGE square
    panels). The legacy PNG is used ONLY as a visual/layout reference; it is
    NOT embedded, upscaled, cropped, or reused. Panel (a) is rebuilt from the
    authoritative frozen arrays (final_figures/scripts/_frozen_preds.npz).
    Changes vs annotfix5:
      * REAL inner spacing: the 3x3 now lives on a nested
        GridSpecFromSubplotSpec with wspace=hspace=0.10 (was inset_axes with
        hand-tuned PAD_F). Panels grow to ~84 x 69 pt (journal, +~68% area vs
        annotfix5), aspect ~1.22 (approximately square), with a real gap
        between every pair of subplots.
      * EDGE-LABEL SUBSETTING (the collision killer): numeric x labels appear
        only on the bottom row and numeric y labels only on the left column,
        AND each outer panel drops the labels that would cross a boundary:
          bottom-left : x 0.0, 0.5          (1.0 suppressed)
          bottom-mid  : x 0.5               (0.0, 1.0 suppressed)
          bottom-right: x 0.5, 1.0          (0.0 suppressed)
          top-left    : y 0.5, 1.0          (0.0 suppressed)
          middle-left : y 0.5               (0.0, 1.0 suppressed)
          bottom-left : y 0.0, 0.5          (1.0 suppressed)
        All other panels keep ticks but no numeric labels. No two numeric
        tick labels can ever touch, regardless of gap size.
      * shared axis labels (manuscript): "True normalized log10 parameter"
        below all bottom-row ticks (axg-frac y = -0.088, va=top, ~6.5 pt
        clearance) and "Predicted normalized log10 parameter" left of the
        grid (x = -0.098, rotated 90, ~5 pt clearance from the tick labels).
      * width allocation: width_ratios [1.7, 1.0] => panel (a) ~63% / panel
        (b) ~37% of the grid width.
      * panel (b) UNCHANGED from annotfix5: same data, same point-offset
        annotations, same labels; only its cell width differs.
    Data, parameter order, Pearson r, S_log, and Spearman statistic are all
    frozen and untouched.

Frozen sources: sensitivity_recomputed/sensitivity_recomputed.csv (S_log,
authoritative), evaluation_fixed/parameter_metrics.csv (Pearson r,
authoritative), final_figures/scripts/_frozen_preds.npz (per-sample
predictions). No data is altered or recomputed.

Outputs:
  final_figures/Fig3/Fig3_recoverability_annotfix6.png / .pdf / .svg
  final_figures/Fig3/Fig3_recoverability_annotfix6_large.png / .pdf / .svg
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

# Panel (b): FIXED annotate offsets (identical to annotfix5/annotfix4).
PARAM_ORDER = ["mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk",
               "Nc_eff_pvk", "Nv_eff_pvk", "tau_ETL", "tau_HTL", "rad_c"]
LABEL_OFFSETS = [
    (10, 4, "left", "bottom"),      #  mu_n
    (-10, -4, "right", "bottom"),   #  mu_p
    (-10, 4, "right", "bottom"),    #  tau_n
    (-12, 16, "right", "bottom"),   #  tau_p
    (-12, 4, "right", "center"),    #  N_c
    (-12, -12, "right", "top"),     #  N_v
    (10, 0, "left", "top"),         #  tau_ETL
    (10, -12, "left", "top"),       #  tau_HTL
    (10, 0, "left", "center"),      #  r_rad
]
LEAD_COLOR = "0.65"

# [annotfix6] edge-label subsetting: numeric x labels only on the bottom row,
# numeric y labels only on the left column, with boundary-crossing labels
# suppressed so no two tick labels ever collide. Keyed by (row, col), row 0 top.
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
        # [annotfix6] width_ratios [1.7, 1.0] => (a) ~63% / (b) ~37%. Height
        # 0.54w so the (a) 3x3 panels are large and ~square.
        fig = plt.figure(figsize=(w, w * 0.54))
        gs = fig.add_gridspec(1, 2, width_ratios=[1.7, 1.0],
                              left=0.085, right=0.99, top=0.90, bottom=0.10,
                              wspace=0.17)

        # ---------------- (a) 3x3 parity, REAL-spacing nested grid ----------------
        # [annotfix6] a true nested GridSpec (wspace/hspace = 0.10) lays the
        # panels out with a real gap between every subplot -- no touching axes.
        gsa = GridSpecFromSubplotSpec(3, 3, subplot_spec=gs[0, 0],
                                      wspace=0.10, hspace=0.10)
        for k in range(9):
            row, col = divmod(k, 3)            # row 0 top .. row 2 bottom
            ax = fig.add_subplot(gsa[row, col])
            ax.scatter(y_true[:, k], y_pred[:, k], s=3, alpha=0.12,
                       color=st.OKABE_ITO[0], linewidths=0, rasterized=True)
            ax.plot([0, 1], [0, 1], ls="--", color="#555555", lw=0.8)
            # manuscript parameter label (top-left) + frozen r (bottom-right)
            ax.text(0.06, 0.94, PARAM_LABELS[k], fontsize=st.FS_ANNOT,
                    fontweight="bold", color=INK, transform=ax.transAxes,
                    va="top", ha="left")
            ax.text(0.97, 0.06, r"$r$ = %.3f" % r_par[st.PARAM_NAMES[k]],
                    fontsize=st.FS_ANNOT, color=INK, transform=ax.transAxes,
                    va="bottom", ha="right")
            ax.set_xlim(0, 1); ax.set_ylim(0, 1)
            ax.set_xticks(XTICKS); ax.set_yticks(YTICKS)
            # [annotfix6] subset tick labels per the edge rule
            ax.set_xticklabels(X_LABELS.get((row, col), ["", "", ""]))
            ax.set_yticklabels(Y_LABELS.get((row, col), ["", "", ""]))
            st.configure_axes(ax)

        # Overlay (invisible) axes for the (a) tag and the shared axis labels,
        # added AFTER the subplots so its text draws on top.
        pos = gs[0, 0].get_position(fig).bounds
        axg = fig.add_axes(pos)
        axg.axis("off"); axg.patch.set_visible(False)
        axg.set_xlim(0, 1); axg.set_ylim(0, 1)
        axg.text(0.0, 1.06, "(a)", fontsize=st.FS_PANEL, fontweight="bold",
                 va="top", color=INK)
        # [annotfix6] shared axis labels: x below all bottom-row ticks
        # (va=top; axg-frac -0.088 puts the label block ~6.5 pt clear of the
        # bottom tick band, measured in figure coords), y left of the grid
        # (frac -0.098 puts it ~5 pt clear of the left-column tick labels).
        axg.text(0.5, -0.088, "True normalized log10 parameter",
                 fontsize=st.FS_TITLE, ha="center", va="top", color=INK)
        axg.text(-0.098, 0.5, "Predicted normalized log10 parameter",
                 fontsize=st.FS_TITLE, rotation=90, ha="center", va="center",
                 color=INK)

        # ---------------- (b) S_log vs recoverability ----------------
        # [annotfix6] UNCHANGED from annotfix5: same data, annotations, labels.
        axb = fig.add_subplot(gs[0, 1])
        axb.scatter(Slog, r_recover, s=46, color=st.OKABE_ITO[2], alpha=0.92,
                    edgecolor="white", linewidth=0.6, zorder=3)
        Slog_by = dict(zip(sens["parameter"], Slog))
        r_by = dict(zip(metr["parameter"], r_recover))
        xb = [Slog_by[p] for p in PARAM_ORDER]
        yb = [r_by[p] for p in PARAM_ORDER]
        for i, (dx, dy, ha, va) in enumerate(LABEL_OFFSETS):
            axb.annotate(PARAM_LABELS[i], xy=(xb[i], yb[i]),
                         xytext=(dx, dy), textcoords="offset points",
                         ha=ha, va=va,
                         fontsize=st.FS_ANNOT, color=INK,
                         arrowprops=dict(arrowstyle="-", color=LEAD_COLOR,
                                         lw=0.8),
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

        stem = os.path.join(OUT_DIR, "Fig3_recoverability_annotfix6"
                            + ("_large" if size == "large" else ""))
        st.save_fig(fig, stem, svg=True)
        print("wrote:", stem)


if __name__ == "__main__":
    main()
