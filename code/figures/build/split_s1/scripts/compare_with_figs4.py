# -*- coding: utf-8 -*-
"""Side-by-side check of the new 4.8 pt tick numbers against SI Figure S4.

Both panels are shown at the SAME plot-area width, which is the basis the
instruction asks for.  The measured quantity is the ink height of a tick
number divided by the plot-area width.
"""
import io
import subprocess
import sys

import numpy as np
from PIL import Image

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REF = r"E:\project\work1\20261024_final_figures_svg\si\FigureS4.svg"
OURS = "out_ticks_small/png/S1a_02_mu_p_600dpi.png"
PY = sys.executable

DPI = 600
PPD = DPI / 72.0                 # px per pt
REF_PLOT = (48.238125, 61.44, 259.23, 214.29)   # x0, ytop, x1, ybottom (pt)
REF_W = REF_PLOT[2] - REF_PLOT[0]
OUR_PLOT_W = 125.569
SCALE = OUR_PLOT_W / REF_W


def render(svg, png, dpi):
    subprocess.run([PY, "scripts/render_svg_px.py", svg, png, "--dpi", str(dpi)],
                   check=True, stdout=subprocess.DEVNULL)
    return png


def ink_rows(img, x0, x1, y0, y1):
    a = np.asarray(img.convert("L")).astype(int)
    sub = (255 - a[y0:y1, x0:x1]) > 40
    rows = np.where(sub.any(axis=1))[0]
    return 0 if not len(rows) else rows[-1] - rows[0] + 1


def main():
    refpng = render(REF, "work/_figs4_600.png", DPI)
    ref = Image.open(refpng).convert("RGB")
    ours = Image.open(OURS).convert("RGB")

    # --- ink height of one y tick number, in px at 600 dpi ---------------
    # reference: the "1000" label, baseline y = 79.478, x 20.9..41.2
    h_ref = ink_rows(ref, int(20.0 * PPD), int(42.0 * PPD),
                     int(72.0 * PPD), int(82.0 * PPD))
    # ours: the "500" label of mu_p (no comma -> no descender, same as "1000")
    x_plot, y_plot = 19.66, 4.30        # plot offset inside our canvas
    y_tick = y_plot + (150.601 - 500 / 2345.70 * 115.162 - 35.4384)
    h_our = ink_rows(ours, int(2.0 * PPD), int((x_plot - 5.2) * PPD),
                     int((y_tick - 4.5) * PPD), int((y_tick + 3.0) * PPD))

    r_ref = h_ref / PPD / REF_W
    r_our = h_our / PPD / OUR_PLOT_W
    print("reference  FigureS4 : ink %5.1f px = %4.2f pt on a %6.2f pt plot"
          " -> %.2f %% of plot width" % (h_ref, h_ref / PPD, REF_W, 100 * r_ref))
    print("previous   12 pt    : ink %5.1f px = %4.2f pt on a %6.2f pt plot"
          " -> %.2f %% (this round before)" % (8.88 * PPD, 8.88, OUR_PLOT_W,
                                               100 * 8.88 / OUR_PLOT_W))
    print("this round 4.8 pt   : ink %5.1f px = %4.2f pt on a %6.2f pt plot"
          " -> %.2f %% of plot width" % (h_our, h_our / PPD, OUR_PLOT_W,
                                         100 * r_our))
    print("ratio new/reference : %.3f" % (r_our / r_ref))

    # --- side by side at the same plot width -----------------------------
    crop = ref.crop((int(14 * PPD), int(46 * PPD),
                     int(262 * PPD), int(236 * PPD)))
    crop = crop.resize((int(crop.width * SCALE), int(crop.height * SCALE)),
                       Image.LANCZOS)
    pad = 40
    W = crop.width + ours.width + 3 * pad
    H = max(crop.height, ours.height) + 2 * pad
    canvas = Image.new("RGB", (W, H), "white")
    canvas.paste(ours, (pad, pad))
    canvas.paste(crop, (2 * pad + ours.width, pad))
    canvas.save("work/_cmp_ref_small.png")
    print("\nwrote work/_cmp_ref_small.png  %dx%d px (left: this round, "
          "right: FigureS4 at the same plot width)" % canvas.size)


if __name__ == "__main__":
    main()
