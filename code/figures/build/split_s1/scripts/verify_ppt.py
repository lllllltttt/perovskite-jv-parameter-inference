# -*- coding: utf-8 -*-
"""Quantify the real-PowerPoint render against the 600 dpi preview.

Reads   work/ppt/probe_split_slide_hi.png   (PowerPoint exported, 8102x4254)
        work/render/_preview_no_text.png    (same document, Chromium @600 dpi)
        work/ppt/control_whole.png          (the WHOLE figure as one picture)

Reports
  1  frame bbox of every piece in both renders
  2  the six y-tick centres of S1a_01 (a direct measure of the vertical map)
  3  the 9x9 heatmap cell colours, PowerPoint vs preview
  4  the same tick measure for the unsplit control picture
"""
import io
import json
import sys

import numpy as np
from PIL import Image

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

GEO = json.load(open("work/geometry.json", encoding="utf-8"))
FIG_W = 972.212
PPT = np.asarray(Image.open("work/ppt/probe_split_slide_hi.png").convert("L")).astype(float)
PRE = np.asarray(Image.open("work/render/_preview_no_text.png").convert("L")).astype(float)
CTR = np.asarray(Image.open("work/ppt/control_whole.png").convert("L")).astype(float)
CPT = np.asarray(Image.open("work/ppt/probe_split_slide_hi.png").convert("RGB")).astype(int)
CPR = np.asarray(Image.open("work/render/_preview_no_text.png").convert("RGB")).astype(int)
S = PPT.shape[1] / FIG_W
TICKS = [35.4384, 58.4709, 81.5034, 104.536, 127.568, 150.601]


def bbox(img, r, pad=1.5):
    X0, X1 = int((r["x"]) * S) + 2, int((r["x"] + r["w"]) * S)
    Y0, Y1 = int((r["y"] - pad) * S), int((r["y"] + r["h"] + pad) * S)
    m = (255 - img[Y0:Y1, X0:X1]) > 40
    rows = np.where(m.any(axis=1))[0]
    cols = np.where(m.any(axis=0))[0]
    return ((Y0 + rows[0]) / S, (Y0 + rows[-1]) / S,
            (X0 + cols[0]) / S, (X0 + cols[-1]) / S)


def centres(img, xpt, y0=30.0, y1=158.0):
    c = int(round(xpt * S))
    v = (255 - img[int(y0 * S):int(y1 * S), c])
    runs, st = [], None
    for i, x in enumerate(v > 40):
        if x and st is None:
            st = i
        if not x and st is not None:
            runs.append((int(y0 * S) + st, int(y0 * S) + i - 1))
            st = None
    out = []
    for p, q in runs:
        w = 255 - img[p:q + 1, c]
        out.append((w * np.arange(p, q + 1)).sum() / w.sum() / S)
    return out


print("== 1  frame bbox, PowerPoint export - Chromium preview (pt) ==")
print("   %-14s %8s %8s %8s %8s" % ("piece", "top", "bottom", "left", "right"))
for p in GEO["pieces"]:
    a, b = bbox(PPT, p["rect"]), bbox(PRE, p["rect"])
    print("   %-14s %+8.3f %+8.3f %+8.3f %+8.3f"
          % (p["name"], a[0] - b[0], a[1] - b[1], a[2] - b[2], a[3] - b[3]))

print("\n== 2  the six y-tick centres of S1a_01 (pt from the piece origin) ==")
a = [v - 29.4384 for v in centres(PPT, 42.7)]
b = [v - 29.4384 for v in centres(PRE, 42.7)]
print("   %-10s %s" % ("nominal", "  ".join("%7.3f" % (t - 29.4384) for t in TICKS)))
print("   %-10s %s" % ("PowerPoint", "  ".join("%7.3f" % v for v in a)))
print("   %-10s %s" % ("Chromium", "  ".join("%7.3f" % v for v in b)))
print("   span: nominal %.3f   PowerPoint %.3f   Chromium %.3f"
      % (TICKS[-1] - TICKS[0], a[-1] - a[0], b[-1] - b[0]))

print("\n== 3  heatmap cell colours, PowerPoint vs preview (0-255) ==")
hx, hy, hw = 539.402, 35.4384, 367.758
worst = 0
for r in range(9):
    row = []
    for c in range(9):
        x = hx + (c + 0.5) * hw / 9
        y = hy + (r + 0.5) * hw / 9
        pa = CPT[int(y * S), int(x * S)]
        pb = CPR[int(y * S), int(x * S)]
        d = int(np.abs(pa - pb).max())
        worst = max(worst, d)
        row.append(d)
    print("   row %d  %s" % (r + 1, " ".join("%2d" % v for v in row)))
print("   worst channel difference over the 81 cells: %d/255" % worst)

print("\n== 4  the same tick measure with the WHOLE figure as one picture ==")
c = [v - 29.4384 for v in centres(CTR, 42.7)]
if len(c) == 6:
    print("   span %.3f  (nominal %.3f)  offsets %s"
          % (c[-1] - c[0], TICKS[-1] - TICKS[0],
             " ".join("%+.3f" % (v - (t - 29.4384)) for v, t in zip(c, TICKS))))
