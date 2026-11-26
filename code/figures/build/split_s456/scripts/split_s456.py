# -*- coding: utf-8 -*-
"""Split FigureS4 / FigureS5 / FigureS6 (SI 3x3 figures) into 27 panels.

Source: E:\\project\\work1\\20261024_final_figures_svg\\si\\FigureS{4,5,6}.svg
The files carry no <text> for S4/S5 (matplotlib fonttype=path) but every label
is its own <g id="text_N"> with an XML comment holding the original string, so
wording can be identified exactly.  Each glyph is a <use> of an embedded glyph
path, i.e. already vector outlines - nothing depends on a font in PowerPoint.

Removed per panel : the panel title / statistic annotation (direct child
                    text groups) and the axis titles (non-tick children of
                    matplotlib.axis_*).
Removed per figure: the figure-level title and, for S6, the overlay axes_10
                    that only carries the shared axis titles and the note.
Kept              : every tick label (inside xtick_/ytick_ groups), every
                    data element (bars / points / images / lines), spines,
                    tick marks, clip paths.
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

BASE = r"E:\project\work1\20261024_final_figures_svg\si"
OUT = "out"
PAD = 2.5
PX_PER_PT = 96.0 / 72.0
PY = sys.executable

FIGS = [("S4", "FigureS4.svg"), ("S5", "FigureS5.svg"), ("S6", "FigureS6.svg")]


def comment_of(g):
    for c in g.iter():
        if not isinstance(c.tag, str):
            s = getattr(c, "text", "") or ""
            if s.strip():
                return re.sub(r"\s+", " ", s).strip()
    return ""


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


def render(svg, png, dpi, bg=None):
    cmd = [PY, "scripts/render_svg_px.py", svg, png, "--dpi", str(dpi)]
    if bg:
        cmd += ["--bg", bg]
    for _ in range(3):
        r = subprocess.run(cmd, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
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


def cut(fig):
    """Delete wording; return [(where, text)]."""
    removed = []
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
    meta = {}
    for tag, fname in FIGS:
        src = etree.parse(os.path.join(BASE, fname)).getroot()
        idmap = {e.get("id"): e for e in src.iter() if e.get("id")}
        order = {i: k for k, i in enumerate(idmap)}
        fig = etree.fromstring(etree.tostring(src.find(".//" + CS + "g[@id='figure_1']")))

        # S6: the overlay axes only carries wording
        if tag == "S6":
            a10 = fig.find(".//" + CS + "g[@id='axes_10']")
            if a10 is not None:
                a10.getparent().remove(a10)

        removed = cut(fig)

        # panels in reading order, from the clip rects of each axes
        panels = []
        for a in [g for g in fig.iter(CS + "g")
                  if re.match(r"^axes_\d+$", g.get("id") or "")]:
            cl = [i for i in ref_ids(a) if i in idmap and
                  idmap[i].tag == CS + "clipPath"]
            box = None
            for i in cl:
                rect = idmap[i].find(CS + "rect")
                if rect is not None:
                    box = tuple(float(rect.get(k)) for k in
                                ("x", "y", "width", "height"))
                    break
            if box:
                panels.append((a, box))
        panels.sort(key=lambda p: (round(p[1][1], 1), round(p[1][0], 1)))
        assert len(panels) == 9, (tag, len(panels))

        W0, H0 = panels[0][1][2], panels[0][1][3]
        for _, b in panels:
            assert abs(b[2] - W0) < 1e-3 and abs(b[3] - H0) < 1e-3, (tag, b)

        # pass 1: ink margins
        geo = []
        for a, (x, y, w, h) in panels:
            win = (x - 60, y - 60, w + 120, h + 120)
            p = build([etree.fromstring(etree.tostring(a))], win, idmap, order,
                      os.path.join(OUT, "work", "%s_%s.svg" % (tag, a.get("id"))))
            render(p, os.path.join(OUT, "work", "%s_%s.png" % (tag, a.get("id"))), 300)
            ib = ink_bbox(os.path.join(OUT, "work", "%s_%s.png" % (tag, a.get("id"))), win, 300)
            geo.append((x - ib[0], y - ib[1], ib[2] - (x + w), ib[3] - (y + h)))

        L = max(g[0] for g in geo); T = max(g[1] for g in geo)
        R = max(g[2] for g in geo); B = max(g[3] for g in geo)
        CW = W0 + L + R + 2 * PAD
        CH = H0 + T + B + 2 * PAD
        print("  %s  plot %.3f x %.3f  margins L%.2f T%.2f R%.2f B%.2f -> canvas %.3f x %.3f"
              % (tag, W0, H0, L, T, R, B, CW, CH))

        pieces = []
        for i, (a, (x, y, w, h)) in enumerate(panels, start=1):
            name = "%s_%02d" % (tag, i)
            win = (round(x - L - PAD, 4), round(y - T - PAD, 4),
                   round(CW, 4), round(CH, 4))
            svg = build([etree.fromstring(etree.tostring(a))], win, idmap, order,
                        os.path.join(OUT, "svg", name + ".svg"))
            png = os.path.join(OUT, "png", name + "_600dpi.png")
            render(svg, png, 600)
            pieces.append(dict(name=name, svg=svg, png=png, win=win,
                               px=list(Image.open(png).size),
                               axes=a.get("id")))
            print("    %-6s <- %-7s %8.3f x %8.3f pt  %dx%d px  %6.1f KB"
                  % (name, a.get("id"), win[2], win[3],
                     pieces[-1]["px"][0], pieces[-1]["px"][1],
                     os.path.getsize(svg) / 1024))

        # 3x3 preview
        s = 600 / 72.0
        GUT = 10.0
        Wc = 3 * CW + 4 * GUT
        Hc = 3 * CH + 4 * GUT
        canvas = Image.new("RGB", (int(round(Wc * s)), int(round(Hc * s))), "white")
        for i, p in enumerate(pieces):
            r, c = divmod(i, 3)
            canvas.paste(Image.open(p["png"]).convert("RGB"),
                         (int(round((GUT + c * (CW + GUT)) * s)),
                          int(round((GUT + r * (CH + GUT)) * s))))
        prev = os.path.join(OUT, "preview", "%s_preview_3x3_600dpi.png" % tag)
        canvas.save(prev)
        print("    preview %s  %dx%d px" % (prev, canvas.size[0], canvas.size[1]))

        meta[tag] = dict(source=fname, pieces=pieces, canvas=[round(CW, 4), round(CH, 4)],
                         plot=[round(W0, 4), round(H0, 4)],
                         margins=dict(L=L, T=T, R=R, B=B, pad=PAD),
                         removed=removed, preview=prev)

    json.dump(meta, open(os.path.join(OUT, "work", "meta.json"), "w",
                         encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\nremoved texts:")
    for tag in meta:
        print("  %s: %d" % (tag, len(meta[tag]["removed"])))
        for w, t in meta[tag]["removed"]:
            print("     %-8s %r" % (w, t[:70]))


if __name__ == "__main__":
    main()
