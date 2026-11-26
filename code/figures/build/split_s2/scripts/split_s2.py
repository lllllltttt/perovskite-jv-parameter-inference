# -*- coding: utf-8 -*-
"""Figure S2 -> two standalone panels (a) and (b).

Source: the original matplotlib SVG of the figure
        (final_figures/SI_final_review/FigS2_sensitivity_recoverability.svg,
        identical to 20261024_final_figures_svg/si/FigureS2.svg),
        produced by final_figures/scripts/plot_FigS2_sensitivity_recoverability.py

Deleted (the user re-adds them in PowerPoint)
  per panel : the panel letter (a)/(b), the title and the subtitle,
              the x axis title "J-V sensitivity, S_log / S_raw",
              the y axis title "Recoverability Pearson r",
              the nine parameter names and their nine grey leader lines,
              the Spearman annotation (rho_s / p / "non-significant")
              there is no legend in this figure.

Kept verbatim
  the nine scatter markers (position, size, colour, alpha, z-order, clip),
  the four spines, the tick marks and the tick numbers.

Rendered on one identical canvas for both panels: the plot areas are already
the same size in the source (341.593 x 269.568 pt), and the crop margins are
taken as the max ink over the two so the two pieces are interchangeable.
"""
import io
import json
import os
import re
import subprocess
import sys

from lxml import etree
from PIL import Image
import numpy as np

if (getattr(sys.stdout, "encoding", "") or "").lower().replace("-", "") != "utf8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

CS = "{http://www.w3.org/2000/svg}"
XL = "{http://www.w3.org/1999/xlink}"
SVGNS = "http://www.w3.org/2000/svg"
XLNS = "http://www.w3.org/1999/xlink"

SRC = r"E:\project\work1\20261024_final_figures_svg\si\FigureS2.svg"
PY = sys.executable
OUT = os.environ.get("S2_OUT", "out")
PAD = 2.5
KEEP_LEADERS = os.environ.get("S2_KEEP_LEADERS") == "1"
FONT_SIZE = float(os.environ.get("S2_FONT", "0")) or None
TICK_LEN = 3.5          # tick mark length in the source (pts)
TICK_PAD = 3.5          # matplotlib tick-label pad (pts)
PX_PER_PT = 96.0 / 72.0

PANELS = [("S2a_sensitivity_log", "axes_1", "PathCollection_1"),
          ("S2b_sensitivity_raw", "axes_2", "PathCollection_2")]

INK = "#1a1a1a"


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
        for a in ("clip-path", "fill", "stroke", "filter", "mask"):
            m = re.search(r"url\(#([^)]+)\)", e.get(a) or "")
            if m:
                ids.add(m.group(1))
        m = re.search(r"url\(#([^)]+)\)", e.get("style") or "")
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
    x0, y0, W, H = win
    root = etree.Element(CS + "svg", nsmap={None: SVGNS, "xlink": XLNS})
    root.set("width", "%.4f" % (W * PX_PER_PT))
    root.set("height", "%.4f" % (H * PX_PER_PT))
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
        defs = etree.Element(CS + "defs")
        for d in extra:
            defs.append(d)
        root.insert(0, defs)
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


def style_prop(text_el, key):
    st = text_el.get("style") or ""
    m = re.search(key + r":\s*([^;]+)", st)
    return m.group(1).strip() if m else None


def font_fix(el, box=None, fs=None):
    """Matplotlib writes the face in the CSS `font:` shorthand, which
    PowerPoint does not reliably apply; pin both as plain attributes.

    When a new size is requested, the tick-label baselines move with the font
    metrics (matplotlib anchors the label's top at tick + pad, and centres the
    y labels on the tick), otherwise bigger digits would run into the ticks.
    """
    box = box or (0.0, 0.0, 0.0, 0.0)
    n = 0
    for g in el.iter(CS + "g"):
        gid = g.get("id") or ""
        if not gid.startswith(("xtick_", "ytick_")):
            continue
        t = next(g.iter(CS + "text"), None)
        u = next(g.iter(CS + "use"), None)
        if t is None:
            continue
        m = re.search(r"([\d.]+)px", t.get("style") or "")
        src = float(m.group(1)) if m else 12.0
        t.set("font-family", "Arial")
        t.set("font-size", "%g" % (fs or src))
        if fs and abs(fs - src) > 1e-9:
            # the CSS `font:` shorthand in style= outranks the presentation
            # attributes, so it has to be rewritten too
            st = t.get("style") or ""
            t.set("style", re.sub(r"font:\s*[\d.]+px", "font: %gpx" % fs, st))
        if fs and abs(fs - src) > 1e-9 and u is not None:
            k = fs / src
            if gid.startswith("xtick_"):
                bottom = box[1] + box[3]
                off = float(t.get("y")) - bottom - (TICK_LEN + TICK_PAD)
                t.set("y", "%.4f" % (bottom + TICK_LEN + TICK_PAD + off * k))
            else:
                ty = float(u.get("y"))
                t.set("y", "%.4f" % (ty + (float(t.get("y")) - ty) * k))
        n += 1
    return n


def cut(a, keep_collection):
    """Delete everything that is wording; return (kept element, removed ids)."""
    removed = []
    for c in list(a):
        if not isinstance(c.tag, str):
            continue
        cid = c.get("id") or ""
        if c.tag == CS + "g" and re.match(r"^text_\d+$", cid):
            removed.append((cid, txt(c)))
            a.remove(c)
            continue
        if c.tag == CS + "g" and cid.startswith("patch_"):
            p = c.find(".//" + CS + "path")
            st = (p.get("style") if p is not None else "") or ""
            if "#a6a6a6" in st:                    # grey leader line
                if KEEP_LEADERS:
                    continue
                removed.append((cid, "(leader line)"))
                a.remove(c)
    for c in list(a):
        cid = c.get("id") or ""
        if not cid.startswith("matplotlib.axis_"):
            continue
        for g in list(c):
            if g.tag != CS + "g":
                continue
            gid = g.get("id") or ""
            if gid.startswith(("xtick_", "ytick_")):
                continue
            if next(g.iter(CS + "text"), None) is not None:   # axis title
                removed.append((gid, txt(g)))
                c.remove(g)
    return a, removed


def plot_box(a):
    xs, ys = [], []
    for c in a:
        cid = c.get("id") or ""
        if not cid.startswith("patch_"):
            continue
        p = c.find(".//" + CS + "path")
        st = (p.get("style") if p is not None else "") or ""
        if INK in st and "stroke-width: 0.8" in st:
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

    boxes, pieces, removed_all = {}, {}, {}
    for name, aid, coll in PANELS:
        a = etree.fromstring(etree.tostring(idmap[aid]))
        a, rem = cut(a, coll)
        removed_all[name] = rem
        font_fix(a, plot_box(a), FONT_SIZE)
        pieces[name] = a
        boxes[name] = plot_box(a)
        print("  %-22s plot %.3f x %.3f at (%.3f, %.3f)  removed %d"
              % (name, boxes[name][2], boxes[name][3], boxes[name][0],
                 boxes[name][1], len(rem)))
    assert abs(boxes["S2a_sensitivity_log"][2] -
               boxes["S2b_sensitivity_raw"][2]) < 1e-6

    # ---- pass 1: ink margins in a generous window ----------------------
    geo = {}
    for name, aid, coll in PANELS:
        x, y, w, h = boxes[name]
        win = (x - 60, y - 60, w + 120, h + 120)
        p = build([etree.fromstring(etree.tostring(pieces[name]))], win,
                  idmap, order, os.path.join(OUT, "work", name + "_probe.svg"))
        png = os.path.join(OUT, "work", name + "_probe.png")
        render(p, png, 300)
        ib = ink_bbox(png, win, 300)
        geo[name] = (x - ib[0], y - ib[1], ib[2] - (x + w), ib[3] - (y + h))
        print("  probe %-22s L %.2f T %.2f R %.2f B %.2f" % ((name,) + geo[name]))

    L = max(g[0] for g in geo.values())
    T = max(g[1] for g in geo.values())
    R = max(g[2] for g in geo.values())
    B = max(g[3] for g in geo.values())
    W0, H0 = boxes["S2a_sensitivity_log"][2:]
    CW = W0 + L + R + 2 * PAD
    CH = H0 + T + B + 2 * PAD
    print("\n  margins L %.2f T %.2f R %.2f B %.2f (+%.2f)  canvas %.3f x %.3f"
          % (L, T, R, B, PAD, CW, CH))

    meta = []
    for name, aid, coll in PANELS:
        x, y, w, h = boxes[name]
        win = (round(x - L - PAD, 4), round(y - T - PAD, 4),
               round(CW, 4), round(CH, 4))
        svg = build([pieces[name]], win, idmap, order,
                    os.path.join(OUT, "svg", name + ".svg"))
        png = os.path.join(OUT, "png", name + "_600dpi.png")
        render(svg, png, 600)
        meta.append(dict(name=name, svg=svg, png=png, win=win,
                         px=list(Image.open(png).size)))
        print("  %-22s %8.3f x %8.3f pt  %s px"
              % (name, win[2], win[3], "%dx%d" % tuple(meta[-1]["px"])))

    json.dump(dict(pieces=meta, canvas=[CW, CH],
                   margins=dict(L=L, T=T, R=R, B=B, pad=PAD),
                   boxes={k: list(v) for k, v in boxes.items()},
                   removed={k: v for k, v in removed_all.items()}),
              open(os.path.join(OUT, "work", "meta.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print("\n  removed:")
    for k, v in removed_all.items():
        print("   ", k, [t for _, t in v])


if __name__ == "__main__":
    main()
