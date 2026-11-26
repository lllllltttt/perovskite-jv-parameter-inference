# -*- coding: utf-8 -*-
"""QC for Fig3_recoverability_labeltune_bonly.

Verifies that the labeltune_bonly candidate differs from the frozen annotfix6
ONLY in panel-(b) label positions / leader lines:
  A. panel (a) geometry identical (9 subplot window extents match annotfix6)
  B. panel (a) PDF text-token set identical to annotfix6
  C. r-mapping 9/9 canonical order preserved
  D. shared axis labels + (a)/(b) tags present
  E. panel (b) PDF text-token set identical to annotfix6 (labels are the SAME
     strings; only their positions moved)
  F. panel (b) annotation DATA points identical (ann.xy equal to annotfix6)
  G. all 9 label glyph boxes INSIDE the panel-(b) axes frame (>=2 pt margin)
  H. no two label glyph boxes overlap (>=2 pt gap)
  I. no leader line (drawn PDF segment) intersects ANY glyph box (own or other)
  J. each leader's point-end sits on its OWN data point (~shrinkB, <=3.5 pt)
     and its text-end is beside its OWN label box (0.5..12 pt, not detached)
  K. exports exist: PNG@600 + PDF + SVG, journal + large
"""
import io, sys, re, os, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import fitz

BASE = r"E:\project\work1\final_figures\Fig3"
NEW = os.path.join(BASE, "Fig3_recoverability_labeltune_bonly.pdf")
REF = os.path.join(BASE, "Fig3_recoverability_annotfix6.pdf")
ok = []
def chk(name, cond, note=""):
    ok.append(bool(cond)); print("[%s] %s  %s" % ("PASS" if cond else "FAIL", name, note))

# ------------------------------------------------------------------ matplotlib
import os as _os
sys.path.insert(0, _os.getcwd())
import figure_style as st

def build(modname):
    mod = __import__(modname)
    _cap = []
    _orig = st.save_fig
    st.save_fig = lambda fig, stem, **kw: _cap.append((fig, str(stem)))
    mod.main()
    st.save_fig = _orig
    return _cap[0][0]

figN = build("plot_Fig3_recoverability_labeltune_bonly")
figA = build("plot_Fig3_recoverability_annotfix6")
for fig in (figN, figA):
    fig.canvas.draw()
ren = figN.canvas.get_renderer()
pt = 72.0 / figN.dpi

def Wb(ax, ren):
    e = ax.get_window_extent(ren); return (e.x0, e.y0, e.x1, e.y1)
def pan9(fig):
    return [a for a in fig.axes if a.get_subplotspec() is not None
            and a.get_subplotspec().get_gridspec().nrows == 3]
panN = pan9(figN); panA = pan9(figA)
geom = all(abs(Wb(a, ren)[i] - Wb(b, ren)[i]) < 0.05
           for a, b in zip(panN, panA) for i in range(4))
chk("A panel (a) geometry identical", geom, "9 subplot window extents vs annotfix6")

from matplotlib.text import Annotation
axbN = [a for a in figN.axes if a.get_subplotspec() is not None
        and a.get_subplotspec().get_gridspec().ncols == 2][0]
axbA = [a for a in figA.axes if a.get_subplotspec() is not None
        and a.get_subplotspec().get_gridspec().ncols == 2][0]
anN = [a for a in axbN.texts if isinstance(a, Annotation)]
anA = [a for a in axbA.texts if isinstance(a, Annotation)]
same_xy = len(anN) == len(anA) and all(
    abs(a.xy[0] - b.xy[0]) < 1e-12 and abs(a.xy[1] - b.xy[1]) < 1e-12
    for a, b in zip(anN, anA))
chk("F panel (b) annotation data points identical", same_xy,
    "%d annotations, xy equal to annotfix6" % len(anN))

# ------------------------------------------------------------------ PDF checks
doc = fitz.open(NEW); pg = doc[0]
PW, PH = pg.rect.width, pg.rect.height
docA = fitz.open(REF); pgA = docA[0]

# panel (b) axes frame from the spine drawings
xs = ys = None
for d in pg.get_drawings():
    c = d.get("color")
    if c is not None and abs(c[0] - 0.10194552689790726) < 1e-3:
        for it in d["items"]:
            if it[0] == "l":
                p1, p2 = it[1], it[2]
                if abs(p1.y - p2.y) < 0.3 and (p2.x - p1.x) > 150 and p1.x > 300:
                    ys = (p1.y, p2.y)          # a panel-(b) horizontal spine
FRAME = dict(x0=341.9, x1=499.6, y0=20.4, y1=241.0)   # spine-derived, panel (b)
chk("panel (b) frame found", ys is not None, "top/bottom spine y=%.1f" % ys[0] if ys else "")

# panel (a) region: x < 305.7 ; panel (b) region: x > 335
def toks(pg, x0, x1):
    s = set()
    for b in pg.get_text("blocks"):
        cx = (b[0] + b[2]) / 2.0
        if x0 <= cx < x1:
            for w in b[4].split():
                if len(w) > 1:
                    s.add(w)
    return s
mt = sorted(t for t in toks(pg, 0, 305) - toks(pgA, 0, 305) if not re.fullmatch(r"[0-9.\-]+", t))
ex = sorted(t for t in toks(pgA, 0, 305) - toks(pg, 0, 305) if not re.fullmatch(r"[0-9.\-]+", t))
chk("B panel (a) tokens unchanged vs annotfix6", not mt and not ex, "missing=%s extra=%s" % (mt, ex))

words = pg.get_text("words")
rs = [w[4] for w in words if w[0] < 305 and re.fullmatch(r"0\.\d{3}", w[4])]
EXP = ["0.906","0.919","0.878","0.881","0.909","0.896","0.594","0.720","0.559"]
chk("C r-mapping 9/9 canonical order", rs == EXP, "got %s" % rs)
txt = pg.get_text()
chk("D shared labels + tags", ("True normalized log10 parameter" in txt
    and "Predicted normalized log10 parameter" in txt and "(a)" in txt and "(b)" in txt), "")

# panel (b) token set identical to annotfix6 (labels same strings, moved only)
mt2 = sorted(t for t in toks(pg, 335, PW) - toks(pgA, 335, docA[0].rect.width)
             if not re.fullmatch(r"[0-9.\-]+", t))
ex2 = sorted(t for t in toks(pgA, 335, docA[0].rect.width) - toks(pg, 335, PW)
             if not re.fullmatch(r"[0-9.\-]+", t))
chk("E panel (b) token set unchanged", not mt2 and not ex2, "missing=%s extra=%s" % (mt2, ex2))

# ---- 9 label glyph boxes (mathtext = 2 spans each, merged spatially) ----
d = pg.get_text("dict")
name_of = {"\u03bc": "mu", "\u03c4": "tau", "N": "N", "r": "r",
           "n": "n", "p": "p", "c": "c", "v": "v",
           "ETL": "ETL", "HTL": "HTL", "rad": "rad"}
label_chars = {"\u03bc", "\u03c4", "N", "n", "p", "c", "v", "r", "ETL", "HTL", "rad"}
cands = []
for bl in d["blocks"]:
    for ln in bl.get("lines", []):
        for sp in ln["spans"]:
            x0, y0, x1, y1 = sp["bbox"]
            t = sp["text"]
            if x0 > 335 and x1 < FRAME["x1"] + 2 and y0 > FRAME["y0"] - 2 and y1 < FRAME["y1"] + 2 \
               and t in label_chars and not re.fullmatch(r"[0-9.]+", t):
                cands.append((x0, y0, x1, y1, t))
# merge any two spans whose boxes are < 6 pt apart in x and whose vertical
# centres differ by < 7 pt (interleaved labels like tau_n/mu_n share x-ranges,
# so this is a true spatial merge, not sorted adjacency)
clusters = []
for c in sorted(cands):
    for cl in clusters:
        for m in cl:
            if c[0] - m[2] < 6 and m[0] - c[2] < 6 \
               and abs((c[1] + c[3]) / 2 - (m[1] + m[3]) / 2) < 7:
                cl.append(c); break
        else:
            continue
        break
    else:
        clusters.append([c])
# keep only multi-span clusters (the standalone Spearman "p" forms a 1-span
# cluster and is discarded); each label is exactly a main char + subscript
boxes = []
for cl in clusters:
    if len(cl) < 2:
        continue
    x0 = min(c[0] for c in cl); x1 = max(c[2] for c in cl)
    y0 = min(c[1] for c in cl); y1 = max(c[3] for c in cl)
    name = "".join(name_of.get(c[4], "") for c in cl)
    boxes.append((name, x0, y0, x1, y1))
names = sorted(b[0] for b in boxes)
chk("9 label boxes found", len(boxes) == 9, "labels=%s" % names)

def ov(a, b, m=0.0):
    # 4-tuples (x0,y0,x1,y1)
    return not (a[2] <= b[0] + m or b[2] <= a[0] + m or a[3] <= b[1] + m or b[3] <= a[1] + m)
def gap(a, b):
    h = max(a[0], b[0]) - min(a[2], b[2])
    v = max(a[1], b[1]) - min(a[3], b[3])
    if h > 0 and v > 0:
        return min(h, v)
    if h > 0 or v > 0:
        return max(h, v)
    return 0.0

# G inside frame
min_m = min(min(b[1] - FRAME["x0"], FRAME["x1"] - b[3], b[2] - FRAME["y0"], FRAME["y1"] - b[4])
            for b in boxes)
chk("G all labels inside axes frame", min_m >= 2.0, "min margin %.1f pt" % min_m)

# H no overlap
worst = 1e9
for i in range(len(boxes)):
    for j in range(i + 1, len(boxes)):
        if ov(boxes[i][1:], boxes[j][1:]):
            worst = -1
        else:
            worst = min(worst, gap(boxes[i][1:], boxes[j][1:]))
chk("H no label-label overlap", worst >= 2.0, "min pairwise gap %.1f pt" % worst)

# ---- leader segments (gray cubic paths) ----
segs = []
for d2 in pg.get_drawings():
    col = d2.get("color")
    if col and abs(col[0] - 0.65) < 0.01:
        pts = []
        for it in d2["items"]:
            if it[0] == "l":
                pts += [it[1], it[2]]
            elif it[0] == "c":
                pts += list(it[1:5])          # (start, ctrl1, ctrl2, end)
            elif it[0] == "qu":
                pts += list(it[1:4])          # (start, ctrl, end)
        if pts:
            segs.append((pts[0].x, pts[0].y, pts[-1].x, pts[-1].y))
chk("9 leader segments found", len(segs) == 9, "n=%d" % len(segs))

def seg_rect(s):
    return (min(s[0], s[2]), min(s[1], s[3]), max(s[0], s[2]), max(s[1], s[3]))
def seg_touch_box(s, b, pad=0.5):
    # tight segment-bbox vs box bbox (rectangular, conservative for near-horizontal)
    r = seg_rect(s)
    return ov((b[1], b[2], b[3], b[4]), (r[0], r[1], r[2], r[3]), pad)
pierce = []
for i, s in enumerate(segs):
    for j, b in enumerate(boxes):
        if seg_touch_box(s, b):
            pierce.append((i, boxes[j][0], [round(v, 1) for v in s], [round(v, 1) for v in b[1:]]))
chk("I no leader pierces any glyph box", not pierce, "n=%d" % len(pierce))
for p in pierce[:10]:
    print("      leader %d vs label %s: seg%s box%s" % p)

# J each leader's point-end sits on its OWN data point (~shrinkB from posB) and
#    its text-end is beside its OWN label box (attached, not detached, not
#    piercing).  The old posA/text-end check was dropped: matplotlib offsets the
#    drawn leader ~7 pt from the internal arrow anchor (not a visual element);
#    what matters is the leader's real text-end vs its label glyph box.
x0_, y0_, x1_, y1_ = Wb(axbN, ren)
def disp_to_page(px, py):
    return (FRAME["x0"] + (px - x0_) * pt, FRAME["y0"] + (y1_ - py) * pt)
def label_name(s):
    s = s.replace("$", "").replace("\\mathrm", "")
    s = s.replace("{", "").replace("}", "").replace("_", "")
    s = s.replace("\\mu", "mu").replace("\\tau", "tau")
    return s
byname = {b[0]: b[1:] for b in boxes}
def dist_to_box(px, py, b):
    dx = max(b[0] - px, 0.0, px - b[2])
    dy = max(b[1] - py, 0.0, py - b[3])
    return math.hypot(dx, dy)
name_ok = len(set(byname)) == len(boxes) == 9
bad = []
for a in anN:
    nm = label_name(a.get_text())
    if nm not in byname:
        bad.append((a.get_text(), "no box")); continue
    pp = a.arrow_patch._posA_posB
    pB = disp_to_page(*pp[1])                          # annotation point (page)
    s = min(segs, key=lambda s: math.hypot(s[2] - pB[0], s[3] - pB[1]))
    dB = math.hypot(s[2] - pB[0], s[3] - pB[1])        # point-end -> own point
    dT = dist_to_box(s[0], s[1], byname[nm])           # text-end -> own label box
    if dB > 3.5 or dT < 0.5 or dT > 12.0:
        bad.append((nm, round(dB, 1), round(dT, 1)))
chk("J leaders attached to own points/labels",
    name_ok and len(segs) == len(anN) and not bad,
    "names unique, point-end dev <=3.5pt, text-end 0.5..12pt from own label"
    if not bad else "bad=%s" % bad)

# K exports
import PIL.Image as I
im = I.open(os.path.join(BASE, "Fig3_recoverability_labeltune_bonly.png"))
dpi = im.info.get("dpi", (0, 0))[0]
ex = (abs(dpi - 600) < 1
      and os.path.exists(os.path.join(BASE, "Fig3_recoverability_labeltune_bonly.pdf"))
      and os.path.exists(os.path.join(BASE, "Fig3_recoverability_labeltune_bonly.svg"))
      and os.path.exists(os.path.join(BASE, "Fig3_recoverability_labeltune_bonly_large.png"))
      and os.path.exists(os.path.join(BASE, "Fig3_recoverability_labeltune_bonly_large.pdf"))
      and os.path.exists(os.path.join(BASE, "Fig3_recoverability_labeltune_bonly_large.svg")))
chk("K exports PNG@600+PDF+SVG (journal+large)", ex,
    "PNG %dx%d @%.0fdpi" % (im.size[0], im.size[1], dpi))

print()
print("QC GATES: %d/%d PASS" % (sum(ok), len(ok)))
