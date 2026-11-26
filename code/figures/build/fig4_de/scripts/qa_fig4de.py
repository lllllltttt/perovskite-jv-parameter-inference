# -*- coding: utf-8 -*-
"""QA for the standalone Figure 4 (d)-(e) assets.  Read-only.

Run:  python -I scripts/qa_fig4de.py
"""
import os
import sys
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd
import fitz
from PIL import Image

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.text import Text
from matplotlib.collections import PathCollection
from matplotlib.patches import PathPatch

try:                       # console is GBK here; never die on a report line
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
FIGD = os.path.join(OUT, "figures")
PREV = os.path.join(OUT, "preview")
DATA = os.path.join(OUT, "data_used")
sys.path.insert(0, HERE)
import fig4de_standalone as G          # noqa: E402
import fig4_forward as f4              # noqa: E402

PASS, FAIL = [], []


def check(cond, name, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("PASS  " if cond else "FAIL  ") + name + ("  " + detail if detail else ""))


D = f4.collect()
rm, dev = D["rm"], D["dev"]

# ---------------------------------------------------------------- data ------
# The numbers the redraw was checked against.  They are compared here, never
# fed into the plotting code: the plot reads f4.collect() only.
for k, want in (("full", 2.692631), ("le1", 0.455349), ("gt1", 5.191600)):
    got = float(np.median(np.asarray(rm[k], float)))
    check(abs(got - want) < 5e-7, "median (d)/%s = %.3f mA cm-2" % (k, want),
          "%.9f" % got)
for k, want, n in (("Jsc", 0.111897, 45), ("Voc", 0.022439, 44),
                   ("FF", 0.015533, 44), ("PCE", 0.471401, 44)):
    a = np.abs(np.asarray(dev[k], float))
    a = a[np.isfinite(a)]
    check(a.size == n, "n (e)/%s = %d" % (k, n), "n=%d" % a.size)
    check(abs(float(np.median(a)) - want) < 5e-7,
          "median (e)/%s = %.4f" % (k, want),
          "%.9f" % float(np.median(a)))
check(all(np.asarray(rm[k], float).size == 45 for k in ("full", "le1", "gt1")),
      "n = 45 in each (d) window")

# the numbers are plotted un-logged and unscaled
check(np.nanmax(np.asarray(dev["FF"], float)) < 0.1,
      "FF plotted as a dimensionless fraction, not x100",
      "max %.4f" % np.nanmax(np.abs(np.asarray(dev["FF"], float))))
check(1.0 < np.nanmax(np.asarray(dev["PCE"], float)) < 5.0,
      "PCE deviations plotted in pp, not x100 again",
      "max %.3f pp" % np.nanmax(np.abs(np.asarray(dev["PCE"], float))))

# --------------------------------------------------- box rule = 1.5 IQR -----
from matplotlib.cbook import boxplot_stats                      # noqa: E402
for i, k in enumerate(("full", "le1", "gt1")):
    s = boxplot_stats(np.asarray(rm[k], float))[0]
    check(abs(s["whislo"] - float(G.box_stats(rm[k])["whisker_lo"])) < 1e-12
          and abs(s["whishi"] - float(G.box_stats(rm[k])["whisker_hi"])) < 1e-12
          and abs(s["q1"] - np.percentile(rm[k], 25)) < 1e-12,
          "(d)/%s box statistics are matplotlib default (Q1/Q3, 1.5 IQR)" % k,
          "whiskers %.4g / %.4g" % (s["whislo"], s["whishi"]))

# ----------------------------------------------------------- file presence --
NAMES = ["Fig4d", "Fig4e_Jsc", "Fig4e_Voc", "Fig4e_FF", "Fig4e_PCE"]
for name in NAMES:
    for ext in ("png", "pdf", "svg"):
        check(os.path.isfile(os.path.join(FIGD, name + "." + ext)),
              "exists %s.%s" % (name, ext))
for ext in ("png", "pdf"):
    check(os.path.isfile(os.path.join(PREV, "Fig4de_preview." + ext)),
          "exists preview/Fig4de_preview.%s" % ext)

# --------------------------------------------------------------- PNG --------
SIZES = {"Fig4d": (G.D_W, G.D_H)}
for name in NAMES[1:]:
    SIZES[name] = (G.E_W, G.E_H)
for name, (w, h) in SIZES.items():
    im = Image.open(os.path.join(FIGD, name + ".png"))
    dpi = im.info.get("dpi", (0, 0))[0]
    check(abs(dpi - 600) < 1, "%s PNG is 600 dpi" % name, "%.0f" % dpi)
    check(abs(im.size[0] - w * 600) <= 1 and abs(im.size[1] - h * 600) <= 1,
          "%s PNG canvas = %.3f x %.3f in" % (name, w, h), "%dx%d" % im.size)

# --------------------------------------------------------------- PDF --------
for name, (w, h) in SIZES.items():
    doc = fitz.open(os.path.join(FIGD, name + ".pdf"))
    check(len(doc) == 1, "%s PDF is a single page" % name)
    check(abs(doc[0].rect.width - w * 72) < 0.5
          and abs(doc[0].rect.height - h * 72) < 0.5,
          "%s PDF page = %.3f x %.3f in" % (name, w, h),
          "%.1f x %.1f pt" % (doc[0].rect.width, doc[0].rect.height))
    doc.close()
doc = fitz.open(os.path.join(PREV, "Fig4de_preview.pdf"))
check(abs(doc[0].rect.width - 6.80 * 72) < 0.5
      and abs(doc[0].rect.height - 2.84 * 72) < 0.5,
      "preview PDF is 6.80 x 2.84 in",
      "%.1f x %.1f pt" % (doc[0].rect.width, doc[0].rect.height))
doc.close()

# --------------------------------------------------------------- SVG --------
# The net figures must carry axis furniture only: tick numbers, no labels.
NS = "{http://www.w3.org/2000/svg}"
BANNED = ["(d)", "(e)", "RMSE", "mA cm", "Voltage", "|Δ", "Full curve",
          "0–1.0 V", "1.3 V", "median", "n = "]
for name in NAMES:
    tree = ET.parse(os.path.join(FIGD, name + ".svg"))
    root = tree.getroot()
    texts = [t for t in root.iter(NS + "text")]
    flat = ["".join(t.itertext()).strip() for t in texts]
    joined = " ".join(flat)
    check(len(texts) >= 3, "%s SVG has live <text> elements" % name,
          "%d text nodes" % len(texts))
    check(len(list(root.iter(NS + "image"))) == 0,
          "%s SVG contains no raster image" % name)
    hit = [b for b in BANNED if b in joined]
    check(not hit, "%s SVG has no baked-in label, unit or caption text" % name,
          "found %s" % hit if hit else "")
    check(abs(float(root.get("width").replace("pt", ""))
              - SIZES[name][0] * 72) < 0.5,
          "%s SVG width = %.3f in" % (name, SIZES[name][0]), root.get("width"))
    for t in texts:                                  # every glyph run is Arial
        if t.get("style") and "font" in t.get("style"):
            check("Arial" in t.get("style") or "Helvetica" in t.get("style"),
                  "%s SVG text keeps an Arial font-family" % name,
                  t.get("style")[:40])
            break

# ---------------------------------------------------- (d) log axis etc ------
fig = G.new_fig(G.D_W, G.D_H)
axd = G.draw_d(fig, 0.0, 0.0)
fig.canvas.draw()
r = fig.canvas.get_renderer()
check(axd.get_yscale() == "log", "(d) y axis is logarithmic")
locs = list(axd.get_yticks())
check(np.allclose(locs, [0.01, 0.1, 1, 10, 100]),
      "(d) major ticks are the five decades",
      str([round(v, 4) for v in locs]))
labs = [t.get_text() for t in axd.get_yticklabels()]
check(labs == ["0.01", "0.1", "1", "10", "100"],
      "(d) major ticks are labelled as plain decimals", str(labs))
check(all(t.get_text() == "" for t in axd.get_yticklabels(minor=True)),
      "(d) minor ticks carry no labels")
xg = [g for g in axd.get_xgridlines() + axd.get_ygridlines() if g.get_visible()]
check(not xg, "(d) has no grid lines")
check(axd.get_ylim()[1] > 113.3393, "(d) top of the axis keeps the >1.0 V maximum",
      "ylim top %.1f (max 113.34)" % axd.get_ylim()[1])
check(axd.get_ylim()[0] <= 0.016265, "(d) bottom of the axis keeps the smallest RMSE",
      "ylim bottom %.4f (min 0.01627)" % axd.get_ylim()[0])
xt = [t.get_text() for t in axd.get_xticklabels()]
check(len(axd.get_xticks()) == 3 and all(s == "" for s in xt),
      "(d) keeps three category tick positions and no category text",
      str(xt))

# no point clipped by the axes
clipped = 0
for i, k in enumerate(("full", "le1", "gt1")):
    v = np.sort(np.asarray(rm[k], float))
    xy = axd.transData.transform(np.column_stack([np.full(v.size, i), v]))
    bb = axd.get_window_extent(renderer=r)
    clipped += int(np.sum((xy[:, 0] < bb.x0 - 0.01) | (xy[:, 0] > bb.x1 + 0.01)
                          | (xy[:, 1] < bb.y0 - 0.01) | (xy[:, 1] > bb.y1 + 0.01)))
check(clipped == 0, "(d) every sample sits inside the axes", "%d outside" % clipped)

# box does not hide points: the scatter sits above the box patch.
# The raw points are Line2D marker artists (ax.plot), not a PathCollection.
patches = [p for p in axd.patches if isinstance(p, PathPatch)]
pts = [ln for ln in axd.lines if ln.get_marker() == "o"]
check(len(patches) == 3 and len(pts) == 3,
      "(d) one box patch and one point layer per group",
      "%d boxes / %d point layers" % (len(patches), len(pts)))
check(all(p.get_zorder() < ln.get_zorder() for p in patches for ln in pts),
      "(d) points are drawn above the boxes",
      "box z%.1f < points z%.1f" % (patches[0].get_zorder(), pts[0].get_zorder()))
check(all(p.get_facecolor()[3] < 1.0 for p in patches),
      "(d) box fill is translucent",
      "face alpha %.2f" % patches[0].get_facecolor()[3])
check(all(ln.get_alpha() < 1.0 for ln in pts), "(d) points are translucent",
      str(pts[0].get_alpha()))
check(all(abs(ln.get_markersize() - G.MS) < 1e-9 for ln in pts),
      "(d) every raw point uses the same %.1f pt marker" % G.MS,
      str(pts[0].get_markersize()))
# no duplicate outlier symbols: the boxplot must not draw fliers at all
flier_lines = [ln for ln in axd.lines if ln.get_marker() not in ("", "None", None)
               and ln.get_markersize() > G.MS + 0.01]
check(len(flier_lines) == 0, "(d) zero flier markers", "%d" % len(flier_lines))
# 3 point layers + 5 Line2D per group (two whisker stems, two caps, one median)
check(len(axd.lines) == 18, "(d) boxplot adds exactly its five lines per group",
      "%d Line2D artists" % len(axd.lines))
meds = [l for l in axd.lines if l.get_color() == "black"
        and l.get_linewidth() == 1.0]
check(len(meds) == 3, "(d) three black median lines", "%d" % len(meds))
ts = [t.get_fontsize() for t in axd.get_yticklabels() if t.get_text()]
check(all(abs(s - G.FS_TICK) < 1e-9 for s in ts),
      "(d) tick numbers are %.1f pt" % G.FS_TICK, str(ts))
fig.canvas.draw()
check(not G.canvas_text_out(axd.figure), "(d) no text outside the canvas")
plt.close(fig)

# ------------------------------------------------------ (e) panels --------
rects, bounds = {}, {}
for k in G.E_ORDER:
    fig = G.new_fig(G.E_W, G.E_H)
    ax = G.draw_e(fig, 0.0, 0.0, k)
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    a = np.abs(np.asarray(dev[k], float))
    a = a[np.isfinite(a)]
    check(ax.get_yscale() == "linear", "(e)/%s y axis is linear" % k)
    check(ax.get_ylim()[0] == 0.0, "(e)/%s y axis starts at zero" % k,
          "%.3f" % ax.get_ylim()[0])
    check(ax.get_ylim()[1] >= a.max(), "(e)/%s keeps its maximum" % k,
          "top %.4f vs max %.4f" % (ax.get_ylim()[1], a.max()))
    locs = list(ax.get_yticks())
    steps = np.diff(locs)
    check(3 <= len(locs) <= 5 and np.allclose(steps, steps[0]),
          "(e)/%s has 3-5 equidistant major ticks" % k,
          "%d ticks from %.4g to %.4g, step %.4g"
          % (len(locs), locs[0], locs[-1], steps[0]))
    check(len(ax.get_xticks()) == 0, "(e)/%s has no x tick numbers" % k)
    xy = ax.transData.transform(np.column_stack([np.zeros(a.size), a]))
    bb = ax.get_window_extent(renderer=r)
    outside = int(np.sum((xy[:, 1] < bb.y0 - 0.01) | (xy[:, 1] > bb.y1 + 0.01)))
    check(outside == 0, "(e)/%s every sample sits inside the axes" % k,
          "%d outside" % outside)
    xg = [g for g in ax.get_xgridlines() + ax.get_ygridlines() if g.get_visible()]
    check(not xg, "(e)/%s has no grid lines" % k)
    pts = [ln for ln in ax.lines if ln.get_marker() == "o"]
    check(len(pts) == 1 and abs(pts[0].get_markersize() - G.MS) < 1e-9,
          "(e)/%s one point layer at %.1f pt" % (k, G.MS))
    check(not [ln for ln in ax.lines if ln.get_marker() not in ("", "None", None)
               and ln.get_markersize() > G.MS + 0.01],
          "(e)/%s no flier markers" % k)
    check(not G.canvas_text_out(fig), "(e)/%s no text outside the canvas" % k)
    rects[k] = tuple(round(v, 6) for v in ax.get_position().bounds)
    bounds[k] = ax.get_window_extent(renderer=r).bounds
    plt.close(fig)

check(len(set(rects.values())) == 1,
      "the four (e) axes rectangles are identical",
      str(list(rects.values())[0]))
check(len({tuple(round(v, 3) for v in b) for b in bounds.values()}) == 1,
      "the four (e) frames occupy identical pixels",
      str(list(bounds.values())[0]))

# --------------------------------------------------------- preview -------
prev = Image.open(os.path.join(PREV, "Fig4de_preview.png"))
check(abs(prev.info.get("dpi", (0, 0))[0] - 600) < 1, "preview PNG is 600 dpi")
check(abs(prev.size[0] - 6.80 * 600) <= 1 and abs(prev.size[1] - 2.84 * 600) <= 1,
      "preview PNG is 6.80 x 2.84 in", "%dx%d" % prev.size)

# ------------------------------------------------------------ tables ------
p = pd.read_csv(os.path.join(DATA, "Figure4d_per_sample.csv"))
check(len(p) == 135 and p.window.value_counts().eq(45).all(),
      "(d) per-sample CSV has 45 rows per window", str(len(p)))
q = pd.read_csv(os.path.join(DATA, "Figure4e_per_sample.csv"))
check(q.metric.value_counts()["Jsc"] == 45
      and (q.metric.value_counts().drop("Jsc") == 44).all(),
      "(e) per-sample CSV has 45 / 44 / 44 / 44 rows", str(len(q)))
check((q.abs_dev >= 0).all(), "(e) CSV holds absolute deviations")
b = pd.read_csv(os.path.join(DATA, "Figure4de_box_stats.csv"))
check(len(b) == 7 and set(b.panel) == {"d", "e"},
      "box-statistics CSV lists all seven groups")

# -------------------------------------------------------------- text -------
txt = open(os.path.join(OUT, "labels_and_caption.txt"), encoding="utf-8").read()
txt = " ".join(txt.split())        # line wraps must not break a phrase match
for s in ["J–V RMSE (mA cm⁻²)", "Full curve", "0–1.0 V", "> 1.0 V",
          "|ΔJsc|", "|ΔVoc|", "|ΔFF|", "|ΔPCE|", "mA cm⁻²", "pp",
          "0.01, 0.1, 1, 10 and 100", "1.5 times the interquartile range",
          "n = 45", "44", "downward zero crossing", "logarithmic"]:
    check(s in txt, "labels/caption file contains '%s'" % s)
check("confidence interval" not in txt.lower().replace("not a confidence interval", ""),
      "caption never calls the whiskers a confidence interval")
check("2.69" in txt and "0.455" in txt and "5.19" in txt,
      "median numbers are listed for the author")

print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
if FAIL:
    print("FAILURES:", FAIL)
    sys.exit(1)
