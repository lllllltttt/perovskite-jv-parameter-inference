# -*- coding: utf-8 -*-
"""Original / expanded model-performance comparison, two standalone panels.

Data (unchanged): 20261021_expanded_ratio_comparison_v2/out/metrics/
table_B_common_tests.csv, rows with test_arm == model_arm ("own test").

Statistics (unchanged, same code as the original fig02):
    bar height / summary point = arithmetic mean over the five training
                                 seeds of that arm and coordinate
    error bar                  = sample standard deviation over the seeds
                                 (ddof = 1)
    small dots                 = the five individual seed values

Panel (a)  grouped bars + SD error bars + small dots   (as before)
Panel (b)  grouped summary points + SD error bars + small dots (no bars)

Presentation only:
  * colours #3A5C94 (original) / #CA7241 (expanded);
  * four-sided frame #404040 0.5 pt, outward ticks left/bottom, no grid;
  * no titles, axis titles, x tick labels or legend;
  * both panels share plot area 210.54 x 158.79 pt and margin box;
  * Arial tick numbers emitted as outlines (svg.fonttype = path).
"""
import os

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = r"E:\project\work1\20261021_expanded_ratio_comparison_v2"
CSV = os.path.join(ROOT, "out", "metrics", "table_B_common_tests.csv")
OUT = r"E:\project\work1\20261119_model_perf\out"
os.makedirs(OUT, exist_ok=True)

COORDS = ["a_mu", "r_mu", "a_tau", "r_tau", "a_D", "r_D"]
C_OLD, C_NEW = "#3A5C94", "#CA7241"
FRAME = "#404040"
W_BAR = 0.36
FS_TICK = 8.0

PLOT_W, PLOT_H = 210.54, 158.79              # pt, identical for both panels
L, R, T, B = 25.0, 3.0, 3.0, 8.0             # pt margins

Y_LIM = {"skill_mse": (0.0, 0.82498), "rmse": (0.0, 1.13538)}
Y_TICKS = {"skill_mse": np.arange(0, 0.81, 0.1),
           "rmse": np.arange(0, 1.01, 0.2)}

# point-plot geometry (panel b)
OFFSET = W_BAR              # group centres at x +/- W_BAR/2, as in panel (a)
MS_SUMMARY = 5.2            # summary point diameter, pt
MS_DOT = 2.4                # per-run dot diameter, pt (as in panel a)
DOT_ALPHA = 0.55            # as in panel a
CAP = 3.4                   # cap width, pt: wider than the summary marker so
                            # the (very short) error bars stay visible

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


def new_figure(metric):
    fig_w = (PLOT_W + L + R) / 72.0
    fig_h = (PLOT_H + T + B) / 72.0
    fig = plt.figure(figsize=(fig_w, fig_h))
    ax = fig.add_axes([L / (PLOT_W + L + R), B / (PLOT_H + T + B),
                       PLOT_W / (PLOT_W + L + R), PLOT_H / (PLOT_H + T + B)])
    ax.set_xlim(-0.62, len(COORDS) - 1 + 0.62)
    ax.set_ylim(*Y_LIM[metric])
    ax.set_yticks(Y_TICKS[metric])
    ax.set_xticks(np.arange(len(COORDS)))
    ax.set_xticklabels([])                     # ticks kept, names removed
    ax.tick_params(axis="both", which="both", direction="out", length=3.5,
                   width=0.5, color=FRAME, labelcolor="#1a1a1a", top=False,
                   right=False)
    for s in ax.spines.values():
        s.set_visible(True)
        s.set_color(FRAME)
        s.set_linewidth(0.5)
    ax.grid(False)
    fig.patch.set_facecolor("white")
    return fig, ax


def save(fig, stem):
    for ext in ("svg", "png"):
        fig.savefig(os.path.join(OUT, "%s.%s" % (stem, ext)),
                    dpi=600, facecolor="white")
    plt.close(fig)


def panel_a(data):
    """Grouped bars + SD error bars + per-run dots (unchanged)."""
    means_o, sd_o, pts_o = data["skill_mse"]["original"]
    means_e, sd_e, pts_e = data["skill_mse"]["expanded"]
    x = np.arange(len(COORDS))
    fig, ax = new_figure("skill_mse")

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
    for ln in ax.lines:
        ln.set_markerfacecolor("black")
        ln.set_markeredgecolor("black")

    for k, pts in enumerate((pts_o, pts_e)):
        for i, p in enumerate(pts):
            ax.plot(np.full(len(p), x[i] + (k - 0.5) * W_BAR), p, "o",
                    ms=MS_DOT, color="black", alpha=DOT_ALPHA, mew=0, zorder=3)
    save(fig, "performance_a_skill")


def panel_b(data):
    """Grouped summary points + SD error bars + per-run dots; no bars."""
    means_o, sd_o, pts_o = data["rmse"]["original"]
    means_e, sd_e, pts_e = data["rmse"]["expanded"]
    x = np.arange(len(COORDS))
    fig, ax = new_figure("rmse")

    for k, (m, s, pts, col) in enumerate((
            (means_o, sd_o, pts_o, C_OLD),
            (means_e, sd_e, pts_e, C_NEW))):
        xk = x + (k - 0.5) * OFFSET
        for i, p in enumerate(pts):                        # runs, behind
            ax.plot(np.full(len(p), xk[i]), p, "o", ms=MS_DOT,
                    color="black", alpha=DOT_ALPHA, mew=0, zorder=3)
        ax.plot(xk, m, "o", ms=MS_SUMMARY, color=col, mec=col, mew=0,
                zorder=4)                                  # summary point
        # error bar last and with wide caps: run-to-run SD is 0.001-0.034 on a
        # 1.135 axis (0.1-4.8 pt), so caps wider than the marker keep it visible
        ax.errorbar(xk, m, yerr=s, fmt="none", ecolor="black",
                    elinewidth=0.8, capsize=CAP, capthick=0.8, zorder=6)
    save(fig, "performance_b_rmse")


def main():
    data = load()
    panel_a(data)
    panel_b(data)
    for metric in ("skill_mse", "rmse"):
        for arm in ("original", "expanded"):
            m, s, p = data[metric][arm]
            print("%-9s %-8s means %s" % (metric, arm, np.round(m, 4)))
            print("%-9s %-8s sd    %s" % ("", "", np.round(s, 5)))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
