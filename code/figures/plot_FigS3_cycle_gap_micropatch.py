"""
plot_FigS3_cycle_gap_micropatch.py — FINAL LAYOUT MICRO-PATCH of SI Fig. S3
panel (d) figure `FigS3_cycle_gap` (the 2x2 cycle-gap distribution figure).

Layout-only. NO data / statistics / axes limits / panel geometry / sample
values / scientific content changed. Rendered from the SAME frozen local data
as the audit (decoder_comsol_audit/decoder_comsol_metrics_per_sample.csv).

Changes (2026-08-29):
  Panel (a): "median 2.56" text moved off the tallest histogram bar and off
             the orange dashed median line into the open upper region
             (x 2.56 -> 13.0 in data coords). Dashed median line UNCHANGED.
  Panel (b): paired gray observation lines lightened (lw 0.5/alpha 0.45 ->
             lw 0.7 / alpha 0.12). All 45 pairs + both boxplots kept.
             Median value labels moved from the median line (inside each box)
             to a consistent position just above each boxplot's upper whisker
             cap (same 3% of y-span padding) and re-worded to
             "median 0.47" / "median 5.30" (source CSV confirms medians).
  Panels (c,d): rho/p annotations moved out of the occupied lower-right
             corner into the empty upper-left (axes-frac 0.05, 0.90; ha=left,
             va=top) so they do not cover any scatter point; a subtle
             semi-transparent white bbox keeps text legible. rho/p values
             unchanged.
  Panel (c): x-axis display text "param log10-RMSE (post-hoc)" ->
             "Parameter log_{10}-RMSE (post-hoc)".

Output: final_figures/SI_final_review/FigS3_cycle_gap.{png,pdf,svg}
        (PNG @600 dpi + vector PDF + editable-text SVG). The frozen
        final_figures/SI/ and final_figures/vector/ copies are NOT touched.
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

DC_CSV = os.path.join(BASE, "decoder_comsol_audit",
                      "decoder_comsol_metrics_per_sample.csv")

INK = "#22262b"


def main():
    df = pd.read_csv(DC_CSV)
    assert len(df) == 45

    # ---- frozen-number sanity (same as the audit script) ----
    med_cg = float(df["cycle_gap"].median())
    med_dt = float(df["rmse_decoder"].median())
    med_ct = float(df["rmse_comsol"].median())
    assert abs(med_cg - 2.5627) < 1e-3
    assert abs(med_dt - 1.88597) < 1e-3
    assert abs(med_ct - 2.69263) < 1e-3
    # rho/p anchors (panels c,d)
    rc, pc = spearmanr(df["param_log10_rmse"], df["cycle_gap"])
    rd, pd_ = spearmanr(df["mean_pred_sigma"], df["cycle_gap"])
    assert abs(rc - (-0.0262)) < 5e-4, rc
    assert abs(rd - 0.1174) < 5e-4, rd
    print("frozen numbers OK: med_cg=%.4f rc=%.4f rd=%.4f"
          % (med_cg, rc, rd))

    # ---- figure, identical geometry to the audit script ----
    w = st.set_fig_width("journal", 1.0)
    fig = plt.figure(figsize=(w, w * 0.62))
    gs = fig.add_gridspec(2, 2, left=0.09, right=0.99, top=0.90, bottom=0.11,
                          wspace=0.42, hspace=0.55)

    qc = []

    def chk(name, cond, note=""):
        qc.append(bool(cond))
        print("[%s] %s  %s" % ("PASS" if cond else "FAIL", name, note))

    # ---------- (a) full-gap histogram ----------
    axa = fig.add_subplot(gs[0, 0])
    axa.hist(df["cycle_gap"], bins=14, color=st.OKABE_ITO[0],
             edgecolor="white", linewidth=0.4)
    axa.axvline(med_cg, color=st.OKABE_ITO[3], ls="--", lw=1.4)   # UNCHANGED
    a_ylim = axa.get_ylim()
    chk("(a) ylim unchanged", tuple(a_ylim) == (0.0, 31.5), str(a_ylim))
    # median label moved off the tall bar & off the dashed line (x 2.56 -> 13)
    a_txt = axa.text(13.0, a_ylim[1] * 0.95, "median %.2f" % med_cg,
                     fontsize=st.FS_ANNOT, color=INK, va="top")
    axa.set_xlabel(r"cycle gap, full 0–1.3 V (mA cm$^{-2}$)")
    axa.set_ylabel("count")
    st.configure_axes(axa)
    axa.text(0.0, 1.16, "(a)", fontsize=st.FS_PANEL, fontweight="bold",
             va="top", transform=axa.transAxes, color=INK)

    # ---------- (b) region paired boxplot ----------
    axb = fig.add_subplot(gs[0, 1])
    x0, x1 = df["cycle_gap_0to1V"].values, df["cycle_gap_gt1V"].values
    bp = axb.boxplot([x0, x1], positions=[0, 1], widths=0.5, patch_artist=True,
                     medianprops=dict(color="black", lw=1.2),
                     flierprops=dict(marker="o", ms=2.5, alpha=0.4,
                                     markeredgecolor="none"))
    for patch, cc in zip(bp["boxes"], [st.OKABE_ITO[0], st.OKABE_ITO[3]]):
        patch.set_facecolor(cc); patch.set_alpha(0.65)
    pair_lines = []
    for i in range(len(x0)):
        ln = axb.plot([0, 1], [x0[i], x1[i]], color="#999999",
                      lw=0.7, alpha=0.12)
        pair_lines.append(ln[0])
    b_ylim = axb.get_ylim()
    # whisker tops from the boxplot artists
    top0 = float(bp["caps"][1].get_ydata()[0])
    top1 = float(bp["caps"][3].get_ydata()[0])

    def upper_whisker(b):
        q1, q3 = np.percentile(b, [25, 75]); iqr = q3 - q1
        return float(np.max(b[b <= q3 + 1.5 * iqr]))

    assert abs(top0 - upper_whisker(x0)) < 1e-6
    assert abs(top1 - upper_whisker(x1)) < 1e-6
    chk("(b) ylim unchanged", tuple(np.round(b_ylim, 3)) ==
        tuple(np.round((-5.604368902518259, 118.67033499480473), 3)),
        str(tuple(np.round(b_ylim, 3))))
    chk("(b) 45 paired lines kept", len(pair_lines) == 45, str(len(pair_lines)))
    chk("(b) two boxplots kept", len(bp["boxes"]) == 2)
    # median labels just above each boxplot's upper whisker, consistent pad
    pad = 0.03 * (b_ylim[1] - b_ylim[0])
    b_txts = []
    for i, m, top in [(0, np.median(x0), top0), (1, np.median(x1), top1)]:
        t = axb.text(i, top + pad, "median %.2f" % m, ha="center",
                     va="bottom", fontsize=st.FS_ANNOT, color=INK)
        b_txts.append(t)
    axb.set_xticks([0, 1])
    axb.set_xticklabels(["0–1.0 V", ">1.0 V"], fontsize=st.FS_TICK)
    axb.set_ylabel(r"cycle gap (mA cm$^{-2}$)")
    st.configure_axes(axb)
    axb.text(0.0, 1.16, "(b)", fontsize=st.FS_PANEL, fontweight="bold",
             va="top", transform=axb.transAxes, color=INK)

    # ---------- (c) param error vs gap ----------
    axc = fig.add_subplot(gs[1, 0])
    axc.scatter(df["param_log10_rmse"], df["cycle_gap"], s=26,
                color=st.OKABE_ITO[2], alpha=0.85, edgecolor="white",
                linewidth=0.4, zorder=3)
    axc.set_xlabel(r"Parameter $\log_{10}$-RMSE (post-hoc)")
    axc.set_ylabel(r"cycle gap (mA cm$^{-2}$)")
    st.configure_axes(axc)
    c_txt = axc.text(0.05, 0.90, r"$\rho$ = %.2f (p = %.2f)" % (rc, pc),
                     transform=axc.transAxes, fontsize=st.FS_ANNOT, va="top",
                     ha="left", color=INK,
                     bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                               edgecolor="none", alpha=0.65))
    axc.text(0.0, 1.16, "(c)", fontsize=st.FS_PANEL, fontweight="bold",
             va="top", transform=axc.transAxes, color=INK)

    # ---------- (d) predicted sigma vs gap ----------
    axd = fig.add_subplot(gs[1, 1])
    axd.scatter(df["mean_pred_sigma"], df["cycle_gap"], s=26,
                color=st.OKABE_ITO[4], alpha=0.85, edgecolor="white",
                linewidth=0.4, zorder=3)
    axd.set_xlabel(r"mean predicted $\sigma$")
    axd.set_ylabel(r"cycle gap (mA cm$^{-2}$)")
    st.configure_axes(axd)
    d_txt = axd.text(0.05, 0.90, r"$\rho$ = %.2f (p = %.2f)" % (rd, pd_),
                     transform=axd.transAxes, fontsize=st.FS_ANNOT, va="top",
                     ha="left", color=INK,
                     bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                               edgecolor="none", alpha=0.65))
    axd.text(0.0, 1.16, "(d)", fontsize=st.FS_PANEL, fontweight="bold",
             va="top", transform=axd.transAxes, color=INK)

    # ---- content / text QC ----
    chk("(c) xlabel", axc.get_xlabel() == r"Parameter $\log_{10}$-RMSE (post-hoc)",
        repr(axc.get_xlabel()))
    chk("(c) rho text", c_txt.get_text() == r"$\rho$ = -0.03 (p = 0.86)",
        c_txt.get_text())
    chk("(d) rho text", d_txt.get_text() == r"$\rho$ = 0.12 (p = 0.44)",
        d_txt.get_text())
    chk("(c,d) same axes-rel pos",
        c_txt.get_position() == d_txt.get_position() == (0.05, 0.90))
    chk("(c,d) bbox present", c_txt.get_bbox_patch() is not None
        and d_txt.get_bbox_patch() is not None)
    chk("(a) median text x away from dashed line", a_txt.get_position()[0] > 8.0,
        "x=%.1f (dashed line at %.2f)" % (a_txt.get_position()[0], med_cg))
    chk("(b) median labels reworded",
        [t.get_text() for t in b_txts] == ["median 0.47", "median 5.30"],
        str([t.get_text() for t in b_txts]))
    for i, (t, top) in enumerate(zip(b_txts, [top0, top1])):
        chk("(b) label %d above whisker" % i,
            t.get_position()[1] > top + pad * 0.95,
            "y=%.2f whisker=%.2f" % (t.get_position()[1], top))

    # ---- layout QC (no overlap / clipping) ----
    fig.canvas.draw()
    ren = fig.canvas.get_renderer()
    ok_in = True
    for nm, t in [("(a) median", a_txt), ("(c) rho", c_txt), ("(d) rho", d_txt),
                  ("(b) median L", b_txts[0]), ("(b) median R", b_txts[1])]:
        e = t.get_window_extent(ren)
        if not (e.x0 >= 0 and e.y0 >= 0 and e.x1 <= fig.bbox.width
                and e.y1 <= fig.bbox.height):
            ok_in = False
    chk("all labels inside figure", ok_in)
    # (c,d) annotation must not overlap ANY scatter marker (rendered extents)
    from matplotlib.transforms import Bbox

    def _marker_boxes(col):
        trans = col.get_transform()
        disp = trans.transform(col.get_offsets())
        r = np.sqrt(float(col.get_sizes()[0]) / np.pi) / 72.0 * fig.dpi
        return [Bbox.from_extents(x - r, y - r, x + r, y + r) for x, y in disp]

    for nm, ax, txt in [("c", axc, c_txt), ("d", axd, d_txt)]:
        e = txt.get_window_extent(ren)
        boxes = _marker_boxes(ax.collections[0])
        ov = [b for b in boxes if e.overlaps(b)]
        chk("(%s) rho text clear of scatter" % nm, len(ov) == 0,
            "%d point(s) in text bbox" % len(ov))
    # (a) median text must not overlap the dashed median line
    dline_x = axa.transData.transform((med_cg, 0))[0]
    a_e = a_txt.get_window_extent(ren)
    chk("(a) median text clear of dashed line",
        a_e.x0 > dline_x + 5, "text-left-x=%.1f line-x=%.1f" % (a_e.x0, dline_x))
    # (a) median text must not overlap the tallest histogram bar window
    tall_patch = axa.patches[0]
    tall_e = tall_patch.get_window_extent(ren)
    chk("(a) median text clear of tall bar",
        a_e.x0 > tall_e.x1, "text-x0=%.1f bar-x1=%.1f" % (a_e.x0, tall_e.x1))
    # (b) labels above their boxes' whisker caps in window coords, no overlap
    eL = b_txts[0].get_window_extent(ren)
    eR = b_txts[1].get_window_extent(ren)
    cap0 = bp["caps"][1].get_window_extent(ren)
    cap1 = bp["caps"][3].get_window_extent(ren)
    chk("(b) label L above left whisker", eL.y0 > cap0.y1 - 1,
        "L-bottom-y=%.1f cap-top-y=%.1f" % (eL.y0, cap0.y1))
    chk("(b) label R above right whisker", eR.y0 > cap1.y1 - 1,
        "R-bottom-y=%.1f cap-top-y=%.1f" % (eR.y0, cap1.y1))
    chk("(b) labels not overlapping each other", not eL.overlaps(eR))

    # ---- save PNG@600 + PDF + SVG to the review copy ----
    stem = os.path.join(OUT_DIR, "FigS3_cycle_gap")
    st.save_fig(fig, stem, dpi=600, pdf=True, svg=True)

    from PIL import Image as _PIL
    _im = _PIL.open(stem + ".png")
    dpi_png = _im.info.get("dpi", (0, 0))[0]
    chk("PNG 600dpi", abs(dpi_png - 600) < 1.0,
        "%dx%d @%.0f" % (_im.size[0], _im.size[1], dpi_png))
    chk("PDF+SVG", os.path.exists(stem + ".pdf") and os.path.exists(stem + ".svg"))
    print("MICROPATCH QC: %d/%d PASS" % (sum(qc), len(qc)))
    print("wrote", stem + ".{png,pdf,svg}")


if __name__ == "__main__":
    main()
