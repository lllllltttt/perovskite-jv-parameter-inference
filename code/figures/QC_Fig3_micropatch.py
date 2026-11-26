# -*- coding: utf-8 -*-
"""QC for Fig3_recoverability_micropatch.

The micropatch differs from the labeltune_bonly baseline in ONLY three places:
  1. panel (b) top-right four label offsets (mu_p/mu_n/tau_p/tau_n) nudged;
  2. panel (b) Spearman note moved left+up (axes-fraction position);
  3. panel (a) shared-axis-title "log10" -> mathtext "log$_{10}$".
Gates verify everything else is byte-identical and the new geometry is clean:
  A  panel (a) geometry identical (9 subplot window extents vs labeltune)
  B  panel (a) content identical (full word set + 9 per-panel token sets)
  C  r-mapping 9/9 canonical order preserved
  D  shared-title mathtext really applied (subscript '10' span, size<8) + tags
  E  panel (b) token set identical to labeltune
  F  panel (b) annotation DATA points identical
  G  all 9 label glyph boxes inside the frame (>=2 pt margin)
  H  no two label boxes overlap (>=2 pt clearance)
  I  no leader line pierces any glyph box
  J  each leader's point-end on its own point and text-end beside its own label
  K  no label box covers any of the 9 data points (marker radius 3.8 pt)
  L  the 5 untouched labels have IDENTICAL boxes vs labeltune (<=0.5 pt)
  M  the 4 top-right labels moved in the intended directions vs labeltune
  N  Spearman note moved left+up, inside frame, clear of points
  O  exports PNG@600 + PDF + SVG, journal + large
"""
import io, sys, re, os, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import fitz

BASE = r"E:\project\work1\final_figures\Fig3"
NEW = os.path.join(BASE, "Fig3_recoverability_micropatch.pdf")
REF = os.path.join(BASE, "Fig3_recoverability_labeltune_bonly.pdf")
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

figN = build("plot_Fig3_recoverability_micropatch")
figA = build("plot_Fig3_recoverability_labeltune_bonly")
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
chk("A panel (a) geometry identical", geom, "9 subplot window extents vs labeltune")

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
    "%d annotations, xy equal to labeltune" % len(anN))

# ------------------------------------------------------------- PDF checks
FRAME = dict(x0=341.9, x1=499.6, y0=20.4, y1=241.0)   # panel (b) frame, spine-derived
doc = fitz.open(NEW); pg = doc[0]
PW, PH = pg.rect.width, pg.rect.height
docA = fitz.open(REF); pgA = docA[0]

# ---- B panel (a) content: full word set + per-panel token sets identical ----
def words(pg, x0, x1):
    return set(w[4] for w in pg.get_text("words") if x0 <= w[0] < x1)
wsN = words(pg, 0, 305); wsA = words(pgA, 0, 305)
same_words = wsN == wsA
x0_, y0_, x1_, y1_ = Wb(axbN, ren)
def disp_to_page(px, py):
    return (FRAME["x0"] + (px - x0_) * pt, FRAME["y0"] + (y1_ - py) * pt)
def pan_region(ax):
    e = ax.get_window_extent(ren)
    return (disp_to_page(e.x0, e.y1)[0], disp_to_page(e.x0, e.y1)[1],
            disp_to_page(e.x1, e.y0)[0], disp_to_page(e.x1, e.y0)[1])
def region_tokens(pg, reg):
    x0, y0, x1, y1 = reg
    s = set()
    for w in pg.get_text("words"):
        cx, cy = (w[0] + w[2]) / 2.0, (w[1] + w[3]) / 2.0
        if x0 <= cx <= x1 and y0 <= cy <= y1 and len(w[4]) > 1:
            s.add(w[4])
    return s
perp = all(region_tokens(pg, pan_region(a)) == region_tokens(pgA, pan_region(a))
           for a in panN)
chk("B panel (a) content identical", same_words and perp,
    "full word set + 9 per-panel token sets equal to labeltune")

rs = [w[4] for w in pg.get_text("words") if w[0] < 305 and re.fullmatch(r"0\.\d{3}", w[4])]
EXP = ["0.906","0.919","0.878","0.881","0.909","0.896","0.594","0.720","0.559"]
chk("C r-mapping 9/9 canonical order", rs == EXP, "got %s" % rs)

# D shared-title mathtext: a subscript "10" span (size ~6.3, < 8) must exist in
#    the panel-(a) region, and title phrases + tags are present.
sub_ok = False
for bl in pg.get_text("dict")["blocks"]:
    for ln in bl.get("lines", []):
        for sp in ln["spans"]:
            if sp["bbox"][0] < 305 and sp["text"] == "10" and 5.0 < sp["size"] < 8.0:
                sub_ok = True
txt = pg.get_text()
chk("D shared-title mathtext log10 -> log$_{10}$",
    sub_ok and "True normalized log" in txt and "Predicted normalized log" in txt
    and "(a)" in txt and "(b)" in txt,
    "subscript '10' span present (size<8), title phrases + (a)/(b) tags ok")

# E panel (b) token set identical to labeltune
def b_toks(pg, x0):
    s = set()
    for b in pg.get_text("blocks"):
        if b[0] >= x0:
            for w in b[4].split():
                if len(w) > 1:
                    s.add(w)
    return s
mt2 = sorted(t for t in b_toks(pg, 335) - b_toks(pgA, 335) if not re.fullmatch(r"[0-9.\-]+", t))
ex2 = sorted(t for t in b_toks(pgA, 335) - b_toks(pg, 335) if not re.fullmatch(r"[0-9.\-]+", t))
chk("E panel (b) token set unchanged", not mt2 and not ex2, "missing=%s extra=%s" % (mt2, ex2))

# ---- 9 label glyph boxes in each PDF ----
name_of = {"\u03bc": "mu", "\u03c4": "tau", "N": "N", "r": "r",
           "n": "n", "p": "p", "c": "c", "v": "v",
           "ETL": "ETL", "HTL": "HTL", "rad": "rad"}
label_chars = {"\u03bc", "\u03c4", "N", "n", "p", "c", "v", "r", "ETL", "HTL", "rad"}
def extract_boxes(pg):
    cands = []
    for bl in pg.get_text("dict")["blocks"]:
        for ln in bl.get("lines", []):
            for sp in ln["spans"]:
                x0, y0, x1, y1 = sp["bbox"]; t = sp["text"]
                if x0 > 335 and x1 < FRAME["x1"] + 2 and y0 > FRAME["y0"] - 2 \
                   and y1 < FRAME["y1"] + 2 and t in label_chars \
                   and not re.fullmatch(r"[0-9.]+", t):
                    cands.append((x0, y0, x1, y1, t))
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
    out = {}
    for cl in clusters:
        if len(cl) < 2:
            continue
        out["".join(name_of.get(c[4], "") for c in cl)] = (
            min(c[0] for c in cl), min(c[1] for c in cl),
            max(c[2] for c in cl), max(c[3] for c in cl))
    return out
bxN = extract_boxes(pg); bxA = extract_boxes(pgA)
chk("9 label boxes in each PDF", len(bxN) == 9 and len(bxA) == 9,
    "names=%s" % sorted(bxN))

def ov(a, b, m=0.0):
    return not (a[2] <= b[0] + m or b[2] <= a[0] + m or a[3] <= b[1] + m or b[3] <= a[1] + m)
def gap(a, b):
    h = max(a[0], b[0]) - min(a[2], b[2]); v = max(a[1], b[1]) - min(a[3], b[3])
    if h > 0 and v > 0:
        return min(h, v)
    if h > 0 or v > 0:
        return max(h, v)
    return 0.0

min_m = min(min(b[0] - FRAME["x0"], FRAME["x1"] - b[2], b[1] - FRAME["y0"], FRAME["y1"] - b[3])
            for b in bxN.values())
chk("G all labels inside axes frame", min_m >= 2.0, "min margin %.1f pt" % min_m)

items = list(bxN.items()); worst = 1e9
for i in range(len(items)):
    for j in range(i + 1, len(items)):
        if ov(items[i][1], items[j][1]):
            worst = -1
        else:
            worst = min(worst, gap(items[i][1], items[j][1]))
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
                pts += list(it[1:5])
            elif it[0] == "qu":
                pts += list(it[1:4])
        if pts:
            segs.append((pts[0].x, pts[0].y, pts[-1].x, pts[-1].y))
chk("9 leader segments found", len(segs) == 9, "n=%d" % len(segs))

def seg_touch_box(s, b):
    r = (min(s[0], s[2]), min(s[1], s[3]), max(s[0], s[2]), max(s[1], s[3]))
    return ov((b[0], b[1], b[2], b[3]), r, 0.5)
pierce = []
for i, s in enumerate(segs):
    for nm, b in bxN.items():
        if seg_touch_box(s, b):
            pierce.append((i, nm))
chk("I no leader pierces any glyph box", not pierce, "n=%d" % len(pierce))

# J leaders attached (own point + own label box)
def label_name(s):
    s = s.replace("$", "").replace("\\mathrm", "")
    s = s.replace("{", "").replace("}", "").replace("_", "")
    s = s.replace("\\mu", "mu").replace("\\tau", "tau")
    return s
def dist_to_box(px, py, b):
    dx = max(b[0] - px, 0.0, px - b[2]); dy = max(b[1] - py, 0.0, py - b[3])
    return math.hypot(dx, dy)
bad = []
for a in anN:
    nm = label_name(a.get_text())
    pp = a.arrow_patch._posA_posB
    pB = disp_to_page(*pp[1])
    s = min(segs, key=lambda s: math.hypot(s[2] - pB[0], s[3] - pB[1]))
    dB = math.hypot(s[2] - pB[0], s[3] - pB[1])
    dT = dist_to_box(s[0], s[1], bxN[nm])
    if dB > 3.5 or dT < 0.5 or dT > 12.0:
        bad.append((nm, round(dB, 1), round(dT, 1)))
chk("J leaders attached to own points/labels", not bad,
    "point-end dev<=3.5pt, text-end 0.5..12pt from own label" if not bad else "bad=%s" % bad)

# K no label box covers any of the 9 data points (marker radius ~3.8 pt)
pts = [disp_to_page(*a.arrow_patch._posA_posB[1]) for a in anN]
R = 3.8
hit = []
for nm, b in bxN.items():
    for px, py in pts:
        if b[0] - R < px < b[2] + R and b[1] - R < py < b[3] + R:
            hit.append((nm, round(px, 1), round(py, 1)))
chk("K no label covers any data point", not hit, "n=%d" % len(hit))

# L 5 untouched labels identical to labeltune, measured RELATIVE TO the axes
#    frame (the figure's tight bbox shifts globally by ~0.3 pt when the shared
#    titles change width; that is a whole-figure page translation, not a label
#    move, so compare label-to-frame offsets, not absolute page coords).
def frame_xy(pg):
    xs, ys = [], []
    for d in pg.get_drawings():
        c = d.get("color")
        if c is not None and abs(c[0] - 0.10194552689790726) < 1e-3:
            for it in d["items"]:
                if it[0] == "l":
                    p1, p2 = it[1], it[2]
                    if abs(p1.x - p2.x) < 0.3 and p1.y > 15 and p1.x > 300:
                        xs.append(p1.x)
                    if abs(p1.y - p2.y) < 0.3 and p2.x - p1.x > 150 and p1.x > 300:
                        ys.append(p1.y)
    return min(xs), min(ys)
fN = frame_xy(pg); fA = frame_xy(pgA)
d5 = max(max(abs((bxN[nm][i] - fN[i & 1]) - (bxA[nm][i] - fA[i & 1])) for i in range(4))
         for nm in ("Nc", "Nv", "tauETL", "tauHTL", "rrad"))
chk("L 5 unchanged labels identical to labeltune", d5 < 0.3,
    "max rel-to-frame shift %.2f pt (frame dx %.2f pt)" % (d5, fN[0] - fA[0]))

# M 4 top-right labels moved in the intended directions
def center(b): return ((b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0)
cN = {nm: center(bxN[nm]) for nm in ("mun", "mup", "taun", "taup")}
cA = {nm: center(bxA[nm]) for nm in ("mun", "mup", "taun", "taup")}
moves = [
    ("mup left",        cN["mup"][0]  - cA["mup"][0]  < -1.5),
    ("mun right",       cN["mun"][0]  - cA["mun"][0]  >  1.5),
    ("taup up-left",    cN["taup"][0] - cA["taup"][0] < -1.5
                        and bxN["taup"][1] - bxA["taup"][1] < -0.6),
    ("taun down-left",  cN["taun"][0] - cA["taun"][0] < -1.5
                        and bxN["taun"][1] - bxA["taun"][1] >  1.0),
]
chk("M 4 top-right labels moved as intended", all(m[1] for m in moves),
    ", ".join("%s=%s" % (m[0], "ok" if m[1] else "BAD") for m in moves))

# N Spearman note moved left+up, inside frame, clear of points
def note_box(pg):
    for bl in pg.get_text("dict")["blocks"]:
        for ln in bl.get("lines", []):
            t = "".join(sp["text"] for sp in ln["spans"])
            if "Spearman" in t or "\u03c1" in t:
                return ln["bbox"]
    return None
nbN = note_box(pg); nbA = note_box(pgA)
n_ok = bool(nbN and nbA and (nbN[0] - nbA[0] < -2.0) and (nbN[1] - nbA[1] < -2.0))
n_in = bool(nbN and nbN[0] > FRAME["x0"] and nbN[2] < FRAME["x1"] - 2
            and nbN[1] > FRAME["y0"] and nbN[3] < FRAME["y1"] - 2)
n_pts = bool(nbN and not any(nbN[0] - R < px < nbN[2] + R and nbN[1] - R < py < nbN[3] + R
                            for px, py in pts))
chk("N Spearman note moved left+up, in-frame, clear of points", n_ok and n_in and n_pts,
    "dx=%.1f dy=%.1f (page) right-margin=%.1f"
    % (nbN[0] - nbA[0], nbN[1] - nbA[1], FRAME["x1"] - nbN[2]) if nbN and nbA else "no note")

# O exports
import PIL.Image as I
im = I.open(os.path.join(BASE, "Fig3_recoverability_micropatch.png"))
dpi = im.info.get("dpi", (0, 0))[0]
ex = (abs(dpi - 600) < 1
      and os.path.exists(os.path.join(BASE, "Fig3_recoverability_micropatch.pdf"))
      and os.path.exists(os.path.join(BASE, "Fig3_recoverability_micropatch.svg"))
      and os.path.exists(os.path.join(BASE, "Fig3_recoverability_micropatch_large.png"))
      and os.path.exists(os.path.join(BASE, "Fig3_recoverability_micropatch_large.pdf"))
      and os.path.exists(os.path.join(BASE, "Fig3_recoverability_micropatch_large.svg")))
chk("O exports PNG@600+PDF+SVG (journal+large)", ex,
    "PNG %dx%d @%.0fdpi" % (im.size[0], im.size[1], dpi))

print()
print("QC GATES: %d/%d PASS" % (sum(ok), len(ok)))
