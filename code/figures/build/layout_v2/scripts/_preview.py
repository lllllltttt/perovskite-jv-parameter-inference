# -*- coding: utf-8 -*-
"""Dev helper (not delivered): downscale a delivered PNG so it can be looked at.

The delivered PNGs are 600 dpi (4200-5700 px wide), which is right for print and
useless for inspection on screen. This writes a ~1500 px preview into
qa_render/ with the same aspect ratio. Optional crop arguments take fractions of
width and height, so a single panel can be inspected at full detail.

    python scripts/_preview.py Figure3
    python scripts/_preview.py Figure3 0.0 0.35 0.55 1.0     # bottom-left area
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
SRC = os.path.join(OUT, "figures")
DST = os.path.join(OUT, "qa_render")
os.makedirs(DST, exist_ok=True)

TARGET = 1500


def main():
    name = sys.argv[1]
    im = Image.open(os.path.join(SRC, name + ".png")).convert("RGB")
    if len(sys.argv) > 5:
        x0, y0, x1, y1 = (float(v) for v in sys.argv[2:6])
        w, h = im.size
        im = im.crop((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h)))
        tag = "_crop"
    else:
        tag = ""
    w, h = im.size
    if w > TARGET:
        im = im.resize((TARGET, max(1, int(h * TARGET / w))), Image.LANCZOS)
    out = os.path.join(DST, "preview_%s%s.png" % (name, tag))
    im.save(out)
    print("preview %dx%d -> %s" % (im.size[0], im.size[1], out))


if __name__ == "__main__":
    main()
