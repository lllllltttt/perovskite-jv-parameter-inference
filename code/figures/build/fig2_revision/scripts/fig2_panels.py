# -*- coding: utf-8 -*-
"""fig2_panels.py -- the six clean single scatter panels, as drawn in Figure 2.

Each file contains ONLY what the supervisor asked a panel to contain: the real
scatter, the frame, the ticks, the tick numbers and the y = x dashed line. No
panel letter, no column name, no axis title, no correlation value -- those are
added at assembly time in the composite (fig2_build.py) as separate text.

Geometry is identical to the composite panel (1.763 in square, same limits,
same tick set, same colours), so a panel dropped into a slide keeps exactly the
look it has in the paper.

Writes figures/panels/Figure2_panel_<id>.{png,pdf,svg}
"""
import os
import sys

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
DATADIR = os.path.join(OUT, "data_used")
FIGDIR = os.path.join(OUT, "figures", "panels")

sys.path.insert(0, HERE)
import fig2_build as B   # style constants only; importing does not save anything

FAMILIES = B.FAMILIES
LIMITS = B.LIMITS
TICKS = B.TICKS
R_LIMIT = B.R_LIMIT
R_TICKS = B.R_TICKS


def one_panel(df, key, lim, ticks, color, fmt, path):
    # the PLOT BOX stays exactly P x P like the composite panel; the canvas is
    # grown by the margins the tick labels need, so nothing is clipped when the
    # file is used on its own.
    ml, mr, mb, mt = 0.40, 0.06, 0.26, 0.05
    wf, hf = B.P + ml + mr, B.P + mb + mt
    fig = plt.figure(figsize=(wf, hf), dpi=100)
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([ml / wf, mb / hf, B.P / wf, B.P / hf])
    t = df[key + "_true"].values
    p = df[key + "_pred"].values
    ax.scatter(t, p, s=1.6, alpha=B.ALPHA, color=color, linewidths=0,
               rasterized=True, zorder=2)
    ax.plot(list(lim), list(lim), ls=(0, (4.0, 2.4)), color=B.MUTED, lw=0.8,
            zorder=3)
    ax.set_xlim(*lim)
    ax.set_ylim(*lim)
    ax.set_xticks(ticks)
    ax.set_yticks(ticks)
    ax.xaxis.set_major_formatter(B.unified(fmt))
    ax.yaxis.set_major_formatter(B.unified(fmt))
    ax.tick_params(axis="both", which="major", direction="out", length=3.0,
                   width=0.7, labelsize=B.FS_TICK, colors=B.INK,
                   top=False, right=False, pad=2.5)
    for sp in ax.spines.values():
        sp.set_color(B.INK)
        sp.set_linewidth(0.7)
    ax.set_facecolor("none")
    fig.savefig(path + ".png", dpi=600, facecolor="white")
    fig.savefig(path + ".pdf", dpi=600, facecolor="white")
    fig.savefig(path + ".svg", dpi=600, facecolor="white")
    plt.close(fig)


def main():
    os.makedirs(FIGDIR, exist_ok=True)
    df = pd.read_csv(os.path.join(DATADIR, "fig2_coordinates.csv"))
    for fam, row in (("a", "a"), ("r", "b")):
        for col, (lab, _title, tag) in enumerate(FAMILIES):
            key = "%s_%s" % (fam, tag)
            lim = LIMITS[lab] if fam == "a" else R_LIMIT
            ticks = TICKS[lab] if fam == "a" else R_TICKS
            color = B.C_A if fam == "a" else B.C_R
            fmt = "%.1f" if fam == "r" else "%d"
            path = os.path.join(FIGDIR, "Figure2_panel_%s%d" % (row, col + 1))
            one_panel(df, key, lim, ticks, color, fmt, path)
            print("wrote", path)


if __name__ == "__main__":
    main()
