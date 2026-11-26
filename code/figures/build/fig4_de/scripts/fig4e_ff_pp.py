# -*- coding: utf-8 -*-
"""Figure 4 (e), bottom-left panel |dFF|, re-expressed in percentage points.

Same data, same canvas, same axes rectangle, same box/whisker rule and the
same seeded jitter as Fig4e_FF; the only change is that the absolute FF
deviation is multiplied by 100 once (dimensionless fraction -> pp) before it
is plotted, and the y axis is scaled to match.  Because values and axis are
scaled together, every mark keeps its relative position in the panel.

Nothing else is touched: the other three (e) panels, (d), and the old
Fig4e_FF files stay as they are.
"""
import os
import sys

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
FIG = os.path.join(OUT, "figures")
sys.path.insert(0, HERE)
import fig4de_standalone as G          # noqa: E402  (also asserts the frozen pins)

PP = 100.0                             # dimensionless fraction -> percentage points

# Same jitter seed the |dFF| panel uses, so the horizontal positions of the
# 44 samples are reproduced exactly.
SEED = 2026 + 10 + G.E_ORDER.index("FF")

FF_PP = np.abs(np.asarray(G.D["dev"]["FF"], float))
FF_PP = (FF_PP[np.isfinite(FF_PP)]) * PP


def draw_ff_pp(fig):
    """The |dFF| panel in pp: identical rect, fonts, colours and box rule."""
    fw, fh = fig.get_size_inches()
    ax = fig.add_axes([(0.0 + G.E_LEFT) / fw, (0.0 + G.E_M["bottom"]) / fh,
                       (G.E_W - G.E_LEFT - G.E_M["right"]) / fw,
                       (G.E_H - G.E_M["bottom"] - G.E_M["top"]) / fh])
    G.draw_box_group(ax, FF_PP, 0, G.BLUE, SEED)

    # The old axis ran 0-0.08 with ticks 0.00...0.08; scaling both by 100
    # gives 0-8 with ticks 0,2,4,6,8 and leaves every mark at the same height.
    top = G.E_LBL["FF"][0] * PP        # 0.0816 -> 8.16
    ticks = [0.0, 2.0, 4.0, 6.0, 8.0]
    ax.set_xlim(-0.5, 0.5)
    ax.set_ylim(0.0, top)
    ax.set_xticks([])
    ax.yaxis.set_major_locator(FixedLocator(ticks))
    ax.set_yticklabels(["%.0f" % t for t in ticks])
    ax.grid(False)
    G.st.configure_axes(ax)
    return ax


def main():
    fig = G.new_fig(G.E_W, G.E_H)
    ax = draw_ff_pp(fig)
    assert not G.canvas_text_out(fig), G.canvas_text_out(fig)

    # sanity, printed so the console carries the numbers
    print("n = %d" % FF_PP.size)
    print("median = %.6f pp" % float(np.median(FF_PP)))
    print("max = %.6f pp, axis top %.4f pp" % (float(FF_PP.max()),
                                               ax.get_ylim()[1]))
    print("ticks:", [t.get_text() for t in ax.get_yticklabels()])

    G.save(fig, os.path.join(FIG, "Fig4e_FF_pp"))
    print("wrote", os.path.join(FIG, "Fig4e_FF_pp.{png,pdf,svg}"))


if __name__ == "__main__":
    main()
