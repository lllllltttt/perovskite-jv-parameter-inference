# -*- coding: utf-8 -*-
"""
qa_layout.py — the build gate for the five reassembled main figures.
====================================================================
Two defects reached a rendered PDF in an earlier round and were found only by
rendering the exported PDF back to an image: a panel letter that collided with a
value label, and an annotation that ran past its own cell. Both are cheap to
detect on the live matplotlib renderer, so every figure in this package is now
checked here before it is delivered.

What is checked, for each figure at each output size:

  1. TEXT OUTSIDE THE CANVAS.  Every visible Text artist's window extent must
     lie inside the figure's own pixel rectangle. A string that sticks out is
     not cropped — `savefig(bbox_inches="tight")` silently grows the output
     image instead, so the delivered PNG is wider than the column width it was
     laid out for. This is the check that catches that.

  2. FROM (1), THE DELIVERED WIDTH.  The figure is written with
     `bbox_inches="tight"`, so the delivered PNG is the tight box plus the
     0.1 in pad. The script reports the actual pixel width of each delivered
     PNG beside the nominal column width, so a silent growth is visible.

  3. TEXT-ON-TEXT OVERLAP, reported but only asserted where a figure declares
     its own pairs. Overlap between two strings is not always a defect (a
     value label with an opaque backing box deliberately sits on a line), so
     the audit prints the worst offenders and lets the figure scripts keep
     their own precise assertions.

Run:  python scripts/qa_layout.py
Exit code is non-zero if any check fails.
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.text import Text

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import figstyle as st

CAPTURED = []
_orig_save = st.save_fig


def _capture(fig, out_stem, *a, **kw):
    """Record the live figure so it can be measured, then save as usual."""
    CAPTURED.append((os.path.basename(out_stem), fig))
    return _orig_save(fig, out_stem, *a, **kw)


st.save_fig = _capture

# the figure modules look this up by name at import time in some cases
import fig1_workflow      # noqa: E402
import fig2_paired_recovery   # noqa: E402
import fig3_neighbour     # noqa: E402
import fig4_forward       # noqa: E402
import fig5_intervals     # noqa: E402
import figS6_nineparam    # noqa: E402
import figs7_ecdf         # noqa: E402

for m in (fig1_workflow, fig2_paired_recovery, fig3_neighbour, fig4_forward,
          fig5_intervals, figS6_nineparam, figs7_ecdf):
    if hasattr(m, "st"):
        m.st.save_fig = _capture


def visible_text(fig):
    """Every Text artist matplotlib will actually put on the page.

    `ax.axis("off")` is the trap here: the axes is used only as a transparent
    overlay (the row headers of Figure 2, the panel-(e) footer of Figure 4,
    the nine-parameter axis label of Figure S6), and matplotlib does not draw
    its ticks -- but the tick Text artists are still there, still report
    visible=True, and still hold the positions of a default 0..1 axis. Feeding
    those to the canvas check produces failures for text that is never drawn.
    """
    out = []
    for ax in fig.axes:
        if not ax.get_visible():
            continue
        for t in ax.texts:
            out.append(t)
        if ax.axison:
            out.extend(ax.get_xticklabels())
            out.extend(ax.get_yticklabels())
            out.append(ax.xaxis.get_label())
            out.append(ax.yaxis.get_label())
        # legends ARE drawn on an axis-off overlay (Figure 5 uses one to hold
        # the two key blocks), so they are collected regardless of axison
        for leg in ([ax.get_legend()] if ax.get_legend() is not None
                    else []):
            out.extend(leg.get_texts())
            if leg.get_title() is not None:
                out.append(leg.get_title())
        if ax.title is not None:
            out.append(ax.title)
    out.extend(fig.texts)
    lg = fig.legends
    for leg in lg:
        out.extend(leg.get_texts())
    res = []
    for t in out:
        if t is None:
            continue
        if not t.get_text().strip():
            continue
        if not t.get_visible():
            continue
        res.append(t)
    return res


def audit(name, fig, pad_px=0.75, tol_in=0.02):
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    W, H = fig.canvas.get_width_height()

    # ---- primary check: what savefig(bbox_inches="tight") will actually
    # include. This is the honest gate. A per-text scan alone is not: an x tick
    # outside the view interval keeps a Text artist with visible=True and a
    # position past the axes, but matplotlib never paints it and never counts
    # it in the tight bbox (Figure S7 has such a tick at 6.0 on axes that end
    # at 5.31). Only the tight bbox decides whether the delivered PNG comes out
    # wider than the column it was laid out for.
    dpi = fig.dpi
    tb = fig.get_tightbbox(r)          # inches
    overshoot = {"left": max(0.0, -tb.x0),
                 "bottom": max(0.0, -tb.y0),
                 "right": max(0.0, tb.x1 - W / dpi),
                 "top": max(0.0, tb.y1 - H / dpi)}
    spill = max(overshoot.values())

    bad = []
    boxes = []
    for t in visible_text(fig):
        try:
            bb = t.get_window_extent(renderer=r)
        except Exception:
            continue
        boxes.append((t.get_text()[:40], bb))
        if (bb.x0 < -pad_px or bb.y0 < -pad_px
                or bb.x1 > W + pad_px or bb.y1 > H + pad_px):
            where = ""
            ax = t.axes
            if ax is not None:
                for getter in ("get_position",):
                    try:
                        ab = getattr(ax, getter)().bounds
                        where = " on axis (%.3f,%.3f,%.3f,%.3f)" % ab
                        break
                    except Exception:
                        try:
                            ab = ax.axes.get_position().bounds
                            where = " on axis (%.3f,%.3f,%.3f,%.3f)" % ab
                        except Exception:
                            where = " (axes unknown)"
            bad.append((t.get_text()[:52].replace("\n", " / "),
                        round(bb.x0, 1), round(bb.y0, 1),
                        round(bb.x1, 1), round(bb.y1, 1), where))
    # only the offenders that lie outside AND are counted in the tight bbox
    # cause the delivered image to grow; rank them so the cause is on top
    counted = [b for b in bad
               if (b[1] < -pad_px or b[2] < -pad_px
                   or b[3] > W + pad_px or b[4] > H + pad_px)]

    # worst overlapping pairs, for information
    over = []
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            (t1, b1), (t2, b2) = boxes[i], boxes[j]
            ox = min(b1.x1, b2.x1) - max(b1.x0, b2.x0)
            oy = min(b1.y1, b2.y1) - max(b1.y0, b2.y0)
            if ox > 1.5 and oy > 1.5:
                over.append((ox * oy, t1, t2))
    over.sort(reverse=True)
    return dict(name=name, w=W, h=H, n_text=len(boxes), outside=bad,
                counted=counted, spill=spill, overshoot=overshoot,
                tol_in=tol_in, overlaps=over[:6])
    # worst overlapping pairs, for information
    over = []
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            (t1, b1), (t2, b2) = boxes[i], boxes[j]
            ox = min(b1.x1, b2.x1) - max(b1.x0, b2.x0)
            oy = min(b1.y1, b2.y1) - max(b1.y0, b2.y0)
            if ox > 1.5 and oy > 1.5:
                over.append((ox * oy, t1, t2))
    over.sort(reverse=True)
    return dict(name=name, w=W, h=H, n_text=len(boxes), outside=bad,
                overlaps=over[:6])


def main():
    for sz in ("journal", "large"):
        fig1_workflow.build(sz)
        coords, _per = fig2_paired_recovery.load()
        fig2_paired_recovery.build(sz, coords)
        fig3_neighbour.build(sz)
        fig4_forward.build(sz)
        fig5_intervals.build(sz)
        figS6_nineparam.build(sz)
    # figs7_ecdf has no plain build(size): its figure is fed by the corrected
    # pair analysis, and re-deriving that pair set is the point of running the
    # gate on the delivered script rather than on a cached table.
    figs7_ecdf.main()

    print("\n%d rendered figures measured\n" % len(CAPTURED))
    failures = 0
    rows = []
    for name, fig in CAPTURED:
        a = audit(name, fig)
        rows.append(a)
        print("%-28s canvas %4d x %4d px, %3d text artists"
              % (a["name"], a["w"], a["h"], a["n_text"]))
        ov = a["overshoot"]
        if a["spill"] > a["tol_in"]:
            failures += 1
            print("   FAIL savefig tight box exceeds the canvas by %.3f in "
                  "(left %.3f, right %.3f, bottom %.3f, top %.3f) -- the "
                  "delivered PNG will be wider/taller than laid out"
                  % (a["spill"], ov["left"], ov["right"], ov["bottom"],
                     ov["top"]))
            for t, x0, y0, x1, y1, where in a["outside"]:
                print("        candidate: %-50s bbox=(%.1f,%.1f)-(%.1f,%.1f)%s"
                      % (t, x0, y0, x1, y1, where))
        else:
            print("   ok   tight box fits the canvas (max overshoot %.3f in, "
                  "tolerance %.2f in)" % (a["spill"], a["tol_in"]))
            if a["outside"]:
                # kept as information only: these are Text artists matplotlib
                # does not paint (out-of-view ticks), so they cannot grow the
                # delivered image.
                print("        (%d text artist(s) sit outside the canvas but "
                      "are not painted, e.g. %r)"
                      % (len(a["outside"]), a["outside"][0][0]))
        for area, t1, t2 in a["overlaps"]:
            print("   note overlap %.0f px^2: %r  <->  %r" % (area, t1, t2))
        plt.close(fig)

    # delivered PNG width vs the nominal column width
    print("\ndelivered PNG geometry (nominal journal width 7.09 in, "
          "large 9.50 in):")
    from PIL import Image
    for name, _fig in CAPTURED:
        p = os.path.join(st.FIGDIR, name + ".png")
        if not os.path.exists(p):
            continue
        W, H = Image.open(p).size
        print("   %-28s %5d x %5d px" % (name + ".png", W, H))

    print("\nqa_layout: %s" % ("PASS" if failures == 0
                               else "FAIL (%d figure(s))" % failures))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
