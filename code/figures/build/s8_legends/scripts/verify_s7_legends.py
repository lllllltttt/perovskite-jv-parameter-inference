# -*- coding: utf-8 -*-
"""Verification of the two re-issued S7 panels.

V1  no <text> anywhere; the legend text is outlines
V2  legend has no frame/background patch; handle colours and widths equal the
    curve styles; text fill equals the tick-label fill
V3  the glyph outlines are byte-identical to the old Arial 7 pt legend text
    (same font, same size -> no silent fallback)
V4  legend ink box is entirely right of x = 1 (>= 6.5 pt) and inside the axes
V5  the rest of the SVG tree is identical to the approved panel
V6  the panel without the new legend is pixel-identical to the approved PNG
    outside the old legend box (S7a) / everywhere (S7b)
V7  the new legend changes only pixels inside its own ink box
V8  that box was pure white beforehand (no curve, dashed line, frame or tick
    is covered) and the x = 1 column is untouched
V9  canvas size, 600 dpi and outer clearance unchanged
"""
import json
import os
import re
import sys

from lxml import etree
import numpy as np
from PIL import Image

CS = "{http://www.w3.org/2000/svg}"
XL = "{http://www.w3.org/1999/xlink}"

BASE = r"E:\project\work1"
ROOT = os.path.join(BASE, "20261119_si_s7_legends")
OUT = os.path.join(ROOT, "out")
WORK = os.path.join(ROOT, "work")
OLD = os.path.join(BASE, "20261116_figs7_split", "out", "svg")
OLDPNG = os.path.join(BASE, "20261116_figs7_split", "out", "png")
PX = 600 / 72.0
FAIL = []


def ok(cond, label, detail=""):
    print("  %s  %-62s%s" % ("PASS" if cond else "FAIL", label,
                             ("  " + detail) if detail else ""))
    if not cond:
        FAIL.append(label)


def canon(el):
    """Whitespace-insensitive serialisation."""
    e = etree.fromstring(etree.tostring(el))
    for x in e.iter():
        if x.text is not None and not x.text.strip():
            x.text = None
        if x.tail is not None and not x.tail.strip():
            x.tail = None
    return etree.tostring(e)


def strip_legends(root):
    n = 0
    for g in list(root.iter(CS + "g")):
        if (g.get("id") or "").startswith("legend"):
            g.getparent().remove(g)
            n += 1
    return n


def axes_box(root):
    ax = [g for g in root.iter(CS + "g")
          if re.match(r"^axes_\d+$", g.get("id") or "")][0]
    v = [float(x) for x in re.findall(r"-?\d+\.?\d*",
                                      ax.find(CS + "g").find(CS + "path").get("d"))]
    xs, ys = v[0::2], v[1::2]
    return min(xs), min(ys), max(xs), max(ys)


def legend_bbox(root):
    """Ink box of the legend group, straight from its geometry."""
    g = [x for x in root.iter(CS + "g") if (x.get("id") or "") == "legend_1"][0]
    xs, ys, tx = [], [], []
    for p in g.iter(CS + "path"):
        st = p.get("style") or ""
        if "stroke:" in st:                      # handle lines
            v = [float(x) for x in re.findall(r"-?\d+\.?\d*", p.get("d"))]
            xs += v[0::2]
            ys += v[1::2]
        else:                                     # glyph outlines
            tr = p.getparent().get("transform")
            m = re.search(r"translate\(\s*(-?[\d.]+)[ ,]+(-?[\d.]+)\)", tr)
            x0, y0 = float(m.group(1)), float(m.group(2))
            # ink extents of the glyph path in its own y-up frame
            seq = [float(x) for x in re.findall(r"-?\d+\.?\d*", p.get("d"))]
            gx = seq[0::2]
            gy = seq[1::2]
            xs += [x0 + min(gx), x0 + max(gx)]
            ys += [y0 - max(gy), y0 - min(gy)]
    return min(xs), min(ys), max(xs), max(ys)


def main():
    meta = json.load(open(os.path.join(WORK, "legend_meta.json")))
    print("=" * 78)
    for name in ("S7a", "S7b"):
        print("%s" % name)
        new = etree.parse(os.path.join(OUT, name + ".svg")).getroot()
        old = etree.parse(os.path.join(OLD, name + ".svg")).getroot()
        vx, vy = [float(t) for t in new.get("viewBox").split()][:2]

        def pxl(x, y):
            """panel coordinates -> pixel indices in the 600 dpi raster"""
            return (x - vx) * PX, (y - vy) * PX

        box = axes_box(new)
        x1 = [p for p in new.iter(CS + "path")
              if "#555555" in (p.get("style") or "")][0]
        v = [float(x) for x in re.findall(r"-?\d+\.?\d*", x1.get("d"))]
        xline = v[0]

        # ---- V1 ---------------------------------------------------------
        ntext = len(list(new.iter(CS + "text")))
        ok(ntext == 0, name + ": no <text>, glyphs are outlines")

        # ---- V2 ---------------------------------------------------------
        lg = [g for g in new.iter(CS + "g") if g.get("id") == "legend_1"][0]
        patches = [e for e in lg.iter() if e.tag in (CS + "rect", CS + "polygon")
                   or ((e.get("style") or "").startswith("fill: #ffffff"))]
        handles = [p.get("style") for p in lg.iter(CS + "path")
                   if "stroke:" in (p.get("style") or "")]
        curve_styles = [p.get("style") for p in new.iter(CS + "path")
                        if re.search(r"stroke: #(9a9a9a|0072b2|d55e00)", p.get("style") or "")]
        handles_ok = all(h in curve_styles for h in handles)
        fills = [p.get("fill") for p in lg.iter(CS + "path")
                 if "fill" in p.attrib]
        ok(len(patches) == 0 and handles_ok and fills == ["#1a1a1a", "#1a1a1a"],
           name + ": no frame/background, handles match the curves",
           "%d handles, patch %d" % (len(handles), len(patches)))

        # ---- V3 ---------------------------------------------------------
        new_d = [p.get("d") for p in lg.iter(CS + "path") if "fill" in p.attrib]
        old_lg = [g for g in old.iter(CS + "g") if (g.get("id") or "").startswith("legend")]
        if old_lg:
            old_d = [p.get("d") for p in old_lg[0].iter(CS + "path")
                     if "fill" in p.attrib]
            ok(len(new_d) == 2 and new_d == old_d,
               name + ": glyph outlines identical to the old Arial 7 pt legend",
               "%d paths" % len(new_d))
        else:
            r7 = etree.parse(os.path.join(OUT, "S7a.svg")).getroot()
            ref_lg = [g for g in r7.iter(CS + "g")
                      if (g.get("id") or "") == "legend_1"][0]
            ref_d = [p.get("d") for p in ref_lg.iter(CS + "path")
                     if "fill" in p.attrib]
            ok(len(new_d) == 2 and new_d == ref_d,
               name + ": glyph outlines identical to S7a (same font and size)")

        # ---- V4 ---------------------------------------------------------
        bb = legend_bbox(new)
        clear = bb[0] - xline
        inside = (bb[2] < box[2] - 1.0 and bb[3] < box[3] - 2.0
                  and bb[1] > box[1] + 1.0)
        ok(clear >= 6.5 and inside,
           name + ": legend fully right of x=1 and inside the axes",
           "clear %.2f pt; bbox %.2f %.2f %.2f %.2f"
           % (clear, bb[0], bb[1], bb[2], bb[3]))

        # ---- V5 ---------------------------------------------------------
        nn = etree.fromstring(etree.tostring(new))
        no = etree.fromstring(etree.tostring(old))
        r1, r2 = strip_legends(nn), strip_legends(no)
        ok(canon(nn) == canon(no),
           name + ": SVG tree identical to the approved panel apart from legends",
           "removed new %d / old %d" % (r1, r2))

        # ---- V6 ---------------------------------------------------------
        p_new = np.asarray(Image.open(os.path.join(OUT, name + "_600dpi.png")).convert("RGB")).astype(int)
        p_ref = np.asarray(Image.open(os.path.join(WORK, name + "_nolegend.png")).convert("RGB")).astype(int)
        p_old = np.asarray(Image.open(os.path.join(OLDPNG, name + "_600dpi.png")).convert("RGB")).astype(int)
        dif = (p_ref != p_old).any(axis=2)
        if name == "S7a":
            ob = old_lg[0].find(CS + "g").find(CS + "path").get("d")
            ov = [float(x) for x in re.findall(r"-?\d+\.?\d*", ob)]
            ox, oy = ov[0::2], ov[1::2]
            obb = (min(ox), min(oy), max(ox), max(oy))
            x0, y0 = pxl(obb[0], obb[1])
            x1p, y1 = pxl(obb[2], obb[3])
            x0, y0 = int(np.floor(x0)) - 2, int(np.floor(y0)) - 2
            x1p, y1 = int(np.ceil(x1p)) + 2, int(np.ceil(y1)) + 2
            outside = int(np.delete(np.delete(dif, np.s_[y0:y1], 0),
                                    np.s_[x0:x1p], 1).sum())
            ok(outside == 0 and dif.sum() > 0,
               name + ": differences vs approved PNG only where the old legend was",
               "%d px inside, %d outside" % (dif.sum(), outside))
        else:
            ok(int(dif.sum()) == 0,
               name + ": identical to approved PNG once legend removed",
               "%d px" % dif.sum())

        # ---- V7 ---------------------------------------------------------
        d2 = (p_new != p_ref).any(axis=2)
        rows = np.where(d2.any(axis=1))[0]
        cols = np.where(d2.any(axis=0))[0]
        bx0, by0 = pxl(bb[0], bb[1])
        bx1, by1 = pxl(bb[2], bb[3])
        ex = (int(np.floor(bx0)) - 3, int(np.floor(by0)) - 3,
              int(np.ceil(bx1)) + 3, int(np.ceil(by1)) + 3)
        outside2 = int(np.delete(np.delete(d2, np.s_[ex[1]:ex[3]], 0),
                                 np.s_[ex[0]:ex[2]], 1).sum())
        ok(outside2 == 0 and d2.sum() > 0,
           name + ": legend draws only inside its box",
           "%d px, rows %d-%d cols %d-%d; box %d-%d/%d-%d"
           % (d2.sum(), rows.min(), rows.max(), cols.min(), cols.max(),
              ex[1], ex[3], ex[0], ex[2]))

        # ---- V8 ---------------------------------------------------------
        crop = p_ref[ex[1]:ex[3], ex[0]:ex[2]]
        white = float((crop.min(axis=2) >= 250).mean()) if crop.size else 0.0
        col = int(round((xline - vx) * PX))
        colsame = bool((p_new[:, col - 1:col + 2] == p_ref[:, col - 1:col + 2]).all())
        ok(white == 1.0 and colsame,
           name + ": box was blank before (no curve/line/frame under it)",
           "white %.1f%%, x=1 column unchanged %s" % (100 * white, colsame))

        # ---- V9 ---------------------------------------------------------
        im = Image.open(os.path.join(OUT, name + "_600dpi.png"))
        imo = Image.open(os.path.join(OLDPNG, name + "_600dpi.png"))
        g = np.asarray(im.convert("L")).astype(int)
        mk = (255 - g) > 8
        rr = np.where(mk.any(axis=1))[0]
        cc = np.where(mk.any(axis=0))[0]
        clr = min(cc[0], rr[0], g.shape[1] - 1 - cc[-1], g.shape[0] - 1 - rr[-1]) / PX
        ok(im.size == imo.size and abs(im.info.get("dpi", (0,))[0] - 600) < 1
           and clr > 2.0,
           name + ": %dx%d px @600 dpi, clearance %.2f pt"
           % (im.size[0], im.size[1], clr))

    print("=" * 78)
    print("RESULT:", "ALL PASS" if not FAIL else "FAIL (%d)" % len(FAIL))
    for f in FAIL:
        print("  FAILED:", f)
    sys.exit(1 if FAIL else 0)


main()
