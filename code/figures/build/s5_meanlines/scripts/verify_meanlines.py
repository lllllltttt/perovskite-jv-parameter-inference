# -*- coding: utf-8 -*-
"""Verify the nine S4 mean-line panels.

Checks, per panel:
  V1  SVG has no <text>; every glyph <use> points at #ArialMT-*; no external refs
  V2  canvas identical to the approved panel; PNG 600 dpi, same pixel size
  V3  the panel WITHOUT the line is pixel-identical to the approved PNG
      (data, bins, bar heights, frame, ticks, margins all unchanged)
  V4  every pixel that differs between WITH-line and WITHOUT-line lies inside
      a narrow band around the mean; the line touches the top and the bottom
      of the plot area
  V5  the line path in the SVG sits at the full-precision mean (not 3 dp);
      colour #ca7241, width 1.2 pt, dasharray 4.8,2.4, spans y 154.991 -> 2.14
  V6  the whole SVG tree equals the approved one once (a) the line group is
      removed and (b) the random clip/marker ids are normalised
  V7  >= 0.8 pt clearance: nothing clipped at the canvas edge
"""
import os
import re
import sys
import copy

import numpy as np
from lxml import etree
from PIL import Image

BASE = r"E:\project\work1"
ROOT = os.path.join(BASE, "20261119_si_s4_meanlines")
OUT = os.path.join(ROOT, "out")
WORK = os.path.join(ROOT, "work")
OLD = os.path.join(BASE, "20261117_si_s4_s5_s8", "out")

SVGNS = "http://www.w3.org/2000/svg"
XLNS = "http://www.w3.org/1999/xlink"
CS = "{%s}" % SVGNS
XL = "{%s}" % XLNS

PARAMS = ["mu_n", "mu_p", "tau_n", "tau_p", "Nc", "Nv",
          "tau_ETL", "tau_HTL", "rad_c"]
MEAN = [0.0927500197, 0.0873836843, 0.1091154274, 0.1091475068,
        0.0747904792, 0.0811762102, 0.2294913005, 0.1909045774,
        0.2282661654]
QUOTED = [0.093, 0.087, 0.109, 0.109, 0.075, 0.081, 0.229, 0.191, 0.228]
PX_PT = 600 / 72.0
FAIL = []


def ok(cond, label, detail=""):
    print("  %s  %-58s%s" % ("PASS" if cond else "FAIL", label,
                             ("  " + detail) if detail else ""))
    if not cond:
        FAIL.append(label)


def canvas(root):
    return float(root.get("width").replace("pt", "")), \
        float(root.get("height").replace("pt", ""))


def axes_box(root):
    for g in root.iter(CS + "g"):
        if g.get("id") == "patch_2":
            d = g.find(CS + "path").get("d")
            v = [float(x) for x in re.findall(r"-?\d+\.?\d*", d)]
            # M x0 y0 L x1 y0 L x1 y1 L x0 y1  (SVG y grows downwards)
            xs, ys = v[0::2], v[1::2]
            return min(xs), min(ys), max(xs), max(ys)
    raise RuntimeError("axes patch not found")


def normalise(root):
    """Replace random ids (p…/m…) by stable names in order of appearance and
    drop the creation timestamp from the RDF metadata."""
    for el in list(root.iter("{%s}date" % "http://purl.org/dc/elements/1.1/")):
        el.text = "DATE"
    mapping = {}

    def key(v):
        if v not in mapping:
            mapping[v] = "ID%d" % len(mapping)
        return mapping[v]

    for el in root.iter():
        i = el.get("id")
        if i and re.match(r"^[pm][0-9a-f]{10,}$", i):
            el.set("id", key(i))
        cp = el.get("clip-path")
        if cp:
            el.set("clip-path", "url(#%s)" % key(cp[5:-1]))
        h = el.get(XL + "href")
        if h and h.startswith("#") and re.match(r"^[pm][0-9a-f]{10,}$", h[1:]):
            el.set(XL + "href", "#" + key(h[1:]))
    return root


def strip_line(root):
    """Drop the mean-line group (the only <g> whose path is #ca7241)."""
    removed = 0
    for g in list(root.iter(CS + "g")):
        if g.get("id", "").startswith("line2d"):
            hit = any("#ca7241" in (p.get("style") or "")
                      for p in g.iter(CS + "path"))
            if hit:
                g.getparent().remove(g)
                removed += 1
    return removed


def main():
    print("=" * 78)
    for i in range(9):
        tag = "S4_%02d" % (i + 1)
        print("%s  (%s, mean = %.10f)" % (tag, PARAMS[i], MEAN[i]))
        new_svg = os.path.join(OUT, tag + ".svg")
        new_png = os.path.join(OUT, tag + "_600dpi.png")
        ref_png = os.path.join(WORK, "_ref_" + tag + ".png")
        old_svg = os.path.join(OLD, tag + ".svg")
        old_png = os.path.join(OLD, tag + ".png")

        r = etree.parse(new_svg).getroot()
        ro = etree.parse(old_svg).getroot()

        # ---- V1 ---------------------------------------------------------
        ntext = len(list(r.iter(CS + "text")))
        hrefs = [u.get(XL + "href") or "" for u in r.iter(CS + "use")]
        glyph = [h for h in hrefs if h.startswith("#") and
                 re.match(r"^#[A-Za-z]+-", h)]
        bad = [h for h in glyph if not h.startswith("#ArialMT-")]
        ext = [h for h in hrefs if h.startswith(("http", "file", "/"))]
        ok(ntext == 0 and glyph and not bad and not ext,
           tag + ": %d glyph uses, all #ArialMT-*, no <text>" % len(glyph),
           (str(bad[:2]) + str(ext[:2])) if (bad or ext) else "")

        # ---- V2 ---------------------------------------------------------
        cw, ch = canvas(r)
        cwo, cho = canvas(ro)
        im = Image.open(new_png)
        imo = Image.open(old_png)
        ok(abs(cw - cwo) < 1e-6 and abs(ch - cho) < 1e-6
           and im.size == imo.size
           and abs(im.info.get("dpi", (0,))[0] - 600) < 1.0,
           tag + ": canvas %.2fx%.2f pt, PNG %dx%d @600 dpi"
           % (cw, ch, im.size[0], im.size[1]))

        # ---- V3 ---------------------------------------------------------
        a_new = np.asarray(Image.open(new_png).convert("RGB")).astype(int)
        a_ref = np.asarray(Image.open(ref_png).convert("RGB")).astype(int)
        a_old = np.asarray(Image.open(old_png).convert("RGB")).astype(int)
        d_ref_old = int((a_ref != a_old).any(axis=2).sum())
        ok(d_ref_old == 0, tag + ": panel without line == approved PNG",
           "%d differing px" % d_ref_old)

        # ---- V4 ---------------------------------------------------------
        x0, y0, x1, y1 = axes_box(r)          # top-left origin, pt
        cx = x0 + (MEAN[i] / 0.5) * (x1 - x0)
        col = cx * PX_PT
        diff = (a_new != a_ref).any(axis=2)
        cols = np.where(diff.any(axis=0))[0]
        rows = np.where(diff.any(axis=1))[0]
        in_band = bool(len(cols)) and bool(cols.min() >= col - 9
                                           and cols.max() <= col + 9)
        top_ok = bool(len(rows)) and rows.min() <= y0 * PX_PT + 12
        bot_ok = bool(len(rows)) and rows.max() >= y1 * PX_PT - 12
        ok(in_band and top_ok and bot_ok,
           tag + ": diffs only in the line band, full plot height",
           "band %d-%d px around %.1f; rows %d-%d of %.1f-%.1f"
           % (cols.min(), cols.max(), col, rows.min(), rows.max(),
              y0 * PX_PT, y1 * PX_PT))

        # ---- V5 ---------------------------------------------------------
        lines = [p for p in r.iter(CS + "path")
                 if "#ca7241" in (p.get("style") or "")]
        ok(len(lines) == 1, tag + ": exactly one mean-line path",
           "%d found" % len(lines))
        p = lines[0]
        st = p.get("style")
        v = [float(x) for x in re.findall(r"-?\d+\.?\d*", p.get("d"))]
        xa, ya, xb, yb = v[0], v[1], v[2], v[3]
        x_data = (xa - x0) / (x1 - x0) * 0.5
        ok(abs(xa - xb) < 1e-4 and abs(x_data - MEAN[i]) < 2e-6
           and abs(x_data - QUOTED[i]) > 1e-5,
           tag + ": line x = %.9f (full precision, not %.3f)" %
           (x_data, QUOTED[i]),
           "|x-full| = %.1e, |x-3dp| = %.1e"
           % (abs(x_data - MEAN[i]), abs(x_data - QUOTED[i])))
        ok(abs(ya - y1) < 1e-3 and abs(yb - y0) < 1e-3
           and "stroke: #ca7241" in st and "stroke-width: 1.2" in st
           and "stroke-dasharray: 4.8,2.4" in st,
           tag + ": bottom->top, #ca7241, 1.2 pt, dashed 4.8/2.4",
           "y %.3f -> %.3f" % (ya, yb))

        # ---- V6 ---------------------------------------------------------
        rn = normalise(copy.deepcopy(r))
        ron = normalise(copy.deepcopy(ro))
        nremoved = strip_line(rn)
        s_new = etree.tostring(rn, encoding="unicode")
        s_old = etree.tostring(ron, encoding="unicode")
        ok(nremoved == 1 and s_new == s_old,
           tag + ": SVG tree identical to approved apart from the line",
           "line groups removed %d, %d vs %d chars"
           % (nremoved, len(s_new), len(s_old)))

        # ---- V7 ---------------------------------------------------------
        g = np.asarray(Image.open(new_png).convert("L")).astype(int)
        mk = (255 - g) > 8
        rr = np.where(mk.any(axis=1))[0]
        cc = np.where(mk.any(axis=0))[0]
        clr = min(cc[0], rr[0], g.shape[1] - 1 - cc[-1],
                  g.shape[0] - 1 - rr[-1]) / PX_PT
        ok(clr > 0.8, tag + ": clearance %.2f pt, nothing clipped" % clr)

    print("=" * 78)
    print("RESULT:", "ALL PASS" if not FAIL else "FAIL (%d)" % len(FAIL))
    for f in FAIL:
        print("  FAILED:", f)
    sys.exit(1 if FAIL else 0)


main()
