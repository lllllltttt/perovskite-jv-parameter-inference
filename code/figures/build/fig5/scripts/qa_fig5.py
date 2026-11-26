# -*- coding: utf-8 -*-
"""QA for the standalone Figure 5 panels.

Read-only: rebuilds every panel in memory and checks the exported files
against the frozen data.  Covers
  * provenance (the plotted arrays are the archived Figure 5 arrays);
  * file set, canvas size, dpi, PDF fonts, live SVG text;
  * axes: (c)(d)(e) identical frames, x ticks, true data positions, no point
    at 1.5, reference lines (a) y=x/100, (d) 0.95, (e) 0;
  * (b): nine rows, ring only on the two "worse" parameters, key clear of
    every marker;
  * the one shared nine-parameter key in (e): two columns, one family per
    row, r_rad alone, no marker inside it;
  * nothing clipped, no grid, no text below 6.5 pt, no baked-in letters,
    titles or axis names in any net panel.
"""
import os
import sys
import csv
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
ROOT = os.path.dirname(HERE)
FIG = os.path.join(ROOT, "figures")
LEG = os.path.join(ROOT, "legends")
PRE = os.path.join(ROOT, "preview")
DATA = os.path.join(ROOT, "data_used")
sys.path.insert(0, HERE)
import fig5_standalone as G      # noqa: E402
import figstyle as st            # noqa: E402

PASS, FAIL = [], []


def check(cond, name, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("PASS  " if cond else "FAIL  ") + name + ("  " + detail if detail else ""))


NS = "{http://www.w3.org/2000/svg}"
DRAW = {"a": G.draw_a, "b": G.draw_b, "c": G.draw_c, "d": G.draw_d,
        "e": G.draw_e}


def svg_texts(name):
    r = ET.parse(os.path.join(FIG, "Fig5%s.svg" % name)).getroot()
    out = []
    for t in r.iter(NS + "text"):
        s = "".join(t.itertext())
        s = " ".join(s.split())
        if s:
            out.append(s)
    return out


def svg_root(name):
    return ET.parse(os.path.join(FIG, "Fig5%s.svg" % name)).getroot()


def build(name):
    fig = G.new_fig(*G.PW[name])
    res = DRAW[name](fig)
    fig.canvas.draw()
    return fig, res


# =============================================================== 1. data ====
check(len(G.COV) == 9 and G.COV.shape == (9, 4), "coverage array is 9 x 4",
      str(G.COV.shape))
check(G.RMAT.shape == G.CMAT.shape == G.SREL.shape == (9, 5),
      "noise arrays are 9 x 5", str(G.SREL.shape))
check(np.allclose(G.ISM, G.F5.IS_MODEL95, rtol=0, atol=2e-6),
      "(b) model values are the archived IS_MODEL95 (6-dp archive copy)")
check(np.allclose(G.ISB, G.F5.IS_BASE95, rtol=0, atol=2e-6),
      "(b) baseline values are the archived IS_BASE95 (6-dp archive copy)")
check(np.allclose(G.RHO, G.F5.RHO, rtol=0, atol=1e-9),
      "rho column is the archived RHO")
check(list(G.F5.LEVELS) == [0.50, 0.80, 0.90, 0.95],
      "(a) four measured nominal levels kept")
check(list(G.F5.NOISE_X) == [0.0, 0.2, 0.5, 1.0, 2.0],
      "(c-e) five noise levels at their true positions")
check(list(np.where(G.WORSE)[0]) == [6, 8],
      "worse-than-prior flag is tau_ETL and r_rad only",
      str(list(np.where(G.WORSE)[0])))
check(np.all(G.SREL[:, 0] == 0.0),
      "(e) 0 % column is exactly the clean-input reference")

# ============================================================ 2. files =====
for n in "abcde":
    for ext in ("png", "pdf", "svg"):
        check(os.path.isfile(os.path.join(FIG, "Fig5%s.%s" % (n, ext))),
              "exists figures/Fig5%s.%s" % (n, ext))
for stem in ("Fig5_param_legend", "Fig5b_marker_legend", "Fig5_color_map"):
    for ext in ("png", "pdf", "svg"):
        check(os.path.isfile(os.path.join(LEG, stem + "." + ext)),
              "exists legends/%s.%s" % (stem, ext))
for f in ("Fig5_preview.png", "Fig5_preview.pdf"):
    check(os.path.isfile(os.path.join(PRE, f)), "exists preview/" + f)
for f in ("Figure5_plotting_values.csv", "Figure5_color_map.csv"):
    check(os.path.isfile(os.path.join(DATA, f)), "exists data_used/" + f)

# canvas, dpi, fonts
for n in "abcde":
    w, h = G.PW[n]
    im = Image.open(os.path.join(FIG, "Fig5%s.png" % n))
    check(abs(im.info.get("dpi", (0, 0))[0] - 600) < 1,
          "(%s) PNG is 600 dpi" % n, "%.0f" % im.info.get("dpi", (0, 0))[0])
    check(abs(im.size[0] - w * 600) <= 1 and abs(im.size[1] - h * 600) <= 1,
          "(%s) PNG canvas %.2f x %.2f in" % (n, w, h), "%dx%d" % im.size)
    doc = fitz.open(os.path.join(FIG, "Fig5%s.pdf" % n))
    check(len(doc) == 1 and abs(doc[0].rect.width - w * 72) < 0.5
          and abs(doc[0].rect.height - h * 72) < 0.5,
          "(%s) PDF page %.2f x %.2f in" % (n, w, h),
          "%.1f x %.1f pt" % (doc[0].rect.width, doc[0].rect.height))
    fonts = [f[3] for f in doc[0].get_fonts()]
    check(any("Arial" in f for f in fonts), "(%s) Arial embedded" % n,
          str(fonts))
    doc.close()
    root = svg_root(n)
    check(abs(float(root.get("width").replace("pt", "")) - w * 72) < 0.5,
          "(%s) SVG width %.2f in" % (n, w), root.get("width"))
    check(len(list(root.iter(NS + "image"))) == 0,
          "(%s) SVG contains no raster image" % n)

# the panels are rebuilt once, before the SVG-text checks need the axes
figs = {}
for n in "abcde":
    figs[n] = build(n)

# ============================================================= 3. SVG text ==
ta = svg_texts("a")
check(sorted(ta) == sorted(["50", "60", "70", "80", "90", "100",
                            "0.5", "0.6", "0.7", "0.8", "0.9", "1.0"]),
      "(a) SVG carries the twelve tick numbers and nothing else", str(ta))
for n, ylab in (("c", ["0.4", "0.5", "0.6", "0.7", "0.8", "0.9", "1.0"]),
                ("d", ["0.70", "0.80", "0.90", "1.00"]),
                ("e", ["-3", "-2", "-1", "0"])):
    t = svg_texts(n)
    xs = [ln.get_text() for ln in figs[n][1][0].get_xticklabels()]
    check(xs == ["0", "0.5", "1.0", "1.5", "2.0"],
          "(%s) five x tick labels 0 / 0.5 / 1.0 / 1.5 / 2.0" % n, str(xs))
    check(all(y in t for y in ylab), "(%s) y tick labels present" % n,
          str(ylab))
tb = svg_texts("b")
check(all(s in tb for s in ("0", "2", "4", "6")),
      "(b) x tick numbers are 0 / 2 / 4 / 6")
check(all(s in tb for s in ("Baseline", "Model", "Worse")),
      "(b) three-key legend words inside the panel")
check(len([s for s in tb if s not in ("0", "2", "4", "6",
                                      "Baseline", "Model", "Worse")]) == 9,
      "(b) nine parameter names on the y axis")
te = svg_texts("e")
check(all(s in te for s in ("Baseline",)) is False,
      "(e) carries no leftover (b) legend word")
banned = ["Nominal", "noise", "coverage", "Interval score", "Pearson",
          "Change in", "(%", "(a)", "(b)", "(c)", "(d)", "(e)", "Figure"]
for n in "abcde":
    t = svg_texts(n)
    hit = [b for b in banned for s in t if b in s]
    check(not hit, "(%s) no baked-in letter, title or axis name" % n, str(hit))

# ============================================== 4. geometry and marks =======
w, h = G.PW["c"]
rects = [figs[n][1][0].get_position().bounds for n in "cde"]
check(all(np.allclose(r, rects[0], rtol=0, atol=1e-12) for r in rects),
      "(c)(d)(e) axes rectangles identical",
      str(tuple(round(v, 6) for v in rects[0])))
fr = []
for n in "cde":
    f, res = figs[n]
    f.canvas.draw()
    fr.append(res[0].get_window_extent(renderer=f.canvas.get_renderer()).bounds)
check(all(np.allclose(x, fr[0], rtol=0, atol=1e-6) for x in fr),
      "(c)(d)(e) frames occupy the same pixels")
check(G.PW["c"] == G.PW["d"] == G.PW["e"], "(c)(d)(e) canvases identical")

# data positions
ax_a = figs["a"][1][0]
xs = [ln.get_xdata() for ln in ax_a.lines if ln.get_marker() in ("o", "s")]
check(len(xs) == 9 and all(np.allclose(x, [50, 80, 90, 95]) for x in xs),
      "(a) every curve sits at 50 / 80 / 90 / 95 %",
      str([list(map(float, x)) for x in xs[:1]]))
for n in "cde":
    ax = figs[n][1][0]
    xs = [ln.get_xdata() for ln in ax.lines if ln.get_marker() in ("o", "s")]
    check(len(xs) == 9
          and all(np.allclose(x, [0.0, 0.2, 0.5, 1.0, 2.0]) for x in xs),
          "(%s) five points at 0 / 0.2 / 0.5 / 1 / 2, none added" % n)
    check(not any(np.any(np.isclose(ln.get_xdata(), 1.5)) for ln in ax.lines),
          "(%s) 1.5 is a tick only, no data there" % n)
    check([round(float(v), 6) for v in ax.get_xticks()]
          == [0.0, 0.5, 1.0, 1.5, 2.0],
          "(%s) x ticks 0 / 0.5 / 1.0 / 1.5 / 2.0" % n)

# reference lines
diag = [ln for ln in ax_a.lines if ln.get_linestyle() == "--"]
check(len(diag) == 1, "(a) one ideal-calibration line")
d = diag[0].get_xydata()
check(np.allclose(d[:, 1], d[:, 0] / 100.0, rtol=0, atol=1e-12),
      "(a) the ideal line is exactly y = x/100",
      str(np.round(d, 3).tolist()))
check(d[0, 0] <= 48 and d[-1, 0] >= 100, "(a) the line spans the whole frame")
ax_d = figs["d"][1][0]
check(any(np.allclose(ln.get_ydata(), 0.95) for ln in ax_d.lines),
      "(d) nominal 0.95 reference line kept")
ax_e = figs["e"][1][0]
check(any(np.allclose(ln.get_ydata(), 0.0) for ln in ax_e.lines),
      "(e) zero baseline kept")

# (b) structure
ax_b = figs["b"][1][0]
rows = [ln for ln in ax_b.lines if ln.get_marker() == "o"
        and ln.get_markersize() > 7.0]
check(len(rows) == 1 and len(rows[0].get_ydata()) == 2,
      "(b) exactly two ring symbols", "n=%d" % len(rows[0].get_ydata()))
check(np.allclose(rows[0].get_ydata(), [2.0, 0.0]),
      "(b) rings sit on the tau_ETL and r_rad rows",
      str(rows[0].get_ydata().tolist()))
check([t.get_text() for t in ax_b.get_yticklabels()] == st.PARAM_LABELS,
      "(b) y axis lists all nine parameter names in canonical order")
conn = [ln for ln in ax_b.lines if ln.get_color() == "#c9ced4"]
check(len(conn) == 9, "(b) nine connector lines", "%d" % len(conn))

# colours and markers, everywhere the nine curves appear
for n in "acde":
    ax = figs[n][1][0]
    ln = [x for x in ax.lines if x.get_marker() in ("o", "s")]
    ok = all(l.get_color() == G.PAL[i][0] and l.get_marker() == G.PAL[i][1]
             for i, l in enumerate(ln))
    check(ok, "(%s) nine curves use the shared colour/marker map" % n)
check(len({p[0] for p in G.PAL}) == 9, "nine distinct colours")
check(all(G.PAL[i][1] == "o" for i in (0, 2, 4, 6, 8)),
      "first member of every family is the filled circle")
check(all(G.PAL[i][1] == "s" for i in (1, 3, 5, 7)),
      "second member of every family is the filled square")

# nothing clipped, nothing outside, no grid, no small type
for n in "abcde":
    f, res = figs[n]
    ax = res[0]
    r = f.canvas.get_renderer()
    bb = ax.get_window_extent(renderer=r)
    bad = 0
    for ln in ax.lines:
        if ln.get_marker() in ("o", "s") and len(ln.get_xdata()):
            P = ax.transData.transform(np.column_stack([ln.get_xdata(),
                                                        ln.get_ydata()]))
            bad += int(np.sum((P[:, 0] < bb.x0 - 0.5) | (P[:, 0] > bb.x1 + 0.5)
                              | (P[:, 1] < bb.y0 - 0.5) | (P[:, 1] > bb.y1 + 0.5)))
    check(bad == 0, "(%s) every marker inside the frame" % n, "%d outside" % bad)
    check(not ax.xaxis.get_gridlines()[0].get_visible()
          if ax.xaxis.get_gridlines() else True, "(%s) no grid" % n)
    sizes = [t.get_fontsize() for t in ax.get_xticklabels() + ax.get_yticklabels()
             if t.get_text()]
    if res[-1] is not None and hasattr(res[-1], "get_texts"):
        sizes += [t.get_fontsize() for t in res[-1].get_texts()]
    check(min(sizes) >= st.MIN_FS - 1e-9,
          "(%s) no text below %.1f pt" % (n, st.MIN_FS),
          "min %.1f" % min(sizes))
    check(not G.canvas_text_out(f), "(%s) no text outside the canvas" % n)

# ==================================================== 5. the two legends ====
fig_e, res_e = figs["e"]
ax_e, _, leg = res_e
labels = [t.get_text() for t in leg.get_texts()]
check(len(labels) == 9, "(e) shared key has nine entries", str(labels))
check(leg._ncols == 2, "(e) shared key has two columns")
order = [st.PARAM_LABELS[i] for i in G.LEG_ORDER]
check(labels == order, "(e) column-major fill puts each pair on one row",
      str(labels))
check(G.LEG_ORDER[:5] == [0, 2, 4, 6, 8] and G.LEG_ORDER[5:] == [1, 3, 5, 7],
      "r_rad (index 8) closes the first column, alone on the last row")
hit, gap = G.legend_clearance(fig_e, ax_e, leg)
check(hit == 0, "(e) shared key covers no marker", "nearest %.1f pt" % gap)
check(gap > 4.0, "(e) nearest marker keeps > 4 pt clearance", "%.1f pt" % gap)

fig_b, res_b = figs["b"]
ax_b, _, leg_b = res_b
check([t.get_text() for t in leg_b.get_texts()] == G.B_LEG_LABELS,
      "(b) three keys: %s" % " / ".join(G.B_LEG_LABELS))
hit, gap = G.legend_clearance(fig_b, ax_b, leg_b)
check(hit == 0, "(b) key covers no marker", "nearest %.1f pt" % gap)
check(gap > 2.0, "(b) nearest marker keeps > 2 pt clearance", "%.1f pt" % gap)

# ==================================================== 6. data tables ========
with open(os.path.join(DATA, "Figure5_color_map.csv"), encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
check(len(rows) == 9, "colour map CSV has nine rows")
check([r["color_hex"] for r in rows] == [p[0] for p in G.PAL],
      "colour map CSV matches the drawn colours")
check([r["marker"] for r in rows] == [p[1] for p in G.PAL],
      "colour map CSV matches the drawn markers")
with open(os.path.join(DATA, "Figure5_plotting_values.csv"), encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
n_a = sum(1 for r in rows if r["panel"] == "a")
n_c = sum(1 for r in rows if r["panel"] == "c")
check(n_a == 36 and n_c == 45, "plotting table holds 9x4 and 9x5 rows",
      "%d / %d" % (n_a, n_c))

# ==================================================== 7. preview + text =====
im = Image.open(os.path.join(PRE, "Fig5_preview.png"))
check(abs(im.size[0] - 6.80 * 200) <= 1 and abs(im.size[1] - 4.70 * 200) <= 1,
      "preview canvas is 6.80 x 4.70 in at 200 dpi", "%dx%d" % im.size)
doc = fitz.open(os.path.join(PRE, "Fig5_preview.pdf"))
check(abs(doc[0].rect.width - 6.80 * 72) < 0.5, "preview PDF is 6.80 in wide",
      "%.1f pt" % doc[0].rect.width)
doc.close()

with open(os.path.join(ROOT, "labels_and_caption.txt"), encoding="utf-8") as f:
    txt = " ".join(f.read().split())
for phrase in ("95% interval score", "LOWER IS BETTER", "nominal level 0.95",
               "not percentage points", "|Jsc|", "σθ", "r_rad", "τ_ETL",
               "τ_HTL", "2.00 x 1.75", "1.5 is only a tick",
               "Fig5_param_legend.svg", "Fig5b_marker_legend.svg"):
    check(phrase in txt, "text list states: %s" % phrase)

for f, res in figs.items():
    plt.close(res[0])

print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
if FAIL:
    print("FAILURES:", FAIL)
    sys.exit(1)
