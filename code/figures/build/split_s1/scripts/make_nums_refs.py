# -*- coding: utf-8 -*-
"""Build the two reference renders used to verify S1b_heatmap_numbers.

  work/nums_ref_full.svg    the original document, same viewBox window
  work/nums_deleted.svg     only the elements that were deleted, same window
"""
import sys

from lxml import etree

CS = "{http://www.w3.org/2000/svg}"
SRC = "work/slide1_image2.svg"
X0, Y0, W, H = 536.0, 26.68, 426.0, 382.56
PX = 96.0 / 72.0


def byid(root, gid):
    for e in root.iter(CS + "g"):
        if e.get("id") == gid:
            return e
    raise KeyError(gid)


def newroot(defs, x0=X0, y0=Y0, w=W, h=H):
    r = etree.Element(CS + "svg", nsmap={None: "http://www.w3.org/2000/svg",
                                         "xlink": "http://www.w3.org/1999/xlink"})
    r.set("width", "%.4f" % (w * PX))
    r.set("height", "%.4f" % (h * PX))
    r.set("viewBox", "%.4f %.4f %.4f %.4f" % (x0, y0, w, h))
    r.set("overflow", "hidden")
    for d in defs:
        r.append(etree.fromstring(etree.tostring(d)))
    return r


# --- 1. whole original document, window only --------------------------------
#     plus the same font-family/font-size the output file carries, so that the
#     comparison isolates the deletions and says nothing about the font fix
t1 = etree.parse(SRC)
r1 = t1.getroot()
out1 = newroot(r1.findall(CS + "defs"))
g1 = etree.SubElement(out1, CS + "g", id="all")
for e in r1:
    if e.tag == CS + "defs":
        continue
    g1.append(e)
for gid in ("axes_10", "axes_11"):
    for t in byid(out1, gid).iter(CS + "text"):
        t.set("font-family", "Arial")
        t.set("font-size", "12")
open("work/nums_ref_full.svg", "wb").write(
    etree.tostring(out1, xml_declaration=True, encoding="utf-8"))

# --- 2. only the deleted elements ------------------------------------------
t2 = etree.parse(SRC)
r2 = t2.getroot()
a10 = byid(r2, "axes_10")
a11 = byid(r2, "axes_11")
# text_151 lives inside matplotlib.axis_22, so the deleted set is rebuilt from
# the three groups themselves (no group in this file carries a transform, so
# moving them to the root keeps every coordinate absolute)
parts = [byid(a10, "matplotlib.axis_19"), byid(a10, "matplotlib.axis_20"),
         byid(a11, "text_151")]
out2 = newroot(r2.findall(CS + "defs"))
g2 = etree.SubElement(out2, CS + "g", id="deleted")
for p_ in parts:
    for t in p_.iter(CS + "text"):
        t.set("font-family", "Arial")
        t.set("font-size", "12")
    g2.append(p_)
open("work/nums_deleted.svg", "wb").write(
    etree.tostring(out2, xml_declaration=True, encoding="utf-8"))
print("wrote work/nums_ref_full.svg work/nums_deleted.svg")
