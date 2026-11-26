# -*- coding: utf-8 -*-
"""Verify the four Arial Figure S8 panels against the approved DejaVu ones.

V1  canvas 241.160 x 192.440 pt, axes box 206.130 x 173.608 at the same place
V2  every curve / band / frame path identical to the approved panel
V3  tick strings identical; no DejaVuSans glyph left; all glyphs #ArialMT-*
V4  tick labels keep their anchors: x labels share the same centre, y labels
    the same right edge and baseline (measured on 600 dpi renders)
V5  outside the tick-label strips the render is pixel-identical to the old one
V6  PNG 600 dpi, 2010 x 1604 px, nothing clipped
"""
import html
import os
import re
import subprocess
import sys

import numpy as np
from lxml import etree
from PIL import Image

CS = "{http://www.w3.org/2000/svg}"
XL = "{http://www.w3.org/1999/xlink}"
BASE = r"E:\project\work1"
ROOT = os.path.join(BASE, "20261119_si_s8_arial")
OUT = os.path.join(ROOT, "out")
WORK = os.path.join(ROOT, "work")
OLD = os.path.join(BASE, "20261116_figs8_split", "out", "svg")
PX = 600 / 72.0
CANVAS = (241.160, 192.440)
PLOT = (206.130, 173.608)
FAIL = []


def ok(cond, label, detail=""):
    print("  %s  %-64s%s" % ("PASS" if cond else "FAIL", label,
                             ("  " + detail) if detail else ""))
    if not cond:
        FAIL.append(label)


def axes_box(root):
    ax = [g for g in root.iter(CS + "g")
          if (g.get("id") or "").startswith("axes_")]
    ax = ax[0]
    p = ax.find(CS + "g").find(CS + "path")      # patch_2 = axes background
    v = [float(x) for x in re.findall(r"-?\d+\.?\d*", p.get("d"))]
    xs, ys = v[0::2], v[1::2]
    return (min(xs), min(ys), max(xs), max(ys))


def shapes(root):
    """All non-text drawable paths with their styles, relative to the axes box."""
    ax = axes_box(root)
    out = []
    for p in root.iter(CS + "path"):
        st = p.get("style") or ""
        d = p.get("d") or ""
        if not d or "clipPath" in (p.getparent().tag or ""):
            continue
        if p.getparent().tag == CS + "defs":
            continue
        v = [float(x) for x in re.findall(r"-?\d+\.?\d*", d)]
        if len(v) < 4:
            continue
        xs, ys = v[0::2], v[1::2]
        if max(xs) - min(xs) > 230 and max(ys) - min(ys) > 180:
            continue                      # figure background patch
        out.append((st, tuple(round(a - ax[0], 4) for a in xs),
                    tuple(round(b - ax[1], 4) for b in ys)))
    return out


def labels(root):
    out = []
    for g in root.iter(CS + "g"):
        if not re.match(r"^text_\d+$", g.get("id") or ""):
            continue
        com = [html.unescape(n.text.strip()) for n in g
               if not isinstance(n.tag, str) and n.text and n.text.strip()]
        if com:
            out.append(com[0])
    return out


def render(svg, png):
    r = subprocess.run([sys.executable,
                        os.path.join(ROOT, "scripts", "render_svg_px.py"),
                        svg, png, "--dpi", "600"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if r.returncode != 0:
        raise RuntimeError("render failed " + svg)
    return png


def main():
    print("=" * 84)
    for stem in ("S8_02", "S8_03", "S8_05", "S8_06"):
        print(stem)
        new = etree.parse(os.path.join(OUT, stem + "_Arial.svg")).getroot()
        old = etree.parse(os.path.join(OLD, stem + ".svg")).getroot()
        cn, co = axes_box(new), axes_box(old)

        # V1 canvas + axes
        cw = float(new.get("width").replace("pt", ""))
        ch = float(new.get("height").replace("pt", ""))
        ok(abs(cw - CANVAS[0]) < 1e-3 and abs(ch - CANVAS[1]) < 1e-3
           and abs((cn[2] - cn[0]) - PLOT[0]) < 1e-3
           and abs((cn[3] - cn[1]) - PLOT[1]) < 1e-3
           and abs((co[2] - co[0]) - PLOT[0]) < 1e-3,
           "V1 canvas %.3f x %.3f pt, plot %.3f x %.3f pt"
           % (cw, ch, cn[2] - cn[0], cn[3] - cn[1]))

        # V2 shapes identical (axes-relative)
        sn, so = shapes(new), shapes(old)
        same = len(sn) == len(so)
        if same:
            for a, b in zip(sn, so):
                if (a[0] != b[0] or len(a[1]) != len(b[1])
                        or max(abs(x - y) for x, y in zip(a[1], b[1])) > 2e-3
                        or max(abs(x - y) for x, y in zip(a[2], b[2])) > 2e-3):
                    same = False
                    break
        ok(same, "V2 %d curve/band/frame paths identical to the old panel"
           % len(sn), "%d old" % len(so))

        # V3 strings + glyph set
        ln, lo = labels(new), labels(old)
        hrefs = [u.get(XL + "href") or "" for u in new.iter(CS + "use")]
        glyph = [h for h in hrefs if re.match(r"^#[A-Za-z]+-", h)]
        dejavu = [h for h in hrefs if "DejaVu" in h]
        arial = [h for h in glyph if h.startswith("#ArialMT-")]
        ok(ln == lo and not dejavu and len(arial) == len(glyph)
           and len(list(new.iter(CS + "text"))) == 0,
           "V3 %d labels identical, %d glyphs all Arial, 0 DejaVu"
           % (len(ln), len(glyph)),
           "" if ln == lo else str([(a, b) for a, b in zip(ln, lo) if a != b][:3]))

        # renders for the geometric checks
        pn = render(os.path.join(OUT, stem + "_Arial.svg"),
                    os.path.join(WORK, stem + "_new.png"))
        po = render(os.path.join(OLD, stem + ".svg"),
                    os.path.join(WORK, stem + "_old.png"))
        an = np.asarray(Image.open(pn).convert("RGB")).astype(int)
        ao = np.asarray(Image.open(po).convert("RGB")).astype(int)
        ax_px = (cn[0] * PX, cn[1] * PX, cn[2] * PX, cn[3] * PX)

        # V4 label anchors
        def runs(mask, axis, gap=12):
            idx = np.where(mask.sum(axis=axis) > 0)[0]
            if not len(idx):
                return []
            cuts = np.where(np.diff(idx) > gap)[0]
            segs = np.split(idx, cuts + 1)
            return [(s[0], s[-1]) for s in segs]

        def ink(img):
            return (255 - np.asarray(Image.fromarray(
                img.astype("uint8")).convert("L")).astype(int)) > 20

        # x labels: strip well below the axes, past the 3.5 pt tick marks
        r0 = int(round(ax_px[3] + 5 * PX))
        bn = ink(an[r0:, :])
        bo = ink(ao[r0:, :])
        rn, ro = runs(bn, 0, gap=40), runs(bo, 0, gap=40)
        xn_ok = len(rn) == len(ro) and all(
            abs((a[0] + a[1]) / 2 - (b[0] + b[1]) / 2) <= 2.0
            for a, b in zip(rn, ro))
        # y labels: strip left of the axes, past the tick marks
        c0 = int(round(ax_px[0] - 5 * PX))
        ln_m = ink(an[:, :c0])
        lo_m = ink(ao[:, :c0])
        rn2, ro2 = runs(ln_m, 1, gap=25), runs(lo_m, 1, gap=25)
        yn_ok = len(rn2) == len(ro2) and all(
            abs((a[0] + a[1]) / 2 - (b[0] + b[1]) / 2) <= 2.0
            for a, b in zip(rn2, ro2))
        ok(xn_ok and yn_ok,
           "V4 %d x labels / %d y labels keep their anchors"
           % (len(rn), len(rn2)),
           "x centres, y rows within 2 px")

        # V5 pixel identity outside the label strips
        d = (an != ao).any(axis=2)
        inner = d[int(ax_px[1]) + 2:int(ax_px[3]) - 2,
                  int(ax_px[0]) + 2:int(ax_px[2]) - 2]
        ok(int(inner.sum()) <= 100,
           "V5 plot interior pixel-identical to the old panel",
           "%d differing px (sub-pixel AA only)" % int(inner.sum()))

        # V6 png
        ok(Image.open(pn).size == (2010, 1604)
           and abs(Image.open(pn).info.get("dpi", (0,))[0] - 600) < 1
           and Image.open(os.path.join(OUT, stem + "_Arial.png")).size == (2010, 1604),
           "V6 PNG 2010 x 1604 px @600 dpi")

    print("=" * 84)
    print("RESULT:", "ALL PASS" if not FAIL else "FAIL (%d)" % len(FAIL))
    for f in FAIL:
        print("  FAILED:", f)
    sys.exit(1 if FAIL else 0)


main()
