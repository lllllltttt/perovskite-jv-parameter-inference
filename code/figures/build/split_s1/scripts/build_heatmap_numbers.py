# -*- coding: utf-8 -*-
"""Build S1b_heatmap_numbers.svg: the heat map with its in-cell numbers and the
colour bar with its ticks and tick numbers, and nothing else.

Edits are made on the SVG that PowerPoint embeds in slide 1 (ppt/media/image2.svg):
elements are deleted, not covered.  The only attribute added is font-family /
font-size on the retained text, because PowerPoint dropped both when it wrote
the SVG back (measuring the current PowerPoint rendering gives Arial at 12 user
units, which is what these values reproduce).

usage:  build_heatmap_numbers.py <out.svg> <x0> <y0> <w> <h>
"""
import io
import re
import sys

from lxml import etree

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

CS = "{http://www.w3.org/2000/svg}"
SRC = "work/slide1_image2.svg"
PX_PER_UNIT = 96.0 / 72.0

out_path = sys.argv[1]
x0, y0, W, H = (float(v) for v in sys.argv[2:6])


def byid(root, gid):
    for e in root.iter(CS + "g"):
        if e.get("id") == gid:
            return e
    raise KeyError(gid)


tree = etree.parse(SRC)
root = tree.getroot()
src_defs = root.findall(CS + "defs")

axes10 = byid(root, "axes_10")
axes11 = byid(root, "axes_11")

removed = []
for gid in ("matplotlib.axis_19", "matplotlib.axis_20"):
    g = byid(axes10, gid)
    removed.append((gid, sum(1 for _ in g.iter())))
    g.getparent().remove(g)
g = byid(axes11, "text_151")
removed.append(("text_151", sum(1 for _ in g.iter())))
g.getparent().remove(g)

# --- font attributes -----------------------------------------------------
texts = [t for t in list(axes10.iter(CS + "text")) + list(axes11.iter(CS + "text"))]
for t in texts:
    t.set("font-family", "Arial")
    t.set("font-size", "12")
print("text elements given font-family/size:", len(texts))

# --- new document --------------------------------------------------------
new = etree.Element(CS + "svg", nsmap={None: "http://www.w3.org/2000/svg",
                                       "xlink": "http://www.w3.org/1999/xlink"})
new.set("width", "%.4f" % (W * PX_PER_UNIT))
new.set("height", "%.4f" % (H * PX_PER_UNIT))
new.set("viewBox", "%.4f %.4f %.4f %.4f" % (x0, y0, W, H))
new.set("stroke-linejoin", "round")
new.set("overflow", "hidden")

for d in src_defs:
    new.append(etree.fromstring(etree.tostring(d)))
wrap = etree.SubElement(new, CS + "g", id="heatmap_with_numbers")
wrap.append(axes10)
wrap.append(axes11)

with open(out_path, "wb") as f:
    f.write(etree.tostring(new, xml_declaration=True, encoding="utf-8",
                           pretty_print=False))

print("wrote", out_path)
print("removed:", removed)
print("canvas %.4f %.4f %.4f %.4f  ->  %.4f x %.4f px"
      % (x0, y0, W, H, W * PX_PER_UNIT, H * PX_PER_UNIT))
