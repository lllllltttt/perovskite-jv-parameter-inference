# -*- coding: utf-8 -*-
"""
figure_font_audit.py — smallest in-figure type size, per delivered figure.
==========================================================================
The assembly step has to choose a display width for every figure. That choice
is not free: a figure authored at W_a cm and displayed at W_d cm renders its
internal type at

    f_rendered = f_internal * W_d / W_a .

The project's legibility rule, recorded when the figure widths were fixed, is

    f_internal >= 0.3886 pt/cm * W_display(cm)          (== 7.0 / 18.01)

i.e. the figure may not be enlarged beyond the scale at which a 7 pt label is
still 7 pt. Rearranged, it gives the widest display each figure tolerates:

    W_d_max = f_min_internal / 0.3886      (cm).

This script measures f_min_internal on the live renderer for every figure at
both output sizes and prints W_d_max, so the widths written into Word are read
off a measurement rather than assumed. It fails if any figure would need a
display width narrower than the manuscript's 17.27 cm text column.

Run:  python scripts/figure_font_audit.py
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import figstyle as st

CAPTURED = []
_orig_save = st.save_fig


def _capture(fig, out_stem, *a, **kw):
    CAPTURED.append((os.path.basename(out_stem), fig))
    plt.close(fig)          # measure only; do not rewrite the delivered files
    return []


st.save_fig = _capture

import fig1_workflow          # noqa: E402
import fig2_paired_recovery   # noqa: E402
import fig3_neighbour         # noqa: E402
import fig4_forward           # noqa: E402
import fig5_intervals         # noqa: E402
import figS6_nineparam        # noqa: E402
import figs7_ecdf             # noqa: E402

for m in (fig1_workflow, fig2_paired_recovery, fig3_neighbour, fig4_forward,
          fig5_intervals, figS6_nineparam, figs7_ecdf):
    if hasattr(m, "st"):
        m.st.save_fig = _capture

PT_PER_CM = 7.0 / 18.01        # the recorded legibility coefficient
AUTHOR_CM = 18.01              # 7.09 in, the authoring width of this package
COLUMN_CM = 17.27              # the manuscript's text column


def smallest_type(fig):
    """(min fontsize in pt, the text it belongs to, count of text artists)."""
    fig.canvas.draw()
    best, who, n = None, "", 0
    for ax in fig.axes:
        items = list(ax.texts)
        if ax.axison:
            items += list(ax.get_xticklabels()) + list(ax.get_yticklabels())
            items += [ax.xaxis.get_label(), ax.yaxis.get_label()]
        if ax.get_legend() is not None:
            items += list(ax.get_legend().get_texts())
        if ax.title is not None:
            items.append(ax.title)
        for t in items:
            if t.get_text().strip() and t.get_visible():
                n += 1
                f = float(t.get_fontsize())
                if best is None or f < best:
                    best, who = f, t.get_text()[:40].replace("\n", " ")
    for t in fig.texts:
        if t.get_text().strip() and t.get_visible():
            n += 1
            f = float(t.get_fontsize())
            if best is None or f < best:
                best, who = f, t.get_text()[:40].replace("\n", " ")
    for leg in fig.legends:
        for t in leg.get_texts():
            n += 1
            f = float(t.get_fontsize())
            if best is None or f < best:
                best, who = f, t.get_text()[:40].replace("\n", " ")
    return best, who, n


def main():
    for sz in ("journal", "large"):
        fig1_workflow.build(sz)
        coords, _per = fig2_paired_recovery.load()
        fig2_paired_recovery.build(sz, coords)
        fig3_neighbour.build(sz)
        fig4_forward.build(sz)
        fig5_intervals.build(sz)
        figS6_nineparam.build(sz)
    figs7_ecdf.main()

    print("\n%-34s %8s %10s %10s  %s"
          % ("figure", "min pt", "W_d_max", "at 17.27cm", "smallest string"))
    print("%-34s %8s %10s %10s  %s"
          % ("", "", "(cm)", "renders at", ""))
    bad = 0
    for name, fig in CAPTURED:
        f, who, _n = smallest_type(fig)
        wmax = f / PT_PER_CM
        rendered = f * COLUMN_CM / AUTHOR_CM
        flag = "" if wmax >= COLUMN_CM else "   <-- TOO NARROW"
        if wmax < COLUMN_CM:
            bad += 1
        print("%-34s %8.1f %10.2f %10.2f  %s%s"
              % (name, f, wmax, rendered, who, flag))
    print("\nlegend: W_d_max is the widest display width at which this figure "
          "still satisfies\n        f_internal >= %.4f pt/cm x W_display; "
          "'renders at' assumes the\n        manuscript column, %.2f cm wide."
          % (PT_PER_CM, COLUMN_CM))
    print("figure_font_audit: %s"
          % ("PASS" if bad == 0 else "FAIL (%d figure(s))" % bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
