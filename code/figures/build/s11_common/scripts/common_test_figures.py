# -*- coding: utf-8 -*-
"""Figure S9 (fig03) re-exported as two standalone sub-figures.

Derived from the original script
    20261021_expanded_ratio_comparison_v2/scripts/05_figures.py  (fig03)
and its frozen result table out/metrics/paired_differences.csv.

Plotted quantity, exactly as in the original:
    Δ = expanded-trained − original-trained  (diff_new_minus_old_rmse)
    one dot per seed (5 per group), no jitter
    black horizontal bar = arithmetic MEAN of the five seeds (not the median)

Presentation changes only:
  * one figure per panel (a: common original-range test, b: common expanded-range test);
  * dot colour #CA7241 (size 3 pt, alpha 0.6 unchanged);
  * full four-sided frame (dark grey, 0.5 pt), ticks left/bottom only;
  * titles, the Δ axis title, the six category names and the bottom note removed;
  * tick numbers kept and emitted as outlines (svg.fonttype = path).
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = r"E:\project\work1\20261021_expanded_ratio_comparison_v2"
CSV = os.path.join(ROOT, "out", "metrics", "paired_differences.csv")
OUT = r"E:\project\work1\20261117_figs9_common\out"
os.makedirs(OUT, exist_ok=True)

COORDS = ["a_mu", "r_mu", "a_tau", "r_tau", "a_D", "r_D"]
COL = "diff_new_minus_old_rmse"
DOT = "#CA7241"
FRAME = "#404040"
GRID = "#D9D9D9"
FS_TICK = 8.0
HALF_BAR = 0.22                      # summary line spans i +- 0.22 (original)

PLOT_W, PLOT_H = 210.54, 158.79      # pt, same as the companion figure
L, R, T, B = 31.0, 3.0, 3.0, 8.0     # pt margins (negative tick labels on the left)

plt.rcParams.update({
    "font.family": "Arial",
    "font.size": FS_TICK,
    "axes.linewidth": 0.5,
    "xtick.labelsize": FS_TICK,
    "ytick.labelsize": FS_TICK,
    "svg.fonttype": "path",
    "pdf.fonttype": 42,
})


def load():
    P = pd.read_csv(CSV)
    out = {}
    for arm in ("original", "expanded"):
        g = P[P["test_arm"] == arm]
        vals = [g[g["quantity"] == c][COL].astype(float).to_numpy() for c in COORDS]
        out[arm] = vals
    return out


def panel(data, arm, stem):
    vals = data[arm]
    x = np.arange(len(COORDS))
    fig_w = (PLOT_W + L + R) / 72.0
    fig_h = (PLOT_H + T + B) / 72.0
    fig = plt.figure(figsize=(fig_w, fig_h))
    ax = fig.add_axes([L / (PLOT_W + L + R), B / (PLOT_H + T + B),
                       PLOT_W / (PLOT_W + L + R), PLOT_H / (PLOT_H + T + B)])

    for i, v in enumerate(vals):
        ax.plot(np.full(len(v), x[i]), v, "o", ms=3, color=DOT, alpha=0.6,
                mew=0, zorder=3)
        ax.plot([x[i] - HALF_BAR, x[i] + HALF_BAR], [np.mean(v)] * 2,
                color="black", lw=1.8, zorder=4, solid_capstyle="butt")
    ax.axhline(0, color="black", lw=0.6, zorder=2)

    ax.set_xticks(x)
    ax.set_xticklabels([])               # names removed, tick marks kept
    ax.tick_params(axis="both", which="both", direction="out", length=3.5,
                   width=0.5, color=FRAME, labelcolor="#1a1a1a",
                   top=False, right=False)
    for s in ax.spines.values():
        s.set_visible(True)
        s.set_color(FRAME)
        s.set_linewidth(0.5)
    ax.grid(axis="y", ls=":", lw=0.5, color=GRID, alpha=0.9, zorder=0)
    ax.set_axisbelow(True)

    fig.patch.set_facecolor("white")
    for ext in ("svg", "png"):
        fig.savefig(os.path.join(OUT, "%s.%s" % (stem, ext)),
                    dpi=600, facecolor="white")
    ylim = ax.get_ylim()
    plt.close(fig)
    return ylim


def main():
    data = load()
    for arm, stem in (("original", "common_test_a"), ("expanded", "common_test_b")):
        ylim = panel(data, arm, stem)
        print("%-9s ylim %.3f .. %.3f" % (stem, ylim[0], ylim[1]),
              "means", np.round([np.mean(v) for v in data[arm]], 4))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
