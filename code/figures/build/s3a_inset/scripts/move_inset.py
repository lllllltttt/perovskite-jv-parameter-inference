# -*- coding: utf-8 -*-
"""S3a_05 (cycle-gap highest) - move the inset zoom box to the right.

Only change: a translate on the nested <g id="axes_6"> inside S3a_05.svg.
That group holds the inset frame, its curves, ticks, tick numbers and clip
path, so the whole inset moves as one rigid body - size, font, data, axis
limits and tick values are untouched.

Why 8 pt:
  the inset's widest y label is "-400" (8 pt Arial, advance 18.019 pt), drawn
  right-aligned at x = 338.259; its ink starts at 320.685, i.e. 2.37 pt left
  of the main left frame (323.050).  +8 pt puts the ink at 328.685, leaving
  5.1 pt of white between the 1.1 pt frame and the text.
  The inset's right edge moves from 453.314 to 461.314; the main curves in
  that vertical band start at x = 494.18 (stroke half-width 1.0), so 31.9 pt
  stay clear.
"""
import os
import re
import subprocess
import sys

from lxml import etree

CS = "{http://www.w3.org/2000/svg}"
BASE = r"E:\project\work1"
ROOT = os.path.join(BASE, "20261119_figS3a_inset")
SRC = os.path.join(BASE, "20261116_figs3_split", "package", "S3a_six_panels",
                   "S3a_05.svg")
OUT = os.path.join(ROOT, "out")
WORK = os.path.join(ROOT, "work")
os.makedirs(OUT, exist_ok=True)

DX = 8.0                                   # pt, translation of the inset


def render(svg, png):
    r = subprocess.run([sys.executable,
                        os.path.join(ROOT, "scripts", "render_svg_px.py"),
                        svg, png, "--dpi", "600"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if r.returncode != 0:
        raise RuntimeError("render failed: " + svg)


def main():
    tree = etree.parse(SRC)
    root = tree.getroot()
    ax6 = [g for g in root.iter(CS + "g") if g.get("id") == "axes_6"]
    assert len(ax6) == 1
    ax6 = ax6[0]
    assert ax6.get("transform") is None, "inset already has a transform"
    ax6.set("transform", "translate(%.4f 0)" % DX)

    dst = os.path.join(OUT, "S3a_05.svg")
    tree.write(dst, xml_declaration=True, encoding="utf-8")

    render(dst, os.path.join(OUT, "S3a_05_600dpi.png"))
    render(SRC, os.path.join(WORK, "S3a_05_old.png"))
    print("wrote", dst, "and", os.path.join(OUT, "S3a_05_600dpi.png"))
    print("transform:", ax6.get("transform"))


if __name__ == "__main__":
    main()
