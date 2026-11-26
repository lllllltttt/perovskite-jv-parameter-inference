# -*- coding: utf-8 -*-
"""Split the finished S3a.svg into its six panels S3a_01 ... S3a_06.

Source is the delivered S3a.svg itself (already cropped, captions removed) -
nothing is redrawn, no font or style is touched, and the other Figure S3
blocks are not involved.

Each output carries one <g id="axes_N"> subtree plus the defs it references
(clipPath of the panel, marker definitions), so the vector content is exact.
The a5 panel keeps its nested inset axes (axes_6 is a child of axes_5).

Order: left to right, top to bottom -> axes_1, axes_2, axes_3, axes_4,
axes_5, axes_7  (axes_6 is the inset inside axes_5, not a panel).
"""
import io
import json
import os
import re
import subprocess
import sys

from lxml import etree
import numpy as np
from PIL import Image

if (getattr(sys.stdout, "encoding", "") or "").lower().replace("-", "") != "utf8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

CS = "{http://www.w3.org/2000/svg}"
XL = "{http://www.w3.org/1999/xlink}"
SVGNS = "http://www.w3.org/2000/svg"
XLNS = "http://www.w3.org/1999/xlink"

SRC = "out/svg/S3a.svg"
OUT = "out_panels"
PAD = 2.5
PX_PER_PT = 96.0 / 72.0
PY = sys.executable

PANELS = ["axes_1", "axes_2", "axes_3", "axes_4", "axes_5", "axes_7"]


def ref_ids(el):
    ids = set()
    for e in el.iter():
        if not isinstance(e.tag, str):
            continue
        for a in (XL + "href", "href"):
            v = e.get(a) or ""
            if v.startswith("#"):
                ids.add(v[1:])
        for a in ("clip-path", "fill", "stroke", "filter", "mask", "style"):
            m = re.search(r"url\(#([^)]+)\)", e.get(a) or "")
            if m:
                ids.add(m.group(1))
    return ids


def defined_ids(el):
    return {e.get("id") for e in el.iter() if isinstance(e.tag, str) and e.get("id")}


def external_defs(piece, idmap, order):
    have = defined_ids(piece)
    need = ref_ids(piece) - have
    out, seen = [], set()
    while need:
        nid = sorted(need, key=lambda i: order[i])[0]
        need.discard(nid)
        if nid in seen:
            continue
        seen.add(nid)
        out.append(etree.fromstring(etree.tostring(idmap[nid])))
        need |= (ref_ids(idmap[nid]) - have - {d.get("id") for d in out})
    return out


def build(groups, win, idmap, order, path):
    root = etree.Element(CS + "svg", nsmap={None: SVGNS, "xlink": XLNS})
    root.set("width", "%.4f" % (win[2] * PX_PER_PT))
    root.set("height", "%.4f" % (win[3] * PX_PER_PT))
    root.set("viewBox", "%.4f %.4f %.4f %.4f" % win)
    root.set("stroke-linejoin", "round")
    root.set("overflow", "hidden")
    body = etree.SubElement(root, CS + "g")
    need = set()
    for g in groups:
        body.append(g)
        need |= ref_ids(g)
    extra = external_defs(body, idmap, order)
    if extra:
        d = etree.Element(CS + "defs")
        for e in extra:
            d.append(e)
        root.insert(0, d)
    with open(path, "wb") as f:
        f.write(etree.tostring(root, xml_declaration=True, encoding="utf-8"))
    return path


def render(svg, png, dpi):
    for _ in range(3):
        r = subprocess.run([PY, "scripts/render_svg_px.py", svg, png,
                            "--dpi", str(dpi)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if r.returncode == 0 and os.path.exists(png):
            return png
    raise RuntimeError("render failed " + svg)


def ink_bbox(png, win, dpi, thr=8):
    a = np.asarray(Image.open(png).convert("L")).astype(int)
    m = (255 - a) > thr
    rows = np.where(m.any(axis=1))[0]
    cols = np.where(m.any(axis=0))[0]
    s = dpi / 72.0
    return (win[0] + cols[0] / s, win[1] + rows[0] / s,
            win[0] + (cols[-1] + 1) / s, win[1] + (rows[-1] + 1) / s)


def plot_box(a):
    """Frame rectangle from the 0.8-pt dark spines of one axes group."""
    xs, ys = [], []
    for c in a:
        cid = c.get("id") or ""
        if not cid.startswith("patch_"):
            continue
        p = c.find(".//" + CS + "path")
        st = (p.get("style") or "") if p is not None else ""
        if "stroke" in st and ("0.8" in st or "#22262b" in st.lower()
                               or "#1a1a1a" in st.lower()):
            n = [float(v) for v in re.findall(r"-?\d+\.?\d*", p.get("d"))]
            xs += n[0::2]
            ys += n[1::2]
    return min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)


def main():
    for d in ("svg", "png", "work"):
        os.makedirs(os.path.join(OUT, d), exist_ok=True)

    src = etree.parse(SRC).getroot()
    idmap = {e.get("id"): e for e in src.iter() if e.get("id")}
    order = {i: k for k, i in enumerate(idmap)}

    # ---- pass 1: plot box and ink margins of each panel ----------------
    geo, boxes = {}, {}
    for aid in PANELS:
        a = etree.fromstring(etree.tostring(idmap[aid]))
        boxes[aid] = plot_box(a)
        x, y, w, h = boxes[aid]
        win = (x - 60, y - 60, w + 120, h + 120)
        p = build([etree.fromstring(etree.tostring(a))], win, idmap, order,
                  os.path.join(OUT, "work", aid + "_probe.svg"))
        render(p, os.path.join(OUT, "work", aid + "_probe.png"), 300)
        ib = ink_bbox(os.path.join(OUT, "work", aid + "_probe.png"), win, 300)
        geo[aid] = (x - ib[0], y - ib[1], ib[2] - (x + w), ib[3] - (y + h))
        print("  %-8s plot %.3f x %.3f at (%.2f, %.2f)  margins L%.2f T%.2f R%.2f B%.2f"
              % (aid, w, h, x, y, *geo[aid]))

    sizes = {(round(boxes[a][2], 4), round(boxes[a][3], 4)) for a in PANELS}
    assert len(sizes) == 1, sizes
    W0, H0 = sizes.pop()

    L = max(g[0] for g in geo.values())
    T = max(g[1] for g in geo.values())
    R = max(g[2] for g in geo.values())
    B = max(g[3] for g in geo.values())
    CW = W0 + L + R + 2 * PAD
    CH = H0 + T + B + 2 * PAD
    print("\n  uniform margins L %.2f T %.2f R %.2f B %.2f (+%.1f pad)"
          % (L, T, R, B, PAD))
    print("  plot %.3f x %.3f pt -> canvas %.3f x %.3f pt" % (W0, H0, CW, CH))

    # ---- pass 2: the six deliverables ---------------------------------
    meta = []
    for i, aid in enumerate(PANELS, start=1):
        name = "S3a_%02d" % i
        a = etree.fromstring(etree.tostring(idmap[aid]))
        x, y, w, h = boxes[aid]
        win = (round(x - L - PAD, 4), round(y - T - PAD, 4),
               round(CW, 4), round(CH, 4))
        svg = build([a], win, idmap, order, os.path.join(OUT, "svg", name + ".svg"))
        png = os.path.join(OUT, "png", name + "_600dpi.png")
        render(svg, png, 600)
        px = Image.open(png).size
        meta.append(dict(file=name, axes=aid, svg=svg, png=png, win=win,
                         px=list(px)))
        print("  %-8s <- %-7s %8.3f x %8.3f pt  %s px"
              % (name, aid, win[2], win[3], "%dx%d" % px))

    json.dump(dict(pieces=meta, panel_ids=PANELS,
                   plot=[W0, H0], canvas=[CW, CH],
                   margins=dict(L=L, T=T, R=R, B=B, pad=PAD)),
              open(os.path.join(OUT, "work", "meta.json"), "w", encoding="utf-8"),
              indent=1)


if __name__ == "__main__":
    main()
