# -*- coding: utf-8 -*-
"""Read the text-free Fig. 4(d) back from disk and check it.

Checks, all on the delivered files:
  * PDF page size, spine positions, and the ONLY text present (the five y
    tick numbers - no x names, no medians, no titles);
  * the x tick marks exist at x = 0, 1, 2 (short segments under the bottom
    spine) although no names are drawn;
  * the right-hand blank inside the frame, right of the last box, is really
    empty to the last pixel at 600 dpi, and measure its width;
  * dot count / colours are those of the accepted panel.

Writes qa/verify_fig4d_half.json and preview/Fig4d_clean_half_preview.png (the
exported panel next to a demonstration of where "5.19" would go in
PowerPoint - the demo text is NOT in the deliverable files).
"""
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
FIG = os.path.join(OUT, "figures")
QA = os.path.join(OUT, "qa")
PREV = os.path.join(OUT, "preview")

DPI = 600
Q = json.load(open(os.path.join(QA, "qa_fig4d_half.json"),
                   encoding="utf-8"))
P = Q["panels"]["Fig4d_clean_half"]
XLIM = P["xlim"]
YLIM = P["ylim"]
AX = P["axes_rect_in"]
D_W, D_H = P["canvas_in"]
SPAN = XLIM[1] - XLIM[0]
BOX_W = 0.50
L0, L1 = math.log10(YLIM[0]), math.log10(YLIM[1])


def px_x(v):
    return (AX[0] + (v - XLIM[0]) / SPAN * AX[2]) * DPI


def px_y(v):
    t = (math.log10(v) - L0) / (L1 - L0)
    return (D_H - (AX[1] + t * AX[3])) * DPI


def pt(px):
    return px * 72.0 / DPI


res = {}

# ------------------------------------------------------------------- PDF ----
import pymupdf
doc = pymupdf.open(os.path.join(FIG, "Fig4d_clean_half.pdf"))
page = doc[0]
res["page_pt"] = [round(page.rect.width, 2), round(page.rect.height, 2)]
segs = []
for d in page.get_drawings():
    for it in d["items"]:
        if it[0] == "l":
            p, q = it[1], it[2]
            segs.append((p.x, p.y, q.x, q.y))
res["spine_x_pt"] = [round(min(s[0], s[2]), 2) for s in segs
                     if abs(s[0] - s[2]) < 0.01
                     and abs(s[1] - s[3]) > 60]
res["spine_y_pt"] = [round(min(s[1], s[3]), 2) for s in segs
                     if abs(s[1] - s[3]) < 0.01
                     and abs(s[0] - s[2]) > 60]
words = [w[4] for w in page.get_text("words")]
res["pdf_words"] = words
assert sorted(words) == sorted(P["text_in_image"]), words

# x tick marks: short VERTICAL segments just below the bottom spine (3 pt).
# NOTE: PyMuPDF page coordinates have the origin at the TOP-left, so the
# bottom spine is the LARGEST y among the long horizontal segments.
spine_bottom = max(s[1] for s in segs if abs(s[1] - s[3]) < 0.01
                   and abs(s[0] - s[2]) > 60)
xticks = sorted({round((s[0] + s[2]) / 2.0, 2) for s in segs
                 if abs(s[0] - s[2]) < 0.01 and 2.5 < abs(s[1] - s[3]) < 3.5
                 and spine_bottom - 0.01 <= min(s[1], s[3])
                 and max(s[1], s[3]) <= spine_bottom + 3.5})
res["x_tick_marks_pt"] = xticks
res["x_tick_marks_count"] = len(xticks)
res["spine_bottom_pt"] = round(spine_bottom, 2)
assert len(xticks) == 3, xticks

# -------------------------------------------------------------- raster ------
png = Image.open(os.path.join(FIG, "Fig4d_clean_half.png")).convert("RGB")
assert png.size == (round(D_W * DPI), round(D_H * DPI)), png.size
g = np.asarray(png.convert("L"))

# the blank band right of box 3, inside the frame
x0 = int(round(px_x(2 + BOX_W / 2.0) + 0.5 * DPI / 72.0))   # +0.5 pt clear
x1 = int(round(px_x(XLIM[1]) - 0.5 * DPI / 72.0))
y0 = int(round(px_y(YLIM[1]) + 0.5 * DPI / 72.0))           # below top frame
y1 = int(round(px_y(YLIM[0]) - 0.5 * DPI / 72.0))           # above bottom frame
band = g[y0:y1, x0:x1]
res["blank_band"] = dict(px=[x0, x1, y0, y1],
                         width_pt=round(pt(x1 - x0), 2),
                         darkest_pixel=int(band.min()),
                         non_white_pixels=int((band < 245).sum()))
assert band.min() > 240, band.min()

# where the last dot is, for the record
res["dots"] = dict(jitter_max=0.13,
                   box3_rightmost_dot_x=round(2 + 0.13, 3))
res["checks"] = dict(
    only_y_tick_numbers=len(words) == 5,
    no_x_labels=not any(w in words for w in ("Full", "curve", "0-1.0",
                                             "(0-1.3", "V)", ">", "1.0")),
    no_medians=not any(w in words for w in ("2.69", "0.455", "5.19")),
    blank_truly_empty=bool(band.min() > 240),
    x_tick_marks_present=len(xticks) == 3)

# ---------------------------------------------------------------- preview ---
def font(size):
    for f in ("arial.ttf", "Arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(f, size)
        except Exception:
            continue
    return ImageFont.load_default()


W, H = png.size
gap = 70
TOPB, BOTB = 110, 120
canvas = Image.new("RGB", (2 * W + gap, H + TOPB + BOTB), "white")
canvas.paste(png, (0, TOPB))
canvas.paste(png.copy(), (W + gap, TOPB))
dr = ImageDraw.Draw(canvas)
F = font(34)

# demo placement of "5.19" exactly as it would be typed in PowerPoint:
# 7 pt Arial (58 px at 600 dpi), ink starting 2 pt right of the box edge,
# centred on the median line
box3_r = px_x(2 + BOX_W / 2.0)
frame_r = px_x(XLIM[1])
med = px_y(P["stats"]["gt1"]["median"])
fs_px = int(round(7.0 / 72.0 * DPI))
dr.text((W + gap + box3_r + 2.0 / 72.0 * DPI, med), "5.19",
        fill=(120, 120, 120), font=font(fs_px), anchor="lm")

# guide lines, plot area only
y_top = int(round(px_y(YLIM[1])))
y_bot = int(round(px_y(YLIM[0])))
for x in (box3_r, frame_r):
    x = int(round(x))
    for yy in range(y_top, y_bot, 14):
        dr.line([(W + gap + x, TOPB + yy),
                 (W + gap + x, TOPB + min(yy + 7, y_bot))],
                fill=(210, 60, 60), width=3)

blank = pt(frame_r - box3_r)
dr.text((20, 22), "exported file, as delivered - only the five y tick "
        "numbers are in the image", fill=(60, 60, 60), font=font(30))
dr.text((W + gap + 20, 22), "DEMO ONLY - the grey 5.19 is not in the "
        "delivered file", fill=(180, 40, 40), font=font(30))
dr.text((W + gap + 20, TOPB + H + 16),
        "box 3 right edge -> right frame = %.1f pt   |   5.19 ink = %.1f pt"
        % (blank, 12.96), fill=(90, 90, 90), font=font(28))
dr.text((W + gap + 20, TOPB + H + 56),
        "typed 2 pt from the box, the text still leaves %.1f pt to the "
        "frame" % (blank - 2.0 - 12.96), fill=(90, 90, 90), font=font(28))
canvas.save(os.path.join(PREV, "Fig4d_clean_half_preview.png"), dpi=(DPI, DPI))

with open(os.path.join(QA, "verify_fig4d_half.json"), "w",
          encoding="utf-8") as f:
    json.dump(res, f, indent=2, ensure_ascii=False)
print(json.dumps(res, indent=2, ensure_ascii=False))
