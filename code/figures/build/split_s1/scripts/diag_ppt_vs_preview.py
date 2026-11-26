# -*- coding: utf-8 -*-
"""Diagnose PowerPoint export vs 600 dpi preview, frame-anchored.

Compares geometry by detecting each panel frame, then compares bar-top
profiles inside the detected frame so a window offset cannot fake a mismatch.
"""
import io
import json
import sys

import numpy as np
from PIL import Image

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

GEO = json.load(open("work/geometry.json", encoding="utf-8"))
FIG_W, FIG_H = 972.212, 510.466

PPT = np.asarray(Image.open("work/ppt/probe_split_slide_hi.png").convert("L"))
PRE = np.asarray(Image.open("work/render/_preview_no_text.png").convert("L"))
s_ppt = PPT.shape[1] / FIG_W
s_pre = PRE.shape[1] / FIG_W
print("ppt  %s  %.4f px/pt" % (PPT.shape, s_ppt))
print("pre  %s  %.4f px/pt" % (PRE.shape, s_pre))


def ink(img):
    return img < 200


def frame_bbox(img, s, x, y, w, h, pad=8.0):
    """Bbox of dark ink in a window around the expected frame, in pt."""
    X0 = int((x - pad) * s)
    X1 = int((x + w + pad) * s) + 1
    Y0 = int((y - pad) * s)
    Y1 = int((y + h + pad) * s) + 1
    sub = ink(img)[Y0:Y1, X0:X1]
    cols = np.where(sub.any(axis=0))[0]
    rows = np.where(sub.any(axis=1))[0]
    if len(cols) == 0:
        return None
    return ((X0 + cols[0]) / s, (Y0 + rows[0]) / s,
            (X0 + cols[-1]) / s, (Y0 + rows[-1]) / s)


def profile(img, s, bbox, band=2.0):
    """Topmost ink for each pixel column inside the frame, as (x_pt, y_pt)
    relative to the frame's top-left corner."""
    x0, y0, x1, y1 = bbox
    X0, X1 = int(round(x0 * s)) + 1, int(round(x1 * s))
    Y0, Y1 = int(round((y0 + band) * s)), int(round((y1 - band) * s)) + 1
    sub = ink(img)[Y0:Y1, max(X0, 0):X1]
    xs, ys = [], []
    for c in range(sub.shape[1]):
        col = np.where(sub[:, c])[0]
        if len(col):
            xs.append((max(X0, 0) + c) / s - x0)
            ys.append((Y0 + col[0]) / s - y0)
    return np.array(xs), np.array(ys)


rows = []
print("\n%-14s %-42s %-42s" % ("piece", "PPT frame (x0,y0,x1,y1)", "PREVIEW frame"))
for p in GEO["pieces"]:
    r = p["rect"]
    b_ppt = frame_bbox(PPT, s_ppt, r["x"], r["y"], r["w"], r["h"])
    b_pre = frame_bbox(PRE, s_pre, r["x"], r["y"], r["w"], r["h"])
    d = [b_ppt[i] - b_pre[i] for i in range(4)] if b_ppt and b_pre else None
    print("%-14s %-42s %-42s  d=%s"
          % (p["name"],
             "(%.2f,%.2f,%.2f,%.2f)" % b_ppt if b_ppt else "none",
             "(%.2f,%.2f,%.2f,%.2f)" % b_pre if b_pre else "none",
             "" if d is None else " ".join("%+.2f" % v for v in d)))
    rows.append((p, b_ppt, b_pre))

print("\nbar-top profile inside the detected frame (pt below frame top):")
for p, b_ppt, b_pre in rows:
    if not p["name"].startswith("S1a") or not b_ppt or not b_pre:
        continue
    a_x, a_y = profile(PPT, s_ppt, b_ppt)
    b_x, b_y = profile(PRE, s_pre, b_pre)
    # sample at the 60 bar centres, where the top edge is flat
    plot_w = p["rect"]["w"]
    centres = (np.arange(60) + 0.5) * plot_w / 60.0
    best = None
    for dx in np.arange(-0.5, 0.5 + 1e-9, 0.05):
        a = np.interp(centres + dx, a_x, a_y)
        b = np.interp(centres, b_x, b_y)
        m = np.abs(a - b).mean()
        if best is None or m < best[0]:
            best = (m, dx, a, b)
    m, dx, a, b = best
    diff = np.abs(a - b)
    print("  %-14s bars=60  best dx=%+.2f pt  mean=%.3f  max=%.3f  "
          "within 0.5 pt: %d/60"
          % (p["name"], dx, diff.mean(), diff.max(), int((diff <= 0.5).sum())))
