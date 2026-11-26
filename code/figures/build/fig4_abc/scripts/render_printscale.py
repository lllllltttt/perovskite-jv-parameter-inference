# -*- coding: utf-8 -*-
"""Render the delivered PDFs at their actual print size for visual QA."""
import os
import fitz

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
FIG = os.path.join(OUT, "figures")
QA = os.path.join(OUT, "qa")
os.makedirs(QA, exist_ok=True)

# whole row, 6.80 in wide as it will sit in the 6.80-in manuscript column
doc = fitz.open(os.path.join(FIG, "Fig4abc_preview_1x3.pdf"))
p = doc[0]
print("preview page size: %.2f x %.2f pt = %.3f x %.3f in"
      % (p.rect.width, p.rect.height, p.rect.width / 72, p.rect.height / 72))
p.get_pixmap(dpi=200).save(os.path.join(QA, "preview_actual_width_200dpi.png"))
doc.close()

# 1:1 detail crops (600 dpi) of the two regions the request calls out
for tag, clip_name, rect_in in [
        ("Fig4a", "a_legend_printscale", (0.25, 0.80, 1.70, 1.36)),
        ("Fig4c", "c_inset_printscale", (0.30, 0.40, 2.11, 1.22)),
        ("Fig4c", "c_tail_printscale", (1.20, 0.85, 2.11, 1.40)),
]:
    doc = fitz.open(os.path.join(FIG, tag + ".pdf"))
    p = doc[0]
    r = fitz.Rect(*[v * 72 for v in rect_in])
    p.get_pixmap(dpi=600, clip=r).save(os.path.join(QA, clip_name + ".png"))
    doc.close()
    print("wrote qa/%s.png" % clip_name)
