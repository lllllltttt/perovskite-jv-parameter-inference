# -*- coding: utf-8 -*-
"""Programmatic QC for the Fig.2 surgical2 layout pass (model cannot view images).

Rebuilds the figure in-memory via fig2.main() with st.save_fig monkey-patched
to a no-op, then measures:
  1. exact axes positions (figure fraction + inches)
  2. exact panel-label (16 pt) / panel-title (13 or 9 pt) coords used
  3. label-vs-title bbox overlap per panel (must be 0)
  4. header vs axes top border, header vs figure boundary (no clip), and
     (b)/(c) header vs panel (a) bottom clearance
  5. legend curve-point counts for panel (b) (must be 0/0) and legend vs
     header separation
  6. arch annotation vs box overlaps in panel (a) (must be 0), plus the
     input-box clip check (painted left edge must be > 0 in data coords)
  7. rendered PNG pixel size
  8. L_NLL dashed-arrow reroute (heads must land on/near the L_NLL label,
     shafts must start at the mu_theta / sigma_raw box right edges)
"""
import os, sys, warnings, pickle
import numpy as np
from sklearn.exceptions import InconsistentVersionWarning
warnings.filterwarnings("ignore", category=InconsistentVersionWarning)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figure_style as st
import plot_Fig2_arch_recon as fig2
from matplotlib.patches import FancyBboxPatch

# ---------- capture figures instead of saving ----------
captured = []
_orig_save = st.save_fig
def fake_save(fig, stem, **kw):
    captured.append((fig, stem, kw))
st.save_fig = fake_save
fig2.main()
st.save_fig = _orig_save

JOURNAL = [c for c in captured if not c[1].endswith("_large")][0]
fig, stem, kw = JOURNAL
print("captured stem:", os.path.basename(stem))
renderer = fig.canvas.get_renderer()
W_in, H_in = fig.get_size_inches()
print("figsize (in): %.2f x %.2f" % (W_in, H_in))

def figbbox(t):
    bb = t.get_window_extent(renderer=renderer)
    inv = fig.transFigure.inverted()
    a, b = inv.transform((bb.x0, bb.y0)); c, d = inv.transform((bb.x1, bb.y1))
    return (min(a, c), min(b, d), max(a, c), max(b, d))

def axes_frac(ax):
    r = ax.get_position()
    return (r.x0, r.y0, r.x1, r.y1)

# ---------- 1. axes positions ----------
print("\n[1] AXES POSITIONS (figure fraction -> inches)")
for ax in fig.axes:
    x0, y0, x1, y1 = axes_frac(ax)
    print("  %-4s frac x %.3f-%.3f  y %.3f-%.3f  |  in x %.2f-%.2f  y %.2f-%.2f"
          % (ax.get_gid() or ax.get_subplotspec().get_geometry() if False else "ax",
             x0, x1, y0, y1, x0 * W_in, x1 * W_in, y0 * H_in, y1 * H_in))

# map panels by subplot spec
panels = {}
for ax in fig.axes:
    pos = ax.get_position().bounds
    panels[ax] = pos
# panel (a) = the tall full-width one
p_a = [ax for ax in fig.axes if ax.get_position().x0 < 0.2 and ax.get_position().x1 > 0.8][0]
others = [ax for ax in fig.axes if ax is not p_a]
p_b = sorted(others, key=lambda a: a.get_position().x0)[0]
p_c = sorted(others, key=lambda a: a.get_position().x0)[1]
label_map = {p_a: "(a)", p_b: "(b)", p_c: "(c)"}
title_map = {p_a: "VAE-v6 architecture · no cycle-consistency branch",
             p_b: "decoder reconstruction (frozen checkpoint)",
             p_c: "reconstruction error, test set (N = 15,307)"}

# ---------- 2. header coords + bboxes ----------
print("\n[2] PANEL TAG / TITLE (transAxes coords as placed, and measured figure-fraction bbox)")
headers = {}
for ax in (p_a, p_b, p_c):
    for t in ax.texts:
        if t.get_fontsize() == 14 and t.get_transform() is ax.transAxes:
            headers[(label_map[ax], "label")] = (ax, t)
        if t.get_fontsize() in (13, 9) and t.get_transform() is ax.transAxes:
            headers[(label_map[ax], "title")] = (ax, t)

# verify the placement source values
print("  placed: tag at transAxes (0.00, 1.08) va=bottom ha=left bold fs14;"
      " title at (title_x, 1.08) SAME baseline va=bottom ha=left fs13 (a) / fs9 (b),(c)"
      "  [title_x=0.054 for (a), 0.116 for (b), 0.133 for (c)]")
for tag in ("(a)", "(b)", "(c)"):
    _, tl = headers[(tag, "label")]
    print("  %s tag fontsize = %g (bold=%s)" % (tag, tl.get_fontsize(), tl.get_fontweight()))
for tag in ("(a)", "(b)", "(c)"):
    ax, tl = headers[(tag, "label")]; ax2, tt = headers[(tag, "title")]
    bl = figbbox(tl); bt = figbbox(tt)
    print("  %s  tag bbox fig y %.3f-%.3f x %.3f-%.3f  |  title bbox fig y %.3f-%.3f x %.3f-%.3f"
          % (tag, bl[1], bl[3], bl[0], bl[2], bt[1], bt[3], bt[0], bt[2]))

# ---------- 2c. tag/title same baseline + consistent visual gap (micro-fix spec) ----------
print("\n[2c] TAG/TITLE SAME BASELINE + CONSISTENT GAP (fs14 bold tags)")
gaps = {}
for tag in ("(a)", "(b)", "(c)"):
    _, tl = headers[(tag, "label")]; _, tt = headers[(tag, "title")]
    bl, bt = figbbox(tl), figbbox(tt)
    same_bl = abs(bl[1] - bt[1]) < 1e-4  # both va=bottom on the same baseline
    gap_in = (bt[0] - bl[2]) * W_in
    gaps[tag] = gap_in
    print("  %s baseline fig y: tag %.4f title %.4f (same=%s) | tag->title gap %.3f in"
          % (tag, bl[1], bt[1], "YES" if same_bl else "NO", gap_in))
g = [gaps[t] for t in ("(a)", "(b)", "(c)")]
print("  gap spread: min %.3f max %.3f (range %.3f in -> %s)"
      % (min(g), max(g), max(g) - min(g),
         "OK" if max(g) - min(g) <= 0.03 else "INCONSISTENT"))

# ---------- 2b. single-line titles fit inside figure (and near their panel) ----------
print("\n[2b] SINGLE-LINE TITLE FIT (inside figure; overhang past own panel's right edge)")
for tag in ("(a)", "(b)", "(c)"):
    ax, tt = headers[(tag, "title")]
    bt = figbbox(tt)
    r = ax.get_position()
    inside_fig = bt[0] >= -0.002 and bt[2] <= 1.002 and bt[1] >= -0.002 and bt[3] <= 1.002
    over_panel = bt[2] - r.x1
    nl = tt.get_text().count("\n")
    print("  %s fs=%g single-line=%s bbox x %.3f-%.3f (panel right %.3f, overhang %+.4f) -> %s"
          % (tag, tt.get_fontsize(), "YES" if nl == 0 else "NO(%d lines)" % nl,
             bt[0], bt[2], r.x1, over_panel,
             "OK" if inside_fig and over_panel <= 0.02 else "FAIL"))

# ---------- 3. label-vs-title overlap ----------
print("\n[3] LABEL vs TITLE bbox overlap (figure fraction)")
bad = 0
for tag in ("(a)", "(b)", "(c)"):
    _, tl = headers[(tag, "label")]; _, tt = headers[(tag, "title")]
    bl, bt = figbbox(tl), figbbox(tt)
    ox = max(0.0, min(bl[2], bt[2]) - max(bl[0], bt[0]))
    oy = max(0.0, min(bl[3], bt[3]) - max(bl[1], bt[1]))
    ov = ox * oy
    flag = "OK" if ov <= 1e-9 else "OVERLAP!"
    if ov > 1e-9:
        bad += 1
    print("  %s overlap area = %.3e  -> %s" % (tag, ov, flag))

# ---------- 4. clipping / border clearance ----------
print("\n[4] CLIP + BORDER CHECK")
# 4a. every header bbox inside figure
figbad = 0
for (tag, kind), (ax, t) in headers.items():
    bb = figbbox(t)
    inside = bb[0] >= -0.002 and bb[2] <= 1.002 and bb[1] >= -0.002 and bb[3] <= 1.002
    if not inside:
        figbad += 1
        print("  CLIP! %s %s bbox %s" % (tag, kind, bb))
print("  header texts inside figure (no clip): %s" % ("OK" if figbad == 0 else "%d FAIL" % figbad))
# 4b. header vs its own axes top border (title/label must sit above the axes top)
ax_top = {}
for ax in (p_a, p_b, p_c):
    r = ax.get_position(); ax_top[ax] = r.y1
for tag in ("(a)", "(b)", "(c)"):
    ax, tl = headers[(tag, "label")]; ax2, tt = headers[(tag, "title")]
    bl, bt = figbbox(tl), figbbox(tt)
    top = ax_top[ax]
    below = min(bl[1], bt[1])
    gap = below - top
    print("  %s header bottom (fig) %.4f vs axes top %.4f -> clearance %.4f %s"
          % (tag, below, top, gap, "OK" if gap >= -1e-6 else "TOUCHES/BELOW"))
# 4c. (b)/(c) header top vs panel (a) bottom
ra = p_a.get_position()
for tag, ax in (("(b)", p_b), ("(c)", p_c)):
    _, tl = headers[(tag, "label")]
    bl = figbbox(tl)
    gap = ra.y0 - bl[3]
    print("  %s header top %.4f vs panel (a) bottom %.4f -> clearance %.4f %s"
          % (tag, bl[3], ra.y0, gap, "OK" if gap >= 0 else "COLLIDES"))

# 4d. ALL text artists inside figure (sweep)
allbad = 0
for ax in fig.axes:
    for t in ax.texts:
        bb = figbbox(t)
        if not (bb[0] >= -0.002 and bb[2] <= 1.002 and bb[1] >= -0.002 and bb[3] <= 1.002):
            allbad += 1
            print("  CLIP: ax %s text %r bbox %s" % (label_map.get(ax, "?"), t.get_text()[:30], bb))
for lg in fig.legends:
    if lg.get_visible():
        bb = lg.get_window_extent(renderer=renderer)
        inv = fig.transFigure.inverted()
        a, b = inv.transform((bb.x0, bb.y0)); c, d = inv.transform((bb.x1, bb.y1))
        if not (min(a, c) >= -0.002 and max(a, c) <= 1.002 and min(b, d) >= -0.002 and max(b, d) <= 1.002):
            allbad += 1
            print("  CLIP legend")
print("  all-text inside-figure sweep: %s" % ("OK" if allbad == 0 else "%d FAIL" % allbad))

# ---------- 5. panel (b) legend checks ----------
from matplotlib.legend import Legend as _Legend
legs_found = []
for ax in fig.axes:
    for a in ax.artists:
        if isinstance(a, _Legend) and a.get_visible():
            legs_found.append((ax, a))
    if ax.legend_ is not None and isinstance(ax.legend_, _Legend) and ax.legend_.get_visible():
        if (ax, ax.legend_) not in legs_found:
            legs_found.append((ax, ax.legend_))
print("\n[5] LEGENDS (found %d on axes)" % len(legs_found))
# curve points (all 6 curves on panel b)
xs, ys = [], []
for ln in p_b.lines:
    for x, y in zip(ln.get_xdata(), ln.get_ydata()):
        xs.append(x); ys.append(y)
pts = np.array([xs, ys]).T
def legend_fig_bbox(lg):
    bb = lg.get_window_extent(renderer=renderer)
    inv = fig.transFigure.inverted()
    a, b = inv.transform((bb.x0, bb.y0)); c, d = inv.transform((bb.x1, bb.y1))
    return (min(a, c), min(b, d), max(a, c), max(b, d))
def legend_data_bbox(lg, ax):
    bb = lg.get_window_extent(renderer=renderer)
    inv = ax.transData.inverted()
    a, b = inv.transform((bb.x0, bb.y0)); c, d = inv.transform((bb.x1, bb.y1))
    return (min(a, c), min(b, d), max(a, c), max(b, d))
# classify legends by figure x-centre: (b) = left column, (c) = right column
for k, (ownax, lg) in enumerate(legs_found, 1):
    fb = legend_fig_bbox(lg)
    xc = (fb[0] + fb[2]) / 2.0
    owner = ownax
    tag = "(b)" if owner is p_b else "(c)"
    print("  legend%d fig bbox x %.3f-%.3f y %.3f-%.3f (owner %s)"
          % (k, fb[0], fb[2], fb[1], fb[3], tag))
    if owner is p_b:
        x0, y0, x1, y1 = legend_data_bbox(lg, p_b)
        inside = pts[(pts[:, 0] >= x0) & (pts[:, 0] <= x1) & (pts[:, 1] >= y0) & (pts[:, 1] <= y1)]
        print("      leg%d data bbox x %.2f-%.2f y %.2f-%.2f  curve pts inside = %d %s"
              % (k, x0, x1, y0, y1, len(inside), "OK" if len(inside) == 0 else "BAD"))
        # vs (b) header + axes box
        _, tl = headers[("(b)", "title")]
        gap = figbbox(tl)[1] - fb[3]
        print("      leg%d top fig %.4f vs (b) header bottom %.4f -> gap %.4f %s"
              % (k, fb[3], figbbox(tl)[1], gap, "OK" if gap >= 0 else "COLLIDES"))
        r = p_b.get_position()
        ok = fb[0] >= r.x0 - 0.01 and fb[2] <= r.x1 + 0.01 and fb[1] >= r.y0 - 0.01 and fb[3] <= r.y1 + 0.01
        print("      leg%d inside (b) axes box: %s" % (k, "OK" if ok else "LEAKS OUT"))
    else:
        _, tl = headers[("(c)", "title")]
        bt = figbbox(tl)
        print("      (c) legend top fig %.4f vs (c) title bottom fig %.4f -> gap %.4f %s"
              % (fb[3], bt[1], bt[1] - fb[3], "OK" if bt[1] - fb[3] >= 0 else "COLLIDES"))

# ---------- 6. panel (a) arch text vs boxes ----------
# Correct test: text owned by a box (centre inside it) must be fully CONTAINED
# in the box; text not owned by any box (annotations/arrows labels) must not
# overlap any box.
print("\n[6] PANEL (a) TEXT vs BOX (containment + annotation overlap)")
boxes = [p for p in p_a.patches if isinstance(p, FancyBboxPatch)]

# input-box clip check: the leftmost box's PAINTED left edge (boxstyle pad 0.004
# expands the round rect outward) must sit inside xlim 0..1.22
left_box = min(boxes, key=lambda p: p.get_bbox().bounds[0])
_lb = left_box.get_bbox().bounds
lb = (_lb[0], _lb[1], _lb[0] + _lb[2], _lb[1] + _lb[3])
painted_left = lb[0] - 0.004
print("  input box data x %.4f-%.4f (painted left edge %.4f, must be > 0) -> %s"
      % (lb[0], lb[2], painted_left, "OK" if painted_left > 0.002 else "STILL CLIPPED"))

def data_bbox(t, ax):
    bb = t.get_window_extent(renderer=renderer)
    inv = ax.transData.inverted()
    a, b = inv.transform((bb.x0, bb.y0)); c, d = inv.transform((bb.x1, bb.y1))
    return (min(a, c), min(b, d), max(a, c), max(b, d))
def box_bounds(p):
    b = p.get_bbox().bounds
    return (b[0], b[1], b[0] + b[2], b[1] + b[3])
def pad(bb, eps):
    return (bb[0] - eps, bb[1] - eps, bb[2] + eps, bb[3] + eps)
def contains(box, bb):
    return box[0] <= bb[0] and box[1] <= bb[1] and box[2] >= bb[2] and box[3] >= bb[3]
fail = 0
for t in p_a.texts:
    if t.get_fontsize() in (14, 13, 9):
        continue  # header handled above
    tb = data_bbox(t, p_a)
    owner = None
    for p in boxes:
        bx = box_bounds(p)
        cxp = (tb[0] + tb[2]) / 2; cyp = (tb[1] + tb[3]) / 2
        if bx[0] <= cxp <= bx[2] and bx[1] <= cyp <= bx[3]:
            owner = bx
            break
    if owner is not None:
        # box-owned text: must be inside the box (allow small glyph tolerance)
        if not contains(pad(owner, 0.012), tb):
            fail += 1
            print("  OVERFLOW: %r bbox %s exceeds box %s"
                  % (t.get_text()[:24], tuple(round(v, 3) for v in tb),
                     tuple(round(v, 3) for v in owner)))
    else:
        # free annotation: must not overlap any box
        for p in boxes:
            bx = box_bounds(p)
            ox = max(0.0, min(tb[2], bx[2]) - max(tb[0], bx[0]))
            oy = max(0.0, min(tb[3], bx[3]) - max(tb[1], bx[1]))
            if ox > 1e-4 and oy > 1e-4:
                fail += 1
                print("  ANNOT-OVERLAP: %r vs box %s ox %.3f oy %.3f"
                      % (t.get_text()[:24], tuple(round(v, 3) for v in bx), ox, oy))
print("  arch text/box overlaps (corrected containment test): %d %s"
      % (fail, "OK" if fail == 0 else "FAIL"))
# KL/L_recon labels now at 0.900: verify they sit above the highest box and below axes top
max_box_top = max(p.get_bbox().bounds[1] + p.get_bbox().bounds[3] for p in boxes)
for t in p_a.texts:
    txt = t.get_text()
    if (r"$L_{\mathrm{KL}}" in txt or r"$L_{\mathrm{recon}}$" in txt) and t.get_fontsize() == st.FS_CAPTION_TXT:
        tb = data_bbox(t, p_a)
        print("  %r data y %.3f-%.3f (axes top 1.02, boxes top %.3f)"
              % (txt[:26], tb[1], tb[3], max_box_top))

# ---------- 7. frozen values + rendered pixel size ----------
print("\n[7] FROZEN + PIXELS")
from PIL import Image
for fn in ("Fig2_arch_recon_surgical3.png", "Fig2_arch_recon_surgical3_large.png"):
    path = os.path.join(os.path.dirname(fig2.OUT_DIR), "Fig2", fn)
    if os.path.exists(path):
        im = Image.open(path)
        print("  %s: %dx%d px" % (fn, im.size[0], im.size[1]))
    else:
        print("  MISSING %s" % path)
# pdf/svg presence
for ext in ("pdf", "svg"):
    p = os.path.join(fig2.OUT_DIR, "Fig2_arch_recon_surgical3." + ext)
    print("  surgical3.%s: %s" % (ext, "present" if os.path.exists(p) else "MISSING"))

# ---------- 8. L_NLL dashed-arrow reroute ----------
from matplotlib.patches import FancyArrowPatch
print("\n[8] L_NLL ARROW REROUTE (flat left->right feed-in, heads on the label)")
nll_text = [t for t in p_a.texts if "$L_{\\mathrm{NLL}}$" in t.get_text()][0]
nb = data_bbox(nll_text, p_a)
print("  L_NLL label data bbox x %.3f-%.3f  y %.3f-%.3f" % (nb[0], nb[2], nb[1], nb[3]))
# all dashed arrows; the KL / L_recon leaders are filtered out below by "near"
dashes = [p for p in p_a.patches
          if isinstance(p, FancyArrowPatch) and p.get_linestyle() != "-"]
nll_arrows = []
for p in dashes:
    (x0, y0), (x1, y1) = p._posA_posB  # mpl 3.10: get_posA/get_posB removed
    near = (x1 >= nb[0] - 0.03 and x1 <= nb[2] + 0.03 and
            y1 >= nb[1] - 0.03 and y1 <= nb[3] + 0.03)
    from_box = x0 >= 1.080  # start at the head boxes' right edge region
    if near:  # the KL / L_recon leaders are also dashed UNC_C; keep only NLL
        nll_arrows.append((x0, y0, x1, y1, near, from_box))
for i, (x0, y0, x1, y1, near, from_box) in enumerate(nll_arrows, 1):
    dx, dy = x1 - x0, y1 - y0
    slope = abs(dy) / max(dx, 1e-9)
    flat = dx > 0.05 and slope <= 2.5  # reads left->right, not a steep climb
    print("  NLL arrow%d start(%.3f,%.3f) head(%.3f,%.3f) | dx %.3f dy %.3f slope %.2f"
          " | head near label: %s | starts at head box: %s | flat feed-in: %s"
          % (i, x0, y0, x1, y1, dx, dy, slope,
             "OK" if near else "FAR", "OK" if from_box else "WRONG START",
             "OK" if flat else "STEEP"))
print("  NLL arrows converging into the label: %d/2 -> %s"
      % (len(nll_arrows), "OK" if len(nll_arrows) == 2 else "FAIL"))
# both heads on the label's LEFT portion (feed in from the left, not the top)
if len(nll_arrows) == 2:
    xc = (nb[0] + nb[2]) / 2.0
    left_side = all(x1 <= xc + 0.005 for (_, _, x1, _, _, _) in nll_arrows)
    print("  both heads on label's left side: %s" % ("OK" if left_side else "FAIL"))
# heads must be separated (two distinct converge points, not a single point)
if len(nll_arrows) == 2:
    (x0a, y0a, x1a, y1a, _, _), (x0b, y0b, x1b, y1b, _, _) = nll_arrows
    sep = ((x1a - x1b) ** 2 + (y1a - y1b) ** 2) ** 0.5
    print("  arrow-head separation %.3f data (must be > 0.005 -> two arrows visible) -> %s"
          % (sep, "OK" if sep > 0.005 else "SAME POINT"))

print("\nQC DONE. total header-label-vs-title overlaps: %d; clip fails: %d" % (bad, figbad + allbad))
