# -*- coding: utf-8 -*-
"""S3b, unadjusted version with only three texts removed.

Source: the original FigureS3b.svg (tick numbers 7.5 pt, legend in place).
Removed: the x axis title "Voltage (V)", the y axis title "RMSE across 45
samples (mA cm-2)" and the in-plot note "noise floor = 0.21 mA cm-2".
Everything else is untouched - curves, colours, dashes, reference lines,
frame, axis ranges, tick positions and tick numbers, the three-entry legend.

The only addition is explicit font-family / font-size attributes on the
surviving <text> nodes (same values that are already in their style=), so
PowerPoint cannot fall back to a default size.
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

SRC = r"E:\project\work1\20261024_final_figures_svg\si\FigureS3b.svg"
OUT = "out_v3"
PAD = 2.5
CROP = os.environ.get("S3B_CROP", "0") == "1"   # 0 = keep the source canvas
PX_PER_PT = 96.0 / 72.0
PY = sys.executable


def txt(e):
    return re.sub(r"\s+", " ", "".join(e.itertext()).replace("\xa0", " ")).strip()


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
    xs, ys = [], []
    for c in a:
        cid = c.get("id") or ""
        if not cid.startswith("patch_"):
            continue
        p = c.find(".//" + CS + "path")
        st = (p.get("style") or "") if p is not None else ""
        if "stroke" in st and ("stroke-width: 0.8" in st or "#22262b" in st.lower()):
            n = [float(v) for v in re.findall(r"-?\d+\.?\d*", p.get("d"))]
            xs += n[0::2]
            ys += n[1::2]
    return min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)


def cut(fig):
    """Delete exactly: the two axis titles and the in-plot note."""
    removed = []
    ax = fig.find(".//" + CS + "g[@id='axes_1']")
    for c in list(ax):
        if not (c.get("id") or "").startswith("matplotlib.axis_"):
            continue
        for g in list(c):
            if g.tag != CS + "g":
                continue
            if (g.get("id") or "").startswith(("xtick_", "ytick_")):
                continue
            if next(g.iter(CS + "text"), None) is not None:
                removed.append((g.get("id"), txt(g)))
                c.remove(g)
    for c in list(ax):
        if c.tag == CS + "g" and re.match(r"^text_\d+$", c.get("id") or ""):
            removed.append((c.get("id"), txt(c)))
            ax.remove(c)
    return removed


def font_attrs(fig):
    n = 0
    for t in fig.iter(CS + "text"):
        st = t.get("style") or ""
        m = re.search(r"([\d.]+)px", st)
        t.set("font-family", "Arial")
        t.set("font-size", "%g" % (float(m.group(1)) if m else 10.0))
        n += 1
    return n


def main():
    for d in ("svg", "png", "work"):
        os.makedirs(os.path.join(OUT, d), exist_ok=True)

    src = etree.parse(SRC).getroot()
    idmap = {e.get("id"): e for e in src.iter() if e.get("id")}
    order = {i: k for k, i in enumerate(idmap)}
    fig = etree.fromstring(etree.tostring(src.find(".//" + CS + "g[@id='figure_1']")))

    removed = cut(fig)
    n_fonts = font_attrs(fig)
    box = plot_box(fig.find(".//" + CS + "g[@id='axes_1']"))
    print("  removed:", removed)
    print("  text nodes kept: %d (with explicit font attributes)" % n_fonts)

    if CROP:
        win0 = (box[0] - 60, box[1] - 60, box[2] + 120, box[3] + 120)
        p = build([etree.fromstring(etree.tostring(fig))], win0, idmap, order,
                  os.path.join(OUT, "work", "probe.svg"))
        render(p, os.path.join(OUT, "work", "probe.png"), 300)
        ib = ink_bbox(os.path.join(OUT, "work", "probe.png"), win0, 300)
        win = (round(ib[0] - PAD, 4), round(ib[1] - PAD, 4),
               round(ib[2] - ib[0] + 2 * PAD, 4), round(ib[3] - ib[1] + 2 * PAD, 4))
    else:
        vb = [float(v) for v in src.get("viewBox").split()]
        win = (round(vb[0], 4), round(vb[1], 4), round(vb[2], 4), round(vb[3], 4))

    svg = build([fig], win, idmap, order, os.path.join(OUT, "svg", "S3b_final.svg"))
    png = os.path.join(OUT, "png", "S3b_final_600dpi.png")
    render(svg, png, 600)
    print("  plot %.3f x %.3f at (%.2f, %.2f)" % (box[2], box[3], box[0], box[1]))
    print("  canvas %.3f x %.3f pt  %dx%d px"
          % (win[2], win[3], *Image.open(png).size))

    json.dump(dict(win=list(win), plot=list(box), removed=removed),
              open(os.path.join(OUT, "work", "meta.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
