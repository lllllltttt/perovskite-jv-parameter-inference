# -*- coding: utf-8 -*-
"""Figure S7 - new legends for the blue row (a) and the orange row (d).

Basis: the approved standalone panels
  20261116_figs7_split/out/svg/S7a.svg  (a_mu,  blue  nearest-neighbour curve)
  20261116_figs7_split/out/svg/S7b.svg  (r_mu,  orange nearest-neighbour curve)
which are the first panel of each row in the layout the supervisor sent
(top row a_mu / a_tau / a_D in blue, bottom row r_mu / r_tau / r_D in orange).

Only change: the legend of the first panel of each row.
  * S7a: the old framed two-row legend (white patch, starting left of x = 1)
    is removed and replaced by a frame-less, transparent legend in the
    lower-right corner, entirely to the right of the x = 1 reference line.
  * S7b: no legend before; the same legend is added there (orange handle).
Everything else - both ECDF curves, the x = 1 dotted line, the frame, tick
marks, tick labels, canvas and axes geometry - is left untouched and is
verified byte-for-byte at the end.

Legend geometry (pt, in the panel coordinate system):
  right edge = axes right - 1.6
  text       = 7.0 pt Arial Regular, converted to outline paths
  handle     = 7.0 pt long, 3.2 pt gap to the text (shortened so that the
               whole block clears x = 1 by > 4.5 pt; the font is NOT shrunk)
  rows       = same y as the original legend (0.80297 / 0.90303 of the axes
               height), random pairs above nearest-neighbour pairs
  frame      = none: no rect, no white patch, transparent background
"""
import io
import os
import re
import subprocess
import sys

from lxml import etree
import numpy as np
from matplotlib import font_manager
from matplotlib.font_manager import FontProperties
from matplotlib.path import Path as MPath
from matplotlib.textpath import TextToPath, TextPath

if (getattr(sys.stdout, "encoding", "") or "").lower().replace("-", "") != "utf8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

CS = "{http://www.w3.org/2000/svg}"
XL = "{http://www.w3.org/1999/xlink}"
SVGNS = "http://www.w3.org/2000/svg"
XLNS = "http://www.w3.org/1999/xlink"

BASE = r"E:\project\work1"
SRC = os.path.join(BASE, "20261116_figs7_split", "out", "svg")
ROOT = os.path.join(BASE, "20261119_si_s7_legends")
OUT = os.path.join(ROOT, "out")
WORK = os.path.join(ROOT, "work")
PY = sys.executable

GREY = "#9a9a9a"
BLUE = "#0072b2"
ORANGE = "#d55e00"
INK = "#1a1a1a"

FS = 7.0                 # legend text, same as the original legend (ticks 7.5)
TXT = [("random pairs", GREY, 1.3),
       ("nearest-neighbour pairs", None, 1.6)]   # None -> panel colour
ROW_DY = (79.087631, 88.989349)   # original legend rows, pt below the axes top
TXT_DY = 2.45            # baseline offset below/above the handle line
HANDLE = 5.5             # handle length, pt (shortened, font NOT shrunk)
GAP = 2.8                # handle -> text gap, pt
RIGHT_INSET = 1.4        # text right edge -> axes frame, pt
MIN_CLEAR = 6.5          # required gap between x = 1 and the legend, pt
PANELS = [("S7a", BLUE), ("S7b", ORANGE)]

TTP = TextToPath()


def path_to_d(p):
    v, c = p.vertices, p.codes
    if c is None:
        c = np.full(len(v), MPath.LINETO)
        c[0] = MPath.MOVETO
    out, i = [], 0
    while i < len(v):
        code = c[i]
        if code == MPath.MOVETO:
            out.append("M %.4f %.4f" % (v[i][0], v[i][1])); i += 1
        elif code == MPath.LINETO:
            out.append("L %.4f %.4f" % (v[i][0], v[i][1])); i += 1
        elif code == MPath.CURVE3:
            pts = [v[i]]; i += 1
            while i < len(v) and c[i] == MPath.CURVE3 and len(pts) % 2:
                pts.append(v[i]); i += 1
            out.append("Q " + " ".join("%.4f %.4f" % (q[0], q[1]) for q in pts))
        elif code == MPath.CURVE4:
            pts = [v[i]]; i += 1
            while i < len(v) and c[i] == MPath.CURVE4 and len(pts) % 3:
                pts.append(v[i]); i += 1
            out.append("C " + " ".join("%.4f %.4f" % (q[0], q[1]) for q in pts))
        elif code == MPath.CLOSEPOLY:
            out.append("Z"); i += 1
        else:
            i += 1
    return " ".join(out)


def text_width(s, size=FS, family="Arial"):
    prop = FontProperties(family=family, size=size)
    w, h, d = TTP.get_text_width_height_descent(s, prop, False)
    return w, h, d


def text_group(s, x, baseline, fill=INK, size=FS):
    prop = FontProperties(family="Arial", size=size)
    g = etree.Element(CS + "g")
    g.set("class", "glyphs")
    g.set("transform", "translate(%.4f %.4f) scale(1 -1)" % (x, baseline))
    p = etree.SubElement(g, CS + "path")
    p.set("d", path_to_d(TextPath((0, 0), s, size=size, prop=prop)))
    p.set("fill", fill)
    return g


def find_axes(svg):
    """The panel has exactly one axes group; its first child is the axes
    background patch, whose path is the plot rectangle."""
    ax = [g for g in svg.iter(CS + "g")
          if re.match(r"^axes_\d+$", g.get("id") or "")]
    if len(ax) != 1:
        raise RuntimeError("expected one axes group, got %d" % len(ax))
    ax = ax[0]
    d = ax.find(CS + "g").find(CS + "path").get("d")
    v = [float(x) for x in re.findall(r"-?\d+\.?\d*", d)]
    xs, ys = v[0::2], v[1::2]
    return ax, (min(xs), min(ys), max(xs), max(ys))


def find_x1(svg):
    for p in svg.iter(CS + "path"):
        st = p.get("style") or ""
        if "#555555" in st:
            v = [float(x) for x in re.findall(r"-?\d+\.?\d*", p.get("d"))]
            return v[0]
    raise RuntimeError("x = 1 line not found")


def drop_legends(svg):
    n = 0
    for g in list(svg.iter(CS + "g")):
        if (g.get("id") or "").startswith("legend"):
            g.getparent().remove(g)
            n += 1
    return n


def build_legend(colour, box, x1):
    """Return (group, bbox, geometry dict)."""
    x0, ytop, x1_ax, ybot = box
    h = ybot - ytop
    w_text, _hh, _dd = text_width("nearest-neighbour pairs")
    text_x = x1_ax - RIGHT_INSET - w_text
    hx2 = text_x - GAP
    hx1 = hx2 - HANDLE
    rows = [ytop + d for d in ROW_DY]

    g = etree.Element(CS + "g")
    g.set("id", "legend_1")
    for k, (label, col, lw) in enumerate(TXT):
        col = col or colour
        gl = etree.SubElement(g, CS + "g")
        gl.set("id", "legend_line_%d" % (k + 1))
        p = etree.SubElement(gl, CS + "path")
        p.set("d", "M %.4f %.4f L %.4f %.4f" % (hx1, rows[k], hx2, rows[k]))
        p.set("style", "fill: none; stroke: %s; stroke-width: %.1f; "
                       "stroke-linecap: square" % (col, lw))
        gt = etree.SubElement(g, CS + "g")
        gt.set("id", "legend_text_%d" % (k + 1))
        gt.append(text_group(label, text_x, rows[k] + TXT_DY))

    # bbox of everything the legend draws (ink extents, not advance box)
    inks = []
    for s, _c, _l in TXT:
        prop = FontProperties(family="Arial", size=FS)
        bb = TextPath((0, 0), s, size=FS, prop=prop).get_extents()
        inks.append(bb.x1)
    text_right = text_x + max(inks)
    text_top = rows[0] + TXT_DY - text_width("random pairs")[1]   # ascender
    text_bot = rows[1] + TXT_DY + text_width("random pairs")[2]   # descender
    bbox = (hx1, text_top, text_right, text_bot)
    geo = dict(hx1=hx1, hx2=hx2, text_x=text_x, text_w=w_text,
               rows=rows, clear=hx1 - x1, bbox=bbox)
    return g, bbox, geo


def render(svg, png, dpi):
    for _ in range(3):
        r = subprocess.run([PY, os.path.join(ROOT, "scripts", "render_svg_px.py"),
                            svg, png, "--dpi", str(dpi)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if r.returncode == 0 and os.path.exists(png):
            return png
    raise RuntimeError("render failed " + svg)


def main():
    for d in (OUT, WORK):
        os.makedirs(d, exist_ok=True)

    # ---- font: Arial must really be used, no silent DejaVu fallback ------
    fp = font_manager.findfont(FontProperties(family="Arial"))
    print("Arial resolves to:", fp)
    assert "arial" in os.path.basename(fp).lower()
    w_ar = text_width("nearest-neighbour pairs")[0]
    w_dv = text_width("nearest-neighbour pairs", family="DejaVu Sans")[0]
    print("  width @7pt: Arial %.3f pt, DejaVu Sans %.3f pt" % (w_ar, w_dv))
    assert abs(w_ar - 73.928) < 0.05 and abs(w_ar - w_dv) > 2.0

    meta = {}
    for name, colour in PANELS:
        src = os.path.join(SRC, name + ".svg")
        svg = etree.parse(src).getroot()
        ax, box = find_axes(svg)
        x1 = find_x1(svg)
        n_old = drop_legends(svg)
        g, bbox, geo = build_legend(colour, box, x1)
        ax.append(g)

        stem = os.path.join(OUT, name)
        etree.ElementTree(svg).write(stem + ".svg", xml_declaration=True,
                                     encoding="utf-8")

        # same tree without the new legend -> reference for the pixel checks
        svg_ref = etree.fromstring(etree.tostring(svg))
        drop_legends(svg_ref)
        ref = os.path.join(WORK, name + "_nolegend.svg")
        etree.ElementTree(svg_ref).write(ref, xml_declaration=True, encoding="utf-8")

        render(stem + ".svg", stem + "_600dpi.png", 600)
        render(ref, os.path.join(WORK, name + "_nolegend.png"), 600)
        meta[name] = dict(colour=colour, box=box, x1=x1, old_legends=n_old,
                          **{k: (list(v) if isinstance(v, (tuple, list)) else v)
                             for k, v in geo.items()})
        print("  %s: old legends removed %d; handle %.2f-%.2f  text x %.2f "
              "(w %.2f)  clear of x=1: %.2f pt"
              % (name, n_old, geo["hx1"], geo["hx2"], geo["text_x"],
                 geo["text_w"], geo["clear"]))
        print("     legend bbox %.2f %.2f %.2f %.2f (right frame %.2f, "
              "bottom frame %.2f)" % (bbox + (box[2], box[3])))
        assert geo["clear"] >= MIN_CLEAR
        assert bbox[0] > x1 and bbox[2] < box[2] - 1.0
        assert bbox[3] < box[3] - 2.0

    # keep the numbers for the verification script
    import json
    json.dump(meta, open(os.path.join(WORK, "legend_meta.json"), "w"),
              indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
