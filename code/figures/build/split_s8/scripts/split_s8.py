# -*- coding: utf-8 -*-
"""Figure S8 -> six standalone panels S8_01 ... S8_06.

Source: E:\\project\\work1\\20261024_final_figures_svg\\si\\FigureS7.svg
        2 x 3 ECDF panels, 127.62 x 98.51 pt each.

Removed: the panel letters and their parameter titles, the x axis title
         "|Δcoord| / random median" (all six), the two y axis titles
         "cumulative fraction", the legend of panel (a) with its samples, and
         the figure-level note at the bottom.
Kept   : both ECDF curves of every panel (grey random pairs, blue/orange
         nearest-neighbour pairs), the dashed grey vertical line at x = 1,
         the frame, tick marks and every tick label (each panel already has
         the full y set 0.0 ... 1.0 and its own x range).

Every surviving label is converted to outline paths, so PowerPoint needs no
font and cannot re-flow the digits.
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

BASE = r"E:\project\work1\20261024_final_figures_svg\si"
SRC = os.path.join(BASE, "FigureS8.svg")
OUT = "out"
PAD = 2.5
PX_PER_PT = 96.0 / 72.0
PY = sys.executable
NAMES = ["S8_01", "S8_02", "S8_03", "S8_04", "S8_05", "S8_06"]
# S7a keeps its two-row legend (the author asked for it to stay)
KEEP_LEGEND_IN = {"axes_1", "axes_4"}

TTP = TextToPath()


def txt(e):
    return re.sub(r"\s+", " ", "".join(e.itertext()).replace("\xa0", " ")).strip()


def comment_of(g):
    for c in g.iter():
        if not isinstance(c.tag, str):
            s = (getattr(c, "text", "") or "").strip()
            if s:
                return re.sub(r"\s+", " ", s)
    return txt(g)


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


def text_to_group(t):
    s = "".join(t.itertext())
    m = re.search(r"font-size:\s*([\d.]+)px", t.get("style") or "")
    fs = float(m.group(1)) if m else 10.0
    prop = FontProperties(family="Arial", size=fs)
    w, _h, _d = TTP.get_text_width_height_descent(s, prop, False)
    an = t.get("text-anchor")
    if an is None:                      # matplotlib puts it inside style=
        m2 = re.search(r"text-anchor:\s*(\w+)", t.get("style") or "")
        an = m2.group(1) if m2 else "start"
    px, py = float(t.get("x")), float(t.get("y"))
    if an == "middle":
        px -= w / 2.0
    elif an == "end":
        px -= w
    fill = "#1a1a1a"
    mf = re.search(r"fill:\s*(#[0-9a-fA-F]{3,6})", t.get("style") or "")
    if mf:
        fill = mf.group(1)
    g = etree.Element(CS + "g")
    g.set("class", "glyphs")
    g.set("transform", "translate(%.4f %.4f) scale(1 -1)" % (px, py))
    p = etree.SubElement(g, CS + "path")
    p.set("d", path_to_d(TextPath((0, 0), s, size=fs, prop=prop)))
    p.set("fill", fill)
    return g


def cut(fig):
    removed = []
    for g in list(fig.iter(CS + "g")):
        gid = g.get("id") or ""
        if not gid.startswith("legend"):
            continue
        p, ax_of = g.getparent(), None
        while p is not None:
            if (p.get("id") or "").startswith("axes_"):
                ax_of = p.get("id")
                break
            p = p.getparent()
        if ax_of in KEEP_LEGEND_IN:
            continue
        removed.append((gid, comment_of(g) or "(legend)"))
        g.getparent().remove(g)
    for a in [g for g in fig.iter(CS + "g")
              if (g.get("id") or "").startswith("axes_")]:
        for c in list(a):
            if c.tag == CS + "g" and re.match(r"^text_\d+$", c.get("id") or ""):
                removed.append((a.get("id"), comment_of(c)))
                a.remove(c)
        for c in list(a):
            if not (c.get("id") or "").startswith("matplotlib.axis_"):
                continue
            for g in list(c):
                if g.tag == CS + "g" and re.match(r"^text_\d+$", g.get("id") or ""):
                    removed.append((a.get("id"), comment_of(g)))
                    c.remove(g)
    for c in list(fig):
        if c.tag == CS + "g" and re.match(r"^text_\d+$", c.get("id") or ""):
            removed.append(("figure", comment_of(c)))
            fig.remove(c)
    return removed


def main():
    for d in ("svg", "png", "work", "preview"):
        os.makedirs(os.path.join(OUT, d), exist_ok=True)

    src = etree.parse(SRC).getroot()
    idmap = {e.get("id"): e for e in src.iter() if e.get("id")}
    order = {i: k for k, i in enumerate(idmap)}
    fig = etree.fromstring(etree.tostring(src.find(".//" + CS + "g[@id='figure_1']")))
    removed = cut(fig)

    # tick labels -> outline paths
    n_txt = 0
    for t in list(fig.iter(CS + "text")):
        t.getparent().replace(t, text_to_group(t))
        n_txt += 1
    print("  removed %d texts; %d tick labels converted to outlines"
          % (len(removed), n_txt))

    # panels in reading order
    panels = []
    for a in [g for g in fig.iter(CS + "g")
              if re.match(r"^axes_\d+$", g.get("id") or "")]:
        cl = [i for i in ref_ids(a) if i in idmap and idmap[i].tag == CS + "clipPath"]
        rect = idmap[cl[0]].find(CS + "rect")
        box = tuple(float(rect.get(k)) for k in ("x", "y", "width", "height"))
        panels.append((a, box))
    panels.sort(key=lambda p: (round(p[1][1], 1), round(p[1][0], 1)))
    assert len(panels) == 6

    W0, H0 = panels[0][1][2], panels[0][1][3]
    for _, b in panels:
        assert abs(b[2] - W0) < 1e-3 and abs(b[3] - H0) < 1e-3

    geo = []
    for a, (x, y, w, h) in panels:
        win = (x - 50, y - 50, w + 100, h + 100)
        p = build([etree.fromstring(etree.tostring(a))], win, idmap, order,
                  os.path.join(OUT, "work", "%s_probe.svg" % a.get("id")))
        render(p, os.path.join(OUT, "work", "%s_probe.png" % a.get("id")), 300)
        ib = ink_bbox(os.path.join(OUT, "work", "%s_probe.png" % a.get("id")), win, 300)
        geo.append((x - ib[0], y - ib[1], ib[2] - (x + w), ib[3] - (y + h)))

    L = max(g[0] for g in geo); T = max(g[1] for g in geo)
    R = max(g[2] for g in geo); B = max(g[3] for g in geo)
    CW, CH = W0 + L + R + 2 * PAD, H0 + T + B + 2 * PAD
    print("  plot %.3f x %.3f  margins L%.2f T%.2f R%.2f B%.2f -> canvas %.3f x %.3f"
          % (W0, H0, L, T, R, B, CW, CH))

    pieces = []
    for i, (a, (x, y, w, h)) in enumerate(panels):
        name = NAMES[i]
        win = (round(x - L - PAD, 4), round(y - T - PAD, 4),
               round(CW, 4), round(CH, 4))
        svg = build([etree.fromstring(etree.tostring(a))], win, idmap, order,
                    os.path.join(OUT, "svg", name + ".svg"))
        png = os.path.join(OUT, "png", name + "_600dpi.png")
        render(svg, png, 600)
        pieces.append(dict(name=name, axes=a.get("id"), svg=svg, png=png, win=win,
                           px=list(Image.open(png).size)))
        print("    %-4s <- %-7s %8.3f x %8.3f pt  %dx%d px"
              % (name, a.get("id"), win[2], win[3], *pieces[-1]["px"]))

    # 2 x 3 preview
    s = 600 / 72.0
    GUT = 10.0
    Wc, Hc = 3 * CW + 4 * GUT, 2 * CH + 3 * GUT
    canvas = Image.new("RGB", (int(round(Wc * s)), int(round(Hc * s))), "white")
    for i, p in enumerate(pieces):
        r, c = divmod(i, 3)
        canvas.paste(Image.open(p["png"]).convert("RGB"),
                     (int(round((GUT + c * (CW + GUT)) * s)),
                      int(round((GUT + r * (CH + GUT)) * s))))
    prev = os.path.join(OUT, "preview", "S8_preview_2x3_600dpi.png")
    canvas.save(prev)
    print("  preview %s  %dx%d px" % (prev, canvas.size[0], canvas.size[1]))

    json.dump(dict(source="FigureS8.svg", pieces=pieces,
                   canvas=[round(CW, 4), round(CH, 4)],
                   plot=[round(W0, 4), round(H0, 4)],
                   margins=dict(L=L, T=T, R=R, B=B, pad=PAD),
                   removed=removed, n_text=n_txt, preview=prev),
              open(os.path.join(OUT, "work", "meta.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print("\nremoved:")
    for w, t in removed:
        print("   %-8s %r" % (w, t))


if __name__ == "__main__":
    main()
