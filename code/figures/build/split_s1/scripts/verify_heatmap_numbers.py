# -*- coding: utf-8 -*-
"""Verification for out/heatmap_numbers/S1b_heatmap_numbers.svg + .png."""
import io
import re
import sys

import numpy as np
from PIL import Image
from lxml import etree

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

CS = "{http://www.w3.org/2000/svg}"
SRC = "work/slide1_image2.svg"
NEW = "out/heatmap_numbers/S1b_heatmap_numbers.svg"
PNG = "out/heatmap_numbers/S1b_heatmap_numbers_600dpi.png"
S = 600 / 72.0
X0, Y0, W, H = 536.0, 26.68, 426.0, 382.56
FAIL = []


def check(cond, msg):
    print(("  PASS  " if cond else "  FAIL  ") + msg)
    if not cond:
        FAIL.append(msg)


def byid(root, gid):
    for e in root.iter(CS + "g"):
        if e.get("id") == gid:
            return e
    raise KeyError(gid)


src = etree.parse(SRC).getroot()
new = etree.parse(NEW).getroot()

# ---------------------------------------------------------------- A structure
print("== A  structure: what is in the file ==")
raw = open(NEW, encoding="utf-8").read()
check(raw.count("<text") == 86 and "<tspan" not in raw,
      "86 <text> elements, 0 <tspan>  (%d / %d)" % (raw.count("<text"), raw.count("<tspan")))
check("<style" not in raw, "no <style> block")

banned = ["Spearman", "ρ", "Retained", "Pairwise", "102,046", "(a)", "(b)",
          "μ", "τ", "N_{", "r_{", "log-space"]
hits = [b for b in banned if b in raw]
check(not hits, "no removed wording anywhere in the file  (hits: %s)" % (hits or "none"))

ids_new = {e.get("id") for e in new.iter() if e.get("id")}
gone = ["axes_%d" % i for i in range(1, 10)] + \
       ["matplotlib.axis_19", "matplotlib.axis_20", "text_151"] + \
       ["text_%d" % i for i in range(152, 157)]
still = [g for g in gone if g in ids_new]
check(not still, "the 9 histograms, the 2 heatmap axes and the 5 figure texts are gone "
                 "(left over: %s)" % (still or "none"))

# every href resolves inside the file
refs = set()
for e in new.iter():
    for k, v in e.attrib.items():
        if k.endswith("href") and v.startswith("#"):
            refs.add(v[1:])
        if isinstance(v, str) and "url(#" in v:
            refs.update(re.findall(r"url\(#([^)]+)\)", v))
dangling = [r for r in refs if r not in ids_new]
check(not dangling, "all #id references resolve  (%d refs, dangling: %s)"
      % (len(refs), dangling or "none"))

# --------------------------------------------------------------- B the numbers
print("\n== B  the 81 in-cell numbers: identical to the original ==")
a10 = byid(src, "axes_10")
a10n = byid(new, "axes_10")
orig = {e.get("id"): e for e in a10.iter(CS + "g") if e.get("id", "").startswith("text_")}
keep = ["text_%d" % i for i in range(65, 146)]
now = {e.get("id"): e for e in a10n.iter(CS + "g") if e.get("id", "").startswith("text_")}
check(sorted(now) == sorted(keep), "exactly text_65..text_145 kept (%d)" % len(now))
bad = 0
for gid in keep:
    o, n = orig[gid].find(CS + "text"), now[gid].find(CS + "text")
    for k in ("x", "y", "fill", "text-anchor"):
        if o.get(k) != n.get(k):
            bad += 1
            print("     %s %s: %r -> %r" % (gid, k, o.get(k), n.get(k)))
    if (o.text or "") != (n.text or ""):
        bad += 1
        print("     %s text: %r -> %r" % (gid, o.text, n.text))
check(bad == 0, "x, y, fill, text-anchor and the string itself unchanged in all 81")
vals = [now[g].find(CS + "text").text for g in keep]
check(all(len(v.split(".")[1]) == 2 for v in vals), "all values carry two decimals")
check("-0.00" in vals and "+0.00" not in vals,
      "negative zero survives: %d cell(s) read -0.00" % vals.count("-0.00"))
white = sum(1 for g in keep if now[g].find(CS + "text").get("fill") == "#FFFFFF")
check(white == len([g for g in keep
                    if orig[g].find(CS + "text").get("fill") == "#FFFFFF"]),
      "black/white per-cell colouring unchanged (%d white)" % white)

# ------------------------------------------------------------- C colour bar
print("\n== C  colour bar: frame, ticks and tick numbers kept, 'Spearman ρ' gone ==")
a11 = byid(src, "axes_11")
a11n = byid(new, "axes_11")
idsA11 = {e.get("id") for e in a11n.iter() if e.get("id")}
for gid in ("patch_592", "patch_593", "matplotlib.axis_22"):
    check(gid in idsA11, "%s retained" % gid)
check("text_151" not in idsA11 and "Spearman" not in raw, "text_151 ('Spearman ρ') removed")
ticks = [e for e in a11n.iter(CS + "use")]
check(len(ticks) == 5, "5 tick marks present (%d <use>)" % len(ticks))
check(all(t.get("x") == "928.76" for t in ticks), "all 5 sit on the bar's right edge x=928.76")
markers = [e for e in a11n.iter(CS + "path") if e.get("id") == "med09aeb6ff"]
check(markers and markers[0].get("d") == "M0 0 3.5 0", "the 3.5-unit tick marker definition is present")
nums = [t for t in a11n.iter(CS + "text")]
ob = [byid(a11, "text_%d" % i).find(CS + "text").text for i in range(146, 151)]
check([t.text for t in nums] == ob, "5 tick numbers identical: %s" % [t.text for t in nums])
check(all(nums[i].get("x") == "935.76" for i in range(len(nums))),
      "all at x=935.76 (unchanged spacing from the bar)")
bar = [s for s in a11n.iter(CS + "image")]
check(len(bar) == 1 and bar[0].get("width") == "21.6" and bar[0].get("height") == "367.92",
      "colour-bar gradient image untouched (21.6 x 367.92, same matrix)")

# -------------------------------------------------------------- D heat map
print("\n== D  heat map matrix geometry ==")
img = [e for e in a10n.iter(CS + "image")]
check(len(img) == 1 and img[0].get("width") == "367.92" and img[0].get("height") == "367.92",
      "matrix image still 367.92 x 367.92 (square), same x/y/transform")
check(len([e for e in a10n.iter(CS + "g") if e.get("id", "").startswith("line2d_")
           and 74 <= int(e.get("id").split("_")[1]) <= 89]) == 16,
      "all 16 white grid separator lines present")
check(all(("patch_%d" % i) in idsA11 or ("patch_%d" % i) in
          {e.get("id") for e in a10n.iter() if e.get("id")} for i in (588, 589, 590, 591)),
      "all 4 heat-map spines (outer frame) present")
check("patch_587" in {e.get("id") for e in a10n.iter() if e.get("id")},
      "the axes background patch is still there (never covered by a white box)")

# ------------------------------------------------------- E element identity
print("\n== E  retained elements are byte-identical apart from the font attributes ==")


def canon(e, drop_font=False):
    a = dict(e.attrib)
    if drop_font:
        a.pop("font-family", None)
        a.pop("font-size", None)
    kids = [canon(c, drop_font) for c in e if isinstance(c.tag, str)]
    return (e.tag, tuple(sorted(a.items())), (e.text or "").strip(), tuple(kids))


src2 = etree.parse(SRC).getroot()
s10 = byid(src2, "axes_10")
s11 = byid(src2, "axes_11")
for gid in ("matplotlib.axis_19", "matplotlib.axis_20"):
    g = byid(s10, gid)
    g.getparent().remove(g)
g = byid(s11, "text_151")
g.getparent().remove(g)
n10, n11 = byid(new, "axes_10"), byid(new, "axes_11")
check(canon(s10, True) == canon(n10, True), "axes_10 subtree identical (81 texts, grid, frame, image)")
check(canon(s11, True) == canon(n11, True), "axes_11 subtree identical (bar image, ticks, frame)")
check(all(t.get("font-size") == "12" and t.get("font-family") == "Arial"
          for t in list(n10.iter(CS + "text")) + list(n11.iter(CS + "text"))),
      "all 86 retained texts carry font-family=Arial font-size=12 (the only added attributes)")

# ---------------------------------------------------------------- F pixels
print("\n== F  pixels: compared with the original in the same window ==")
mine = np.asarray(Image.open(PNG).convert("RGB")).astype(int)
full = np.asarray(Image.open("work/nums_ref_full.png").convert("RGB")).astype(int)
dele = np.asarray(Image.open("work/nums_deleted.png").convert("RGB")).astype(int)
check(mine.shape == full.shape == dele.shape, "same canvas %s" % (mine.shape[:2],))
# mask = where the deleted elements had ink (dilated by 2 px)
dm = ((255 - dele).max(axis=2) > 8).astype(np.uint8)
d = dm.copy()
for dy in (-2, -1, 1, 2):
    d |= np.roll(dm, dy, axis=0)
dm2 = d.copy()
for dx in (-2, -1, 1, 2):
    d |= np.roll(dm2, dx, axis=1)
diff = np.abs(mine - full).max(axis=2)
outside = diff * (1 - d)
n = int((outside > 0).sum())
print("      deleted-element ink covers %d px (%.1f%%)"
      % (int(d.sum()), 100 * d.sum() / d.size))
print("      pixels differing outside that mask: %d   (max channel diff %d)"
      % (n, int(outside.max())))
check(n == 0, "no pixel of the retained drawing changed")

# an unmasked count tells the whole story too
tot = int((diff > 0).sum())
inside = int((diff * d > 0).sum())
print("      total differing pixels %d, of which inside the mask %d" % (tot, inside))
check(tot == inside, "every difference is exactly where a deleted element used to be")

# ---------------------------------------------------------------- G margins
print("\n== G  crop: small even margin, nothing clipped ==")
L = (255 - mine).max(axis=2) > 8
rows = np.where(L.any(axis=1))[0]
cols = np.where(L.any(axis=0))[0]
top, bot = Y0 + rows[0] / S, Y0 + (rows[-1] + 1) / S
left, right = X0 + cols[0] / S, X0 + (cols[-1] + 1) / S
print("      ink bbox  %.3f .. %.3f  x   %.3f .. %.3f  (canvas %.3f .. %.3f / %.3f .. %.3f)"
      % (left, right, top, bot, X0, X0 + W, Y0, Y0 + H))
for name, v in (("left", left - X0), ("right", X0 + W - right),
                ("top", top - Y0), ("bottom", Y0 + H - bot)):
    check(2.8 <= v <= 3.2, "%s margin %.3f pt" % (name, v))
check(mine.shape == (3188, 3550, 3), "PNG is %d x %d px = 426.00 x 382.56 pt at 600 dpi"
      % (mine.shape[1], mine.shape[0]))
print("\n%s" % ("ALL PASS" if not FAIL else "FAILURES:\n  " + "\n  ".join(FAIL)))
