"""Verify the 11 pieces against the original document.

Checks
  A  every piece SVG parses, carries no text, and every #id reference resolves
  B  geometry: 9 identical histogram canvases, square heatmap, plot area inside
  C  XML identity: the piece's axes subtree is element-for-element identical to
     the original axes subtree (the only change in the document is that the
     <g id="text_N"> groups were deleted)
  D  pixel identity: piece PNG == a render of the same document, same window,
     with the other panels removed (same engine, same sub-pixel phase)
  E  nothing is cropped: the outer 2 pt ring of every piece is empty
"""
import io
import json
import os
import re
import sys

import numpy as np
from lxml import etree
from PIL import Image

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

CS = "{http://www.w3.org/2000/svg}"
XL = "{http://www.w3.org/1999/xlink}"
PT = 600.0 / 72.0
GEO = json.load(open("work/geometry.json", encoding="utf-8"))
SRC = "out/svg/_preview_no_text.svg"
fails = []


def ref_ids(el):
    out = set()
    for e in el.iter():
        if not isinstance(e.tag, str):
            continue
        for a in (XL + "href", "href"):
            v = e.get(a) or ""
            if v.startswith("#"):
                out.add(v[1:])
        for a in ("clip-path", "fill", "stroke", "filter", "mask"):
            m = re.search(r"url\(#([^)]+)\)", e.get(a) or "")
            if m:
                out.add(m.group(1))
    return out


def ids_of(el):
    return {e.get("id") for e in el.iter()
            if isinstance(e.tag, str) and e.get("id")}


def axes_id(p):
    n = p["name"]
    if n == "S1b_heatmap":
        return "axes_10"
    if n == "S1b_colorbar":
        return "axes_11"
    return "axes_%d" % int(n.split("_")[1])


def sig(e):
    return (e.tag, tuple(sorted(e.attrib.items())), (e.text or "").strip())


def cmp_tree(a, b, path="", mism=None):
    """Element-for-element comparison of two lxml subtrees."""
    if mism is None:
        mism = []
    sa, sb = sig(a), sig(b)
    if sa != sb:
        mism.append(path or a.tag)
        return mism
    ca, cb = [c for c in a if isinstance(c.tag, str)], \
             [c for c in b if isinstance(c.tag, str)]
    if len(ca) != len(cb):
        mism.append("%s child-count %d vs %d" % (path, len(ca), len(cb)))
        return mism
    for i, (x, y) in enumerate(zip(ca, cb)):
        cmp_tree(x, y, "%s/%s[%d]" % (path, x.tag.split('}')[-1], i), mism)
    return mism


# ---------------- A: structure ------------------------------------------
print("== A  structure / references ==")
total_el = 0
for p in GEO["pieces"]:
    root = etree.parse(p["file"]).getroot()
    n_text = len(list(root.iter(CS + "text")))
    n_tspan = len(list(root.iter(CS + "tspan")))
    n_style = len(list(root.iter(CS + "style")))
    have, need = ids_of(root), ref_ids(root)
    dangling = sorted(need - have)
    n_el = sum(1 for e in root.iter() if isinstance(e.tag, str))
    total_el += n_el
    ok = (n_text == 0 and n_tspan == 0 and n_style == 0 and not dangling)
    print("  %-14s elements=%-4d text=%d tspan=%d dangling=%s  %s"
          % (p["name"], n_el, n_text, n_tspan, dangling or "none",
             "PASS" if ok else "FAIL"))
    if not ok:
        fails.append(p["name"])

# ---------------- B: geometry -------------------------------------------
print("\n== B  geometry ==")
hist = [p for p in GEO["pieces"] if p["name"].startswith("S1a")]
dims = {(round(p["W"], 4), round(p["H"], 4)) for p in hist}
heat = [p for p in GEO["pieces"] if p["name"] == "S1b_heatmap"][0]
cbar = [p for p in GEO["pieces"] if p["name"] == "S1b_colorbar"][0]
print("  9 histograms: %s  -> %s" % (sorted(dims), "PASS" if len(dims) == 1 else "FAIL"))
print("  heatmap %.4f x %.4f  -> %s" % (heat["W"], heat["H"],
                                        "PASS" if abs(heat["W"] - heat["H"]) < 1e-9 else "FAIL"))
print("  colorbar %.4f x %.4f" % (cbar["W"], cbar["H"]))
if len(dims) != 1 or len(hist) != 9 or abs(heat["W"] - heat["H"]) > 1e-9:
    fails.append("geometry")

# ---------------- C: XML identity ---------------------------------------
print("\n== C  XML identity with the original axes subtree ==")
src = etree.parse(SRC).getroot()
src_byid = {e.get("id"): e for e in src.iter() if e.get("id")}
for p in GEO["pieces"]:
    want = src_byid[axes_id(p)]
    got = [e for e in etree.parse(p["file"]).getroot().iter(CS + "g")
           if e.get("id") == axes_id(p)][0]
    mism = cmp_tree(want, got)
    n = sum(1 for e in want.iter() if isinstance(e.tag, str))
    print("  %-14s %4d elements compared, mismatches: %d  %s"
          % (p["name"], n, len(mism), "PASS" if not mism else "FAIL " + str(mism[:3])))
    if mism:
        fails.append(p["name"] + "-xml")

# ---------------- D: pixel identity -------------------------------------
print("\n== D  pixel identity vs the same window of the original document ==")
for p in GEO["pieces"]:
    A = np.asarray(Image.open("work/render/%s.png" % p["name"]).convert("RGB"))
    B = np.asarray(Image.open("work/render_ref/%s.png" % p["name"]).convert("RGB"))
    if A.shape != B.shape:
        print("  %-14s SHAPE %s vs %s" % (p["name"], A.shape, B.shape))
        fails.append(p["name"] + "-shape")
        continue
    d = np.abs(A.astype(np.int16) - B.astype(np.int16)).max(axis=2)
    pct = 100.0 * (d > 0).mean()
    print("  %-14s %5d x %5d  differing pixels: %8d (%.4f%%)  max %3d  %s"
          % (p["name"], A.shape[1], A.shape[0], int((d > 0).sum()), pct,
             int(d.max()), "PASS" if pct == 0 else "FAIL"))
    if pct != 0:
        fails.append(p["name"] + "-pixel")

# ---------------- E: nothing cropped ------------------------------------
print("\n== E  no cropping (outer 2 pt ring must be blank) ==")
ring = int(round(2 * PT))
for p in GEO["pieces"]:
    A = np.asarray(Image.open("work/render/%s.png" % p["name"]).convert("RGB"))
    m = (A < 250).any(axis=2)
    edge = np.concatenate([m[:ring].reshape(-1), m[-ring:].reshape(-1),
                           m[:, :ring].reshape(-1), m[:, -ring:].reshape(-1)])
    n = int(edge.sum())
    print("  %-14s ink pixels inside the 2 pt outer ring: %d  %s"
          % (p["name"], n, "PASS" if n == 0 else "FAIL"))
    if n:
        fails.append(p["name"] + "-crop")

print("\nRESULT:", "ALL PASS" if not fails else "FAILURES: %s" % fails)
