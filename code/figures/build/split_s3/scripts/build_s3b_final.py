# -*- coding: utf-8 -*-
"""S3b, final version.

From the original FigureS3b.svg (the file that still carries the legend):

  * tick numbers 7.5 -> 11.25 pt (x1.5), same Arial, normal weight, baselines
    moved with the font metric so the bigger digits clear the tick marks;
  * the three-entry legend is KEPT in place (line samples + labels);
  * axis titles and the in-plot "noise floor = ..." note are still removed;
  * every remaining <text> is converted to outline paths (no font dependency
    in PowerPoint, no glyph squeezing) - nothing is rasterised;
  * curves, colours, line widths/dashes, reference lines, frame, ranges and
    tick positions are untouched.
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
from matplotlib.font_manager import FontProperties
from matplotlib.path import Path as MPath
from matplotlib.textpath import TextToPath, TextPath

if (getattr(sys.stdout, "encoding", "") or "").lower().replace("-", "") != "utf8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

CS = "{http://www.w3.org/2000/svg}"
XL = "{http://www.w3.org/1999/xlink}"
SVGNS = "http://www.w3.org/2000/svg"
XLNS = "http://www.w3.org/1999/xlink"

SRC = r"E:\project\work1\20261024_final_figures_svg\si\FigureS3b.svg"
OUT = "out_final"
PAD = 2.5
PX_PER_PT = 96.0 / 72.0
PY = sys.executable

FS_OLD = 7.5
FS_NEW = 11.25          # x1.5
TICK_LEN = 3.0
TICK_PAD = 3.5

TTP = TextToPath()
CONVERT = True          # False = keep <text> (used by the verifier as a twin)


# ---------------------------------------------------------------- helpers --
def txt(e):
    return "".join(e.itertext()).strip()


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


def style_prop(el, key):
    m = re.search(key + r":\s*([^;]+)", el.get("style") or "")
    return m.group(1).strip() if m else None


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


# ------------------------------------------------------ text -> outline ----
def path_to_d(p):
    v, c = p.vertices, p.codes
    if c is None:
        c = np.full(len(v), MPath.LINETO)
        c[0] = MPath.MOVETO
    out, i = [], 0
    while i < len(v):
        code = c[i]
        if code == MPath.MOVETO:
            out.append("M %.4f %.4f" % (v[i][0], v[i][1]))
            i += 1
        elif code == MPath.LINETO:
            out.append("L %.4f %.4f" % (v[i][0], v[i][1]))
            i += 1
        elif code == MPath.CURVE3:
            pts = [v[i]]
            i += 1
            while i < len(v) and c[i] == MPath.CURVE3 and len(pts) % 2:
                pts.append(v[i])
                i += 1
            out.append("Q " + " ".join("%.4f %.4f" % (p[0], p[1]) for p in pts))
        elif code == MPath.CURVE4:
            pts = [v[i]]
            i += 1
            while i < len(v) and c[i] == MPath.CURVE4 and len(pts) % 3:
                pts.append(v[i])
                i += 1
            out.append("C " + " ".join("%.4f %.4f" % (p[0], p[1]) for p in pts))
        elif code == MPath.CLOSEPOLY:
            out.append("Z")
            i += 1
        else:
            i += 1
    return " ".join(out)


def text_to_group(t, size=None, fill=None, anchor=None, x=None, y=None):
    s = "".join(t.itertext())
    fs = size or float(re.search(r"([\d.]+)px",
                                 t.get("style") or "").group(1))
    prop = FontProperties(family="Arial", size=fs)
    w, _h, _d = TTP.get_text_width_height_descent(s, prop, False)
    an = anchor or t.get("text-anchor") or "start"
    px = float(t.get("x")) if x is None else x
    py = float(t.get("y")) if y is None else y
    if an == "middle":
        px -= w / 2.0
    elif an == "end":
        px -= w
    col = fill or style_prop(t, "fill") or "#000000"
    g = etree.Element(CS + "g")
    g.set("class", "glyphs")
    g.set("transform", "translate(%.4f %.4f) scale(1 -1)" % (px, py))
    p = etree.SubElement(g, CS + "path")
    # TextPath gives the outline in points at the requested size;
    # TextToPath.get_text_path would return 1/10 glyph units.
    tp = TextPath((0, 0), s, size=fs, prop=prop)
    p.set("d", path_to_d(tp))
    p.set("fill", col)
    return g


# ------------------------------------------------------------------ main ---
def make_fig():
    for d in ("svg", "png", "work"):
        os.makedirs(os.path.join(OUT, d), exist_ok=True)

    src = etree.parse(SRC).getroot()
    idmap = {e.get("id"): e for e in src.iter() if e.get("id")}
    order = {i: k for k, i in enumerate(idmap)}
    fig = etree.fromstring(etree.tostring(src.find(".//" + CS + "g[@id='figure_1']")))
    ax = fig.find(".//" + CS + "g[@id='axes_1']")
    box = plot_box(ax)
    bottom = box[1] + box[3]

    removed = []
    # axis titles --------------------------------------------------------
    for c in list(ax):
        if not (c.get("id") or "").startswith("matplotlib.axis_"):
            continue
        for g in list(c):
            if g.tag != CS + "g":
                continue
            if (g.get("id") or "").startswith(("xtick_", "ytick_")):
                continue
            if next(g.iter(CS + "text"), None) is not None:
                removed.append(txt(g))
                c.remove(g)
    # in-plot note (direct text child of the axes); the legend is an id="legend_*"
    for c in list(ax):
        cid = c.get("id") or ""
        if c.tag == CS + "g" and re.match(r"^text_\d+$", cid):
            removed.append(txt(c))
            ax.remove(c)
    print("  removed:", removed)

    # tick numbers x1.5 ---------------------------------------------------
    k = FS_NEW / FS_OLD
    n_tick = 0
    for g in ax.iter(CS + "g"):
        gid = g.get("id") or ""
        if not gid.startswith(("xtick_", "ytick_")):
            continue
        t = next(g.iter(CS + "text"), None)
        u = next(g.iter(CS + "use"), None)
        if t is None or u is None:
            continue
        if gid.startswith("xtick_"):
            off = float(t.get("y")) - bottom - (TICK_LEN + TICK_PAD)
            t.set("y", "%.4f" % (bottom + TICK_LEN + TICK_PAD + off * k))
        else:
            ty = float(u.get("y"))
            t.set("y", "%.4f" % (ty + (float(t.get("y")) - ty) * k))
        t.set("style", re.sub(r"([\d.]+)px", "%gpx" % FS_NEW, t.get("style") or ""))
        n_tick += 1
    print("  tick labels rescaled:", n_tick)

    # every remaining text -> outline path --------------------------------
    texts = list(fig.iter(CS + "text"))
    if not CONVERT:
        return fig, box, removed, n_tick, texts
    for t in texts:
        g = text_to_group(t)
        p = t.getparent()
        p.replace(t, g)
    print("  texts converted to outlines:", len(texts))

    return fig, box, removed, n_tick, texts


def finish(fig, box, idmap, order):
    # crop -----------------------------------------------------------------
    win0 = (box[0] - 60, box[1] - 60, box[2] + 120, box[3] + 120)
    p = build([etree.fromstring(etree.tostring(fig))], win0, idmap, order,
              os.path.join(OUT, "work", "probe.svg"))
    render(p, os.path.join(OUT, "work", "probe.png"), 300)
    ib = ink_bbox(os.path.join(OUT, "work", "probe.png"), win0, 300)
    win = (round(ib[0] - PAD, 4), round(ib[1] - PAD, 4),
           round(ib[2] - ib[0] + 2 * PAD, 4), round(ib[3] - ib[1] + 2 * PAD, 4))
    print("  plot %.2f x %.2f at (%.2f, %.2f) -> canvas %.3f x %.3f"
          % (box[2], box[3], box[0], box[1], win[2], win[3]))

    svg = build([fig], win, idmap, order, os.path.join(OUT, "svg", "S3b_final.svg"))
    png = os.path.join(OUT, "png", "S3b_final_600dpi.png")
    render(svg, png, 600)
    print("  S3b_final  %s" % ("%dx%d px" % Image.open(png).size))

    return win


def main():
    fig, box, removed, n_tick, texts = make_fig()
    src = etree.parse(SRC).getroot()
    idmap = {e.get("id"): e for e in src.iter() if e.get("id")}
    order = {i: k for k, i in enumerate(idmap)}
    win = finish(fig, box, idmap, order)
    json.dump(dict(win=list(win), plot=list(box), removed=removed,
                   fs_old=FS_OLD, fs_new=FS_NEW, n_text=len(texts)),
              open(os.path.join(OUT, "work", "meta.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
