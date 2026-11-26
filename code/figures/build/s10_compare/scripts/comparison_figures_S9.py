# -*- coding: utf-8 -*-
"""Figure S9 panels re-exported as two standalone sub-figures.

Derived from the original script
    20261021_expanded_ratio_comparison_v2/scripts/05_figures.py  (fig02)
and its frozen result table out/metrics/table_B_common_tests.csv.

Only the presentation changed:
  * one figure per panel (a: Skill_MSE, b: RMSE) instead of one wide figure;
  * bar colours fixed to #3A5C94 / #CA7241 with alpha = 1;
  * a full four-sided frame (dark grey, 0.5 pt) with outward ticks on the
    left and bottom only, and no gridlines inside the plot;
  * every title / axis title / tick label on x / legend removed;
  * tick numbers kept and emitted as outlines (svg.fonttype = path).

Data and statistics are untouched:
    bar height      = mean of the five seeds of that arm x coordinate
    error bar       = sample standard deviation over the seeds (ddof = 1)
    small dots      = every individual seed value (5 per bar)
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = r"E:\project\work1\20261021_expanded_ratio_comparison_v2"
CSV = os.path.join(ROOT, "out", "metrics", "table_B_common_tests.csv")
OUT = r"E:\project\work1\20261117_figs9_compare\out"
os.makedirs(OUT, exist_ok=True)

COORDS = ["a_mu", "r_mu", "a_tau", "r_tau", "a_D", "r_D"]
C_OLD, C_NEW = "#3A5C94", "#CA7241"          # blue / orange, opaque
FRAME = "#404040"                            # dark grey frame + ticks
GRID = "#D9D9D9"
W_BAR = 0.36
FS_TICK = 8.0

# geometry: identical plot area and margins for both panels
PLOT_W, PLOT_H = 210.54, 158.79              # pt, as in the original figure
L, R, T, B = 25.0, 3.0, 3.0, 8.0             # pt margins (ticks + y numbers)

Y_LIM = {"skill_mse": (0.0, 0.82498), "rmse": (0.0, 1.13538)}
Y_TICKS = {"skill_mse": np.arange(0, 0.81, 0.1),
           "rmse": np.arange(0, 1.01, 0.2)}

plt.rcParams.update({
    "font.family": "Arial",
    "font.size": FS_TICK,
    "axes.linewidth": 0.5,
    "xtick.labelsize": FS_TICK,
    "ytick.labelsize": FS_TICK,
    "svg.fonttype": "path",        # tick numbers become outlines
    "pdf.fonttype": 42,
})


def load():
    df = pd.read_csv(CSV)
    A = df[df["test_arm"] == df["model_arm"]]
    out = {}
    for metric in ("skill_mse", "rmse"):
        out[metric] = {}
        for arm in ("original", "expanded"):
            g = A[A["model_arm"] == arm]
            means, sds, pts = [], [], []
            for c in COORDS:
                v = g[g["quantity"] == c][metric].astype(float).to_numpy()
                means.append(np.nanmean(v))
                sds.append(np.nanstd(v, ddof=1))
                pts.append(v)
            out[metric][arm] = (np.array(means), np.array(sds), pts)
    return out


def panel(data, metric, stem):
    means_o, sd_o, pts_o = data[metric]["original"]
    means_e, sd_e, pts_e = data[metric]["expanded"]
    x = np.arange(len(COORDS))

    fig_w = (PLOT_W + L + R) / 72.0
    fig_h = (PLOT_H + T + B) / 72.0
    fig = plt.figure(figsize=(fig_w, fig_h))
    ax = fig.add_axes([L / (PLOT_W + L + R), B / (PLOT_H + T + B),
                       PLOT_W / (PLOT_W + L + R), PLOT_H / (PLOT_H + T + B)])

    ax.bar(x - W_BAR / 2, means_o, W_BAR, color=C_OLD, alpha=1.0,
           yerr=sd_o, capsize=2, error_kw={"lw": 0.8, "ecolor": "black",
                     "markeredgecolor": "black",
                     "markerfacecolor": "black"},
           zorder=2)
    ax.bar(x + W_BAR / 2, means_e, W_BAR, color=C_NEW, alpha=1.0,
           yerr=sd_e, capsize=2, error_kw={"lw": 0.8, "ecolor": "black",
                     "markeredgecolor": "black",
                     "markerfacecolor": "black"},
           zorder=2)
    # error-bar caps: force black face as well (matplotlib leaves the cap
    # marker face on its default C0 blue, which would show up when zoomed)
    for ln in ax.lines:
        ln.set_markerfacecolor("black")
        ln.set_markeredgecolor("black")

    for k, pts in enumerate((pts_o, pts_e)):
        for i, p in enumerate(pts):
            ax.plot(np.full(len(p), x[i] + (k - 0.5) * W_BAR), p, "o",
                    ms=2.4, color="black", alpha=0.55, mew=0, zorder=3)

    ax.set_xlim(-0.62, len(COORDS) - 1 + 0.62)
    ax.set_ylim(*Y_LIM[metric])
    ax.set_yticks(Y_TICKS[metric])
    ax.set_xticks(x)
    ax.set_xticklabels([])                     # names removed, ticks kept
    ax.tick_params(axis="both", which="both", direction="out", length=3.5,
                   width=0.5, color=FRAME, labelcolor="#1a1a1a", top=False,
                   right=False)
    for s in ax.spines.values():
        s.set_visible(True)
        s.set_color(FRAME)
        s.set_linewidth(0.5)
    ax.grid(False)                     # no gridlines inside the plot

    fig.patch.set_facecolor("white")
    for ext in ("svg", "png"):
        fig.savefig(os.path.join(OUT, "%s.%s" % (stem, ext)),
                    dpi=600, facecolor="white")
    plt.close(fig)
    return dict(mean_o=means_o, sd_o=sd_o, mean_e=means_e, sd_e=sd_e,
                pts_o=pts_o, pts_e=pts_e)


def main():
    data = load()
    a = panel(data, "skill_mse", "comparison_a")
    b = panel(data, "rmse", "comparison_b")
    for k, v in (("a", a), ("b", b)):
        print("panel", k, "means O", np.round(v["mean_o"], 4),
              "E", np.round(v["mean_e"], 4))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
