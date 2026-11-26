"""Split the slide-1 SI figure (Figure S1) into 11 text-free, standalone SVG pieces.

Source: work/slide1_image2.svg  (the original vector PowerPoint kept for slide 1)
Output: out/svg/<name>.svg  +  out/svg/_preview_no_text.svg  +  work/geometry.json

Every piece is produced by MOVING the original <g id="axes_N"> subtree unchanged
(a single translate on a wrapper group) and DELETING the <g id="text_k"> groups.
No geometry, colour, path data, image data or clip path is modified.
"""
import copy
import json
import os
import re
import sys
from lxml import etree

SRC = "work/slide1_image2.svg"
OUTDIR = "out/svg"
CS = "{http://www.w3.org/2000/svg}"
XL = "{http://www.w3.org/1999/xlink}"
SVGNS = "http://www.w3.org/2000/svg"
XLNS = "http://www.w3.org/1999/xlink"

MARGIN = 6.0          # pt of clear space on every side of every piece
PX_PER_PT = 96.0 / 72.0   # PowerPoint's own convention: 1 pt = 4/3 px

# original plot rectangles (pt, top-left origin, figure coordinates)
HIST_W, HIST_H = 125.569, 115.162
HIST_X = [44.2399, 209.992, 375.743]
HIST_Y = [35.4384, 198.969, 362.5]
HEAT = dict(x=539.402, y=35.4384, w=367.758, h=367.758)
CBAR = dict(x=907.16, y=35.4384, w=21.6, h=367.758)

HIST_NAMES = [
    ("S1a_01_mu_n", "mu_n"), ("S1a_02_mu_p", "mu_p"), ("S1a_03_tau_n", "tau_n"),
    ("S1a_04_tau_p", "tau_p"), ("S1a_05_Nc", "Nc"), ("S1a_06_Nv", "Nv"),
    ("S1a_07_tau_ETL", "tau_ETL"), ("S1a_08_tau_HTL", "tau_HTL"),
    ("S1a_09_r_rad", "r_rad"),
]


def strip_text(root):
    """Delete every <g id="text_N"> group. Returns count removed."""
    n = 0
    for e in list(root.iter()):
        if not isinstance(e.tag, str):
            continue
        if e.get("id") and re.match(r"^text_\d+$", e.get("id")):
            e.getparent().remove(e)
            n += 1
    return n


def ref_ids(el):
    """Every id referenced from a subtree: xlink:href="#x" and url(#x)."""
    ids = set()
    for e in el.iter():
        if not isinstance(e.tag, str):
            continue
        for attr in (XL + "href", "href"):
            v = e.get(attr) or ""
            if v.startswith("#"):
                ids.add(v[1:])
        for attr in ("clip-path", "fill", "stroke", "filter", "mask"):
            m = re.search(r"url\(#([^)]+)\)", e.get(attr) or "")
            if m:
                ids.add(m.group(1))
    return ids


def defined_ids(el):
    return {e.get("id") for e in el.iter() if isinstance(e.tag, str) and e.get("id")}


def external_defs(piece, idmap, order):
    """Definitions referenced by `piece` but defined outside it (matplotlib
    shares one marker <path> per tick style across all axes of a figure)."""
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
        out.append(el)
        need |= (ref_ids(el) - have - set(d.get("id") for d in out))
    return out


def build_piece(axes_el, rect, idmap, order, name):
    """Wrap a copy of axes_el in a new canvas with `rect` placed at MARGIN."""
    g = copy.deepcopy(axes_el)
    g.tail = None
    tx = MARGIN - rect["x"]
    ty = MARGIN - rect["y"]
    W = rect["w"] + 2 * MARGIN
    H = rect["h"] + 2 * MARGIN

    root = etree.Element(CS + "svg", nsmap={None: SVGNS, "xlink": XLNS})
    root.set("width", "%.4f" % (W * PX_PER_PT))
    root.set("height", "%.4f" % (H * PX_PER_PT))
    root.set("viewBox", "0 0 %.4f %.4f" % (W, H))
    root.set("stroke-linejoin", "round")
    root.set("overflow", "hidden")

    extra = external_defs(g, idmap, order)
    if extra:
        defs = etree.SubElement(root, CS + "defs")
        for d in extra:
            defs.append(copy.deepcopy(d))
    wrap = etree.SubElement(root, CS + "g")
    wrap.set("transform", "translate(%.6f, %.6f)" % (tx, ty))
    wrap.set("id", "piece_" + name)
    wrap.append(g)

    path = os.path.join(OUTDIR, name + ".svg")
    with open(path, "wb") as f:
        f.write(etree.tostring(root, xml_declaration=True, encoding="utf-8"))
    return dict(name=name, file=path, W=W, H=H, tx=tx, ty=ty,
                rect=rect, bytes=os.path.getsize(path),
                px_w=round(W * PX_PER_PT, 4), px_h=round(H * PX_PER_PT, 4))


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    tree = etree.parse(SRC)
    root = tree.getroot()

    clip_defs = [e for e in root.iter(CS + "clipPath")]

    # ---- text-free preview, original arrangement -------------------------
    prev = copy.deepcopy(root)
    n_prev = strip_text(prev)
    with open(os.path.join(OUTDIR, "_preview_no_text.svg"), "wb") as f:
        f.write(etree.tostring(prev, xml_declaration=True, encoding="utf-8"))

    # ---- pieces ---------------------------------------------------------
    work = copy.deepcopy(root)
    n_pieces = strip_text(work)
    assert n_prev == n_pieces, (n_prev, n_pieces)
    byid = {e.get("id"): e for e in work.iter() if e.get("id")}
    order = {i: k for k, i in enumerate(byid)}
    assert not list(work.iter(CS + "text")), "text survived"

    pieces = []
    for i, (name, tag) in enumerate(HIST_NAMES):
        r = i // 3
        c = i % 3
        rect = dict(x=HIST_X[c], y=HIST_Y[r], w=HIST_W, h=HIST_H)
        pieces.append(build_piece(byid["axes_%d" % (i + 1)], rect,
                                  byid, order, name))
        pieces[-1]["panel"] = tag
    pieces.append(build_piece(byid["axes_10"], HEAT, byid, order, "S1b_heatmap"))
    pieces[-1]["panel"] = "heatmap"
    pieces.append(build_piece(byid["axes_11"], CBAR, byid, order, "S1b_colorbar"))
    pieces[-1]["panel"] = "colorbar"

    # -- every id used by every piece must resolve inside that piece -------
    for p in pieces:
        pr = etree.parse(p["file"]).getroot()
        have = defined_ids(pr)
        missing = sorted(ref_ids(pr) - have)
        p["dangling"] = missing
        p["defs"] = sorted(have - defined_ids(byid["axes_" + "1"]))
        print("  refs ok: %-14s dangling=%d  defs=%d"
              % (p["name"], len(missing), len(p["defs"])))

    geo = dict(source=SRC, margin=MARGIN, removed_text_groups=n_pieces,
               hist_rect=dict(w=HIST_W, h=HIST_H), pieces=pieces)
    with open("work/geometry.json", "w", encoding="utf-8") as f:
        json.dump(geo, f, ensure_ascii=False, indent=1)

    for p in pieces:
        print("%-14s %9.3f x %9.3f pt   %6.1f x %6.1f px svg   %7d B"
              % (p["name"], p["W"], p["H"], p["px_w"], p["px_h"], p["bytes"]))
    print("removed text groups:", n_pieces)


if __name__ == "__main__":
    sys.stdout = __import__("io").TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    main()
