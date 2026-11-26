# -*- coding: utf-8 -*-
import os, pymupdf
from PIL import Image
V2  = r"E:\project\work1\20261006\manuscript_figures_SI_integrated_v2"
NEW = r"E:\project\work1\20261006\manuscript_figures_SI_integrated_v2_layout_final"
OUT = os.path.join(NEW, "render_checks"); BEF = os.path.join(OUT, "before_v2")
SI = r"\si\Supplementary_Information_synced.pdf"
DPI = 300
CROPS = {"03a_si_p15_bottom_T69_orphan_header": pymupdf.Rect(50, 683, 560, 764)}
for name, clip in CROPS.items():
    imgs = []
    for tag, root in (("before", V2), ("final", NEW)):
        d = pymupdf.open(root + SI)
        pix = d[14].get_pixmap(clip=clip, dpi=DPI)   # page 15
        p = os.path.join(OUT if tag == "final" else BEF, f"{name}_{tag}.png")
        pix.save(p); imgs.append((tag, p, pix.width, pix.height)); print("wrote", p, pix.width, pix.height)
    a, b = Image.open(imgs[0][1]).convert("RGB"), Image.open(imgs[1][1]).convert("RGB")
    w = max(a.width, b.width); gap = 26
    c = Image.new("RGB", (w, a.height+gap+b.height), (255,255,255))
    c.paste(a,(0,0)); c.paste(b,(0,a.height+gap))
    for x in range(w):
        for y in range(a.height, a.height+3): c.putpixel((x,y),(170,170,170))
    out = os.path.join(OUT, f"{name}_BEFORE_vs_AFTER.png"); c.save(out)
    print("wrote", out, c.width, c.height)
