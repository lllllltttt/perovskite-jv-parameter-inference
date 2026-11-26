"""
plot_Fig3_recoverability_annotfix5.py — Fig. 3 of the FINAL figure package.
===========================================================================
(a) 3x3 parity plots: true vs predicted parameters, normalized log10 space
    (shared [0,1] axes, y = x, Pearson r per parameter). All 15,307 test
    points preserved; each panel carries its mathematical parameter label and
    the frozen Pearson r. Ticks only on the outer row/column.
(b) Correlation-based J-V linear sensitivity S_log (recomputed, log10
    parameter space, test set) vs parameter recoverability (Pearson r).

2026-08-28 REDESIGN (annotfix5) — layout reference: legacy
    9D-HTL-new/fig_parameter_scatter_all9.png (3600x3600, 9 LARGE square
    panels). The legacy PNG is used ONLY as a visual/layout reference; it is
    NOT embedded, upscaled, cropped, or reused. Panel (a) is rebuilt from the
    authoritative frozen arrays (final_figures/scripts/_frozen_preds.npz).
    Changes vs annotfix4:
      * width allocation: 1.25:1 -> 1.7:1  => panel (a) ~63% of figure width,
        panel (b) ~37% (legacy-style dominance for the information-dense
        scatter grid).
      * figure height 0.50w -> 0.54w so the 3x3 panels grow to ~65x52 pt
        (journal), ~38% larger in area, aspect ~1.25:1 (approximately
        square) — the legacy large-panel look.
      * shared axis labels switched to manuscript notation:
        "True normalized log10 parameter" / "Predicted normalized log10
        parameter" (replaces the terse "true" / "predicted").
      * per-panel manuscript labels (PARAM_LABELS, incl. r_rad) and frozen
        r = %.3f annotations unchanged; identity dashed line unchanged;
        tick-label rules unchanged (x numbers bottom row only, y numbers
        left column only; inter-panel gap >= 11.5 pt so no boundary
        overlap).
      * panel (b) is UNCHANGED except its cell width (narrowed to the 37%
        allocation): same data, same point-offset annotations, same labels,
        same colors/markers.
    Data, parameter order, Pearson r, S_log, and Spearman statistic are all
    frozen and untouched.

Frozen sources: sensitivity_recomputed/sensitivity_recomputed.csv (S_log,
authoritative), evaluation_fixed/parameter_metrics.csv (Pearson r,
authoritative), final_figures/scripts/_frozen_preds.npz (per-sample
predictions). No data is altered or recomputed.

Outputs:
  final_figures/Fig3/Fig3_recoverability_annotfix5.png / .pdf / .svg
  final_figures/Fig3/Fig3_recoverability_annotfix5_large.png / .pdf / .svg
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


# Panel (b): FIXED annotate offsets — no automatic repulsion (identical to
# annotfix4). Each parameter's label is anchored to its OWN data point by
# parameter name in paper order; the offsets below are frozen and unchanged.
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
    r_par = dict(zip(pnames, r_recover))

    for size in ("journal", "large"):
        w = st.set_fig_width(size)
        # [annotfix5] width_ratios 1.25:1 -> 1.7:1  => panel (a) ~63% /
        # panel (b) ~37% of the grid width. Figure height 0.50w -> 0.54w so
        # the (a) 3x3 panels are ~38% larger in area and ~1.25:1 (approx.
        # square), after the legacy large-panel reference. Panel (b) keeps
        # identical content/annotations and only its cell width changes.
        fig = plt.figure(figsize=(w, w * 0.54))
        gs = fig.add_gridspec(1, 2, width_ratios=[1.7, 1.0],
                              left=0.085, right=0.99, top=0.90, bottom=0.10,
                              wspace=0.17)

        # ---------------- (a) 3x3 parity, shared axes ----------------
        axg = fig.add_subplot(gs[0, 0])
        axg.axis("off")
        axg.set_xlim(0, 1); axg.set_ylim(0, 1)
        axg.text(0.0, 1.06, "(a)", fontsize=st.FS_PANEL, fontweight="bold",
                 va="top", color=INK)

        # [annotfix5] legacy-style large panels: grid footprint fills 86% of
        # axg width and 84% of its height; each panel is 85% of its cell
        # (centered) -> ~65x52 pt, aspect 1.25, gap >= 11.5 pt between
        # panels so the 7.5-pt outer tick labels (5.2-pt overhang each side)
        # never touch at the subplot boundaries.
        L, B, Wg, Hg = 0.09, 0.08, 0.86, 0.84
        dx = Wg / 3.0; dy = Hg / 3.0
        PAD_F = 0.85
        ipad = dx * (1.0 - PAD_F) / 2.0
        jpad = dy * (1.0 - PAD_F) / 2.0
        for k in range(9):
            row, col = divmod(k, 3)            # row 0 top .. row 2 bottom
            ax = axg.inset_axes([L + col * dx + ipad, B + (2 - row) * dy + jpad,
                                 dx * PAD_F, dy * PAD_F])
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
            # shared axes: numeric tick labels only on outer row/column
            if row != 2:
                ax.tick_params(labelbottom=False)
            if col != 0:
                ax.tick_params(labelleft=False)
            ax.set_xlim(0, 1); ax.set_ylim(0, 1)
            ax.set_xticks([0.0, 0.5, 1.0]); ax.set_yticks([0.0, 0.5, 1.0])
            st.configure_axes(ax)
        # [annotfix5] shared axis labels in manuscript notation, centered on
        # the 3x3 grid (were terse "true"/"predicted"). The x label sits BELOW
        # the bottom-row tick labels: data y = B - 0.095 places the text band
        # ~11 pt clear of the tick-label band (verified by PDF bbox QC).
        axg.text(L + Wg / 2.0, B - 0.095, "True normalized log10 parameter",
                 fontsize=st.FS_TITLE, ha="center", va="center", color=INK)
        axg.text(0.018, 0.5, "Predicted normalized log10 parameter",
                 fontsize=st.FS_TITLE, rotation=90, ha="center", va="center",
                 color=INK)

        # ---------------- (b) S_log vs recoverability ----------------
        # [annotfix5] UNCHANGED from annotfix4 except cell width: same data,
        # same point-anchored offset annotations, same labels.
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

        stem = os.path.join(OUT_DIR, "Fig3_recoverability_annotfix5"
                            + ("_large" if size == "large" else ""))
        st.save_fig(fig, stem, svg=True)
        print("wrote:", stem)


if __name__ == "__main__":
    main()
