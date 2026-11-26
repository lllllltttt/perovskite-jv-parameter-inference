# -*- coding: utf-8 -*-
"""Regenerate the QA crops from the FINAL exported PNGs (600 dpi).

Run after every rebuild so the crops can never go stale.
"""
import os

from PIL import Image

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(OUT, "figures")
CROP = os.path.join(OUT, "qa", "crops")
os.makedirs(CROP, exist_ok=True)

# (source stem, box in px, output name)
JOBS = [
    ("Fig3a", (1280, 460, 1980, 900), "Fig3a_topright"),
    ("Fig3b", (1280, 460, 1980, 900), "Fig3b_topright"),
    ("Fig3c", (900, 440, 1980, 1000), "Fig3c_topright"),
    ("Fig3c", (330, 850, 1900, 1560), "Fig3c_labels"),
    ("Fig3d", (1280, 460, 1980, 900), "Fig3d_topright"),
    ("Fig3a", (0, 1300, 1980, 1620), "Fig3a_corner"),
    ("Fig3c", (0, 1300, 1980, 1620), "Fig3c_corner"),
    ("Fig3d", (0, 1300, 1980, 1620), "Fig3d_corner"),
    ("Fig4e_Jsc", (330, 300, 860, 600), "Fig4e_Jsc_box"),
    ("Fig4e_Voc", (330, 300, 860, 600), "Fig4e_Voc_box"),
    ("Fig4e_FF_pp", (330, 300, 860, 600), "Fig4e_FF_pp_box"),
    ("Fig4e_PCE", (330, 300, 860, 600), "Fig4e_PCE_box"),
    ("Fig4d", (150, 30, 1560, 1464), "Fig4d_full_plot"),
    ("Fig5a", (330, 300, 1110, 1000), "Fig5a_legend"),
    ("Fig5b", (900, 700, 1200, 1050), "Fig5b_legend"),
]

for stem, box, name in JOBS:
    src = os.path.join(FIG, stem + ".png")
    im = Image.open(src)
    w, h = im.size
    box = (max(0, box[0]), max(0, box[1]), min(w, box[2]), min(h, box[3]))
    c = im.crop(box)
    scale = 2 if c.size[0] < 900 else 1
    if scale > 1:
        c = c.resize((c.size[0] * scale, c.size[1] * scale), Image.LANCZOS)
    c.save(os.path.join(CROP, name + ".png"))
    print(name, c.size)
