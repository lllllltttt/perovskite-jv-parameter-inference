"""
plot_Fig3_recoverability.py — Fig. 3 of the FINAL figure package.
=================================================================
(a) 3x3 parity plots: true vs predicted parameters, normalized log10 space
    (shared [0,1] axes, y = x, Pearson r per parameter). All 15,307 test
    points preserved; each panel carries its mathematical parameter label and
    the frozen Pearson r. Labels simplified: single shared "true" / "predicted"
    axes, ticks only on the outer row/column.
(b) Correlation-based J-V linear sensitivity S_log (recomputed, log10
    parameter space, test set) vs parameter recoverability (Pearson r).
    Panel is given substantially more horizontal space; the nine parameters
    carry mathematical labels anchored to their OWN data points with FIXED
    annotate offsets (points) and thin light-gray leader lines — no automatic
    repulsion. All labels are placed INWARD (toward the center of the axes)
    so none extends outside the plotting frame. tau_n/tau_p point LEFTWARD
    from their right-edge points; tau_ETL/r_ad point RIGHTWARD from their
    left-edge points. No regression line; the Spearman statistic is placed
    in an empty region.
    Spearman rho_s = 0.533, p = 0.139 (NOT significant) — plotted without
    significance asterisks.

2026-08-28 FIX (annotfix3): panel (a)'s Pearson-r annotations were all
assigned to the WRONG parameter. Panel index k is the CANONICAL order (same
as y_true/pred[:, k] and st.PARAM_LABELS[k]), but the r annotation indexed
r_par[pnames[k]] where pnames is the ALPHABETICALLY-sorted parameter list, so
every subplot showed another parameter's frozen r. Fixed by indexing with
st.PARAM_NAMES[k] (the canonical column order). Scatter data, labels, and
frozen r values untouched; only the r text is now attached to its OWN panel.
Notation: r_ad -> r_rad (overridden locally, figure_style.PARAM_LABELS shared
with FigS2). Panel (b) was already correct and is unchanged.

2026-08-28 LAYOUT fix (annotfix4): panel (a)'s 7.5-pt tick labels overhang
~5 pt past each axis edge, but the 0.96 inset factor left only ~2.6 pt between
subplots, so the bottom-row x labels ("1.0"/"0.0") and the left-column y labels
collided at every subplot boundary. Panels are now centered in their cells at
0.82 of the cell width/height (gaps ~11.5 pt), so edge labels never touch.
Tick-label visibility is unchanged: x numbers only on the bottom row, y numbers
only on the left column, interior panels keep ticks only. Shared "true" /
"predicted" labels, data, parameter order, r values, colors, and panel (b) are
all unchanged.

Frozen sources: sensitivity_recomputed/sensitivity_recomputed.csv (S_log,
authoritative), evaluation_fixed/parameter_metrics.csv (Pearson r,
authoritative), final_figures/scripts/_frozen_preds.npz (per-sample
predictions). No data is altered or recomputed.

Outputs:
  final_figures/Fig3/Fig3_recoverability_annotfix4.png / .pdf / .svg
  final_figures/Fig3/Fig3_recoverability_annotfix4_large.png / .pdf / .svg
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
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

# 2026-08-28 notation fix (Fig.3 ONLY): r_ad -> r_rad. figure_style.PARAM_LABELS
# is shared with FigS2, so override locally instead of editing the style file.
PARAM_LABELS = list(st.PARAM_LABELS)
PARAM_LABELS[8] = r"$r_\mathrm{rad}$"


# Panel (b): FIXED annotate offsets — no automatic repulsion. Each parameter's
# label is anchored to its OWN data point (labels are paired to points by
# parameter name, in st.PARAM_LABELS paper order) and offset in points via
# (dx, dy, ha, va). All labels point INWARD (toward the axes center) so none
# extends outside the plotting frame; tau_n/tau_p go LEFTWARD from their
# right-edge points, tau_ETL/r_ad go RIGHTWARD from their left-edge points.
#
# DEVIATIONS from the user's verbatim offset spec, forced by the hard rules
# (no label outside the plotting frame / no label-label overlap):
#   * mu_p  (10,-10) -> (-10,-4): mu_p is the highest point (r=0.919); the
#     verbatim +10pt with va=bottom placed the text 0.903-0.938, ABOVE the
#     top frame (0.900). Moved down-left (inward) to stay inside.
#   * tau_n dy 8 -> 4 and tau_p dy 12 -> 16: the two right-edge points are
#     nearly coincident (dy~0.005); verbatim offsets made their leftward
#     labels overlap. Separated vertically (tau_p above tau_n).
#   * tau_ETL dy -12 -> 0: verbatim label overlapped rad_c's (both point
#     rightward from close left-edge points). Raised tau_ETL to clear rad_c.
PARAM_ORDER = ["mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk",
               "Nc_eff_pvk", "Nv_eff_pvk", "tau_ETL", "tau_HTL", "rad_c"]
LABEL_OFFSETS = [
    (10, 4, "left", "bottom"),      #  mu_n    up-right (inward)
    (-10, -4, "right", "bottom"),   #  mu_p    down-left (inward) [dy 10->-4]
    (-10, 4, "right", "bottom"),    #  tau_n   LEFTWARD from right-edge [dy 8->4]
    (-12, 16, "right", "bottom"),   #  tau_p   LEFTWARD from right-edge [dy 12->16]
    (-12, 4, "right", "center"),    #  N_c     left (inward)
    (-12, -12, "right", "top"),     #  N_v     down-left (inward)
    (10, 0, "left", "top"),         #  tau_ETL RIGHTWARD from left-edge [dy -12->0]
    (10, -12, "left", "top"),       #  tau_HTL down-right (inward)
    (10, 0, "left", "center"),      #  r_ad    RIGHTWARD from left-edge
]
LEAD_COLOR = "0.65"   # thin light-gray leader lines (matplotlib gray 65%)


def main():
    d = np.load(NPZ)
    y_true = d["params_test"]          # normalized log10, 15,307 rows
    y_pred = d["param_mu"]

    sens = pd.read_csv(SENS_CSV).sort_values("parameter")
    metr = pd.read_csv(METRICS_CSV).sort_values("parameter")
    Slog = sens["S_log"].values
    r_recover = metr["pearson_r"].values
    pnames = sens["parameter"].values

    # sanity: S_log matches frozen manuscript numbers (keyed by parameter)
    for nm, exp in SLOG_EXPECTED.items():
        got = float(sens.loc[sens["parameter"] == nm, "S_log"].iloc[0])
        assert abs(got - exp) < 1e-3, (nm, got, exp)
    rho, pval = spearmanr(Slog, r_recover)
    print("Spearman(S_log, r) = %.4f  p = %.4f" % (rho, pval))
    assert abs(rho - 0.533) < 1e-3 and abs(pval - 0.139) < 1e-2, "Spearman mismatch!"
    # frozen per-parameter recoverability (from the frozen metrics file)
    r_par = dict(zip(pnames, r_recover))

    for size in ("journal", "large"):
        w = st.set_fig_width(size)
        # Two GridSpec columns only. width_ratios=[1.25, 1.0] with wspace=0.17
        # pins panel (a) to ~336 px (its previous width) while making panel (b)
        # ~1.5x wider (263 px) and keeping the central gap large enough to hold
        # panel (b)'s left-side y tick labels AND its y-axis label without
        # colliding with panel (a) (wspace raised 0.12 -> 0.17 for that reason).
        fig = plt.figure(figsize=(w, w * 0.50))
        gs = fig.add_gridspec(1, 2, width_ratios=[1.25, 1.0],
                              left=0.085, right=0.99, top=0.90, bottom=0.10,
                              wspace=0.17)

        # ---------------- (a) 3x3 parity, shared axes ----------------
        axg = fig.add_subplot(gs[0, 0])
        axg.axis("off")
        axg.set_xlim(0, 1); axg.set_ylim(0, 1)
        axg.text(0.0, 1.06, "(a)", fontsize=st.FS_PANEL, fontweight="bold",
                 va="top", color=INK)

        L, B, Wg, Hg = 0.16, 0.06, 0.82, 0.84
        dx = Wg / 3.0; dy = Hg / 3.0
        # 2026-08-28 tick-label spacing fix (annotfix4): 7.5-pt tick labels
        # overhang ~5 pt past each axis edge, but the 0.96 factor left only
        # ~2.6 pt between subplots, so the bottom-row x labels ("1.0"/"0.0")
        # and left-column y labels collided at every boundary. Panels are now
        # centered in their cells at 0.82 of cell width/height (gaps ~11.5 pt).
        # Data, labels, r values, colors, and panel (b) unchanged.
        PAD_F = 0.82
        ipad = dx * (1.0 - PAD_F) / 2.0
        jpad = dy * (1.0 - PAD_F) / 2.0
        for k in range(9):
            row, col = divmod(k, 3)            # row 0 top .. row 2 bottom
            ax = axg.inset_axes([L + col * dx + ipad, B + (2 - row) * dy + jpad,
                                 dx * PAD_F, dy * PAD_F])
            ax.scatter(y_true[:, k], y_pred[:, k], s=3, alpha=0.12,
                       color=st.OKABE_ITO[0], linewidths=0, rasterized=True)
            ax.plot([0, 1], [0, 1], ls="--", color="#555555", lw=0.8)
            # mathematical parameter label (top-left) + frozen r (bottom-right)
            ax.text(0.06, 0.94, PARAM_LABELS[k], fontsize=st.FS_ANNOT,
                    fontweight="bold", color=INK, transform=ax.transAxes,
                    va="top", ha="left")
            # 2026-08-28 FIX: index the frozen r by the CANONICAL column order
            # st.PARAM_NAMES[k] (== the order of y_true/pred[:, k] and the label).
            # The previous r_par[pnames[k]] indexed the ALPHABETICALLY-sorted
            # list, so every subplot annotated another parameter's r. Root cause
            # fixed here; data and frozen r values untouched.
            ax.text(0.97, 0.06, r"$r$ = %.3f" % r_par[st.PARAM_NAMES[k]],
                    fontsize=st.FS_ANNOT, color=INK, transform=ax.transAxes,
                    va="bottom", ha="right")
            # shared axes: ticks only on outer row/column
            if row != 2:
                ax.tick_params(labelbottom=False)
            if col != 0:
                ax.tick_params(labelleft=False)
            ax.set_xlim(0, 1); ax.set_ylim(0, 1)
            ax.set_xticks([0.0, 0.5, 1.0]); ax.set_yticks([0.0, 0.5, 1.0])
            st.configure_axes(ax)
        # single shared axis labels
        axg.text(0.5 + L * 0.0, B - 0.035, "true", fontsize=st.FS_TITLE,
                 ha="center", va="center", color=INK)
        axg.text(L * 0.22, 0.5, "predicted", fontsize=st.FS_TITLE,
                 rotation=90, ha="center", va="center", color=INK)

        # ---------------- (b) S_log vs recoverability ----------------
        axb = fig.add_subplot(gs[0, 1])
        axb.scatter(Slog, r_recover, s=46, color=st.OKABE_ITO[2], alpha=0.92,
                    edgecolor="white", linewidth=0.6, zorder=3)
        # Fixed annotate offsets: each label is anchored to its OWN parameter's
        # point (paired by name in paper order), NOT to the sorted-index array
        # order — the previous pairing landed every label on the wrong
        # parameter's point. Only the text anchor moves; data, point
        # coordinates, sizes and colors are unchanged.
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
        # pull the y-axis label slightly right (out of panel (a)) so it sits
        # between panel (a) and panel (b)'s own y tick labels
        axb.yaxis.set_label_coords(-0.12, 0.5)
        st.configure_axes(axb)
        # Spearman statistic in an empty region (bottom-right), no asterisks
        axb.text(0.97, 0.04,
                 r"Spearman $\rho_s$ = 0.533,  $p$ = 0.139"
                 "\n(non-significant)",
                 transform=axb.transAxes, fontsize=st.FS_ANNOT, va="bottom",
                 ha="right", color=INK, linespacing=1.35)
        # "(b)" tag placed in the upper-left margin, fully outside the axes
        axb.text(0.0, 1.06, "(b)", fontsize=st.FS_PANEL, fontweight="bold",
                 va="top", transform=axb.transAxes, color=INK)

        stem = os.path.join(OUT_DIR, "Fig3_recoverability_annotfix4"
                            + ("_large" if size == "large" else ""))
        st.save_fig(fig, stem, svg=True)
        print("wrote:", stem)


if __name__ == "__main__":
    main()
