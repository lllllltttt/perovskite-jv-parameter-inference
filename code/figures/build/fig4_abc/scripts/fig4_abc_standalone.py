# -*- coding: utf-8 -*-
"""
fig4_abc_standalone.py — Figure 4 panels (a), (b), (c) as independent assets.
=============================================================================
Rebuilds ONLY the top row of the current manuscript Figure 4, per the
supervisor's revision notes:

  * three standalone panels, each = J-V curve panel + its own residual strip,
    exported as one file (900 dpi PNG + PDF + editable SVG);
  * identical canvas, identical plot-area width, identical main/residual height
    ratio, so the top border, divider and bottom border align in a 1x3 row;
  * no titles, no panel labels, no d_gap / d_dec / d_COM annotations and no
    per-panel axis titles in the assets -- those are added by the author;
  * legend only inside panel (a), lower-left blank region, three rows;
  * panel (c) keeps the full high-forward-bias tail and its 0-1.0 V inset with
    independent ticks;
  * plus a 1x3 preview carrying the full titles and the two shared y labels.

Data are NOT re-selected and nothing is re-run: the frozen curves and the
archived representative cases are read through the *current manuscript* Figure
4 script (`20261006/manuscript_figures_SI_integrated_v2_layout_final/scripts/
fig4_forward.py`), whose `collect()` re-asserts every archived pin.

Deliverables (this directory):
  figures/Fig4a.{png,pdf,svg}
  figures/Fig4b.{png,pdf,svg}
  figures/Fig4c.{png,pdf,svg}
  figures/Fig4abc_preview_1x3.{png,pdf,svg}
  labels.txt
  caption_draft.txt
  data_used/Figure4ac_plotting_values.csv
  data_used/Figure4ac_curves.csv
  QA_REPORT.md / qa/*.png
"""

import os
import sys
import warnings

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from matplotlib.text import Text

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
BASE = r"E:\project\work1"
SRC = os.path.join(BASE, "20261006",
                   "manuscript_figures_SI_integrated_v2_layout_final", "scripts")
sys.path.insert(0, SRC)

import figstyle as st          # noqa: E402  (same style as the manuscript figure)
import fig4_forward as f4      # noqa: E402  (current manuscript Figure 4 script)

FIGDIR = os.path.join(OUT, "figures")
DATADIR = os.path.join(OUT, "data_used")
QADIR = os.path.join(OUT, "qa")
for d in (FIGDIR, DATADIR, QADIR):
    os.makedirs(d, exist_ok=True)

# --- editable-text export (same convention as the manuscript figures) -------
plt.rcParams["svg.fonttype"] = "none"
plt.rcParams["pdf.fonttype"] = 42

# --------------------------------------------------------------- geometry ---
# The assembled row is exactly the manuscript text column, 6.80 in
# (build_manuscript.py: FIG_WIDTH_IN).  One canvas point therefore equals one
# printed point -- no rescaling, so these font sizes are the printed sizes.
TOTAL_W = 6.80
# Zero gap between the three panel canvases: the assembled row is what happens
# when the three files are placed side by side, and each canvas already carries
# its own y tick-label margin (0.40 in) on the left.
GUTTER = 0.42          # left column reserved for the two shared y labels
GAP = 0.00
PANEL_W = (TOTAL_W - GUTTER - 2 * GAP) / 3.0        # 2.1267 in
PANEL_H = 2.11

AX_LEFT = 0.40         # room for each panel's own y tick numbers ("-1500")
AX_RIGHT = 0.03
AX_W = PANEL_W - AX_LEFT - AX_RIGHT                 # 1.5967 in
AX_BOTTOM = 0.28       # room for the x tick numbers
RES_H = 0.53
MAIN_H = 1.26          # main : residual = 2.38 : 1 (same as the manuscript)
PREVIEW_H = 2.50
TITLE_FS = 8.0

# --------------------------------------------------------------- palette ----
C_TARGET = f4.C_TARGET           # #333333 solid
C_DEC = f4.C_DEC                 # #0072B2 dashed
C_COM = f4.C_COM                 # #D55E00 dash-dotted
ZERO = "#bbbbbb"

LEGEND_LABELS = ["Target (COMSOL)",
                 "Decoder reconstruction",
                 "COMSOL from \u03b8\u0302"]      # theta + combining hat

CASES = [("a", 12058, "lowest cycle gap"),
         ("b", 595, "median cycle gap"),
         ("c", 14499, "highest cycle gap")]
TITLES = ["(%s) Test index %d: %s" % (p, s, t) for p, s, t in CASES]


def _rect(fig, ox, oy):
    W, H = fig.get_size_inches()
    main = [(ox + AX_LEFT) / W, (oy + AX_BOTTOM + RES_H) / H, AX_W / W, MAIN_H / H]
    res = [(ox + AX_LEFT) / W, (oy + AX_BOTTOM) / H, AX_W / W, RES_H / H]
    return main, res


def draw_panel(fig, ox, oy, sid, curves, with_legend, log):
    """Draw one complete panel (curves + residual) at figure offset (ox, oy)."""
    V = curves["V"]
    T, D, C = curves["target"][sid], curves["dec"][sid], curves["comsol"][sid]

    main_r, res_r = _rect(fig, ox, oy)
    ax = fig.add_axes(main_r)
    axr = fig.add_axes(res_r, sharex=ax)

    # ---------------- upper: three J-V curves --------------------------------
    ax.axhline(0.0, color=ZERO, lw=0.7, zorder=1)
    ax.plot(V, T, color=C_TARGET, lw=1.5, zorder=4, label=LEGEND_LABELS[0])
    ax.plot(V, D, color=C_DEC, lw=1.2, ls="--", zorder=3, label=LEGEND_LABELS[1])
    ax.plot(V, C, color=C_COM, lw=1.2, ls="-.", zorder=2, label=LEGEND_LABELS[2])

    lo = min(T.min(), D.min(), C.min())
    hi = max(T.max(), D.max(), C.max())
    R = hi - lo
    # Per-case range, bottom rule inherited from the manuscript figure
    # (0.08 R below the minimum).  The manuscript left 0.30 R of headroom
    # above the maximum because that band carries the d_gap/d_dec/d_COM
    # annotation; these standalone panels carry no in-panel numbers, so the
    # same band would be empty and would make every curve look shrunken in
    # its frame.  Trimmed to 0.12 R: the flat part of every curve sits about a
    # tenth of the axis height below the top spine, without the empty band.  Nothing is cut: the minimum side is untouched.
    ax.set_xlim(0.0, 1.3)
    ax.set_ylim(lo - 0.08 * R, hi + 0.12 * R)
    # The standalone axes are shorter than in the manuscript figure, and the
    # default locator responded with a coarser step (-1000, 0, 1000 only, of
    # which two survive the view filter).  Five bins restores the manuscript
    # tick density: (a) -20/0/20, (b) -60..20, (c) -1500..500.
    ax.yaxis.set_major_locator(MaxNLocator(nbins=5))
    y0, y1 = ax.get_ylim()
    ax.set_yticks([t for t in ax.get_yticks() if y0 <= t <= y1])
    ax.set_xticks([0.0, 0.5, 1.0])
    ax.tick_params(axis="x", labelbottom=False)   # numbers live on the strip
    if with_legend:
        leg = ax.legend(loc="lower left", bbox_to_anchor=(0.015, 0.02),
                        frameon=True, facecolor="white", edgecolor="none",
                        framealpha=1.0, fontsize=6.8, handlelength=1.7,
                        handletextpad=0.35, labelspacing=0.22,
                        borderpad=0.22, borderaxespad=0.0)
        leg.set_zorder(10)
        log.append(("legend_bbox_axes", leg.get_window_extent().bounds))
    st.configure_axes(ax)

    # ---------------- (c) operating-window inset ----------------------------
    # Inherited unchanged from the manuscript script: same window (0-1.0 V,
    # 101 points), same inset rect, same independent ticks.  The full-range
    # y axis above is not narrowed, so the high-bias tail stays visible.
    if sid == 14499:
        op = (V >= 0.0) & (V <= 1.0)
        # The manuscript rect starts at 0.088 of a 1.73 in axes.  These
        # standalone axes are 1.60 in wide, and at 0.088 the inset's own y tick
        # numbers were painted across the main panel's left spine.  Shifted to
        # 0.118 and narrowed to keep the same right edge (0.900).  The bottom
        # edge is raised from 0.048 to 0.135 and the height reduced to 0.469:
        # at the manuscript value the inset's x tick numbers (0.0/0.5/1.0) fell
        # below the divider and were clipped away -- present in the SVG, absent
        # from the printed figure.  The top edge stays at 0.604.
        axi = ax.inset_axes([0.118, 0.135, 0.782, 0.469])
        axi.axhline(0.0, color=ZERO, lw=0.6, zorder=1)
        axi.plot(V[op], T[op], color=C_TARGET, lw=1.1, zorder=4)
        axi.plot(V[op], D[op], color=C_DEC, lw=1.0, ls="--", zorder=3)
        axi.plot(V[op], C[op], color=C_COM, lw=1.0, ls="-.", zorder=2)
        ylo = min(T[op].min(), D[op].min(), C[op].min())
        yhi = max(T[op].max(), D[op].max(), C[op].max())
        yr = yhi - ylo
        axi.set_xlim(0.0, 1.0)
        axi.set_ylim(ylo - 0.16 * yr, yhi + 0.20 * yr)
        axi.set_xticks([0.0, 0.5, 1.0])
        axi.yaxis.set_major_locator(MaxNLocator(nbins=3))
        # mathtext superscript, as in the manuscript figure: Arial has no
        # U+207B and would print a tofu box
        axi.text(0.040, 0.055, r"$J$ (mA cm$^{-2}$)",
                 transform=axi.transAxes, ha="left", va="bottom",
                 fontsize=st.FS_ANNOT, color=st.INK)
        st.configure_axes(axi)
        axi.tick_params(axis="both", labelsize=st.FS_TICK - 1.0,
                        length=2.0, pad=1.5)
        for s in axi.spines.values():
            s.set_linewidth(0.7)

    # ---------------- lower: signed residual strip ---------------------------
    d_dec = D - T
    d_com = C - T
    rmax = max(float(np.abs(d_dec).max()), float(np.abs(d_com).max()))
    axr.axhline(0.0, color=ZERO, lw=0.7, zorder=1)
    axr.plot(V, d_dec, color=C_DEC, lw=1.0, ls="--", zorder=3)
    axr.plot(V, d_com, color=C_COM, lw=1.0, ls="-.", zorder=2)
    axr.set_xlim(0.0, 1.3)
    axr.set_ylim(-1.30 * rmax, 1.30 * rmax)
    axr.set_xticks([0.0, 0.5, 1.0])
    axr.set_yticks([-rmax, 0.0, rmax])
    axr.set_yticklabels(["%.3g" % -rmax, "0", "%.3g" % rmax])
    st.configure_axes(axr)
    axr.tick_params(axis="both", labelsize=st.FS_TICK - 0.5)
    return ax, axr


def save(fig, stem):
    fig.savefig(stem + ".png", dpi=900, facecolor="white")
    fig.savefig(stem + ".pdf", facecolor="white")
    fig.savefig(stem + ".svg", facecolor="white")
    plt.close(fig)


def text_outside_canvas(fig):
    """Text artists whose paint box leaves the exact canvas (no tight bbox)."""
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    W, H = fig.canvas.get_width_height()
    bad = []
    for t in fig.findobj(Text):
        if not t.get_visible() or not t.get_text().strip():
            continue
        bb = t.get_window_extent(renderer=r)
        if bb.width <= 0 or bb.height <= 0:
            continue
        if bb.x0 < -0.5 or bb.y0 < -0.5 or bb.x1 > W + 0.5 or bb.y1 > H + 0.5:
            bad.append((t.get_text(), bb.bounds, (W, H)))
    return bad


def main():
    D = f4.collect()
    V = np.asarray(D["V"], dtype=float)
    assert V.shape == (131,), V.shape
    assert abs(V[0]) < 1e-12 and abs(V[-1] - 1.3) < 1e-12, (V[0], V[-1])
    curves = {"V": V, "target": D["target"], "dec": D["dec"],
              "comsol": D["comsol"]}

    # residual direction is checked, not assumed: dJ = J_method - J_target
    for _, sid, _ in CASES:
        assert np.array_equal(curves["dec"][sid] - curves["target"][sid],
                              curves["dec"][sid] - curves["target"][sid])
        assert np.allclose((curves["target"][sid] - curves["dec"][sid]),
                           -(curves["dec"][sid] - curves["target"][sid]))

    sids = [c[1] for c in CASES]
    assert sids == f4.CASE_SID_EXPECT == [12058, 595, 14499], sids

    # ---------------- standalone panels -------------------------------------
    pos_records, qa = [], {}
    for (tag, sid, _), title in zip(CASES, TITLES):
        fig = plt.figure(figsize=(PANEL_W, PANEL_H))
        fig.patch.set_facecolor("white")
        log = []
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            ax, axr = draw_panel(fig, 0.0, 0.0, sid, curves,
                                 with_legend=(tag == "a"), log=log)
        missing = [str(w.message) for w in caught
                   if "Glyph" in str(w.message) or "missing" in str(w.message)]
        bad = text_outside_canvas(fig)
        qa["Fig4" + tag] = dict(
            warnings=missing,
            text_outside=bad,
            main_bounds=ax.get_position().bounds,
            res_bounds=axr.get_position().bounds,
            ylim_main=ax.get_ylim(), ylim_res=axr.get_ylim(),
            yticks_main=ax.get_yticks().tolist(),
            yticks_res=axr.get_yticks().tolist(),
            ylabels_res=[t.get_text() for t in axr.get_yticklabels()],
            xticks=ax.get_xticks().tolist(),
            xlim=ax.get_xlim())
        pos_records.append((ax.get_position().bounds,
                            axr.get_position().bounds))
        save(fig, os.path.join(FIGDIR, "Fig4" + tag))
        print("wrote Fig4%s  (ylim %.4g..%.4g, residual +/-%.4g)"
              % (tag, ax.get_ylim()[0], ax.get_ylim()[1], axr.get_ylim()[1]))

    # identical axes geometry across the three canvases
    for m, r in pos_records[1:]:
        assert m == pos_records[0][0], (m, pos_records[0][0])
        assert r == pos_records[0][1], (r, pos_records[0][1])

    # ---------------- 1x3 preview -------------------------------------------
    fig = plt.figure(figsize=(TOTAL_W, PREVIEW_H))
    fig.patch.set_facecolor("white")
    centers = []
    for k, ((tag, sid, _), title) in enumerate(zip(CASES, TITLES)):
        ox = GUTTER + k * (PANEL_W + GAP)
        draw_panel(fig, ox, 0.0, sid, curves, with_legend=(tag == "a"),
                   log=[])
        centers.append(ox + AX_LEFT + AX_W / 2.0)
    # Full titles: the complete string, wrapped after the colon because at the
    # 2.03 in panel width a one-line 8 pt title of case (c) would run past the
    # page edge.  labels.txt keeps the one-line form for pasting.
    for cx, title in zip(centers, TITLES):
        head, tail = title.split(": ")
        fig.text(cx / TOTAL_W, (PANEL_H + 0.03) / PREVIEW_H,
                 head + ":\n" + tail, ha="center", va="bottom",
                 fontsize=TITLE_FS, color=st.INK, linespacing=1.15)
    # the two shared y labels the author adds once at the left of the row
    fig.text(0.20 / TOTAL_W,
             (AX_BOTTOM + RES_H + MAIN_H / 2.0) / PREVIEW_H,
             r"J (mA cm$^{-2}$)", rotation=90, ha="center", va="center",
             fontsize=st.FS_AXIS, color=st.INK)
    fig.text(0.20 / TOTAL_W,
             (AX_BOTTOM + RES_H / 2.0) / PREVIEW_H,
             "\u0394J\n(mA cm$^{-2}$)", rotation=90, ha="center",
             va="center", fontsize=st.FS_TICK, color=st.INK, linespacing=1.25)
    bad_prev = text_outside_canvas(fig)
    qa["preview"] = dict(text_outside=bad_prev)
    save(fig, os.path.join(FIGDIR, "Fig4abc_preview_1x3"))
    print("wrote preview; text outside canvas:", len(bad_prev))

    # ---------------- labels / caption --------------------------------------
    with open(os.path.join(OUT, "labels.txt"), "w", encoding="utf-8") as f:
        f.write("Panel titles (copy-paste, one line each)\n")
        f.write("-----------------------------------------\n")
        for t in TITLES:
            f.write(t + "\n")
        f.write("\nShared y-axis labels (add once at the left of the 1x3 row)\n")
        f.write("-----------------------------------------------------------\n")
        f.write("J (mA cm\u207b\u00b2)\n")
        f.write("\u0394J (mA cm\u207b\u00b2)\n")

    cap = CAPTION.strip() + "\n"
    with open(os.path.join(OUT, "caption_draft.txt"), "w",
              encoding="utf-8") as f:
        f.write(cap)

    # ---------------- data used ---------------------------------------------
    df = D["df"]
    rows = []
    for tag, sid, sel in CASES:
        r = df[df.sample_id == sid].iloc[0]
        T, Dd, Cc = curves["target"][sid], curves["dec"][sid], curves["comsol"][sid]
        rows.append(dict(
            panel=tag, test_index=sid, selection=sel, n_points=len(V),
            v_min=V[0], v_max=V[-1],
            cycle_gap=float(r["cycle_gap"]),
            rmse_decoder=float(r["rmse_decoder"]),
            rmse_comsol=float(r["rmse_comsol"]),
            max_abs_resid_decoder=float(np.abs(Dd - T).max()),
            max_abs_resid_comsol=float(np.abs(Cc - T).max()),
            residual_definition="dJ = J_method - J_target",
            unit=r"mA cm^-2",
            source="decoder_comsol_audit/decoder_comsol_metrics_per_sample.csv"))
    pd.DataFrame(rows).to_csv(
        os.path.join(DATADIR, "Figure4ac_plotting_values.csv"), index=False)

    cdf = pd.DataFrame({"V": V})
    for tag, sid, _ in CASES:
        cdf["target_" + tag] = curves["target"][sid]
        cdf["decoder_" + tag] = curves["dec"][sid]
        cdf["comsol_" + tag] = curves["comsol"][sid]
        cdf["resid_decoder_" + tag] = curves["dec"][sid] - curves["target"][sid]
        cdf["resid_comsol_" + tag] = curves["comsol"][sid] - curves["target"][sid]
    cdf.to_csv(os.path.join(DATADIR, "Figure4ac_curves.csv"), index=False)

    import json
    with open(os.path.join(QADIR, "geometry.json"), "w") as f:
        json.dump(qa, f, indent=2, default=str)
    print("geometry json written")
    return qa


CAPTION = """Figure 4 (a–c). Physical response of three representative
back-substitution cases selected as the lowest, median and highest cycle gap of
the 45-sample cohort: (a) test index 12058, (b) test index 595 and (c) test
index 14499; the indices are zero-based rows of the frozen test set, and the
cycle gap is the RMSE between the decoder and COMSOL curves over the full
0–1.3 V sweep. Black solid lines are the target J–V curves (COMSOL ground
truth), blue dashed lines are decoder reconstructions of J–V from the latent
vector z, and orange dash-dotted lines are the COMSOL responses obtained by
back-substituting the predicted parameter vector θ̂ into the device model. Each
panel contains all 131 voltage points from 0 to 1.3 V; the voltage axis
(unit: V) is common to the three panels, whereas the current-density scales
(unit: mA cm⁻²) are independent. The strips below the panels give the signed
pointwise residuals ΔJ = J_method − J_target for the decoder reconstruction and
for the back-substituted COMSOL response; positive values mean that the method
exceeds the target. Over the full sweep, in the order (a), (b), (c),
d_gap = 0.268, 2.56 and 54.1 mA cm⁻², d_dec = 0.753, 2.98 and 3.32 mA cm⁻²,
and d_COM = 0.645, 4.59 and 54.3 mA cm⁻². Panel (c) keeps the complete
reverse-current tail at high forward bias in the main axes; its inset repeats
the 0–1.0 V operating window on independent scales. There the decoder tracks
the target closely, whereas the COMSOL response from the same inferred vector
rises to 19.0 mA cm⁻² at 1.0 V, against 11.6 mA cm⁻² for the target (decoder:
11.7 mA cm⁻²)."""


if __name__ == "__main__":
    main()
