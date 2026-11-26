# -*- coding: utf-8 -*-
"""fig2_build.py -- Figure 2, supervisor revision.

Layout
------
row 1 : (a1) (a2) (a3)   shared scale a      mobility / bulk lifetime / DOS
row 2 : (b1) (b2) (b3)   log-ratio r
row 3 : (c) Pearson correlation      (d) MAE reduction vs training median

Design rules enforced here rather than eyeballed later
-------------------------------------------------------
* every scatter panel is a SQUARE box with IDENTICAL x and y limits and the
  same tick set on both axes, so the identity line is exactly the diagonal;
* points, frame, ticks and the identity line are the only things drawn inside
  a panel; every title, axis name, unit, panel letter and correlation value is
  placed here at assembly time as its own text object;
* colours are the first two entries of Seaborn's "deep" qualitative palette
  (SEABORN_PALETTES["deep"]), #4C72B0 and #DD8452;
* both bar panels start at zero, have equal plot-box heights and their own y
  axes; the single legend sits in a reserved band inside the lower block;
* the PDF/PNG are set with a plain-text/mathtext mix; the SVG writer replaces
  every mathtext string by ONE <text> element with inline <tspan> runs, so the
  delivered SVG stays live, editable text.
"""
import json
import os

import numpy as np
import pandas as pd
from scipy.stats import pearsonr

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter, FormatStrFormatter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
DATADIR = os.path.join(OUT, "data_used")
FIGDIR = os.path.join(OUT, "figures")

# ------------------------------------------------------------------ style --
C_A = "#4C72B0"          # Seaborn deep[0]  (76, 114, 176)
C_R = "#DD8452"          # Seaborn deep[1]  (221, 132, 82)
INK = "#1a1a1a"
MUTED = "#555555"

FONT = "Arial"
FS_GROUP = 8.5
FS_COL = 8.0
FS_UNIT = 7.0
FS_LETTER = 8.5
FS_AXLAB = 7.5
FS_TICK = 7.0
FS_RHO = 7.5
FS_VAL = 7.0
FS_LEG = 7.5

ALPHA = 0.16             # identical rule for both scatter rows

matplotlib.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": [FONT, "DejaVu Sans"],
    "mathtext.fontset": "custom",
    "mathtext.rm": FONT,
    "mathtext.it": FONT + ":italic",
    "mathtext.bf": FONT + ":bold",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "svg.fonttype": "none",
    "axes.unicode_minus": True,
})

# ----------------------------------------------------------------- canvas --
W = 6.8                    # 172.72 mm -- the width the figure is displayed at
LEFT = 0.50
RIGHT = 0.05
GAP = 0.48
P = (W - LEFT - RIGHT - 2 * GAP) / 3.0     # square panel side, inches

Y_GROUP1 = 0.19
Y_COLNAME = Y_GROUP1 + 0.255
Y_COLUNIT = Y_COLNAME + 0.16
Y_LETTER1 = Y_COLUNIT + 0.16
Y_P1_TOP = Y_LETTER1 + 0.083
Y_P1_BOT = Y_P1_TOP + P
Y_XLAB1 = Y_P1_BOT + 0.275      # clears the tick labels (font box, not caps)
Y_GROUP2 = Y_XLAB1 + 0.245
Y_LETTER2 = Y_GROUP2 + 0.16
Y_P2_TOP = Y_LETTER2 + 0.083
Y_P2_BOT = Y_P2_TOP + P
Y_XLAB2 = Y_P2_BOT + 0.275
Y_LEGEND = Y_XLAB2 + 0.235
Y_LETTER3 = Y_LEGEND + 0.18
Y_BAR_TOP = Y_LETTER3 + 0.083
BAR_H = 1.15
Y_BAR_BOT = Y_BAR_TOP + BAR_H
Y_TICKBAR = Y_BAR_BOT + 0.145
H = Y_TICKBAR + 0.05

FAMILIES = [
    ("mobility", "Mobility", "mu"),
    ("lifetime", "Bulk lifetime", "tau"),
    ("DOS", "Density of states", "D"),
]
LIMITS = {"mobility": (-6.6, -1.4), "lifetime": (-9.9, -1.6), "DOS": (22.5, 26.8)}
TICKS = {"mobility": [-6, -5, -4, -3, -2],
         "lifetime": [-9, -8, -7, -6, -5, -4, -3, -2],
         "DOS": [23, 24, 25, 26]}
R_LIMIT = (-0.95, 1.30)
R_TICKS = [-0.5, 0.0, 0.5, 1.0]

# ------------------------------------------------------- text run machinery -
MATH = []          # ordered registry consumed by svg_textify.py

MINUS = "−"


def R(t):
    return ("r", t)


def I(t):
    return ("i", t)


def SUB(t):
    return ("sub", t)


def SUBI(t):
    return ("subi", t)


def SUP(t):
    return ("sup", t)


def S():
    return ("sp", "")


def SPACE(n):
    return ("sp%d" % n, "")


LOG = ("op", "log")


def _mathify(kind, text):
    if kind == "i":
        return text
    if kind == "op":
        return "\\" + text
    if kind == "sub":
        return "_{\\mathrm{%s}}" % text
    if kind == "subi":
        return "_{%s}" % text
    if kind == "sup":
        return "^{\\mathrm{%s}}" % text
    if kind == "supi":
        return "^{%s}" % text
    raise ValueError(kind)


def to_mathtext(runs):
    """Plain text outside $...$, math inside, one string per logical label."""
    parts, buf, mode = [], [], None

    def flush():
        if not buf:
            return
        parts.append(("$" + "".join(buf) + "$") if mode == "m" else "".join(buf))
        del buf[:]

    for kind, text in runs:
        if kind == "r":
            if mode != "t":
                flush(); mode = "t"
            buf.append(text)
        elif kind in ("sp", "sp2", "sp3"):
            if mode != "t":
                flush(); mode = "t"
            buf.append({"sp": " ", "sp2": "  ", "sp3": "   "}[kind])
        else:
            if mode != "m":
                flush(); mode = "m"
            buf.append(_mathify(kind, text))
    flush()
    return "".join(parts)


def mtext(x_in, y_in, runs, size, color=INK, ha="left", rot=0.0):
    fig.text(x_in / W, 1.0 - y_in / H, to_mathtext(runs), fontsize=size,
             color=color, ha=ha, va="baseline", rotation=rot,
             rotation_mode="anchor" if rot else "default")
    MATH.append(dict(runs=runs, size=size, color=color, ha=ha, rot=rot,
                     ax=x_in * 72.0, ay=y_in * 72.0))


def ptext(x_in, y_in, s, size, color=INK, ha="left", va="baseline",
          weight="normal", rot=0.0):
    return fig.text(x_in / W, 1.0 - y_in / H, s, fontsize=size, color=color,
                    ha=ha, va=va, fontweight=weight, rotation=rot,
                    rotation_mode="anchor" if rot else "default")


def fig_axes(x_in, y_in, w_in, h_in):
    return fig.add_axes([x_in / W, 1.0 - (y_in + h_in) / H,
                         w_in / W, h_in / H])


def panel_left(col):
    return LEFT + col * (P + GAP)


def unified(fmt):
    """Format a tick with the typographic minus, not an ASCII hyphen.

    FormatStrFormatter formats numbers without matplotlib's unicode-minus
    substitution, so "-2" would come out with a short hyphen that reads as a
    different glyph from the minus inside the formulas.
    """
    return FuncFormatter(lambda v, _pos: (fmt % v).replace("-", MINUS))


def swatch(x_in, base_y, color, w=0.085):
    """Small colour key sitting on the baseline, spanning the cap height."""
    # top of the square 0.006 in above the baseline, bottom one square lower
    fig.patches.append(Rectangle((x_in / W, 1.0 - (base_y - 0.006) / H),
                                 w / W, w / H, transform=fig.transFigure,
                                 facecolor=color, edgecolor="none", zorder=5))


# ------------------------------------------------------------------- build --
def build(df):
    global fig
    fig = plt.figure(figsize=(W, H), dpi=100)
    fig.patch.set_facecolor("white")

    coords = {c: (df[c + "_true"].values, df[c + "_pred"].values)
              for c in ("a_mu", "a_tau", "a_D", "r_mu", "r_tau", "r_D")}
    rho = {k: float(pearsonr(*v)[0]) for k, v in coords.items()}
    metric = pd.read_csv(os.path.join(DATADIR, "fig2_metrics.csv"))
    red = {r.symbol: float(r.mae_reduction) for _, r in metric.iterrows()}

    # ---- six scatter panels ------------------------------------------------
    for fam, y_top, letter in (("a", Y_P1_TOP, "a"), ("r", Y_P2_TOP, "b")):
        for col, (lab, _title, tag) in enumerate(FAMILIES):
            x0 = panel_left(col)
            ax = fig_axes(x0, y_top, P, P)
            key = "%s_%s" % (fam, tag)
            t, p = coords[key]
            color = C_A if fam == "a" else C_R
            lim = LIMITS[lab] if fam == "a" else R_LIMIT
            ticks = TICKS[lab] if fam == "a" else R_TICKS
            ax.scatter(t, p, s=1.6, alpha=ALPHA, color=color, linewidths=0,
                       rasterized=True, zorder=2)
            ax.plot(list(lim), list(lim), ls=(0, (4.0, 2.4)), color=MUTED,
                    lw=0.8, zorder=3)
            ax.set_xlim(*lim)
            ax.set_ylim(*lim)
            ax.set_xticks(ticks)
            ax.set_yticks(ticks)
            fmt = "%.1f" if fam == "r" else "%d"
            ax.xaxis.set_major_formatter(unified(fmt))
            ax.yaxis.set_major_formatter(unified(fmt))
            ax.tick_params(axis="both", which="major", direction="out",
                           length=3.0, width=0.7, labelsize=FS_TICK,
                           colors=INK, top=False, right=False, pad=2.5)
            for sp in ax.spines.values():
                sp.set_color(INK)
                sp.set_linewidth(0.7)
            ax.set_facecolor("none")

            # panel letter just outside the top-left corner of the frame
            ptext(x0 - 0.02, y_top - 0.075, "(%s%d)" % (letter, col + 1),
                  FS_LETTER, weight="bold")
            # correlation, same relative spot in all six panels, in the empty
            # lower-right corner
            mtext(x0 + P - 0.115, y_top + P - 0.115,
                  [I("ρ"), S(), R("="), S(), R("%.3f" % rho[key])],
                  FS_RHO, ha="right")
            # axis names
            mtext(x0 + P / 2.0, y_top + P + 0.275,
                  [R("True "), I("a" if fam == "a" else "r")],
                  FS_AXLAB, ha="center")
            mtext(x0 - 0.315, y_top + P / 2.0,
                  [R("Predicted "), I("a" if fam == "a" else "r")],
                  FS_AXLAB, ha="center", rot=90)

    # ---- column names, written once ---------------------------------------
    for col, (lab, title, tag) in enumerate(FAMILIES):
        xc = panel_left(col) + P / 2.0
        ptext(xc, Y_COLNAME, title, FS_COL, ha="center")
        if lab == "mobility":
            unit = [I("μ"), SUBI("n"), R(", "), I("μ"), SUBI("p"),
                    R(" (m"), SUP("2"), R(" V"), SUP(MINUS + "1"),
                    R(" s"), SUP(MINUS + "1"), R(")")]
        elif lab == "lifetime":
            unit = [I("τ"), SUBI("n"), R(", "), I("τ"), SUBI("p"),
                    R(" (s)")]
        else:
            unit = [I("N"), SUBI("c"), R(", "), I("N"), SUBI("v"),
                    R(" (m"), SUP(MINUS + "3"), R(")")]
        mtext(xc, Y_COLUNIT, unit, FS_UNIT, color=MUTED, ha="center")

    # ---- the two row group names ------------------------------------------
    swatch(LEFT, Y_GROUP1, C_A)
    mtext(LEFT + 0.155, Y_GROUP1,
          [R("Shared scale"), SPACE(2), I("a"), R(" = ("), LOG, SUB("10"),
           S(), I("p"), SUBI("n"), R(" + "), LOG, SUB("10"), S(),
           I("p"), SUBI("p"), R(")/2")], FS_GROUP)

    swatch(LEFT, Y_GROUP2, C_R)
    mtext(LEFT + 0.155, Y_GROUP2,
          [R("Electron–hole log-ratio"), SPACE(2), I("r"), R(" = "),
           LOG, SUB("10"), R("("), I("p"), SUBI("n"), R("/"),
           I("p"), SUBI("p"), R(")")], FS_GROUP)

    # ---- the two bar panels ------------------------------------------------
    BW = 0.36
    x = np.arange(3, dtype=float)
    bwidth = (W - LEFT - RIGHT - 0.85) / 2.0
    bx = [LEFT, LEFT + bwidth + 0.85]

    axc = fig_axes(bx[0], Y_BAR_TOP, bwidth, BAR_H)
    a_vals = [rho["a_" + t] for _l, _ti, t in FAMILIES]
    r_vals = [rho["r_" + t] for _l, _ti, t in FAMILIES]
    axc.bar(x - BW / 2, a_vals, BW, color=C_A, linewidth=0, zorder=3)
    axc.bar(x + BW / 2, r_vals, BW, color=C_R, linewidth=0, zorder=3)
    for xs, vals in ((x - BW / 2, a_vals), (x + BW / 2, r_vals)):
        for xi, v in zip(xs, vals):
            axc.text(xi, v + 0.018, "%.3f" % v, ha="center", va="bottom",
                     fontsize=FS_VAL, color=INK, zorder=4)
    axc.set_xlim(-0.62, 2.62)
    axc.set_ylim(0.0, 1.05)
    axc.set_yticks([0.0, 0.25, 0.5, 0.75, 1.0])
    axc.yaxis.set_major_formatter(FormatStrFormatter("%.2f"))
    axc.set_xticks(x)
    axc.set_xticklabels([ti for _l, ti, _t in FAMILIES], fontsize=FS_TICK)
    axc.tick_params(axis="x", length=0, pad=3.5)
    _bar_style(axc)
    ptext(bx[0] - 0.02, Y_BAR_TOP - 0.075, "(c)", FS_LETTER, weight="bold")
    ptext(bx[0] - 0.30, Y_BAR_TOP + BAR_H / 2, "Pearson correlation ρ",
          FS_AXLAB, ha="center", rot=90)

    axd = fig_axes(bx[1], Y_BAR_TOP, bwidth, BAR_H)
    a_red = [100.0 * red["a_" + t] for _l, _ti, t in FAMILIES]
    r_red = [100.0 * red["r_" + t] for _l, _ti, t in FAMILIES]
    axd.bar(x - BW / 2, a_red, BW, color=C_A, linewidth=0, zorder=3)
    axd.bar(x + BW / 2, r_red, BW, color=C_R, linewidth=0, zorder=3)
    for xs, vals in ((x - BW / 2, a_red), (x + BW / 2, r_red)):
        for xi, v in zip(xs, vals):
            axd.text(xi, v + 1.9, "%.1f%%" % v, ha="center", va="bottom",
                     fontsize=FS_VAL, color=INK, zorder=4)
    axd.set_xlim(-0.62, 2.62)
    axd.set_ylim(0.0, 80.0)
    axd.set_yticks([0, 20, 40, 60, 80])
    axd.set_xticks(x)
    axd.set_xticklabels([ti for _l, ti, _t in FAMILIES], fontsize=FS_TICK)
    axd.tick_params(axis="x", length=0, pad=3.5)
    _bar_style(axd)
    ptext(bx[1] - 0.02, Y_BAR_TOP - 0.075, "(d)", FS_LETTER, weight="bold")
    ptext(bx[1] - 0.48, Y_BAR_TOP + BAR_H / 2, "MAE reduction (%)",
          FS_AXLAB, ha="center", rot=90)
    ptext(bx[1] - 0.27, Y_BAR_TOP + BAR_H / 2, "vs. training median",
          FS_AXLAB, ha="center", rot=90)

    # ---- one shared legend inside the lower block --------------------------
    _legend(cx=3.40, cy=Y_LEGEND)

    return rho, red


def _bar_style(ax):
    ax.tick_params(axis="y", which="major", direction="out", length=3.0,
                   width=0.7, labelsize=FS_TICK, colors=INK, pad=2.5)
    for sp in ax.spines.values():
        sp.set_color(INK)
        sp.set_linewidth(0.7)
    ax.set_facecolor("none")


def _legend(cx, cy):
    entries = [([R("Shared scale"), S(), I("a")], C_A),
               ([R("Electron–hole log-ratio"), S(), I("r")], C_R)]
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    widths = []
    for runs, _c in entries:
        t = fig.text(0.0, 0.99, to_mathtext(runs), fontsize=FS_LEG)
        widths.append(t.get_window_extent(renderer).width / fig.dpi)
        t.remove()
    pad, gap_in = 0.175, 0.45
    total = sum(pad + w for w in widths) + gap_in * (len(entries) - 1)
    x0 = cx - total / 2.0
    for (runs, col), w in zip(entries, widths):
        swatch(x0, cy, col)
        mtext(x0 + pad, cy, runs, FS_LEG)
        x0 += pad + w + gap_in


def main():
    df = pd.read_csv(os.path.join(DATADIR, "fig2_coordinates.csv"))
    rho, red = build(df)
    os.makedirs(FIGDIR, exist_ok=True)

    stem = os.path.join(FIGDIR, "Figure2_revision")
    fig.savefig(stem + ".pdf", dpi=600, facecolor="white")
    fig.savefig(stem + ".png", dpi=600, facecolor="white")
    fig.savefig(stem + "_raw.svg", dpi=600, facecolor="white")

    with open(os.path.join(OUT, "work", "fig2_math_registry.json"), "w",
              encoding="utf-8") as fh:
        json.dump(dict(W=W, H=H, labels=MATH), fh, indent=1, ensure_ascii=False)

    print("canvas %.2f x %.2f in (%.1f x %.1f mm)"
          % (W, H, W * 25.4, H * 25.4))
    print("panel side %.3f in (%.1f mm)" % (P, P * 25.4))
    print("mathtext labels:", len(MATH))


if __name__ == "__main__":
    main()
