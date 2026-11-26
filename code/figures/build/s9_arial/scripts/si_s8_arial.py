# -*- coding: utf-8 -*-
"""Figure S8 - the four right-hand panels re-rendered with Arial tick numbers.

The current Figure S8 in the SI deck is a 2 x 3 set of distribution panels.
The two left panels already use Arial; the other four carry the original
DejaVu Sans tick glyphs (the source FigureS8.svg had its text outlined from
DejaVu).  This script re-draws ONLY those four panels - S8_02 (log10 g_tau),
S8_03 (log10 g_D), S8_05 (q_tau), S8_06 (q_D) - from the same frozen data and
the same plotting code, with Arial tick numbers at the same 8 pt.

Geometry is locked to the approved 2026-11-16 panels:
    canvas      241.160 x 192.440 pt   (= 2010 x 1604 px @600 dpi)
    plot area   206.130 x 173.608 pt
    margins     L 32.10  R 2.93  T 3.06  B 15.772  pt
    axes box    x 32.10..238.23, y 3.06..176.668  (local canvas coordinates)

Nothing else changes: same bins, same densities, same 1.6 pt step curves,
same #0072B2 / #D55E00 colours, same grey 0.2-5 band and 0-21 / 0-0.24 limits
for the ratio panels, same #000000 0.8 pt frame, same tick geometry.
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
ROOT = os.path.join(BASE, "20261119_si_s8_arial")
OUT = os.path.join(ROOT, "out")
WORK = os.path.join(ROOT, "work")
os.makedirs(OUT, exist_ok=True)
os.makedirs(WORK, exist_ok=True)

PARAMS = ["mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk",
          "Nc_eff_pvk", "Nv_eff_pvk", "tau_ETL", "tau_HTL", "rad_c"]
NEW_CSV = os.path.join(BASE, "20261021",
                       "JV_database_9D_interface_lifetimes-newratio.csv")
OLD_CSV = os.path.join(BASE, "data",
                       "JV_database_9D_interface_lifetimes-2.csv")
C_BLUE, C_ORANGE, C_GREY = "#0072B2", "#D55E00", "#999999"

W_PT, H_PT, FS = 206.130, 173.608, 8.0
L, R, T, B = 32.10, 2.93, 3.06, 15.772        # approved canvas 241.16 x 192.44


def require_arial():
    path = font_manager.findfont(font_manager.FontProperties(family="Arial"))
    print("Arial resolves to:", path)
    if "arial" not in os.path.basename(path).lower():
        raise SystemExit("FATAL: Arial not available (%s)" % path)


def load_s8():
    new = pd.read_csv(NEW_CSV)
    old = pd.read_csv(OLD_CSV)
    Pn = new[PARAMS].to_numpy(float)
    Po = old[PARAMS].to_numpy(float)

    def rec(P):
        g = {"g_mu": np.sqrt(P[:, 0] * P[:, 1]),
             "g_tau": np.sqrt(P[:, 2] * P[:, 3]),
             "g_D": np.sqrt(P[:, 4] * P[:, 5])}
        q = {"q_mu": P[:, 0] / P[:, 1], "q_tau": P[:, 2] / P[:, 3],
             "q_D": P[:, 4] / P[:, 5]}
        return {**g, **q}

    print("S8 rows: expanded %d, original %d" % (len(Pn), len(Po)))
    return rec(Pn), rec(Po)


def draw(ax, kind):
    if kind in ("g_mu", "g_tau", "g_D"):
        lo = np.log10(min(Ro[kind].min(), Rn[kind].min()))
        hi = np.log10(max(Ro[kind].max(), Rn[kind].max()))
        bins = np.linspace(lo, hi, 60)
        ax.hist(np.log10(Ro[kind]), bins=bins, density=True, histtype="step",
                lw=1.6, color=C_BLUE)
        ax.hist(np.log10(Rn[kind]), bins=bins, density=True, histtype="step",
                lw=1.6, color=C_ORANGE)
    else:
        bins = np.linspace(0.0, 21.0, 85)
        ax.hist(Ro[kind], bins=bins, density=True, histtype="step", lw=1.6,
                color=C_BLUE)
        ax.hist(Rn[kind], bins=bins, density=True, histtype="step", lw=1.6,
                color=C_ORANGE)
        ax.axvspan(0.2, 5.0, color=C_GREY, alpha=0.12, lw=0)
        ax.set_xlim(0, 21)
        ax.set_ylim(0, 0.24)


def style(ax):
    ax.tick_params(axis="both", which="both", direction="out", length=3.5,
                   width=0.8, color="#000000", labelcolor="#1a1a1a",
                   top=False, right=False, labelsize=FS)
    for s in ax.spines.values():
        s.set_visible(True)
        s.set_color("#000000")
        s.set_linewidth(0.8)


def render(kind, stem):
    fig = plt.figure(figsize=((W_PT + L + R) / 72.0, (H_PT + T + B) / 72.0))
    ax = fig.add_axes([L / (W_PT + L + R), B / (H_PT + T + B),
                       W_PT / (W_PT + L + R), H_PT / (H_PT + T + B)])
    draw(ax, kind)
    style(ax)
    fig.patch.set_facecolor("white")
    lims = (ax.get_xlim(), ax.get_ylim(), len(ax.patches))
    svg = os.path.join(OUT, stem + ".svg")
    fig.savefig(svg, dpi=600, facecolor="white")
    plt.close(fig)
    # PNG from the SVG through the same Edge pipeline as the approved panels,
    # so the pixel grid is 2010 x 1604 exactly (matplotlib's own savefig
    # truncates the half pixel and would give 2009 x 1603)
    png = os.path.join(OUT, stem + ".png")
    r = subprocess.run([sys.executable,
                        os.path.join(ROOT, "scripts", "render_svg_px.py"),
                        svg, png, "--dpi", "600"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if r.returncode != 0:
        raise RuntimeError("SVG rasterisation failed for " + svg)
    return lims


def main():
    global Ro, Rn
    require_arial()
    plt.rcParams.update({
        "font.family": "Arial",
        "font.size": FS,
        "axes.linewidth": 0.5,
        "svg.fonttype": "path",
        "pdf.fonttype": 42,
        "axes.unicode_minus": True,
    })
    Rn, Ro = load_s8()
    plan = [("S8_02", "g_tau"), ("S8_03", "g_D"),
            ("S8_05", "q_tau"), ("S8_06", "q_D")]
    for stem, kind in plan:
        lims = render(kind, stem + "_Arial")
        print("%-10s <- log10 %-6s xlim %s ylim %s patches %d"
              % (stem, kind, np.round(lims[0], 3), np.round(lims[1], 3), lims[2]))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
