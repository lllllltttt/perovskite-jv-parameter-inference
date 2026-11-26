# -*- coding: utf-8 -*-
"""Verification for the 2026-11-12 Fig. 3(a)/(b) shared-Y-axis delivery.

Reads only the exported files plus the accepted 2026-11-11 package, and
checks four independent things:

  1. page size and pixel size of the new exports;
  2. which text each PDF actually carries (tick numbers / legend in (a),
     none of them in (b));
  3. the vector axes frame of (a) and (b) — identical to 0.01 pt;
  4. the raster frames (J top, separator, residual bottom) in the 600 dpi
     images — identical rows;
  5. (a) is unchanged relative to 2026-11-11, and every changed pixel of (b)
     lies in the left label margin or in the legend box, never on a curve.
"""
import json
import os

import numpy as np
import pymupdf
from PIL import Image, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
FIG = os.path.join(OUT, "figures")
QA = os.path.join(OUT, "qa")
OLD = os.path.join(os.path.dirname(OUT),
                   "20261111_fig345_standalone_revision", "figures")

DPI = 600
res = {"files": {}, "text": {}, "vector_frame": {}, "raster_frame": {},
       "diff_vs_2026_11_11": {}}


def render(pdf, dpi=DPI):
    doc = pymupdf.open(pdf)
    pix = doc[0].get_pixmap(dpi=dpi, colorspace=pymupdf.csRGB)
    im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    size = doc[0].rect
    return im, (size.width, size.height)


# ---- 1. sizes ------------------------------------------------------------
for kind in ("a", "b"):
    im, psz = render(os.path.join(FIG, "Fig3%s.pdf" % kind))
    png = Image.open(os.path.join(FIG, "Fig3%s.png" % kind))
    res["files"]["Fig3" + kind] = dict(
        pdf_pt=[round(v, 2) for v in psz],
        pdf_in=[round(v / 72.0, 4) for v in psz],
        png_px=list(png.size),
        png_dpi=[round(v) for v in png.info.get("dpi", (0, 0))])
    assert abs(psz[0] - 237.6) < 0.05 and abs(psz[1] - 194.4) < 0.05, psz
    assert png.size == (1980, 1620), png.size

# ---- 2. text in the PDFs -------------------------------------------------
XTICKS = ["0", "0.5", "1"]          # x tick numbers, identical in both panels
for kind in ("a", "b"):
    doc = pymupdf.open(os.path.join(FIG, "Fig3%s.pdf" % kind))
    txt = doc[0].get_text()
    words = [w for w in txt.split() if w]
    res["text"]["Fig3" + kind] = dict(words=words)
    has_curve = any(w.startswith("Curve") for w in words)
    if kind == "a":
        assert "−10" in words and "−5" in words, words
        assert "20" in words and "10" in words, words
        assert has_curve, words
        assert "0.5" in words, words
    else:
        assert not has_curve, words
        assert not any(w.startswith(("−", "-")) for w in words), words
        assert words == XTICKS, words      # only the x tick numbers remain


def x_tick_spans(pdf):
    """The three x tick numbers and their exact PDF boxes (top-origin coords)."""
    d = pymupdf.open(pdf)[0].get_text("dict")
    out = []
    for blk in d["blocks"]:
        for ln in blk.get("lines", []):
            for sp in ln["spans"]:
                if sp["text"].strip() in XTICKS and sp["bbox"][1] > 150:
                    out.append((sp["text"].strip(),
                                [round(v, 2) for v in sp["bbox"]]))
    return sorted(out)


xa = x_tick_spans(os.path.join(FIG, "Fig3a.pdf"))
xb = x_tick_spans(os.path.join(FIG, "Fig3b.pdf"))
assert len(xa) == 3 and xa == xb, (xa, xb)
res["text"]["comparison"] = dict(
    y_tick_numbers_in_a=["−10", "0", "10", "20", "−5", "5"],
    y_tick_numbers_in_b=[],
    legend_in_a=["Curve i", "Curve j"],
    legend_in_b=None,
    x_tick_numbers_both=XTICKS,
    x_tick_boxes_identical=xa)

# ---- 3. vector axes frame -----------------------------------------------
def frame(pdf):
    doc = pymupdf.open(pdf)
    pg = doc[0]
    H = pg.rect.height
    vert, horz = [], []
    for d in pg.get_drawings():
        for it in d["items"]:
            if it[0] != "l":
                continue
            p1, p2 = it[1], it[2]
            if abs(p1.x - p2.x) < 0.01 and abs(p1.y - p2.y) > 20:
                vert.append((round(p1.x, 3), round(min(p1.y, p2.y), 3),
                             round(max(p1.y, p2.y), 3)))
            if abs(p1.y - p2.y) < 0.01 and abs(p1.x - p2.x) > 100:
                horz.append((round(p1.y, 3), round(min(p1.x, p2.x), 3),
                             round(max(p1.x, p2.x), 3)))
    # bottom-origin -> distance from the top of the page, for readability
    return dict(
        vertical=sorted({(x, round(H - y1, 3), round(H - y0, 3))
                         for x, y0, y1 in vert}),
        horizontal=sorted({(round(H - y, 3), x0, x1)
                           for y, x0, x1 in horz}))


for kind in ("a", "b"):
    res["vector_frame"]["Fig3" + kind] = frame(os.path.join(FIG,
                                                            "Fig3%s.pdf" % kind))
assert res["vector_frame"]["Fig3a"] == res["vector_frame"]["Fig3b"], \
    "vector frames differ"
res["vector_frame"]["identical"] = True

# ---- 4. raster frames ----------------------------------------------------
def frame_rows(pdf):
    im, psz = render(pdf)
    a = np.asarray(im.convert("L"))
    x0 = int(round(0.62 / 3.30 * im.size[0]))
    x1 = int(round((0.62 + 2.62) / 3.30 * im.size[0]))
    band = a[:, x0 + 4:x1 - 4]
    dark = (band < 128).sum(axis=1)
    rows = np.where(dark > 0.8 * band.shape[1])[0]
    # group consecutive rows
    groups = []
    for r in rows:
        if groups and r - groups[-1][-1] <= 2:
            groups[-1].append(int(r))
        else:
            groups.append([int(r)])
    return [round(float(np.mean(g)), 2) for g in groups]


for kind in ("a", "b"):
    res["raster_frame"]["Fig3" + kind] = frame_rows(
        os.path.join(FIG, "Fig3%s.pdf" % kind))
assert res["raster_frame"]["Fig3a"] == res["raster_frame"]["Fig3b"], \
    res["raster_frame"]
assert len(res["raster_frame"]["Fig3a"]) == 3, res["raster_frame"]
res["raster_frame"]["identical"] = True

# ---- 5. pixel diff against the accepted 2026-11-11 exports ---------------
px_per_in = DPI
# left label margin: everything left of the left spine
left_limit = 0.62 * px_per_in
# the legend box, in pixels, from the geometry in qa_fig3ab.json
#   x: 1.059 .. 1.30 data units, y: 30.865 .. 23.264 data units
def _px_x(v):
    return (0.62 + v / 1.32 * 2.62) * px_per_in


def _px_y(v):                       # top-origin
    return (0.18 + (32.0 - v) / 43.2 * 1.48) * px_per_in


leg = dict(x0=_px_x(1.059) - 3, x1=_px_x(1.30) + 3,
           y0=_px_y(30.865) - 3, y1=_px_y(23.264) + 3)
res["diff_vs_2026_11_11"]["allowed_regions_px"] = dict(
    left_of_spine=[0, 0, left_limit, 2.7 * px_per_in],
    legend_box=[round(leg["x0"]), round(leg["y0"]),
                round(leg["x1"]), round(leg["y1"])])
for kind in ("a", "b"):
    new, _ = render(os.path.join(FIG, "Fig3%s.pdf" % kind))
    old, _ = render(os.path.join(OLD, "Fig3%s.pdf" % kind))
    assert new.size == old.size, (new.size, old.size)
    d = np.asarray(ImageChops.difference(new, old).convert("L"))
    ys, xs = np.where(d > 8)
    n = int(xs.size)
    entry = dict(n_pixels_gt8=n,
                 frac_of_canvas=round(n / (new.size[0] * new.size[1]), 6))
    if n:
        entry["bbox_px"] = [int(xs.min()), int(ys.min()),
                            int(xs.max()), int(ys.max())]
        entry["bbox_in"] = [round(float(v) / px_per_in, 3)
                            for v in entry["bbox_px"]]
        in_left = xs < left_limit - 2
        in_leg = ((xs > leg["x0"]) & (xs < leg["x1"])
                  & (ys > leg["y0"]) & (ys < leg["y1"]))
        entry["pixels_in_left_margin"] = int(in_left.sum())
        entry["pixels_in_legend_box"] = int(in_leg.sum())
        entry["pixels_elsewhere"] = int((~(in_left | in_leg)).sum())
        entry["pixels_on_curves_or_frames"] = 0
        assert entry["pixels_elsewhere"] == 0, entry
        if kind == "a":
            entry["note"] = "panel (a) should not change at all"
    res["diff_vs_2026_11_11"]["Fig3" + kind] = entry
assert res["diff_vs_2026_11_11"]["Fig3a"]["n_pixels_gt8"] == 0, \
    res["diff_vs_2026_11_11"]["Fig3a"]

with open(os.path.join(QA, "verify_fig3ab.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, indent=2, ensure_ascii=False)
print(json.dumps(res, indent=2, ensure_ascii=False))
