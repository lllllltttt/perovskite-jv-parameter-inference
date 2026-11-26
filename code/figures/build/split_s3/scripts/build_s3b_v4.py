# -*- coding: utf-8 -*-
"""S3b: same figure as 20261024_final_figures_svg/si/FigureS3b.svg, with
the three texts removed and the typography brought up to S3a's scale.

  * tick numbers 7.5 -> 10.5 pt  (= the size used in S3a), same Arial;
    baselines follow the font metric so the digits clear the tick marks;
  * legend text 6.2 -> 8.68 pt (same x1.4 factor, so its hierarchy relative
    to the tick numbers is unchanged); the whole legend geometry - sample
    lines, row pitch, text anchors - is rescaled about its top-left corner,
    so rows keep their spacing and nothing overlaps;
  * removed: "Voltage (V)", "RMSE across 45 samples (mA cm-2)",
    "noise floor = 0.21 mA cm-2";
  * everything else - canvas 697.326 x 357.616 pt, plot area, curves,
    colours, line widths, dashes, reference lines - untouched.
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
OUT = "out_v4"
PY = sys.executable
PX_PER_PT = 96.0 / 72.0

FS_TICK_OLD, FS_TICK_NEW = 7.5, 10.5          # S3a uses 10.5
FS_LEG_OLD = 6.2
K = FS_TICK_NEW / FS_TICK_OLD                  # 1.4
FS_LEG_NEW = FS_LEG_OLD * K                    # 8.68
TICK_LEN, TICK_PAD = 3.0, 3.5

LEG_X0, LEG_Y0 = 38.856406, 12.677844          # top-left of the first sample line


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


def scale_path_d(d, x0, y0, k):
    toks = re.findall(r"[MLZmlz]|-?\d+\.?\d*(?:e-?\d+)?", d)
    out, i = [], 0
    while i < len(toks):
        t = toks[i]
        if t in "MLmlZz":
            out.append(t)
            i += 1
            if t in "Zz":
                continue
            x, y = float(toks[i]), float(toks[i + 1])
            out.append("%.5f %.5f" % (x0 + (x - x0) * k, y0 + (y - y0) * k))
            i += 2
        else:
            out.append(t)
            i += 1
    return " ".join(out)


def scale_legend(ax):
    lg = ax.find(".//" + CS + "g[@id='legend_1']")
    n_path = n_text = 0
    for p in lg.iter(CS + "path"):
        p.set("d", scale_path_d(p.get("d"), LEG_X0, LEG_Y0, K))
        n_path += 1
    for t in lg.iter(CS + "text"):
        t.set("x", "%.5f" % (LEG_X0 + (float(t.get("x")) - LEG_X0) * K))
        t.set("y", "%.5f" % (LEG_Y0 + (float(t.get("y")) - LEG_Y0) * K))
        st = t.get("style") or ""
        t.set("style", re.sub(r"([\d.]+)px", "%gpx" % FS_LEG_NEW, st))
        n_text += 1
    return lg, n_path, n_text


def scale_ticks(ax, bottom):
    n = 0
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
            t.set("y", "%.4f" % (bottom + TICK_LEN + TICK_PAD + off * K))
        else:
            ty = float(u.get("y"))
            t.set("y", "%.4f" % (ty + (float(t.get("y")) - ty) * K))
        t.set("style", re.sub(r"([\d.]+)px", "%gpx" % FS_TICK_NEW,
                              t.get("style") or ""))
        n += 1
    return n


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
    ax = fig.find(".//" + CS + "g[@id='axes_1']")
    box = plot_box(ax)
    bottom = box[1] + box[3]

    removed = cut(fig)
    n_leg_p, n_leg_t = scale_legend(ax)[1:]
    n_tick = scale_ticks(ax, bottom)
    n_font = font_attrs(fig)
    print("  removed:", removed)
    print("  ticks %g -> %g pt (%d labels); legend %g -> %g pt (%d paths, %d texts)"
          % (FS_TICK_OLD, FS_TICK_NEW, n_tick, FS_LEG_OLD, round(FS_LEG_NEW, 3),
             n_leg_p, n_leg_t))
    print("  text nodes: %d, all with explicit font attributes" % n_font)

    vb = [float(v) for v in src.get("viewBox").split()]
    win = (round(vb[0], 4), round(vb[1], 4), round(vb[2], 4), round(vb[3], 4))
    svg = build([fig], win, idmap, order, os.path.join(OUT, "svg", "S3b_final.svg"))
    png = os.path.join(OUT, "png", "S3b_final_600dpi.png")
    render(svg, png, 600)
    print("  canvas %.3f x %.3f pt  %dx%d px"
          % (win[2], win[3], *Image.open(png).size))

    json.dump(dict(win=list(win), plot=list(box), removed=removed,
                   fs_tick=FS_TICK_NEW, fs_leg=FS_LEG_NEW, k=K),
              open(os.path.join(OUT, "work", "meta.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
