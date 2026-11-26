# -*- coding: utf-8 -*-
"""Figure S10 (common-test Delta-RMSE) - two standalone panels with the mean
value printed next to each black summary bar.

Everything except the twelve numbers is the approved 2026-11-17 delivery
(20261117_figs9_common/out/common_test_a.svg / _b.svg):

    Delta = expanded-trained - original-trained   (diff_new_minus_old_rmse)
    orange dots            = one per seed, 5 per group, no jitter
    black horizontal bar   = arithmetic MEAN of the five seeds (np.mean)
    zero line, dotted horizontal grid, four-sided frame, limits, ticks,
    colours and plot area are unchanged.

Added:
    one black Arial Regular 8 pt label per bar, 3 decimals, standard minus
    U+2212, placed in screen points (1.8 pt to the right of the bar end,
    lifted above the bar), automatically nudged so that it never touches the
    bar, a dot, a grid line, the zero line, the frame or another label.
    The right-most group has no room on its right, so its label goes on the
    left of the bar (as requested).
"""
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath, TextToPath

ROOT = r"E:\project\work1\20261021_expanded_ratio_comparison_v2"
CSV = os.path.join(ROOT, "out", "metrics", "paired_differences.csv")
OUT = r"E:\project\work1\20261119_si_s10_labels\out"
WORK = r"E:\project\work1\20261119_si_s10_labels\work"
os.makedirs(OUT, exist_ok=True)
os.makedirs(WORK, exist_ok=True)

COORDS = ["a_mu", "r_mu", "a_tau", "r_tau", "a_D", "r_D"]
COL = "diff_new_minus_old_rmse"
DOT = "#CA7241"
FRAME = "#404040"
GRID = "#D9D9D9"
FS_TICK = 8.0
HALF_BAR = 0.22

PLOT_W, PLOT_H = 210.54, 158.79
L, R, T, B = 31.0, 3.0, 3.0, 8.0

DX = 1.8          # text gap to the bar end, pt
DY0 = 2.2         # preferred lift of the baseline above the bar, pt
MIN_DY = 0.9      # baseline stays above the bar centre
MARGIN = 0.8      # clearance to the axes frame, pt
EXCL = 0.8        # clearance to dots / bars / other labels, pt
GRID_CLEAR = 0.5  # clearance to the light dotted grid, pt (4.2 px at 600 dpi)
DOT_R = 1.5       # dot radius, pt (ms = 3)
BAR_HALF_T = 0.9  # half thickness of the 1.8 pt summary bar

plt.rcParams.update({
    "font.family": "Arial",
    "font.size": FS_TICK,
    "axes.linewidth": 0.5,
    "xtick.labelsize": FS_TICK,
    "ytick.labelsize": FS_TICK,
    "svg.fonttype": "path",
    "pdf.fonttype": 42,
})

PROP = FontProperties(family="Arial", size=FS_TICK)
TTP = TextToPath()


def label_text(v):
    s = "%.3f" % abs(v)
    return ("\u2212" if v < 0 else "") + s


def ink_size(s):
    tp = TextPath((0, 0), s, size=FS_TICK, prop=PROP)
    bb = tp.get_extents()
    w_adv = TTP.get_text_width_height_descent(s, PROP, False)[0]
    return bb.x0, bb.y0, bb.x1, bb.y1, w_adv


def load():
    P = pd.read_csv(CSV)
    out = {}
    for arm in ("original", "expanded"):
        g = P[P["test_arm"] == arm]
        out[arm] = [g[g["quantity"] == c][COL].astype(float).to_numpy()
                    for c in COORDS]
    return out


def build(ax, vals):
    x = np.arange(len(COORDS))
    for i, v in enumerate(vals):
        ax.plot(np.full(len(v), x[i]), v, "o", ms=3, color=DOT, alpha=0.6,
                mew=0, zorder=3)
        ax.plot([x[i] - HALF_BAR, x[i] + HALF_BAR], [np.mean(v)] * 2,
                color="black", lw=1.8, zorder=4, solid_capstyle="butt")
    ax.axhline(0, color="black", lw=0.6, zorder=2)
    ax.set_xticks(x)
    ax.set_xticklabels([])
    ax.tick_params(axis="both", which="both", direction="out", length=3.5,
                   width=0.5, color=FRAME, labelcolor="#1a1a1a",
                   top=False, right=False)
    for s in ax.spines.values():
        s.set_visible(True)
        s.set_color(FRAME)
        s.set_linewidth(0.5)
    ax.grid(axis="y", ls=":", lw=0.5, color=GRID, alpha=0.9, zorder=0)
    ax.set_axisbelow(True)
    return x


def to_pt(fig, ax):
    """figure -> points helpers"""
    k = fig.dpi / 72.0
    bb = ax.get_window_extent(fig.canvas.get_renderer())
    return k, (bb.x0 / k, bb.y0 / k, bb.x1 / k, bb.y1 / k)


def place(fig, ax, vals):
    fig.canvas.draw()
    x = np.arange(len(COORDS))
    k, (AX0, AY0, AX1, AY1) = to_pt(fig, ax)
    y0lim, y1lim = ax.get_ylim()
    grid = [(ax.transData.transform((0, t))[1]) / k
            for t in ax.get_yticks() if y0lim - 1e-9 <= t <= y1lim + 1e-9]
    bars = []
    dots = []
    for i, v in enumerate(vals):
        m = float(np.mean(v))
        yb = ax.transData.transform((0, m))[1] / k
        xa = ax.transData.transform((x[i] - HALF_BAR, 0))[0] / k
        xb = ax.transData.transform((x[i] + HALF_BAR, 0))[0] / k
        bars.append((xa, yb - BAR_HALF_T, xb, yb + BAR_HALF_T))
        for vv in v:
            px, py = ax.transData.transform((x[i], vv))
            dots.append((px / k, py / k))
    xzero = ax.transData.transform((0, 0))[1] / k
    zero = (AX0, xzero - 0.3, AX1, xzero + 0.3)

    placed = []
    out = []
    for i, v in enumerate(vals):
        m = float(np.mean(v))
        txt = label_text(m)
        x0i, y0i, x1i, y1i, adv = ink_size(txt)
        right = i < len(COORDS) - 1
        if right:
            anchor = ax.transData.transform((x[i] + HALF_BAR, m))[0] / k
            origin = anchor + DX
            ha = "left"
        else:
            anchor = ax.transData.transform((x[i] - HALF_BAR, m))[0] / k
            origin = anchor - DX - adv
            ha = "right"
        by = ax.transData.transform((0, m))[1] / k

        def box(dy):
            return (origin + x0i, by + dy + y0i, origin + x1i, by + dy + y1i)

        def ok(dy, allow=()):
            b = box(dy)
            if b[0] < AX0 + MARGIN or b[2] > AX1 - MARGIN:
                return False
            if b[1] < AY0 + MARGIN or b[3] > AY1 - MARGIN:
                return False
            for g in grid:
                g0, g1 = g - 0.25, g + 0.25        # 0.5 pt line width
                if b[1] < g1 + GRID_CLEAR and b[3] > g0 - GRID_CLEAR:
                    return False
            for (rx0, ry0, rx1, ry1) in bars + [zero]:
                if b[0] < rx1 + EXCL and b[2] > rx0 - EXCL and \
                        b[1] < ry1 + EXCL and b[3] > ry0 - EXCL:
                    return False
            for (cx, cy) in dots:
                if b[0] - DOT_R < cx < b[2] + DOT_R and \
                        b[1] - DOT_R < cy < b[3] + DOT_R:
                    return False
            for pb in placed:
                if b[0] < pb[2] + 0.5 and b[2] > pb[0] - 0.5 and \
                        b[1] < pb[3] + 0.5 and b[3] > pb[1] - 0.5:
                    return False
            return True

        cands = [round(DY0 + 0.2 * j, 2) for j in range(0, 50)] + \
                [round(DY0 - 0.2 * j, 2) for j in range(1, 40)]
        cands = [d for d in cands if d >= MIN_DY]
        cands.sort(key=lambda d: (abs(d - DY0), -d))
        chosen = next((d for d in cands if ok(d)), None)
        if chosen is None:
            raise RuntimeError("no free spot for group %d (%s)" % (i, txt))

        ax.annotate(txt, xy=(x[i] + (HALF_BAR if right else -HALF_BAR), m),
                    xytext=(DX if right else -DX, chosen),
                    textcoords="offset points", ha=ha, va="baseline",
                    color="#1a1a1a", fontsize=FS_TICK,
                    fontproperties=PROP, zorder=6, annotation_clip=False)
        placed.append(box(chosen))
        out.append(dict(group=COORDS[i], value=m, text=txt, side="right" if right else "left",
                        dy=chosen, box=box(chosen)))
    return out


def panel(data, arm, stem):
    vals = data[arm]
    fig_w = (PLOT_W + L + R) / 72.0
    fig_h = (PLOT_H + T + B) / 72.0
    fig = plt.figure(figsize=(fig_w, fig_h))
    ax = fig.add_axes([L / (PLOT_W + L + R), B / (PLOT_H + T + B),
                       PLOT_W / (PLOT_W + L + R), PLOT_H / (PLOT_H + T + B)])
    build(ax, vals)
    info = place(fig, ax, vals)
    fig.patch.set_facecolor("white")
    for ext in ("svg", "png"):
        fig.savefig(os.path.join(OUT, "%s.%s" % (stem, ext)),
                    dpi=600, facecolor="white")
    ylim = ax.get_ylim()
    plt.close(fig)
    return ylim, info


def main():
    data = load()
    report = {}
    for arm, stem in (("original", "common_test_a"), ("expanded", "common_test_b")):
        ylim, info = panel(data, arm, stem)
        print("%-14s ylim %.5f .. %.5f" % (stem, *ylim))
        for d in info:
            b = d["box"]
            print("   %-6s %-8s dy %4.2f  box x %.2f..%.2f  y %.2f..%.2f"
                  % (d["group"], d["text"], d["dy"], b[0], b[2], b[1], b[3]))
        report[stem] = info
    import json
    json.dump(report, open(os.path.join(WORK, "labels.json"), "w"), indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
