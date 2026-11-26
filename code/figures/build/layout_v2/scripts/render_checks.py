# -*- coding: utf-8 -*-
"""Render the three repaired locations from the delivered PDFs (and the same
crops from the previous v2 PDFs, for comparison)."""
import os, pymupdf
from PIL import Image

V2  = r"E:\project\work1\20261006\manuscript_figures_SI_integrated_v2"
NEW = r"E:\project\work1\20261006\manuscript_figures_SI_integrated_v2_layout_final"
OUT = os.path.join(NEW, "render_checks")
BEF = os.path.join(OUT, "before_v2")
os.makedirs(BEF, exist_ok=True)
DPI = 300

MS  = r"\manuscript\Manuscript_20261002_Working_integrated.pdf"
SI  = r"\si\Supplementary_Information_synced.pdf"

# clip rectangles in PDF points
CROPS = {
 "01_manuscript_p8_unit":            (MS, 8,  pymupdf.Rect(50, 68, 566, 156)),
 "02_si_p14_bottom_T68a_end":        (SI, 14, pymupdf.Rect(50, 660, 560, 742)),
 "02_si_p15_top_T68b_row":           (SI, 15, pymupdf.Rect(50, 66, 560, 140)),
 "03_si_p16_top_T69_header_rows":    (SI, 16, pymupdf.Rect(50, 66, 560, 146)),
}

def render(root, rel, page, clip, dpi=DPI):
    d = pymupdf.open(root + rel)
    return d[page-1].get_pixmap(clip=clip, dpi=dpi)

made = {}
for name, (rel, page, clip) in CROPS.items():
    for tag, root in (("final", NEW), ("before", V2)):
        pix = render(root, rel, page, clip)
        path = os.path.join(OUT if tag == "final" else BEF, f"{name}_{tag}.png")
        pix.save(path)
        made.setdefault(name, {})[tag] = path
        print("wrote", path, pix.width, "x", pix.height)

# stacked comparison sheets: before on top, final below, with a separator
for name in CROPS:
    a = Image.open(made[name]["before"]).convert("RGB")
    b = Image.open(made[name]["final"]).convert("RGB")
    w = max(a.width, b.width); gap = 26
    canvas = Image.new("RGB", (w, a.height + gap + b.height), (255, 255, 255))
    canvas.paste(a, (0, 0))
    canvas.paste(b, (0, a.height + gap))
    for x in range(w):                       # separator rule
        for y in range(a.height, a.height + 3):
            canvas.putpixel((x, y), (170, 170, 170))
    path = os.path.join(OUT, f"{name}_BEFORE_vs_AFTER.png")
    canvas.save(path)
    print("wrote", path, canvas.width, "x", canvas.height)
