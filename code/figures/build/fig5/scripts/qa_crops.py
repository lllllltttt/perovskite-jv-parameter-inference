# -*- coding: utf-8 -*-
"""Print-scale crops used for the three visual checks the author asked for.

  * does the shared key cover any curve?            -> qa/crop_e_key.png
  * can the two lines of one family be told apart?  -> qa/crop_a_families.png
  * are the 90/95 % points of (a) still separate?   -> qa/crop_a_9095.png
  * are the 0 and 0.2 noise points of (c-e) separate?
                                                    -> qa/crop_c_0_02.png
                                                    -> qa/crop_d_0_02.png

Crops come from the delivered 600 dpi PNGs, so they show exactly what will be
printed.  Read-only.
"""
import os
import sys

import numpy as np
from PIL import Image

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIG = os.path.join(ROOT, "figures")
QA = os.path.join(ROOT, "qa")
sys.path.insert(0, HERE)
import fig5_standalone as G      # noqa: E402


def crop(name, xlim=None, ylim=None, frac=None, scale=1.0, out=None):
    """Crop the delivered PNG to a data window (or a fractional window)."""
    fig = G.new_fig(*G.PW[name])
    res = {"a": G.draw_a, "b": G.draw_b, "c": G.draw_c,
           "d": G.draw_d, "e": G.draw_e}[name](fig)
    ax = res[0]
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    bb = ax.get_window_extent(renderer=r)
    dpi = fig.dpi
    if xlim is None:
        x0, x1, y0, y1 = frac
        px0 = bb.x0 + x0 * bb.width
        px1 = bb.x0 + x1 * bb.width
        py0 = bb.y0 + y0 * bb.height
        py1 = bb.y0 + y1 * bb.height
    else:
        p0 = ax.transData.transform((xlim[0], ylim[0]))
        p1 = ax.transData.transform((xlim[1], ylim[1]))
        px0, px1, py0, py1 = p0[0], p1[0], p0[1], p1[1]
    k = 600.0 / dpi
    H = G.PW[name][1] * dpi
    box = (int(round(px0 * k)), int(round((H - py1) * k)),
           int(round(px1 * k)), int(round((H - py0) * k)))
    im = Image.open(os.path.join(FIG, "Fig5%s.png" % name)).crop(box)
    if scale != 1.0:
        im = im.resize((int(im.width * scale), int(im.height * scale)),
                       Image.LANCZOS)
    im.save(os.path.join(QA, out))
    plt.close(fig)
    return out, im.size


if __name__ == "__main__":
    os.makedirs(QA, exist_ok=True)
    print(crop("e", (-0.06, 1.10), (-3.30, -0.60), scale=1.6,
               out="crop_e_key.png"))
    print(crop("a", (78.0, 102.0), (0.74, 1.00), scale=1.6,
               out="crop_a_families.png"))
    print(crop("a", (88.0, 97.0), (0.87, 0.95), scale=3.0,
               out="crop_a_9095.png"))
    print(crop("c", (-0.06, 0.60), (0.80, 0.96), scale=2.0,
               out="crop_c_0_02.png"))
    print(crop("d", (-0.06, 0.60), (0.88, 0.98), scale=2.0,
               out="crop_d_0_02.png"))
    print(crop("a", (48.0, 62.0), (0.44, 0.56), scale=3.0,
               out="crop_a_50.png"))
