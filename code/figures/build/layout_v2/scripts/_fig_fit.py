# -*- coding: utf-8 -*-
"""Dev helper (not delivered): full overlap / containment report for one figure.

qa_layout.py prints only the six largest text-on-text overlaps per figure, which
is enough to gate delivery but not enough to re-tune a dense schematic. This
prints every overlap above a small area, every string that runs past its own
axes in the horizontal direction, and every string that leaves the canvas, so a
layout change can be driven by measurements instead of by re-reading the code.

    python scripts/_fig_fit.py fig1 journal
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import figstyle as st          # noqa: E402
from qa_layout import visible_text   # noqa: E402


def report(name, fig, min_area=12.0, min_axes_over=2.0):
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    W, H = fig.canvas.get_width_height()
    items = []
    for t in visible_text(fig):
        try:
            bb = t.get_window_extent(renderer=r)
        except Exception:
            continue
        items.append((t, bb))

    print("\n=== %s   canvas %d x %d px, %d strings" % (name, W, H, len(items)))

    print("-- text past the canvas edge")
    n = 0
    for t, bb in items:
        if bb.x0 < -0.5 or bb.x1 > W + 0.5 or bb.y0 < -0.5 or bb.y1 > H + 0.5:
            print("   %-46r x %7.1f .. %7.1f   y %7.1f .. %7.1f"
                  % (t.get_text()[:44].replace("\n", " / "), bb.x0, bb.x1,
                     bb.y0, bb.y1))
            n += 1
    if not n:
        print("   none")

    print("-- string wider than its own axes")
    n = 0
    for t, bb in items:
        ax = t.axes
        if ax is None:
            continue
        ab = ax.get_window_extent(renderer=r)
        over_l = max(0.0, ab.x0 - bb.x0)
        over_r = max(0.0, bb.x1 - ab.x1)
        if max(over_l, over_r) > min_axes_over:
            print("   %-46r left %6.1f  right %6.1f px"
                  % (t.get_text()[:44].replace("\n", " / "), over_l, over_r))
            n += 1
    if not n:
        print("   none")

    print("-- text out of the drawn box that holds it")
    n = 0
    for t, bb in items:
        ax = t.axes
        if ax is None:
            continue
        cx, cy = (bb.x0 + bb.x1) / 2, (bb.y0 + bb.y1) / 2
        best = None
        for p in ax.patches:
            if not isinstance(p, (FancyBboxPatch, Rectangle)):
                continue
            try:
                pb = p.get_window_extent(renderer=r)
            except Exception:
                continue
            if pb.x0 <= cx <= pb.x1 and pb.y0 <= cy <= pb.y1:
                # the smallest box containing this text's centre is the one it
                # is meant to be inside
                if best is None or pb.width * pb.height < (best.width
                                                           * best.height):
                    best = pb
        if best is None:
            continue
        out = max(best.x0 - bb.x0, bb.x1 - best.x1,
                  best.y0 - bb.y0, bb.y1 - best.y1)
        if out > min_axes_over:
            print("   %-46r out by %5.1f px  (text x %7.1f..%7.1f  "
                  "box x %7.1f..%7.1f)"
                  % (t.get_text()[:44].replace("\n", " / "), out,
                     bb.x0, bb.x1, best.x0, best.x1))
            n += 1
    if not n:
        print("   none")

    print("-- text-on-text overlaps above %.0f px^2" % min_area)
    over = []
    for i in range(len(items)):
        ti, bi = items[i]
        for j in range(i + 1, len(items)):
            tj, bj = items[j]
            ox = min(bi.x1, bj.x1) - max(bi.x0, bj.x0)
            oy = min(bi.y1, bj.y1) - max(bi.y0, bj.y0)
            if ox > 0 and oy > 0 and ox * oy >= min_area:
                over.append((ox * oy, ti.get_text()[:40].replace("\n", " / "),
                             tj.get_text()[:40].replace("\n", " / ")))
    over.sort(reverse=True)
    if not over:
        print("   none")
    for a, t1, t2 in over:
        print("   %8.0f px^2  %r\n                      <-> %r" % (a, t1, t2))
    return len(over)


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "fig1"
    size = sys.argv[2] if len(sys.argv) > 2 else "journal"
    mod = __import__(which)
    if which == "fig1_workflow":
        mod.build(size)
    elif which == "fig2_paired_recovery":
        coords, _ = mod.load()
        mod.build(size, coords)
    elif which == "figs7_ecdf":
        mod.main()
    else:
        mod.build(size)
    for name, fig in CAPTURED:
        report("%s [%s]" % (name, size), fig)
        plt.close(fig)


CAPTURED = []
_orig = st.save_fig


def _cap(fig, stem, *a, **k):
    CAPTURED.append((os.path.basename(stem), fig))
    return []


st.save_fig = _cap

if __name__ == "__main__":
    main()
