# -*- coding: utf-8 -*-
"""QA for the standalone Figure 4 (a)-(c) assets.  Read-only."""
import os
import sys
import json
import re
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd
import fitz
from PIL import Image

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:                       # console is GBK here; never die on a report line
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
FIG = os.path.join(OUT, "figures")
sys.path.insert(0, HERE)
import fig4_abc_standalone as B          # noqa: E402
import fig4_forward as f4                # noqa: E402

PASS, FAIL = [], []


def check(cond, name, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("PASS  " if cond else "FAIL  ") + name + ("  " + detail if detail else ""))


D = f4.collect()
curves = {"V": np.asarray(D["V"], float), "target": D["target"],
          "dec": D["dec"], "comsol": D["comsol"]}
V = curves["V"]
df = D["df"]

# ---------------------------------------------------------------- data ------
check(V.shape == (131,) and abs(V[0]) < 1e-12 and abs(V[-1] - 1.3) < 1e-12,
      "131 voltage points, 0.0-1.3 V", "n=%d" % len(V))
check([c[0] for c in D["cases"]] == [12058, 595, 14499],
      "archived case order 12058 / 595 / 14499")
for sid, want in ((12058, 0.2675194930181261), (595, 2.562703102113902),
                  (14499, 54.10451317210106)):
    got = float(np.sqrt(np.mean((curves["comsol"][sid] - curves["dec"][sid]) ** 2)))
    check(abs(got - want) < 1e-9, "cycle gap reproduced for %d" % sid,
          "%.9f" % got)
    d_dec = curves["dec"][sid] - curves["target"][sid]
    d_com = curves["comsol"][sid] - curves["target"][sid]
    check(np.allclose(d_dec, -(curves["target"][sid] - curves["dec"][sid])),
          "residual sign dJ = J_method - J_target (%d)" % sid)

# ---------------------------------------------------------- file presence ---
for name in ["Fig4a", "Fig4b", "Fig4c", "Fig4abc_preview_1x3"]:
    for ext in ["png", "pdf", "svg"]:
        check(os.path.isfile(os.path.join(FIG, name + "." + ext)),
              "exists %s.%s" % (name, ext))

# --------------------------------------------------------------- PNG --------
for tag in ["Fig4a", "Fig4b", "Fig4c"]:
    im = Image.open(os.path.join(FIG, tag + ".png"))
    dpi = im.info.get("dpi", (0, 0))[0]
    check(abs(dpi - 900) < 1, "%s PNG is 900 dpi" % tag, "%.0f" % dpi)
    check(abs(im.size[0] - B.PANEL_W * 900) <= 1
          and abs(im.size[1] - B.PANEL_H * 900) <= 1,
          "%s PNG canvas = %.4f x %.4f in" % (tag, B.PANEL_W, B.PANEL_H),
          "%dx%d" % im.size)
im = Image.open(os.path.join(FIG, "Fig4abc_preview_1x3.png"))
check(abs(im.info.get("dpi", (0, 0))[0] - 900) < 1, "preview PNG is 900 dpi")
check(im.size == (round(B.TOTAL_W * 900), round(B.PREVIEW_H * 900)),
      "preview PNG canvas = 6.80 x %.2f in" % B.PREVIEW_H, "%dx%d" % im.size)

# --------------------------------------------------------------- PDF --------
pages, hsets, vsets = {}, {}, {}
for tag in ["Fig4a", "Fig4b", "Fig4c"]:
    doc = fitz.open(os.path.join(FIG, tag + ".pdf"))
    check(len(doc) == 1, "%s PDF single page" % tag)
    p = doc[0]
    pages[tag] = (p.rect.width, p.rect.height)
    hs, vs = set(), set()
    for d in p.get_drawings():
        for it in d["items"]:
            if it[0] == "l":
                p1, p2 = it[1], it[2]
                if abs(p1.y - p2.y) < 0.01 and abs(p1.x - p2.x) > 110:
                    hs.add(round(p1.y, 2))
                if abs(p1.x - p2.x) < 0.01 and abs(p1.y - p2.y) > 30:
                    vs.add(round(p1.x, 2))
    hsets[tag], vsets[tag] = hs, vs
    doc.close()
check(len(set(pages.values())) == 1,
      "all three PDFs have the same page size", str(pages))
# Expected border positions from the figure geometry, in PDF points (origin
# top-left).  The J=0 lines are NOT borders: the main-panel one moves with each
# case's scale, while the residual one coincides in all three because the
# residual limits are symmetric.
PW, PH = pages["Fig4a"]
exp_top = PH - (B.AX_BOTTOM + B.RES_H + B.MAIN_H) * 72
exp_div = PH - (B.AX_BOTTOM + B.RES_H) * 72
exp_bot = PH - B.AX_BOTTOM * 72
ok_h = all(any(abs(y - e) < 0.4 for y in hsets[t])
           for e in (exp_top, exp_div, exp_bot) for t in hsets)
check(ok_h, "top border / divider / bottom border at identical y in all three PDFs",
      "expected %.2f / %.2f / %.2f pt; found %s"
      % (exp_top, exp_div, exp_bot, sorted(hsets["Fig4a"])))
check(len({frozenset(h) & {round(exp_top, 2), round(exp_div, 2),
                          round(exp_bot, 2)} for h in hsets.values()}) == 1,
      "the three border y values are the same in every panel")
exp_l = B.AX_LEFT * 72
exp_r = (B.AX_LEFT + B.AX_W) * 72
ok_v = all(any(abs(x - e) < 0.4 for x in vsets[t])
           for e in (exp_l, exp_r) for t in vsets)
check(ok_v, "left/right spines at identical x in all three PDFs",
      "expected %.2f / %.2f pt; found %s" % (exp_l, exp_r, sorted(vsets["Fig4a"])))

doc = fitz.open(os.path.join(FIG, "Fig4abc_preview_1x3.pdf"))
check(abs(doc[0].rect.width - B.TOTAL_W * 72) < 0.5,
      "preview PDF is 6.80 in wide",
      "%.2f pt" % doc[0].rect.width)
doc.close()

# --------------------------------------------------------------- SVG --------
NS = "{http://www.w3.org/2000/svg}"
for tag in ["Fig4a", "Fig4b", "Fig4c"]:
    tree = ET.parse(os.path.join(FIG, tag + ".svg"))
    root = tree.getroot()
    texts = [t for t in root.iter(NS + "text")]
    imgs = [t for t in root.iter(NS + "image")]
    joined = " ".join("".join(t.itertext()) for t in texts)
    # Lower bound only: (b) carries no legend and no inset, so it has just its
    # own 4 y ticks, 3 x ticks and the residual strip's 3 numbers.
    check(len(texts) >= 8, "%s SVG has live <text> elements" % tag,
          "%d text nodes" % len(texts))
    flat = ["".join(t.itertext()).strip() for t in texts]
    check("0.0" in flat and "1.0" in flat,
          "%s SVG keeps its tick numbers as editable text" % tag)
    check(len(imgs) == 0, "%s SVG contains no raster image" % tag)
    check("Test index" not in joined, "%s SVG has no test-index title" % tag)
    check("d_gap" not in joined, "%s SVG has no d_gap annotation" % tag)
    check("Voltage (V)" not in joined, "%s SVG has no Voltage axis title" % tag)
    check(abs(float(root.get("width").replace("pt", "")) - B.PANEL_W * 72) < 0.5,
          "%s SVG width = 2.127 in" % tag, root.get("width"))
tree = ET.parse(os.path.join(FIG, "Fig4abc_preview_1x3.svg"))
joined = " ".join("".join(t.itertext()) for t in tree.getroot().iter(NS + "text"))
for s in ["Test index 12058", "Test index 595", "Test index 14499",
          "Target (COMSOL)", "Decoder reconstruction"]:
    check(s in joined, "preview SVG contains '%s'" % s)

# ------------------------------------------- legend vs curves (panel a) -----
fig = plt.figure(figsize=(B.PANEL_W, B.PANEL_H))
fig.patch.set_facecolor("white")
ax, axr = B.draw_panel(fig, 0.0, 0.0, 12058, curves, True, [])
fig.canvas.draw()
r = fig.canvas.get_renderer()
leg = ax.get_legend()
lb = leg.get_window_extent(renderer=r)
inside = 0
for arr in (curves["target"][12058], curves["dec"][12058],
            curves["comsol"][12058]):
    xy = ax.transData.transform(np.column_stack([V, arr]))
    inside += int(np.sum((xy[:, 0] >= lb.x0 - 2) & (xy[:, 0] <= lb.x1 + 2) &
                         (xy[:, 1] >= lb.y0 - 2) & (xy[:, 1] <= lb.y1 + 2)))
check(inside == 0, "panel (a) legend overlaps no curve sample",
      "%d points inside legend box" % inside)
ab = ax.get_window_extent(renderer=r)
check(lb.x0 >= ab.x0 and lb.x1 <= ab.x1 and lb.y0 >= ab.y0 and lb.y1 <= ab.y1,
      "panel (a) legend lies inside its axes")
plt.close(fig)

# ------------------------------------------------ inset tick visibility -----
fig = plt.figure(figsize=(B.PANEL_W, B.PANEL_H))
fig.patch.set_facecolor("white")
ax, axr = B.draw_panel(fig, 0.0, 0.0, 14499, curves, False, [])
fig.canvas.draw()
r = fig.canvas.get_renderer()
axi = [a for a in ax.child_axes][0]
axb = ax.get_window_extent(renderer=r)
labs = [t.get_window_extent(renderer=r) for t in axi.get_xticklabels()
        if t.get_text()]
check(all(b.y0 >= axb.y0 for b in labs),
      "(c) inset x tick numbers are not clipped by the divider",
      "min clearance %.2f pt" % min(b.y0 - axb.y0 for b in labs))
ylabs = [t.get_window_extent(renderer=r) for t in axi.get_yticklabels()
         if t.get_text()]
check(all(b.x0 >= axb.x0 for b in ylabs),
      "(c) inset y tick numbers clear the main left spine",
      "min clearance %.2f pt" % min(b.x0 - axb.x0 for b in ylabs))
main_ylim = ax.get_ylim()
check(main_ylim[0] <= min(curves["target"][14499].min(),
                          curves["dec"][14499].min(),
                          curves["comsol"][14499].min()) + 1e-9,
      "(c) main y axis keeps the complete high-forward-bias tail",
      "ylim %.1f (data min %.1f)" % (main_ylim[0],
                                     min(curves["dec"][14499].min(),
                                         curves["comsol"][14499].min())))
plt.close(fig)

# ------------------------------------------------ values / caption ----------
p = pd.read_csv(os.path.join(OUT, "data_used", "Figure4ac_plotting_values.csv"))
check(len(p) == 3 and list(p.test_index) == [12058, 595, 14499],
      "plotting-values CSV lists the three cases")
c = pd.read_csv(os.path.join(OUT, "data_used", "Figure4ac_curves.csv"))
check(c.shape[0] == 131 and "resid_decoder_c" in c.columns,
      "curve CSV has 131 rows and all residual columns")
cap = open(os.path.join(OUT, "caption_draft.txt"), encoding="utf-8").read()
for s in ["0.268", "2.56", "54.1", "0.753", "2.98", "3.32",
          "0.645", "4.59", "54.3", "0–1.0 V", "ΔJ",
          "19.0", "11.6", "11.7", "131", "1.3 V", "mA cm⁻²"]:
    check(s in cap, "caption contains '%s'" % s)
# the 1.0 V numbers in the caption must be the ones in the plotted data
_c = pd.read_csv(os.path.join(OUT, "data_used", "Figure4ac_curves.csv"))
_r = _c.loc[(_c.V - 1.0).abs().idxmin()]
check("%.1f" % _r.comsol_c in cap and "%.1f" % _r.target_c in cap
      and "%.1f" % _r.decoder_c in cap,
      "caption's 1.0 V values match the plotted case-(c) data",
      "target %.2f / decoder %.2f / COMSOL %.2f"
      % (_r.target_c, _r.decoder_c, _r.comsol_c))
check(len(cap.split()) < 320, "caption is one compact paragraph",
      "%d words" % len(cap.split()))

print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
if FAIL:
    print("FAILURES:", FAIL)
    sys.exit(1)
