# -*- coding: utf-8 -*-
"""Read-only audit of the Figure 4(e) bottom row: |dFF| and |dPCE|.

1. traces the units from the frozen curves to the plotted values;
2. recomputes n / median / max from the unrounded per-sample deviations;
3. reads the ACTUAL ylim of each panel (not the top labelled tick);
4. inspects the exported PDF vectors and the 600 dpi PNG to prove that the
   highest marker and the upper whisker cap are complete.

Writes qa/ff_pce_audit.json and prints the numbers.  Nothing is redrawn.
"""
import os
import sys
import glob
import json
import re

import numpy as np
import pandas as pd
import fitz
from PIL import Image

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
FIG = os.path.join(OUT, "figures")
QA = os.path.join(OUT, "qa")
sys.path.insert(0, HERE)
import fig4de_standalone as G          # noqa: E402
import fig4e_ff_pp as P                # noqa: E402
import fig4_forward as f4              # noqa: E402

D = G.D
sids = sorted(int(re.search(r"Sample_(\d+)_", p).group(1))
              for p in glob.glob(os.path.join(f4.FW_PRED, "Sample_*_pred.mat")))
assert len(sids) == 45

dev = {k: np.asarray(v, float) for k, v in D["dev"].items()}
absff = np.abs(dev["FF"])
abspce = np.abs(dev["PCE"])

res = {}

# ------------------------------------------------------------ 1. units -----
# J in the .mat is A/m^2 and load_mat_J multiplies by 0.1 -> mA/cm^2.
# v2lib.device_metrics (module of the manuscript extraction convention):
#   Jsc  = |J(V=0)|                          mA cm^-2
#   Voc  = interpolated first downward zero crossing   V
#   Pmax = max(V*J) over the generation quadrant       V*mA/cm^2 = mW/cm^2
#   FF   = Pmax/(Jsc*Voc)                    dimensionless 0..1
#   PCE  = Jsc*Voc*FF*0.1?  no: Jsc[mA/cm2]*Voc[V] = mW/cm2, and at
#          100 mW/cm2 (1 sun) the percent number equals mW/cm2, so PCE is
#          stored as a percent number (range below)
#   dev[k] = metric(predicted) - metric(target)  (signed); panels plot |dev|
src = f4.FW_PER
fw = pd.read_csv(src)
res["units"] = dict(
    source_csv=src,
    J_unit="A m^-2 in the .mat, x0.1 -> mA cm^-2",
    Jsc="mA cm^-2",
    Voc="V",
    FF="dimensionless fraction, 0-1",
    PCE="percent number (mW cm^-2 at 100 mW cm^-2 illumination)",
    ff_target_range=[float(fw.FF_t.min()), float(fw.FF_t.max())],
    pce_target_range=[float(fw.PCE_t.min()), float(fw.PCE_t.max())],
    formula_plotted="|metric(pred) - metric(target)|; FF x100 once for the pp "
                    "panel; PCE used as stored (already pp)",
)

# ------------------------------------------------------- 2. statistics -----
for tag, arr, scale in (("FF", absff, 100.0), ("PCE", abspce, 1.0)):
    a = arr[np.isfinite(arr)] * scale
    i = int(np.nanargmax(arr))
    res[tag] = dict(
        n=int(a.size),
        median=float(np.median(a)),
        maximum=float(a.max()),
        max_test_index=int(sids[i]),
        max_sample_id=int(D["db_id"][sids[i]]),
        max_raw_unscaled=float(arr[i]),
        scale=scale,
    )

# ------------------------------------------------- 3. actual axis top ------
def panel_geometry(mod, key, values):
    """ylim, ticks and the clearances of the top marker and cap, in points."""
    fig = G.new_fig(G.E_W, G.E_H)
    ax = mod.draw_ff_pp(fig) if mod is P else mod.draw_e(fig, 0.0, 0.0, key)
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    top_px = ax.get_window_extent(renderer=r).y1
    dpi = fig.dpi
    vmax = float(np.max(values))
    yc = ax.transData.transform((0.0, vmax))[1]
    clear_pt = (top_px - yc) * 72.0 / dpi
    caps = []
    for ln in ax.lines:
        xd, yd = np.asarray(ln.get_xdata()), np.asarray(ln.get_ydata())
        if len(xd) == 2 and xd[0] != xd[1] and yd[0] == yd[1]:
            caps.append(float(yd[0]))
    cap = max(caps)
    cap_pt = (top_px - ax.transData.transform((0.0, cap))[1]) * 72.0 / dpi
    out = dict(ylim=[float(v) for v in ax.get_ylim()],
               ticks=[float(v) for v in ax.get_yticks()],
               top_tick=float(ax.get_yticks()[-1]),
               marker_radius_pt=G.MS / 2.0,
               marker_centre_below_top_spine_pt=float(clear_pt),
               marker_fully_visible=bool(clear_pt > G.MS / 2.0),
               cap_value=float(cap),
               cap_below_top_spine_pt=float(cap_pt),
               cap_fully_visible=bool(cap_pt > 0.35),
               samples_above_ylim=int(np.sum(np.asarray(values) >
                                             ax.get_ylim()[1])),
               samples_at_cap=int(np.sum(np.isclose(np.asarray(values), cap,
                                                    rtol=0, atol=1e-9))))
    plt.close(fig)
    return out


res["FF"].update(panel_geometry(P, "FF", absff[np.isfinite(absff)] * 100.0))
res["PCE"].update(panel_geometry(G, "PCE", abspce[np.isfinite(abspce)]))

# ------------------------------------- 4. exported PDF: vectors vs frame ---
def pdf_check(path):
    """Top spine, top whisker cap and topmost marker circle, in PDF points."""
    doc = fitz.open(path)
    pg = doc[0]
    segs, circles = [], []
    for d in pg.get_drawings():
        rect = d["rect"]
        for it in d["items"]:
            if it[0] == "l":
                p1, p2 = it[1], it[2]
                if abs(p1.y - p2.y) < 0.01:
                    segs.append((round(float(p1.y), 2), abs(p1.x - p2.x)))
        if 1.4 < rect.width < 4.5 and 1.4 < rect.height < 4.5:
            circles.append((float(rect.y0), float(rect.y1)))
    doc.close()
    frame = [y for y, w in segs if w > 40]
    caps = [y for y, w in segs if 5 < w < 35]
    top_spine = min(frame)
    top_cap = min(caps)
    top_circle = min(circles) if circles else (None, None)
    return dict(top_spine=round(top_spine, 2), bottom_spine=round(max(frame), 2),
                frame_lines=len(frame), cap_lines=len(caps),
                top_cap_y=round(top_cap, 2),
                top_cap_clearance_pt=round(top_cap - top_spine, 2),
                top_circle_top_edge=round(top_circle[0], 2),
                top_circle_clearance_pt=round(top_circle[0] - top_spine, 2),
                circles=len(circles))


res["FF_pdf"] = pdf_check(os.path.join(FIG, "Fig4e_FF_pp.pdf"))
res["PCE_pdf"] = pdf_check(os.path.join(FIG, "Fig4e_PCE.pdf"))

# --------------------------------------------- 5. exported PNG: pixels -----
def _runs(row):
    """Longest contiguous True run in a boolean row."""
    best = cur = 0
    for v in row:
        cur = cur + 1 if v else 0
        best = cur if cur > best else best
    return best


def png_check(path):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(int)
    R, Gc, B = a[..., 0], a[..., 1], a[..., 2]
    dark = (R < 90) & (Gc < 90) & (B < 90)
    blue = (B > R + 25) & (B > 120)
    # the top spine is the first row holding one very long dark run
    spine = None
    for y in range(a.shape[0]):
        if _runs(dark[y]) > 400:
            spine = y
            break
    sub = blue[spine + 3:, :]
    ys = np.where(sub.any(axis=1))[0]
    top_blue = int(ys[0] + spine + 3)
    return dict(size=list(im.size), top_spine_row=spine,
                top_blue_row=top_blue,
                gap_px=int(top_blue - spine),
                gap_pt=round((top_blue - spine) * 72.0 / 600.0, 2),
                marker_radius_px=round(G.MS / 2.0 * 600.0 / 72.0, 1),
                top_row_blue_px=int(sub[ys[0]].sum()))


res["FF_png"] = png_check(os.path.join(FIG, "Fig4e_FF_pp.png"))
res["PCE_png"] = png_check(os.path.join(FIG, "Fig4e_PCE.png"))

# --------------------------------------------------------------- output ----
os.makedirs(QA, exist_ok=True)
with open(os.path.join(QA, "ff_pce_audit.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, indent=2)

print(json.dumps(res["units"], indent=2))
for k in ("FF", "PCE"):
    print("\n%s\n%s" % (k, json.dumps(res[k], indent=2)))
for k in ("FF_pdf", "FF_png", "PCE_pdf", "PCE_png"):
    print("\n%s\n%s" % (k, json.dumps(res[k], indent=2)))
