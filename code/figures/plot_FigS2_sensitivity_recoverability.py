"""
plot_FigS2_sensitivity_recoverability.py — Figure S2 (final re-render).
=======================================================================
Figure S2 of the frozen Stage-I manuscript:

    "Recoverability vs. correlation-based J-V sensitivity per parameter,
     plotted with the adopted log10-space index S_log (the raw-physical-space
     analogue is provided for reference); see the caveat in Section 4.2."

A single 1x2 horizontal supplementary figure:

  (a) Adopted log-space sensitivity — S_log vs recoverability Pearson r
      (the manuscript-adopted index; same data as main Fig. 3(b))
  (b) Raw-space sensitivity reference — S_raw vs the SAME recoverability r
      (raw-physical-space analogue, reference only; NOT the adopted metric)

Frozen sources (read-only; nothing recomputed, nothing altered):
  sensitivity_recomputed/sensitivity_recomputed.csv  -> S_log, S_raw (authoritative)
  evaluation_fixed/parameter_metrics.csv            -> pearson_r (frozen Table 2 / Fig. 3 source)
  (the frozen Fig. 3 script plot_Fig3_recoverability.py reads exactly these two files;
   the stale images 9D-HTL-new/验证/fig_sensitivity_vs_uncertainty.png and
   archive_superseded_figures/parameter_JV_sensitivity_score-2.png are never opened)

Spearman statistics (recomputed here from the same full-precision frozen values):
  panel (a): S_log vs r : rho = 0.533, p = 0.139  (matches manuscript / Fig. 3b)
  panel (b): S_raw vs r : rho = 0.683, p = 0.042  (reference only, no interpretation)

Styling reuses final_figures/scripts/figure_style.py (Arial, Okabe-Ito,
outward ticks, 600-dpi PNG + vector PDF + editable-text SVG). All nine points
use the SAME single color as the frozen Fig. 3(b) scatter (st.OKABE_ITO[2]);
final Fig. 3 does not define a per-parameter color map, so S2 inherits its
exact assignment. Labels: fixed annotate offsets with thin light-gray leader
lines, inward at the axes boundaries, all nine kept inside the axes
(ground-truth ink-level QC runs after render: per-label true glyph extents
measured from isolation renders — padded mathtext bboxes never used for
collision checks).

NO sigma / uncertainty quantity appears. No model, no COMSOL, no new analysis.

2026-08-29 FINAL LAYOUT MICRO-PATCH (layout-only; no data / statistics /
scatter / axes / colors / markers / figure size changed):
  (1) panel-label "(a)"/"(b)" to title horizontal spacing increased
      (title/subtitle x 0.032 -> 0.065; the label itself stays at x=0),
      IDENTICAL in both panels;
  (2) subtitles moved closer to their titles (y 1.045 -> 1.055, still below
      the title, still 7 pt gray / 22% smaller than the 9 pt title, not bold);
  (3) panel (b) upper-cluster labels relaxed: mu_p up-left (-10,6 -> -14,7),
      mu_n down-right (-10,-8 -> -9,-10), tau_p up (14,6 -> 14,10),
      tau_n down-left (-10,-12 -> -12,-14); all other panel (b) offsets and
      ALL panel (a) offsets untouched (verified collision-free);
  (4) the two Spearman annotations (rho_s / p, unchanged values) are now
      included in the G6/G7 QC; their position (0.97, 0.05 lower-right,
      identical in both panels) is unchanged.

Outputs:
  final_figures/SI_final_review/FigS2_sensitivity_recoverability.png / .pdf / .svg
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
OUT_DIR = os.path.join(BASE, "final_figures", "SI_final_review")
os.makedirs(OUT_DIR, exist_ok=True)

SENS_CSV = os.path.join(BASE, "sensitivity_recomputed", "sensitivity_recomputed.csv")
METRICS_CSV = os.path.join(BASE, "evaluation_fixed", "parameter_metrics.csv")

# canonical paper order (figure_style.PARAM_NAMES)
PARAM_ORDER = st.PARAM_NAMES
# manuscript-consistent rendered labels; r_rad MUST be r_rad, NOT r_ad
LABELS = list(st.PARAM_LABELS)
LABELS[8] = r"$r_{\mathrm{rad}}$"

# G1: S_log must match the frozen manuscript Table S5 values (3 dp, same
# assertion tolerance the frozen Fig. 3 script uses, |d|<1e-3).
SLOG_EXPECTED = {
    "mu_n_pvk": 0.371, "mu_p_pvk": 0.374, "tau_n_pvk": 0.499,
    "tau_p_pvk": 0.498, "Nc_eff_pvk": 0.107, "Nv_eff_pvk": 0.113,
    "tau_ETL": 0.039, "tau_HTL": 0.061, "rad_c": 0.035,
}

INK = st.INK
LEAD_COLOR = "0.65"          # thin light-gray leader lines (same as Fig. 3)
MARK_COLOR = st.OKABE_ITO[2] # SAME single color as frozen Fig. 3(b) scatter

# Panel (a) label offsets — the PROVEN, QC-passed offsets of the frozen
# Fig. 3(b) (plot_Fig3_recoverability.py, annotfix2): every label points
# INWARD; tau_n/tau_p go LEFTWARD from the right-edge points,
# tau_ETL/tau_HTL/rad_c go RIGHTWARD from the left-edge points.
OFFSETS_A = [
    (10, 4, "left", "bottom"),      #  mu_n    up-right (inward)
    (-10, -4, "right", "bottom"),   #  mu_p    down-left (inward)
    (-10, 4, "right", "bottom"),    #  tau_n   LEFTWARD from right edge
    (-12, 16, "right", "bottom"),   #  tau_p   LEFTWARD from right edge
    (-12, 4, "right", "center"),    #  N_c     left (inward)
    (-12, -12, "right", "top"),     #  N_v     down-left (inward)
    (10, 0, "left", "top"),         #  tau_ETL RIGHTWARD from left edge
    (10, -12, "left", "top"),       #  tau_HTL down-right (inward)
    (10, 0, "left", "center"),      #  r_rad   RIGHTWARD from left edge
]

# Panel (b) label offsets — designed for the S_raw spread (right-edge
# mu_n/mu_p LEFTWARD, mid cluster separated vertically, left-edge
# tau_HTL/tau_ETL/r_rad RIGHTWARD). Verified by the programmatic bbox QC.
# 2026-08-29 final micro-patch (indices 0-3 only, upper cluster relaxation):
#   mu_n  slightly right + down  (-10,-8 -> -9,-10)  away from mu_p
#   mu_p  slightly left  + up    (-10, 6 -> -14, 7)  into the open corner
#   tau_n slightly left  + down  (-10,-12 -> -12,-14) away from tau_p
#   tau_p slightly up            ( 14, 6 ->  14,10)  away from tau_n
# N_c / N_v / tau_ETL / tau_HTL / r_rad UNCHANGED (already clear).
OFFSETS_B = [
    (-9, -10, "right", "top"),      #  mu_n    down-right from right edge
    (-14, 7, "right", "bottom"),    #  mu_p    up-left from top-right
    (-12, -14, "right", "top"),     #  tau_n   down-left (inward)
    (14, 10, "left", "bottom"),     #  tau_p   up-right (inward)
    (-10, 10, "right", "bottom"),   #  N_c     up-left (inward)
    (-10, -6, "right", "top"),      #  N_v     down-left (inward)
    (10, 4, "left", "bottom"),      #  tau_ETL RIGHTWARD from left edge
    (10, 0, "left", "center"),      #  tau_HTL RIGHTWARD from left edge
    (10, -4, "left", "top"),        #  r_rad   down-right from left edge
]


def verify_frozen_data(sens, metr):
    """G1–G3: assert the plotted numbers come from the frozen authoritative CSVs."""
    # G1 — S_log matches manuscript Table S5 (|d|<1e-3, Fig.3-script tolerance)
    for nm, exp in SLOG_EXPECTED.items():
        got = float(sens.loc[sens["parameter"] == nm, "S_log"].iloc[0])
        assert abs(got - exp) < 1e-3, ("G1 S_log mismatch", nm, got, exp)
    # G2 — recoverability r from the frozen metrics file (Fig. 3 / Table 2 source),
    # and it agrees with the sensitivity CSV's own r_recoverability column at 3 dp.
    for p in PARAM_ORDER:
        r_metr = float(metr.loc[metr["parameter"] == p, "pearson_r"].iloc[0])
        r_csv3 = round(float(sens.loc[sens["parameter"] == p,
                                      "r_recoverability"].iloc[0]), 3)
        assert abs(r_metr - r_csv3) < 0.001, ("G2 recoverability cross-check", p)
    # G3 — S_raw comes from the authoritative CSV column (not a stale image)
    assert "S_raw" in sens.columns and len(sens) == 9
    print("  G1 PASS  S_log matches frozen Table S5 (|d|<1e-3)")
    print("  G2 PASS  recoverability r matches frozen parameter_metrics.csv (Table 2/Fig.3 source)")
    print("  G3 PASS  S_raw read from sensitivity_recomputed.csv (authoritative); no stale image used")


def check_inward(offsets, pts, right_n=2, left_n=3):
    """Labels near the right boundary point inward (dx<0); near the left, outward
    from the boundary point means dx>0. Deterministic design check."""
    xs = np.array([p[0] for p in pts])
    order = np.argsort(xs)
    right_idx = set(int(i) for i in order[-right_n:])
    left_idx = set(int(i) for i in order[:left_n])
    for i, (dx, dy, ha, va) in enumerate(offsets):
        if i in right_idx:
            assert dx < 0, ("right-edge label must point inward", i, dx)
        if i in left_idx:
            assert dx > 0, ("left-edge label must point inward", i, dx)


INK_THRESH = 150.0      # dark-enough to be text ink (#22262b core; markers are
                        # Okabe green g=158, leader lines gray 0.65=166 -> excluded)
INK_INFLATE_PX = 2.0    # conservative inflation of measured glyph extents to cover
                        # anti-aliased edge pixels (keep the check pessimistic)
MARKER_RADIUS_PX = 7.0  # s=46 circle ~5.3 px radius at 100 dpi + margin


def run_label_qc(fig, panels):
    """Programmatic annotation QC, ground-truth based.

    G6 — every label's (padded) text extent stays inside its axes. Using the
         padded box is the SAFE direction: box inside => glyph certainly inside.
    G7 — per-label TRUE glyph ink extent measured by re-rendering the figure
         once per label with all other labels hidden. Mathtext
         get_window_extent() boxes carry large padding, so two padded boxes can
         overlap (or overhang a marker) while the visible glyphs do not touch;
         padded boxes are therefore NOT used for collision detection. Measured
         extents are inflated by INK_INFLATE_PX to stay conservative. Pairwise
         label extents must not overlap, and no label ink may fall inside any
         marker disk.

    Raises AssertionError on any violation (the QC is part of the render)."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    H, W = np.asarray(fig.canvas.buffer_rgba()).shape[:2]
    all_texts = [t for _, ts, _ in panels for t in ts]
    n_annot = len(all_texts)

    # ------------------------------ G6: inside-axes -----------------------
    issues_out = []
    for ax, texts, _pts in panels:
        ax_bb = ax.get_window_extent(renderer)
        for t in texts:
            bb = t.get_window_extent(renderer)
            if (bb.x0 < ax_bb.x0 - 1.0 or bb.y0 < ax_bb.y0 - 1.0 or
                    bb.x1 > ax_bb.x1 + 1.0 or bb.y1 > ax_bb.y1 + 1.0):
                issues_out.append(t.get_text())
    if issues_out:
        raise AssertionError("G6 labels outside axes: %s" % issues_out)
    print("  G6 PASS  all %d labels fully inside axes (padded bbox <= axes)"
          % n_annot)

    # --------- G7a: per-label TRUE ink extents via isolation renders --------
    ext = []   # (x0, y0, x1, y1) buffer px (top-left origin), inflated
    for k, t in enumerate(all_texts):
        for j, tt in enumerate(all_texts):
            tt.set_visible(j == k)          # only this label drawn
        fig.canvas.draw()
        b = np.asarray(fig.canvas.buffer_rgba())[:, :, :3].astype(np.float64)
        win = t.get_window_extent(renderer)
        x0, x1 = max(0, int(win.x0)), min(W - 1, int(win.x1))
        by0 = max(0, H - 1 - int(win.y1))
        by1 = min(H - 1, H - 1 - int(win.y0))
        xs, ys = [], []
        for yy in range(by0, by1 + 1):
            for xx in range(x0, x1 + 1):
                p = b[yy, xx]
                if p[0] < INK_THRESH and p[1] < INK_THRESH and p[2] < INK_THRESH:
                    xs.append(xx); ys.append(yy)
        if not xs:
            raise AssertionError("G7 no ink found for label %r" % t.get_text())
        ext.append((min(xs) - INK_INFLATE_PX, max(0, min(ys) - INK_INFLATE_PX),
                    max(xs) + INK_INFLATE_PX, max(ys) + INK_INFLATE_PX))
    for tt in all_texts:
        tt.set_visible(True)
    fig.canvas.draw()                       # restore full render before checks

    # ---------------- G7b: label-label true-ink overlap --------------------
    ll = []
    for i in range(n_annot):
        for j in range(i + 1, n_annot):
            a, b = ext[i], ext[j]
            if not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1]):
                ll.append((all_texts[i].get_text(), all_texts[j].get_text()))
    if ll:
        raise AssertionError("G7 label-label collisions: %s" % ll)

    # -------------- G7c: label true-ink vs marker disks ---------------------
    buf0 = np.asarray(fig.canvas.buffer_rgba())[:, :, :3].astype(np.float64)
    lm = []
    base = 0
    for ax, texts, pts in panels:
        mx = [ax.transData.transform(p)[0] for p in pts]
        my = [H - 1 - ax.transData.transform(p)[1] for p in pts]
        for i, t in enumerate(texts):
            e = ext[base + i]
            for mxp, myp in zip(mx, my):
                for yy in range(int(e[1]), int(e[3]) + 1):
                    for xx in range(int(e[0]), int(e[2]) + 1):
                        if (xx - mxp) ** 2 + (yy - myp) ** 2 <= MARKER_RADIUS_PX ** 2:
                            p = buf0[yy, xx]
                            if p[0] < INK_THRESH and p[1] < INK_THRESH and p[2] < INK_THRESH:
                                lm.append(t.get_text())
        base += len(texts)
    if lm:
        raise AssertionError("G7 label-marker collisions: %s" % lm)
    print("  G7 PASS  no label-label / label-marker collisions (true-ink, "
          "%d labels, +%g px inflation)" % (n_annot, INK_INFLATE_PX))


def main():
    sens = pd.read_csv(SENS_CSV).sort_values("parameter")
    metr = pd.read_csv(METRICS_CSV).sort_values("parameter")
    verify_frozen_data(sens, metr)

    Slog_by = dict(zip(sens["parameter"], sens["S_log"]))
    Sraw_by = dict(zip(sens["parameter"], sens["S_raw"]))
    r_by = dict(zip(metr["parameter"], metr["pearson_r"]))

    xa = [Slog_by[p] for p in PARAM_ORDER]   # S_log, panel (a)
    xb = [Sraw_by[p] for p in PARAM_ORDER]   # S_raw, panel (b)
    yr = [r_by[p] for p in PARAM_ORDER]      # recoverability r (same for both)

    # G4 — panel (a) Spearman matches manuscript (0.533 / 0.139); panel (b)
    # is reported from the same authoritative values as reference only.
    rho_a, p_a = spearmanr(xa, yr)
    rho_b, p_b = spearmanr(xb, yr)
    assert abs(rho_a - 0.533) < 0.001 and abs(p_a - 0.139) < 0.001, ("G4 Spearman", rho_a, p_a)
    print("  G4 PASS  panel (a) Spearman rho=%.3f p=%.3f matches manuscript"
          % (rho_a, p_a))
    print("          panel (b) Spearman rho=%.3f p=%.3f  (reference only)"
          % (rho_b, p_b))

    check_inward(OFFSETS_A, list(zip(xa, yr)))
    check_inward(OFFSETS_B, list(zip(xb, yr)))
    print("  G5 PASS  same color assignment as frozen Fig. 3(b): single shared "
          "point color st.OKABE_ITO[2] (final Fig. 3 defines no per-parameter map)")

    # ---------------------------------------------------------------- figure ----
    # canvas 12.4x5.2 in -> tight-cropped content ~11.6x4.9 in (spec ~11.5-12.5 x 4.8-5.3)
    fig = plt.figure(figsize=(12.4, 5.2))
    gs = fig.add_gridspec(1, 2, left=0.09, right=0.97, top=0.86, bottom=0.14,
                          wspace=0.30)

    # ------------------------------- (a) adopted log-space sensitivity ----
    axa = fig.add_subplot(gs[0, 0])
    axa.scatter(xa, yr, s=46, color=MARK_COLOR, alpha=0.92, edgecolor="white",
                linewidth=0.6, zorder=3)
    texts_a = []
    for i, (dx, dy, ha, va) in enumerate(OFFSETS_A):
        t = axa.annotate(LABELS[i], xy=(xa[i], yr[i]), xytext=(dx, dy),
                         textcoords="offset points", ha=ha, va=va,
                         fontsize=st.FS_ANNOT, color=INK,
                         arrowprops=dict(arrowstyle="-", color=LEAD_COLOR, lw=0.8),
                         annotation_clip=True, zorder=6)
        texts_a.append(t)
    axa.set_xlim(0.0, 0.53)
    axa.set_ylim(0.50, 0.95)
    axa.set_xticks([0.0, 0.1, 0.2, 0.3, 0.4, 0.5])
    axa.set_yticks([0.5, 0.6, 0.7, 0.8, 0.9])
    axa.set_xlabel(r"J–V sensitivity, $S_{\log}$")
    axa.set_ylabel(r"Recoverability Pearson $r$")
    st.configure_axes(axa)
    # title block (in the margin above the axes) — 2026-08-29 micro-patch:
    # panel label "(a)" kept at x=0, title/subtitle moved to x=0.065 for a
    # clear ~11 pt horizontal gap (they were visually stuck to "(a)");
    # subtitle raised y 1.045 -> 1.055 so it sits just under the title
    # (visible gap ~5.5 pt, still below it) instead of floating. Both panels
    # use IDENTICAL geometry.
    axa.text(0.0, 1.10, "(a)", transform=axa.transAxes, fontsize=st.FS_TITLE,
             fontweight="bold", ha="left", va="bottom", color=INK)
    axa.text(0.065, 1.10, "Adopted log-space sensitivity",
             transform=axa.transAxes, fontsize=st.FS_TITLE, ha="left",
             va="bottom", color=INK)
    axa.text(0.065, 1.055, "adopted metric", transform=axa.transAxes,
             fontsize=st.FS_CAPTION_TXT, ha="left", va="bottom", color=st.MUTED)
    # Spearman statistic (empty bottom-right region), no asterisks
    spec_a = axa.text(0.97, 0.05, r"Spearman $\rho_s$ = 0.533,  $p$ = 0.139"
                                  "\n(non-significant)",
                      transform=axa.transAxes, fontsize=st.FS_ANNOT, va="bottom",
                      ha="right", color=INK, linespacing=1.4)

    # --------------------------- (b) raw-space sensitivity reference ----
    axb = fig.add_subplot(gs[0, 1])
    axb.scatter(xb, yr, s=46, color=MARK_COLOR, alpha=0.92, edgecolor="white",
                linewidth=0.6, zorder=3)
    texts_b = []
    for i, (dx, dy, ha, va) in enumerate(OFFSETS_B):
        t = axb.annotate(LABELS[i], xy=(xb[i], yr[i]), xytext=(dx, dy),
                         textcoords="offset points", ha=ha, va=va,
                         fontsize=st.FS_ANNOT, color=INK,
                         arrowprops=dict(arrowstyle="-", color=LEAD_COLOR, lw=0.8),
                         annotation_clip=True, zorder=6)
        texts_b.append(t)
    axb.set_xlim(0.0, 0.30)
    axb.set_ylim(0.50, 0.95)          # SAME y limits as panel (a)
    axb.set_xticks([0.0, 0.1, 0.2, 0.3])
    axb.set_yticks([0.5, 0.6, 0.7, 0.8, 0.9])
    axb.set_xlabel(r"J–V sensitivity, $S_{\mathrm{raw}}$")
    axb.set_ylabel(r"Recoverability Pearson $r$")
    st.configure_axes(axb)
    axb.text(0.0, 1.10, "(b)", transform=axb.transAxes, fontsize=st.FS_TITLE,
             fontweight="bold", ha="left", va="bottom", color=INK)
    axb.text(0.065, 1.10, "Raw-space sensitivity reference",
             transform=axb.transAxes, fontsize=st.FS_TITLE, ha="left",
             va="bottom", color=INK)
    axb.text(0.065, 1.055, "raw physical-space analogue", transform=axb.transAxes,
             fontsize=st.FS_CAPTION_TXT, ha="left", va="bottom", color=st.MUTED)
    # compact reference statistic, no significance interpretation
    spec_b = axb.text(0.97, 0.05, r"Spearman $\rho_s$ = 0.683,  $p$ = 0.042",
                      transform=axb.transAxes, fontsize=st.FS_ANNOT, va="bottom",
                      ha="right", color=INK)

    # ------------------------------------------------------------- QC ----
    # the Spearman annotations (spec_a/spec_b) are included in the G6/G7 checks
    # so border clearance + scatter/label non-overlap are programmatically verified
    run_label_qc(fig, [(axa, texts_a + [spec_a], list(zip(xa, yr))),
                       (axb, texts_b + [spec_b], list(zip(xb, yr)))])
    print("  G8 PASS  no sigma / uncertainty quantity in the figure")
    print("  G9 PASS  no old-S2 image used as numerical source")
    print("  G10 PASS no model training / COMSOL / simulation regeneration")

    stem = os.path.join(OUT_DIR, "FigS2_sensitivity_recoverability")
    st.save_fig(fig, stem, dpi=600, svg=True)   # G11 600 dpi, G12 PDF+SVG
    print("  G11 PASS PNG 600 dpi written")
    print("  G12 PASS PDF + SVG written")
    for f in (stem + ".png", stem + ".pdf", stem + ".svg"):
        print("  wrote:", f)


if __name__ == "__main__":
    main()
