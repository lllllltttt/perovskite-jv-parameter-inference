# -*- coding: utf-8 -*-
"""Figure S1 split, second specification: keep every tick mark and tick number,
delete only the explanatory words.

Deleted
  histograms : the panel title above each plot (mu_n ... r_rad),
               the y-axis title "Count" (left column only),
               the x-axis title log10(...)  (bottom row only)
  heat map   : the nine x tick labels and nine y tick labels (the parameter
               names), the colour-bar title "Spearman rho"
  everywhere : (a), (b), the two panel titles, "N = 102,046"

Kept
  everything else, verbatim: bars, colours, frames, grid, tick marks, tick
  numbers, the 9x9 matrix, its in-cell numbers, the colour bar with its own
  tick marks and tick numbers.

The nine histograms share one canvas so that the plot areas sit at identical
offsets; the crop window is measured from the rendered ink in pass 1, padded by
PAD on every side, and reused for all nine (worst case over the nine).
"""
import io
import json
import os
import re
import subprocess
import sys
import time

import numpy as np
from lxml import etree
from PIL import Image

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

CS = "{http://www.w3.org/2000/svg}"
XL = "{http://www.w3.org/1999/xlink}"
SVGNS = "http://www.w3.org/2000/svg"
XLNS = "http://www.w3.org/1999/xlink"
SRC = "work/slide1_image2.svg"
PY = sys.executable

OUT = "out_ticks"
PAD = 3.0
PX_PER_PT = 96.0 / 72.0

HIST_W, HIST_H = 125.569, 115.162
HIST_X = [44.2399, 209.992, 375.743]
HIST_Y = [35.4384, 198.969, 362.5]

HIST_NAMES = [
    ("S1a_01_mu_n", "mu_n"), ("S1a_02_mu_p", "mu_p"), ("S1a_03_tau_n", "tau_n"),
    ("S1a_04_tau_p", "tau_p"), ("S1a_05_N_c", "N_c"), ("S1a_06_N_v", "N_v"),
    ("S1a_07_tau_ETL", "tau_ETL"), ("S1a_08_tau_HTL", "tau_HTL"),
    ("S1a_09_r_rad", "r_rad"),
]
HEAT_NAME = "S1b_heatmap_numbers"


# --------------------------------------------------------------------------
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
        el = idmap[nid]
        # deep copy: appending the live element would move it out of the
        # source document, emptying the <defs> it lives in (line2d_1)
        out.append(etree.fromstring(etree.tostring(el)))
        need |= (ref_ids(el) - have - {d.get("id") for d in out})
    return out


# --------------------------------------------------------------------------
def strip_histogram_labels(a):
    """axes_k -> remove panel title, 'Count' y title, log10(...) x title."""
    removed = []
    for c in list(a):
        if c.tag == CS + "g" and re.match(r"^text_\d+$", c.get("id") or ""):
            removed.append((c.get("id"), txt(c)))
            a.remove(c)
    for c in list(a):
        if not (c.get("id") or "").startswith("matplotlib.axis_"):
            continue
        for g in list(c):
            if g.tag != CS + "g":
                continue
            cid = g.get("id") or ""
            if cid.startswith("xtick_") or cid.startswith("ytick_"):
                continue                      # tick mark + tick number: keep
            if next(g.iter(CS + "text"), None) is not None:
                removed.append((cid or "(unnamed)", txt(g)))
                c.remove(g)
    return removed


def strip_heatmap_labels(a10, a11):
    removed = []
    for c in list(a10):
        if c.tag != CS + "g":
            continue
        for g in list(c):                      # xtick_N / ytick_N
            if g.tag != CS + "g":
                continue
            for lab in list(g):
                if re.match(r"^text_\d+$", lab.get("id") or ""):
                    removed.append((lab.get("id"), txt(lab)))
                    g.remove(lab)
    for g in list(a11.iter(CS + "g")):
        if g.get("id") == "text_151":
            removed.append(("text_151", txt(g)))
            g.getparent().remove(g)
    return removed


def font_fix(el):
    n = 0
    for t in el.iter(CS + "text"):
        t.set("font-family", "Arial")
        t.set("font-size", "12")
        n += 1
    return n


def build(groups, win, idmap, order, path):
    """groups: list of axes elements (already stripped). win = (x0, y0, W, H)."""
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
    for attempt in range(3):
        r = subprocess.run([PY, "scripts/render_svg_px.py", svg, png, "--dpi", str(dpi)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if r.returncode == 0 and os.path.exists(png) and os.path.getsize(png) > 1000:
            return png
        time.sleep(2.0)
    raise RuntimeError("render failed: " + svg)


def ink_bbox(png, win, dpi, thr=8):
    a = np.asarray(Image.open(png).convert("L")).astype(int)
    m = (255 - a) > thr
    rows = np.where(m.any(axis=1))[0]
    cols = np.where(m.any(axis=0))[0]
    s = dpi / 72.0
    return (win[0] + cols[0] / s, win[1] + rows[0] / s,
            win[0] + (cols[-1] + 1) / s, win[1] + (rows[-1] + 1) / s)


# --------------------------------------------------------------------------
def main():
    for d in ("svg", "png", "preview", "work"):
        os.makedirs(os.path.join(OUT, d), exist_ok=True)

    src = etree.parse(SRC).getroot()
    idmap = {e.get("id"): e for e in src.iter() if e.get("id")}
    order = {i: k for k, i in enumerate(idmap)}

    gone = {}
    pieces = []          # (name, [axes ids], anchor) anchor = plot rect or None
    for i, (name, tag) in enumerate(HIST_NAMES):
        r, c = divmod(i, 3)
        pieces.append((name, ["axes_%d" % (i + 1)],
                       dict(x=HIST_X[c], y=HIST_Y[r], w=HIST_W, h=HIST_H)))
    pieces.append((HEAT_NAME, ["axes_10", "axes_11"], None))

    # ---- pass 1: generous windows, measure the ink ----------------------
    geowin, rects = {}, {}
    for name, ids, anchor in pieces:
        a = etree.fromstring(etree.tostring(idmap[ids[0]]))
        if ids[0] == "axes_10":
            a11 = etree.fromstring(etree.tostring(idmap["axes_11"]))
            gone[name] = strip_heatmap_labels(a, a11)
            grp = [a, a11]
        else:
            gone[name] = strip_histogram_labels(a)
            grp = [a]
        for g in grp:
            font_fix(g)
        if anchor:
            win = (anchor["x"] - 45, anchor["y"] - 45,
                   anchor["w"] + 90, anchor["h"] + 90)
        else:
            win = (489, -15, 500, 470)
        p = build(grp, win, idmap, order,
                  os.path.join(OUT, "work", name + "_probe.svg"))
        png = os.path.join(OUT, "work", name + "_probe.png")
        render(p, png, 300)
        geowin[name] = (win, ink_bbox(png, win, 300))
        print("  probe %-18s ink %s" % (name, "  ".join("%8.2f" % v for v in geowin[name][1])))

    # ---- common window for the nine histograms -------------------------
    LEFT = TOP = RIGHT = BOTTOM = 0.0
    for name, ids, anchor in pieces[:9]:
        _, (ix0, iy0, ix1, iy1) = geowin[name]
        LEFT = max(LEFT, anchor["x"] - ix0)
        TOP = max(TOP, anchor["y"] - iy0)
        RIGHT = max(RIGHT, ix1 - (anchor["x"] + anchor["w"]))
        BOTTOM = max(BOTTOM, iy1 - (anchor["y"] + anchor["h"]))
    hx0 = HIST_X[0] - LEFT - PAD
    hy0 = HIST_Y[0] - TOP - PAD
    HW = HIST_W + LEFT + RIGHT + 2 * PAD
    HH = HIST_H + TOP + BOTTOM + 2 * PAD
    hist_win = (round(hx0, 4), round(hy0, 4), round(HW, 4), round(HH, 4))
    print("\n  histogram margins  left %.3f top %.3f right %.3f bottom %.3f  (+ %.2f pad)"
          % (LEFT, TOP, RIGHT, BOTTOM, PAD))
    print("  histogram canvas   %.3f x %.3f pt" % (HW, HH))

    # ---- heat map window ------------------------------------------------
    _, (ix0, iy0, ix1, iy1) = geowin[HEAT_NAME]
    heat_win = (round(ix0 - PAD, 4), round(iy0 - PAD, 4),
                round(ix1 - ix0 + 2 * PAD, 4), round(iy1 - iy0 + 2 * PAD, 4))
    print("  heat-map canvas    %.3f x %.3f pt" % (heat_win[2], heat_win[3]))

    # ---- pass 2: final SVGs + 600 dpi PNGs ------------------------------
    print("\n== final pieces ==")
    meta = []
    for name, ids, anchor in pieces:
        a = etree.fromstring(etree.tostring(idmap[ids[0]]))
        if ids[0] == "axes_10":
            a11 = etree.fromstring(etree.tostring(idmap["axes_11"]))
            strip_heatmap_labels(a, a11)
            grp = [a, a11]
            win = heat_win
        else:
            strip_histogram_labels(a)
            grp = [a]
            win = (round(anchor["x"] - LEFT - PAD, 4),
                   round(anchor["y"] - TOP - PAD, 4), hist_win[2], hist_win[3])
        for g in grp:
            font_fix(g)
        svg = build(grp, win, idmap, order, os.path.join(OUT, "svg", name + ".svg"))
        png = os.path.join(OUT, "png", name + "_600dpi.png")
        render(svg, png, 600)
        sz = Image.open(png).size
        meta.append(dict(name=name, svg=svg, png=png, win=win, px=sz,
                         bytes=os.path.getsize(svg)))
        print("  %-18s %8.3f x %8.3f pt   %s px   %6d B"
              % (name, win[2], win[3], "%dx%d" % sz, os.path.getsize(svg)))

    # ---- preview: the pieces pasted back at their original positions ----
    #      alpha renders, so the overlapping margins (the canvases are 4 pt
    #      wider than the column pitch) cannot paint over a neighbour
    s = 600 / 72.0
    X0 = min(m["win"][0] for m in meta)
    Y0 = min(m["win"][1] for m in meta)
    X1 = max(m["win"][0] + m["win"][2] for m in meta)
    Y1 = max(m["win"][1] + m["win"][3] for m in meta)
    canvas = Image.new("RGBA", (int(round((X1 - X0) * s)), int(round((Y1 - Y0) * s))),
                       (255, 255, 255, 255))
    for m in meta:
        apng = os.path.join(OUT, "work", m["name"] + "_alpha.png")
        subprocess.run([PY, "scripts/render_svg_px.py", m["svg"], apng,
                        "--dpi", "600", "--bg", "transparent"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        im = Image.open(apng).convert("RGBA")
        canvas.alpha_composite(im, (int(round((m["win"][0] - X0) * s)),
                                    int(round((m["win"][1] - Y0) * s))))
    prev = os.path.join(OUT, "preview", "FigureS1_ticks_preview_600dpi.png")
    canvas.convert("RGB").save(prev)
    print("\n  preview %s  %dx%d px = %.2f x %.2f pt"
          % (prev, canvas.size[0], canvas.size[1], X1 - X0, Y1 - Y0))

    json.dump(dict(pieces=meta, hist_win=hist_win, heat_win=heat_win,
                   removed=gone, removed_count={k: len(v) for k, v in gone.items()},
                   preview=prev, pad=PAD),
              open(os.path.join(OUT, "work", "ticks_meta.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print("\n== deleted (%d groups) ==" % sum(len(v) for v in gone.values()))
    for k, v in gone.items():
        print("  %-18s %s" % (k, [t for _, t in v]))


if __name__ == "__main__":
    main()
