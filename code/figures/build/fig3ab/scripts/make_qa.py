# -*- coding: utf-8 -*-
"""QA images for the Fig. 3(a)/(b) shared-Y-axis delivery.

Writes, into qa/:
  crops/Fig3a_left_edge.png     left strip of (a): numbers + tick marks
  crops/Fig3b_left_edge.png     left strip of (b): tick marks only
  crops/Fig3ab_topright.png     upper-right corner, (a) legend vs (b) empty
  alignment_overlay.png         both panels at assembly distance, with the
                                three frame rows and both spines drawn as
                                dashed guides
  diff_b_vs_2026_11_11.png      every pixel (b) lost, painted red
"""
import json
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
FIG = os.path.join(OUT, "figures")
QA = os.path.join(OUT, "qa")
CROP = os.path.join(QA, "crops")
OLD = os.path.join(os.path.dirname(OUT),
                   "20261111_fig345_standalone_revision", "figures")
os.makedirs(CROP, exist_ok=True)

A = Image.open(os.path.join(FIG, "Fig3a.png"))
B = Image.open(os.path.join(FIG, "Fig3b.png"))
assert A.size == B.size == (1980, 1620)

# ---- crops ---------------------------------------------------------------
A.crop((0, 0, 470, 1620)).save(os.path.join(CROP, "Fig3a_left_edge.png"),
                               dpi=(600, 600))
B.crop((0, 0, 470, 1620)).save(os.path.join(CROP, "Fig3b_left_edge.png"),
                               dpi=(600, 600))
box = (1400, 60, 1980, 460)
ca, cb = A.crop(box), B.crop(box)
two = Image.new("RGB", (2 * ca.size[0] + 24, ca.size[1]), "white")
two.paste(ca, (0, 0))
two.paste(cb, (ca.size[0] + 24, 0))
two.save(os.path.join(CROP, "Fig3ab_topright.png"), dpi=(600, 600))

# ---- diff map of (b) against 2026-11-11 ---------------------------------
def render(pdf):
    import pymupdf
    doc = pymupdf.open(pdf)
    pix = doc[0].get_pixmap(dpi=600, colorspace=pymupdf.csRGB)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


old_b = render(os.path.join(OLD, "Fig3b.pdf"))
new_b = render(os.path.join(FIG, "Fig3b.pdf"))
d = np.asarray(ImageChops.difference(old_b, new_b).convert("L"))
mask = d > 8
gray = np.asarray(new_b.convert("L"))
rgb = np.dstack([gray, gray, gray]).astype(np.uint8)
rgb[mask] = [220, 30, 30]
Image.fromarray(rgb).save(os.path.join(QA, "diff_b_vs_2026_11_11.png"),
                          dpi=(600, 600))

# ---- alignment overlay --------------------------------------------------
qa = json.load(open(os.path.join(QA, "verify_fig3ab.json"), encoding="utf-8"))
rows_px = qa["raster_frame"]["Fig3a"]
spine_x = [0.62, 0.62 + 2.62]
GUT = 0.10
CV = 3.30
W = 2 * CV + GUT
H = 2.70

fig = plt.figure(figsize=(W, H), dpi=300)
fig.patch.set_facecolor("white")
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.axis("off")
ax.imshow(np.asarray(A), extent=[0, CV, 0, H], zorder=1)
ax.imshow(np.asarray(B), extent=[CV + GUT, W, 0, H], zorder=1)

for r in rows_px:
    y = H - r / 600.0
    ax.plot([0, W], [y, y], color="#d62728", lw=0.7,
            ls=(0, (6, 3)), zorder=5, alpha=0.9)
for x0 in (0, CV + GUT):
    for dx in spine_x:
        ax.plot([x0 + dx, x0 + dx], [0, H], color="#2ca02c", lw=0.6,
                ls=(0, (2, 2)), zorder=5, alpha=0.85)
ax.text(CV / 2, H - 0.06, "frame rows (600 dpi): " +
        " / ".join("%.1f" % r for r in rows_px) + " px — identical in (a) and (b)",
        ha="center", va="center", fontsize=6.5, color="#d62728")
fig.savefig(os.path.join(QA, "alignment_overlay.png"), dpi=300,
            facecolor="white")
fig.savefig(os.path.join(QA, "alignment_overlay.pdf"), facecolor="white")
plt.close(fig)
print("wrote crops, diff map and alignment overlay")
print("frame rows:", rows_px, "spines x (in):", spine_x)
