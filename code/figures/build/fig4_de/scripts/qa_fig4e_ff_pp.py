# -*- coding: utf-8 -*-
"""QA for Fig4e_FF_pp: the |dFF| panel re-expressed in percentage points.

Read-only.  Checks the numbers, and that the new panel is a drop-in
replacement for Fig4e_FF - same canvas, same axes rectangle, same jitter x,
same relative heights, same fonts.
"""
import os
import sys
import xml.etree.ElementTree as ET

import numpy as np
import fitz
from PIL import Image

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
FIG = os.path.join(OUT, "figures")
sys.path.insert(0, HERE)
import fig4de_standalone as G          # noqa: E402
import fig4e_ff_pp as P                # noqa: E402

PASS, FAIL = [], []


def check(cond, name, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("PASS  " if cond else "FAIL  ") + name + ("  " + detail if detail else ""))


dev = np.abs(np.asarray(G.D["dev"]["FF"], float))
dev = dev[np.isfinite(dev)]
pp = dev * 100.0

# ---------------------------------------------------------------- data ------
check(pp.size == 44, "n = 44 valid samples", "%d" % pp.size)
check(abs(float(np.median(pp)) - 1.5533056) < 5e-7,
      "median = 1.5533 pp (un-rounded data, x100 exactly once)",
      "%.9f pp" % float(np.median(pp)))
check(abs(float(np.median(pp)) - 100 * float(np.median(dev))) < 1e-12,
      "median is exactly 100x the dimensionless median",
      "%.9f -> %.9f" % (float(np.median(dev)), float(np.median(pp))))
check(np.allclose(pp, dev * 100.0, rtol=0, atol=0),
      "every sample is the original value times 100, nothing else")
check(abs(float(pp.max()) - 6.4926312) < 5e-6, "top sample = 6.4926 pp",
      "%.6f" % float(pp.max()))

# ------------------------------------------------------------- file set -----
for ext in ("png", "pdf", "svg"):
    check(os.path.isfile(os.path.join(FIG, "Fig4e_FF_pp." + ext)),
          "exists Fig4e_FF_pp.%s" % ext)
for ext in ("png", "pdf", "svg"):
    check(os.path.isfile(os.path.join(FIG, "Fig4e_FF." + ext)),
          "old Fig4e_FF.%s is still there" % ext)

im = Image.open(os.path.join(FIG, "Fig4e_FF_pp.png"))
check(abs(im.info.get("dpi", (0, 0))[0] - 600) < 1,
      "PNG is 600 dpi", "%.0f" % im.info.get("dpi", (0, 0))[0])
check(abs(im.size[0] - G.E_W * 600) <= 1 and abs(im.size[1] - G.E_H * 600) <= 1,
      "PNG canvas = %.3f x %.3f in" % (G.E_W, G.E_H), "%dx%d" % im.size)

doc = fitz.open(os.path.join(FIG, "Fig4e_FF_pp.pdf"))
check(len(doc) == 1, "PDF is a single page")
check(abs(doc[0].rect.width - G.E_W * 72) < 0.5
      and abs(doc[0].rect.height - G.E_H * 72) < 0.5,
      "PDF page = %.3f x %.3f in" % (G.E_W, G.E_H),
      "%.1f x %.1f pt" % (doc[0].rect.width, doc[0].rect.height))
fonts = doc[0].get_fonts()
check(any(f[3].endswith("ArialMT") for f in fonts), "Arial is embedded",
      str([f[3] for f in fonts]))
doc.close()

# ----------------------------------------------------------------- SVG ------
NS = "{http://www.w3.org/2000/svg}"
root = ET.parse(os.path.join(FIG, "Fig4e_FF_pp.svg")).getroot()
texts = ["".join(t.itertext()).strip() for t in root.iter(NS + "text")]
check(texts == ["0", "2", "4", "6", "8"],
      "SVG carries the five tick numbers and nothing else", str(texts))
check(len(list(root.iter(NS + "image"))) == 0, "SVG contains no raster image")
check(abs(float(root.get("width").replace("pt", "")) - G.E_W * 72) < 0.5,
      "SVG width = %.3f in" % G.E_W, root.get("width"))

# ------------------------------------------------ axes and geometry --------
fig_new = G.new_fig(G.E_W, G.E_H)
ax_new = P.draw_ff_pp(fig_new)
fig_new.canvas.draw()
r_new = fig_new.canvas.get_renderer()

fig_old = G.new_fig(G.E_W, G.E_H)
ax_old = G.draw_e(fig_old, 0.0, 0.0, "FF")
fig_old.canvas.draw()
r_old = fig_old.canvas.get_renderer()

check(np.allclose(ax_new.get_position().bounds, ax_old.get_position().bounds,
                  rtol=0, atol=1e-12),
      "axes rectangle identical to Fig4e_FF",
      str(tuple(round(v, 6) for v in ax_new.get_position().bounds)))
check(np.allclose(ax_new.get_window_extent(renderer=r_new).bounds,
                  ax_old.get_window_extent(renderer=r_old).bounds,
                  rtol=0, atol=1e-6),
      "frame occupies the same pixels as Fig4e_FF")

check(ax_new.get_yscale() == "linear", "y axis is linear")
locs = list(ax_new.get_yticks())
check(np.allclose(locs, [0, 2, 4, 6, 8]),
      "major ticks are 0, 2, 4, 6, 8", str([round(v, 3) for v in locs]))
check([t.get_text() for t in ax_new.get_yticklabels()]
      == ["0", "2", "4", "6", "8"],
      "tick labels are the plain numbers, not renamed 0.00-0.08")
check(ax_new.get_ylim()[0] == 0.0, "axis starts at zero")
check(abs(ax_new.get_ylim()[1] - 100 * ax_old.get_ylim()[1]) < 1e-9,
      "axis top is exactly 100x the old one",
      "%.4f vs %.4f" % (ax_new.get_ylim()[1], 100 * ax_old.get_ylim()[1]))
check(ax_new.get_ylim()[1] > pp.max(), "the top sample keeps headroom",
      "top %.2f pp vs max %.2f pp" % (ax_new.get_ylim()[1], pp.max()))
check(len(ax_new.get_xticks()) == 0, "no x tick numbers")

# ------------------------------------- same marks, same relative places ----
def points(ax):
    return [ln for ln in ax.lines if ln.get_marker() == "o"][0]


po, pn = points(ax_old), points(ax_new)
check(len(pn.get_xdata()) == 44, "44 points drawn", "%d" % len(pn.get_xdata()))
check(np.allclose(pn.get_xdata(), po.get_xdata(), rtol=0, atol=0),
      "horizontal jitter positions identical to Fig4e_FF")
check(np.allclose(pn.get_ydata(), 100 * po.get_ydata(), rtol=0, atol=1e-9),
      "every point sits at 100x its old value, none added or dropped")
check(abs(pn.get_markersize() - po.get_markersize()) < 1e-12
      and abs(pn.get_alpha() - po.get_alpha()) < 1e-12,
      "marker size and transparency unchanged",
      "ms %.1f, alpha %.2f" % (pn.get_markersize(), pn.get_alpha()))

# relative height inside the axes must be unchanged
fy_new = pn.get_ydata() / ax_new.get_ylim()[1]
fy_old = po.get_ydata() / ax_old.get_ylim()[1]
check(np.allclose(fy_new, fy_old, rtol=0, atol=1e-12),
      "points keep the same height fraction inside the frame",
      "max deviation %.2e" % np.max(np.abs(fy_new - fy_old)))

old_box = ax_old.patches[0].get_path().vertices
new_box = ax_new.patches[0].get_path().vertices
check(np.allclose(new_box[:, 1], 100 * old_box[:, 1], rtol=0, atol=1e-9),
      "box outline is the old one scaled by 100 (same quartiles)")
old_lines = [ln for ln in ax_old.lines if ln.get_marker() != "o"]
new_lines = [ln for ln in ax_new.lines if ln.get_marker() != "o"]
check(len(old_lines) == len(new_lines) == 5,
      "five boxplot lines (2 whiskers, 2 caps, 1 median)",
      "%d / %d" % (len(old_lines), len(new_lines)))
ok = all(np.allclose(ln_new.get_ydata(), 100 * ln_old.get_ydata(),
                     rtol=0, atol=1e-9)
         for ln_old, ln_new in zip(old_lines, new_lines))
check(ok, "whisker ends, caps and median all scale by 100")

# no duplicate symbols, nothing clipped, no text outside
check(not [ln for ln in ax_new.lines
           if ln.get_marker() not in ("", "None", None)
           and ln.get_markersize() > G.MS + 0.01],
      "no flier markers from the boxplot")
xy = ax_new.transData.transform(np.column_stack([pn.get_xdata(), pn.get_ydata()]))
bb = ax_new.get_window_extent(renderer=r_new)
outside = int(np.sum((xy[:, 0] < bb.x0 - 0.01) | (xy[:, 0] > bb.x1 + 0.01)
                     | (xy[:, 1] < bb.y0 - 0.01) | (xy[:, 1] > bb.y1 + 0.01)))
check(outside == 0, "every sample inside the axes", "%d outside" % outside)
check(not G.canvas_text_out(fig_new), "no text outside the canvas")
ts = [t.get_fontsize() for t in ax_new.get_yticklabels() if t.get_text()]
check(all(abs(s - G.FS_TICK) < 1e-9 for s in ts),
      "tick numbers stay at %.1f pt" % G.FS_TICK, str(ts))
plt.close(fig_old)
plt.close(fig_new)

print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
if FAIL:
    print("FAILURES:", FAIL)
    sys.exit(1)
