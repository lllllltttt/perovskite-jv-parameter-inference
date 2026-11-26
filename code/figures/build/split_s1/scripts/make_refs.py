"""Build a 'reference window' SVG for every piece.

Each reference is the *whole* text-free figure viewed through the same window
as the piece (same viewBox origin, same size, same px-per-pt convention).  It
is rendered by the same engine at the same scale, so the piece and its
reference have identical sub-pixel phase and can be compared pixel for pixel.
"""
import io
import json
import os
import sys
import copy
from lxml import etree

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

GEO = json.load(open("work/geometry.json", encoding="utf-8"))
SRC = "out/svg/_preview_no_text.svg"
OUT = "work/ref"
os.makedirs(OUT, exist_ok=True)
PX_PER_PT = 96.0 / 72.0
M = GEO["margin"]

CS = "{http://www.w3.org/2000/svg}"


def axes_id(p):
    n = p["name"]
    if n == "S1b_heatmap":
        return "axes_10"
    if n == "S1b_colorbar":
        return "axes_11"
    return "axes_%d" % (int(n.split("_")[1]))


for p in GEO["pieces"]:
    r = p["rect"]
    x0, y0 = r["x"] - M, r["y"] - M
    W, H = p["W"], p["H"]

    # The heatmap and colour bar sit 0 pt apart, so for those two windows the
    # neighbour bleeds into the 6 pt margin: drop it.  The nine histograms are
    # 40 pt apart and no neighbour reaches their margin, so their window is
    # taken from the untouched document (which also keeps the shared tick
    # <path> definitions that live inside axes_1 alive).
    full = etree.parse(SRC).getroot()
    if p["name"] in ("S1b_heatmap", "S1b_colorbar"):
        keep = axes_id(p)
        for g in list(full.iter(CS + "g")):
            gid = g.get("id") or ""
            if gid.startswith("axes_") and gid != keep:
                g.getparent().remove(g)
    root = full
    root.set("width", "%.4f" % (W * PX_PER_PT))
    root.set("height", "%.4f" % (H * PX_PER_PT))
    root.set("viewBox", "%.6f %.6f %.4f %.4f" % (x0, y0, W, H))
    path = os.path.join(OUT, p["name"] + ".svg")
    with open(path, "wb") as f:
        f.write(etree.tostring(root, xml_declaration=True, encoding="utf-8"))
    print("%-14s viewBox %.4f %.4f %.4f %.4f" % (p["name"], x0, y0, W, H))
