# -*- coding: utf-8 -*-
"""Figure S5 - nine sigma-versus-error scatter panels, re-rendered with Arial
tick numbers.

Same frozen data, same drawing code as the approved panels:
    x = predictive scale sigma_theta = clip(softplus(raw) + 0.01, 0.01, 1.0)
    y = |params_test - param_mu|   (normalised log10 error)
    scatter: s = 4, alpha = 0.35, colour #0072B2, no edges, xlim 0-0.5,
    y autoscaled with 5 % margins, four-sided #000000 0.8 pt frame,
    outward 3.5 pt / 0.8 pt ticks, 10 pt tick numbers.

Only the font changes: DejaVu Sans -> Arial Regular (same 10 pt, same anchors).
Geometry is locked to the approved 2026-11-16 panels so the canvas and the
plot area are byte-for-byte unchanged:
    canvas    216.200 x 174.920 pt  (= 1802 x 1458 px @600 dpi)
    plot      181.5976 x 154.6364 pt
    margins   L 24.820  R 9.7824  T 2.980  B 17.3036 pt
"""
import os
import subprocess
import sys

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

BASE = r"E:\project\work1"
ROOT = os.path.join(BASE, "20261119_si_s5_arial")
OUT = os.path.join(ROOT, "out")
WORK = os.path.join(ROOT, "work")
os.makedirs(OUT, exist_ok=True)

NPZ = os.path.join(BASE, "data", "dataset_normalized.npz")
MODEL_DIR = os.path.join(BASE, "data", "vae-v6", "vae-v6")
SIG_CSV = os.path.join(BASE, "evaluation_fixed", "sigma_statistics_fixed.csv")
MET_CSV = os.path.join(BASE, "evaluation_fixed", "parameter_metrics.csv")

PARAMS = ["mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk",
          "Nc_eff_pvk", "Nv_eff_pvk", "tau_ETL", "tau_HTL", "rad_c"]
C_BLUE = "#0072B2"
W_PT, H_PT, FS = 181.5976, 154.6364, 10.0
L, R, T, B = 24.820, 9.7824, 2.980, 17.3036


def require_arial():
    path = font_manager.findfont(font_manager.FontProperties(family="Arial"))
    print("Arial resolves to:", path)
    if "arial" not in os.path.basename(path).lower():
        raise SystemExit("FATAL: Arial not available (%s)" % path)


def load_sigma_error():
    cache = os.path.join(WORK, "sigma_error.npz")
    d = np.load(cache)
    sigma, error = d["sigma"], d["error"]
    print("cached sigma/error:", sigma.shape)
    fs = pd.read_csv(SIG_CSV)
    for i, p in enumerate(PARAMS):
        s = sigma[:, i]
        row = fs.iloc[i]
        for got, key in ((np.mean(s), "mean"), (np.median(s), "median"),
                         (np.percentile(s, 25), "q25"),
                         (np.percentile(s, 75), "q75"),
                         (s.min(), "min"), (s.max(), "max")):
            assert abs(got - row[key]) < 2e-5, (p, key, got, row[key])
    fm = pd.read_csv(MET_CSV)
    for i, p in enumerate(PARAMS):
        assert abs(np.mean(error[:, i]) - fm.iloc[i]["mae"]) < 2e-4
    print("  frozen CSV cross-check: PASS")
    return sigma, error


def style(ax):
    ax.tick_params(axis="both", which="both", direction="out", length=3.5,
                   width=0.8, color="#000000", labelcolor="#1a1a1a",
                   top=False, right=False, labelsize=FS)
    for s in ax.spines.values():
        s.set_visible(True)
        s.set_color("#000000")
        s.set_linewidth(0.8)


def panel(i, stem):
    fig = plt.figure(figsize=((W_PT + L + R) / 72.0, (H_PT + T + B) / 72.0))
    ax = fig.add_axes([L / (W_PT + L + R), B / (H_PT + T + B),
                       W_PT / (W_PT + L + R), H_PT / (H_PT + T + B)])
    ax.scatter(SIGMA[:, i], ERROR[:, i], s=4, alpha=0.35, color=C_BLUE,
               linewidths=0)
    ax.set_xlim(0.0, 0.5)
    ax.margins(y=0.05)
    style(ax)
    fig.patch.set_facecolor("white")
    lims = (ax.get_xlim(), ax.get_ylim())
    svg = os.path.join(OUT, stem + ".svg")
    fig.savefig(svg, dpi=600, facecolor="white")
    plt.close(fig)
    r = subprocess.run([sys.executable,
                        os.path.join(ROOT, "scripts", "render_svg_px.py"),
                        svg, os.path.join(OUT, stem + ".png"), "--dpi", "600"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if r.returncode != 0:
        raise RuntimeError("rasterisation failed: " + svg)
    return lims


def main():
    global SIGMA, ERROR
    require_arial()
    plt.rcParams.update({
        "font.family": "Arial",
        "font.size": FS,
        "axes.linewidth": 0.5,
        "svg.fonttype": "path",
        "pdf.fonttype": 42,
        "axes.unicode_minus": True,
    })
    SIGMA, ERROR = load_sigma_error()
    for i in range(9):
        lims = panel(i, "S5_%02d_Arial" % (i + 1))
        print("S5_%02d  xlim %s ylim %s" % (i + 1, np.round(lims[0], 3),
                                            np.round(lims[1], 3)))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
