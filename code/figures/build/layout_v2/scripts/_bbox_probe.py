# -*- coding: utf-8 -*-
"""Dev helper (not delivered): print the window extents of the artists named by
a callable, for one figure, so a reported overlap can be traced to its slot.

    python scripts/_bbox_probe.py fig3 0.713
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import figstyle as st          # noqa: E402

CAP = []
_orig = st.save_fig


def _cap(fig, stem, *a, **k):
    CAP.append((os.path.basename(stem), fig))
    return []


st.save_fig = _cap
import fig3_neighbour as F     # noqa: E402

filt = sys.argv[1] if len(sys.argv) > 1 else "0.713"

F.build("journal")
for name, fig in CAP:
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    W, H = fig.canvas.get_width_height()
    print("=== %s canvas %d x %d" % (name, W, H))
    for ax in fig.axes:
        items = list(ax.texts)
        leg = ax.get_legend()
        if leg is not None:
            items += list(leg.get_texts())
        items.append(ax.title)
        items += list(ax.get_xticklabels()) + list(ax.get_yticklabels())
        for t in items:
            s = t.get_text()
            if filt and filt not in s:
                continue
            bb = t.get_window_extent(renderer=r)
            ab = ax.get_window_extent(renderer=r)
            print("  axes %-28r  text %-40r\n      y %7.1f .. %7.1f   "
                  "x %7.1f .. %7.1f   (axes y %7.1f .. %7.1f  "
                  "x %7.1f .. %7.1f)"
                  % (ax.get_label(), s[:38].replace("\n", " / "),
                     bb.y0, bb.y1, bb.x0, bb.x1, ab.y0, ab.y1, ab.x0, ab.x1))
    plt.close(fig)
