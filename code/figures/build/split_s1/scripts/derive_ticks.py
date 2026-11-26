# -*- coding: utf-8 -*-
"""Derive the per-panel x/y tick values straight from the original Figure S1
script (final_figures/scripts/plot_FigS1_eda.py) and its data, then check the
derived positions against the tick marks that survive in the PowerPoint SVG.

Nothing is guessed from the screenshot: the nine histogram axes are rebuilt
headlessly with the identical code path (same figure size, gridspec, 60 bins,
nice_ticks, autoscale margins) and every limit / tick / label is read back off
the live matplotlib axes -- including the ones the original hid
(labelbottom=False for rows 0-1, left=False for columns 1-2).
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.ticker import FuncFormatter
from lxml import etree

BASE = r"E:\project\work1"
CSV = os.path.join(BASE, "data", "JV_database_9D_interface_lifetimes-2.csv")
SRC = "work/slide1_image2.svg"
OUTJSON = "work/ticks_derived.json"

CS = "{http://www.w3.org/2000/svg}"

PARAM_NAMES = [
    "mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk",
    "Nc_eff_pvk", "Nv_eff_pvk", "tau_ETL", "tau_HTL", "rad_c",
]
SHORT = ["mu_n", "mu_p", "tau_n", "tau_p", "N_c", "N_v",
         "tau_ETL", "tau_HTL", "r_rad"]
N_EXPECTED = 102046
N_BINS = 60
FIG_W, FIG_H = 13.0, 7.4

HIST_W, HIST_H = 125.569, 115.162
HIST_X = [44.2399, 209.992, 375.743]
HIST_Y = [35.4384, 198.969, 362.5]


def nice_ticks(lo, hi, max_n=5):
    """Byte-for-byte copy of plot_FigS1_eda.nice_ticks."""
    lo, hi = float(lo), float(hi)
    if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
        return np.array([lo, hi])
    span = hi - lo
    raw_step = span / max(1, max_n - 1)
    base = 10.0 ** np.floor(np.log10(raw_step))
    for m in (1, 2, 5, 10):
        s = m * base
        if span / s <= (max_n - 1):
            start = np.ceil(lo / s) * s
            return np.arange(start, hi + s * 0.5, s)
    return np.array([lo, hi])


def _count_fmt(v, _pos=None):
    return f"{int(round(v)):,}"


def build_axes():
    """Re-run the original panel-(a) construction; return the nine axes."""
    df = pd.read_csv(CSV, usecols=PARAM_NAMES)
    assert len(df) == N_EXPECTED, len(df)
    logX = np.log10(df[PARAM_NAMES].to_numpy(dtype=float))

    fig = plt.figure(figsize=(FIG_W, FIG_H))
    gs = fig.add_gridspec(1, 2, width_ratios=[0.54, 0.46],
                          left=0.045, right=0.99, top=0.905, bottom=0.075,
                          wspace=0.09)
    gsa = gridspec.GridSpecFromSubplotSpec(3, 3, subplot_spec=gs[0],
                                           wspace=0.32, hspace=0.42)
    axes, counts_max, edges_all, counts_all = [], [], [], []
    for k in range(9):
        row, col = divmod(k, 3)
        ax = fig.add_subplot(gsa[row, col])
        ax.tick_params(axis="both", which="major", direction="out",
                       length=3.0, width=0.8, labelsize=7.5,
                       colors="#1a1a1a", top=False, right=False)
        for spine in ax.spines.values():
            spine.set_color("#1a1a1a")
            spine.set_linewidth(0.8)
        counts, edges = np.histogram(logX[:, k], bins=N_BINS)
        ax.hist(logX[:, k], bins=edges, color="#6C92C3", edgecolor="#3D5E8D",
                lw=0.5, zorder=2)
        counts_max.append(float(counts.max()))
        counts_all.append([int(c) for c in counts])
        edges_all.append((float(edges[0]), float(edges[-1])))
        if col == 0:
            ax.set_ylabel("Count", fontsize=8.5)
            ax.set_yticks(nice_ticks(0.0, counts.max(), max_n=6))
            ax.yaxis.set_major_formatter(FuncFormatter(_count_fmt))
        else:
            ax.set_yticklabels([])
            ax.tick_params(labelleft=False, left=False)
        if row == 2:
            ax.set_xlabel("x", fontsize=8.5)
            ax.set_xticks(nice_ticks(edges[0], edges[-1]))
        else:
            ax.tick_params(labelbottom=False)
        axes.append(ax)
    fig.canvas.draw()
    global COUNTS
    COUNTS = counts_all
    return fig, axes, counts_max, edges_all, logX


def svg_ticks():
    """(x tick marks, y tick marks, y labels) per axes_1..axes_9, in pt."""
    root = etree.parse(SRC).getroot()
    out = []
    for i in range(1, 10):
        a = root.find(".//%sg[@id='axes_%d']" % (CS, i))
        xs, ys, ylab = [], [], []
        for axis in a:
            aid = axis.get("id") or ""
            if not aid.startswith("matplotlib.axis_"):
                continue
            for g in axis:
                gid = g.get("id") or ""
                if not (gid.startswith("xtick_") or gid.startswith("ytick_")):
                    continue
                u = g.find(".//%suse" % CS)
                t = g.find(".//%stext" % CS)
                if gid.startswith("xtick_"):
                    if u is not None:
                        xs.append(float(u.get("x")))
                else:
                    if u is not None:
                        ys.append(float(u.get("y")))
                    if t is not None and t.text is not None:
                        ylab.append((float(u.get("y")) if u is not None else None,
                                     t.text))
        xs.sort(); ys.sort()
        out.append(dict(x=xs, y=ys, ylab=ylab))
    return out


def main():
    fig, axes, counts_max, edges_all, logX = build_axes()
    svg = svg_ticks()

    rec = []
    print("=" * 78)
    print("derived from the original script + data, checked against the SVG")
    print("=" * 78)
    for k, ax in enumerate(axes):
        row, col = divmod(k, 3)
        x0, x1 = ax.get_xlim()
        y0, y1 = ax.get_ylim()
        xt = [float(v) for v in ax.get_xticks() if x0 - 1e-9 <= v <= x1 + 1e-9]
        xtl = ax.xaxis.get_major_formatter().format_ticks(xt)
        # what the original left visible
        x_hidden = (row != 2)
        # for columns 1-2 the y labels were never drawn: use the col-0 rule
        if col == 0:
            # left column: the original drew these; set_yticks also pulled the
            # view up to the top tick, so every tick sits inside the frame
            yt = [float(v) for v in ax.get_yticks()]
        else:
            # columns 1-2 never had y numbers.  Same rule the original used on
            # the left column, but the view here is the plain 1.05 x max margin
            # autoscale, so a tick that would fall outside the panel's own
            # y range is dropped rather than moving the axis range.
            yt = [float(v) for v in nice_ticks(0.0, counts_max[k], max_n=6)
                  if v <= y1 + 1e-9]
        ytl = [_count_fmt(v) for v in yt]

        # --- check x tick marks present in the SVG -------------------------
        exp_x = [HIST_X[col] + (t - x0) / (x1 - x0) * HIST_W for t in xt]
        got_x = svg[k]["x"]
        dx = max((abs(a - b) for a, b in zip(exp_x, got_x)), default=float("nan"))
        n_x_ok = len(exp_x) == len(got_x)

        # some panels carry more x ticks than the visible ones (all are marks)
        rec.append(dict(k=k, name=SHORT[k], row=row, col=col,
                        xlim=[x0, x1], ylim=[y0, y1],
                        xticks=xt, xlabels=list(xtl),
                        yticks=yt, ylabels=ytl,
                        counts_max=counts_max[k],
                        counts=COUNTS[k],
                        edges=list(edges_all[k]),
                        x_tick_count_svg=len(got_x),
                        x_tick_count_derived=len(exp_x),
                        x_tick_max_dev_pt=dx,
                        x_count_ok=n_x_ok,
                        y_labels_in_svg=[t for _, t in svg[k]["ylab"]],
                        y_tick_count_svg=len(svg[k]["y"]),
                        y_tick_max_dev_pt=(max((abs(a - b) for a, b in zip(
                            sorted(svg[k]["y"]),
                            sorted(HIST_Y[row] + HIST_H -
                                   (v - y0) / (y1 - y0) * HIST_H for v in yt))),
                            default=float("nan"))
                                           if svg[k]["y"] else None)))

    for r in rec:
        print("\n%-8s (row %d col %d)  xlim [%.4f, %.4f]  ylim [%.2f, %.2f]"
              % (r["name"], r["row"], r["col"], *r["xlim"], *r["ylim"]))
        print("   x ticks %-2d %s" % (len(r["xticks"]),
                                      "  ".join("%-7s" % v for v in r["xlabels"])))
        print("   SVG x marks %d, derived %d, max dev %.4f pt  %s"
              % (r["x_tick_count_svg"], r["x_tick_count_derived"],
                 r["x_tick_max_dev_pt"], "OK" if r["x_count_ok"] and
                 r["x_tick_max_dev_pt"] < 0.02 else "MISMATCH"))
        print("   y ticks %s   (max count %.0f)" % (r["ylabels"], r["counts_max"]))
        if r["y_tick_count_svg"]:
            print("   SVG y marks %d (labels %s)  max dev %.4f pt"
                  % (r["y_tick_count_svg"], r["y_labels_in_svg"],
                     r["y_tick_max_dev_pt"]))

    json.dump(rec, open(OUTJSON, "w", encoding="utf-8"), ensure_ascii=False,
              indent=1)
    print("\nwrote", OUTJSON)


if __name__ == "__main__":
    main()
