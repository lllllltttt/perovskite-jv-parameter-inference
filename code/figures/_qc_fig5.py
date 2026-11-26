# -*- coding: utf-8 -*-
"""Programmatic QC for the Fig.5 micro-fix pass (model cannot view images).

Rebuilds the journal figure in-memory via fig5.build_figure() with
st.save_fig monkey-patched to a no-op, then measures:
  1. frozen values are asserted inside build_figure itself (MSE/correlations/
     tier medians/param order/representative cases/transitions)
  2. panel-(b) two-line x-category labels vs panel-(d) heading band: no
     vertical overlap, heading centred over the bottom-right subpanel
  3. heading vs mechanism sub-titles and vs panel-(b) axes box: no overlap
  4. panel tags (a)(b)(c)(d) present, consistent placement
  5. (d) minis: internal gap, inline "curve 1/2" labels in the LOWER-LEFT
     quadrant stacked above the annotation block, line samples left of the
     text, no curve points inside any label/annotation/sample bbox, no label
     vs annotation overlap, no text vs axes-frame collision
  6. axes ranges identical to the frozen values on all panels + minis
  7. all text inside the figure (no clipping)
  8. rendered PNG pixel sizes + pdf/svg presence for the new stem
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
import plot_Fig5_final as fig5
from matplotlib.lines import Line2D

# ---------- capture the journal figure instead of saving ----------
captured = []
_orig_save = st.save_fig
def fake_save(fig, stem, **kw):
    captured.append((fig, stem, kw))
st.save_fig = fake_save
fig, info = fig5.build_figure("journal")
st.save_fig = _orig_save

renderer = fig.canvas.get_renderer()
W_in, H_in = fig.get_size_inches()
print("figsize (in): %.2f x %.2f" % (W_in, H_in))

def figbbox(t):
    bb = t.get_window_extent(renderer=renderer)
    inv = fig.transFigure.inverted()
    a, b = inv.transform((bb.x0, bb.y0)); c, d = inv.transform((bb.x1, bb.y1))
    return (min(a, c), min(b, d), max(a, c), max(b, d))

def data_bbox(t, ax):
    bb = t.get_window_extent(renderer=renderer)
    inv = ax.transData.inverted()
    a, b = inv.transform((bb.x0, bb.y0)); c, d = inv.transform((bb.x1, bb.y1))
    return (min(a, c), min(b, d), max(a, c), max(b, d))

# ---------- map panels ----------
axa, axb = info["axa"], info["axb"]
axc, axd = info["axc"], info["axd"]
insets = info["insets"]
d_info = info["d_info"]
ra, rb, rc, rd = (ax.get_position().bounds for ax in (axa, axb, axc, axd))
print("\n[1] AXES (fig frac)  a x%.2f-%.2f y%.2f-%.2f | b x%.2f-%.2f y%.2f-%.2f"
      % (ra[0], ra[0]+ra[2], ra[1], ra[1]+ra[3], rb[0], rb[0]+rb[2], rb[1], rb[1]+rb[3]))
print("                     c x%.2f-%.2f y%.2f-%.2f | d x%.2f-%.2f y%.2f-%.2f"
      % (rc[0], rc[0]+rc[2], rc[1], rc[1]+rc[3], rd[0], rd[0]+rd[2], rd[1], rd[1]+rd[3]))

# ---------- 2. (b) x-category labels vs (d) heading ----------
print("\n[2] PANEL (b) CATEGORY LABELS vs (d) HEADING BAND")
tickbb = None
for lab in axb.get_xticklabels():
    b = figbbox(lab)
    tickbb = b if tickbb is None else (
        min(tickbb[0], b[0]), min(tickbb[1], b[1]),
        max(tickbb[2], b[2]), max(tickbb[3], b[3]))
print("  (b) x-tick labels bbox fig y %.4f-%.4f  x %.4f-%.4f"
      % (tickbb[1], tickbb[3], tickbb[0], tickbb[2]))
head = [t for t in axd.texts if "Representative collisions" in t.get_text()][0]
hb = figbbox(head)
d_xc = rd[0] + rd[2] / 2.0
h_xc = (hb[0] + hb[2]) / 2.0
print("  (d) heading bbox fig y %.4f-%.4f  x %.4f-%.4f  (fs %g, centered=%s,"
      " |dxc-%.3f|) "
      % (hb[1], hb[3], hb[0], hb[2], head.get_fontsize(),
         "YES" if abs(h_xc - d_xc) < 0.03 else "NO", abs(h_xc - d_xc)))
# heading must be below the tick-label band (no overlap)
ov_y = max(0.0, min(hb[3], tickbb[3]) - max(hb[1], tickbb[1]))
ov_x = max(0.0, min(hb[2], tickbb[2]) - max(hb[0], tickbb[0]))
print("  heading vs (b) tick labels: overlap area = %.3e -> %s"
      % (ov_x * ov_y, "OK" if ov_x * ov_y <= 1e-9 else "OVERLAP!"))
# heading must not touch the (b) axes box either
ov_b = max(0.0, min(hb[3], rb[1]+rb[3]) - max(hb[1], rb[1])) * \
       max(0.0, min(hb[2], rb[0]+rb[2]) - max(hb[0], rb[0]))
print("  heading vs panel-(b) axes box: overlap area = %.3e -> %s"
      % (ov_b, "OK" if ov_b <= 1e-9 else "OVERLAP!"))
# gap between (b) axes bottom and heading top
print("  (b) axes bottom fig %.4f vs heading top %.4f -> gap %.4f in %s"
      % (rb[1], hb[3], (rb[1] - hb[3]) * H_in,
         "OK" if rb[1] - hb[3] >= 0.01 else "TIGHT"))

# ---------- 3. heading vs mechanism sub-titles ----------
print("\n[3] HEADING vs MECHANISM SUB-TITLES")
for t in axd.texts:
    txt = t.get_text()
    if "collision" in txt and "Representative" not in txt:
        sb = figbbox(t)
        ovx = max(0.0, min(hb[2], sb[2]) - max(hb[0], sb[0]))
        ovy = max(0.0, min(hb[3], sb[3]) - max(hb[1], sb[1]))
        print("  '%s' bbox fig y %.4f-%.4f | vs heading overlap %.3e -> %s"
              % (txt[:22], sb[1], sb[3], ovx * ovy,
                 "OK" if ovx * ovy <= 1e-9 else "OVERLAP!"))

# ---------- 4. panel tags ----------
print("\n[4] PANEL TAGS")
for ax, tag in ((axa, "(a)"), (axb, "(b)"), (axc, "(c)"), (axd, "(d)")):
    tt = [t for t in ax.texts if t.get_text() == tag and
          t.get_transform() is ax.transAxes][0]
    bb = figbbox(tt)
    r = ax.get_position()
    inside = bb[0] >= r.x0 - 0.12 and bb[2] <= r.x1 + 0.12
    print("  %s fs %g bold=%s bbox fig x%.3f-%.3f y%.3f-%.3f (near own panel: %s)"
          % (tag, tt.get_fontsize(), tt.get_fontweight(), bb[0], bb[2], bb[1], bb[3],
             "OK" if inside else "WRONG PANEL"))

# ---------- 5. (d) minis ----------
print("\n[5] PANEL (d) MINIS + INLINE CURVE LABELS")

def ins_frac_bbox(t, ins):
    """Text bbox in inset-axes fraction coords (0..1 within the mini)."""
    bb = t.get_window_extent(renderer=renderer)
    inv = ins.transAxes.inverted()
    a, b = inv.transform((bb.x0, bb.y0)); c, d = inv.transform((bb.x1, bb.y1))
    return (min(a, c), min(b, d), max(a, c), max(b, d))

# 5a. mini frames + internal gap (figure fraction -> inches)
f1 = insets[0].get_position().bounds
f2 = insets[1].get_position().bounds
gap = (f2[0] - (f1[0] + f1[2])) * W_in
print("  mini1 x%.3f-%.3f  mini2 x%.3f-%.3f  (fig frac) | internal gap = %.3f in -> %s"
      % (f1[0], f1[0]+f1[2], f2[0], f2[0]+f2[2], gap,
         "OK" if gap >= 0.25 else "TIGHT"))
# 5b. inline labels + annotation: placement and overlap (ins-fraction coords)
for k, ins in enumerate(insets):
    tag = "d%d" % (k + 1)
    c1 = [t for t in ins.texts if t.get_text() == "curve 1"][0]
    c2 = [t for t in ins.texts if t.get_text() == "curve 2"][0]
    ann = [t for t in ins.texts if "$d_J" in t.get_text()][0]
    b1, b2, ba = (ins_frac_bbox(t, ins) for t in (c1, c2, ann))
    db1, db2, dba = (data_bbox(t, ins) for t in (c1, c2, ann))
    # lower-left quadrant (left half, and in the lower-to-mid band that stays
    # clear of the plateau curves) + stacked ABOVE the annotation block
    ll = (b1[2] < 0.60 and b2[2] < 0.60 and b1[1] >= 0.30 and b2[1] >= 0.30
          and b1[1] >= ba[3] - 0.001 and b2[1] >= ba[3] - 0.001)
    def ov(a, b):
        return max(0.0, min(a[2], b[2]) - max(a[0], b[0])) * \
               max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    ov_ann = ov(b1, ba) + ov(b2, ba)
    ov_12 = ov(b1, b2)
    # line samples: two Line2D with transAxes in this ins, left of the texts
    sames = [ln for ln in ins.lines if isinstance(ln, Line2D)
             and ln.get_transform() is ins.transAxes]
    s1, s2 = sames
    x1s = s1.get_xdata(); x2s = s2.get_xdata()
    lx = (x1s[0] < b1[0] and x1s[1] < b1[0] and x2s[0] < b2[0] and x2s[1] < b2[0])
    # style association
    col_ok = (s1.get_color() == st.OKABE_ITO[0] and s1.get_linestyle() == "-"
              and s2.get_color() == st.OKABE_ITO[3] and s2.get_linestyle() == "--")
    # stacked order: curve 2 below curve 1 (lower y), each row = its own curve
    stack_ok = b2[1] < b1[1]
    print("  %s curve1 bbox x%.3f-%.3f y%.3f-%.3f | curve2 x%.3f-%.3f y%.3f-%.3f |"
          " ann top y%.3f"
          % (tag, b1[0], b1[2], b1[1], b1[3], b2[0], b2[2], b2[1], b2[3], ba[3]))
    print("      lower-left+above-ann: %s | label/ann overlap: %s |"
          " label-label overlap: %s | stacked(c2 below c1): %s"
          " | samples left: %s | blue-solid/orange-dashed: %s"
          % ("OK" if ll else "FAIL", "OK" if ov_ann <= 1e-9 else "OVERLAP!",
             "OK" if ov_12 <= 1e-9 else "OVERLAP!", "OK" if stack_ok else "FAIL",
             "OK" if lx else "FAIL", "OK" if col_ok else "FAIL"))
    # 5c. no curve points inside the label / annotation / sample bboxes (data coords)
    pts = []
    for ln in ins.lines:
        if ln.get_transform() is ins.transData:
            for x, y in zip(ln.get_xdata(), ln.get_ydata()):
                pts.append((x, y))
    pts = np.array(pts)
    bad = 0
    for nm, bb in (("c1", db1), ("c2", db2), ("ann", dba)):
        inside = pts[(pts[:, 0] >= bb[0]) & (pts[:, 0] <= bb[2]) &
                     (pts[:, 1] >= bb[1]) & (pts[:, 1] <= bb[3])]
        if len(inside):
            bad += 1
            print("      %s bbox contains %d curve pts!" % (nm, len(inside)))
    print("      curve points inside labels/annotation: %d -> %s"
          % (bad, "OK" if bad == 0 else "FAIL"))
    # 5d. annotation + labels clear of the mini's axes frame (ins-fraction coords)
    ann_clear = ba[0] >= 0.01 and ba[1] >= 0.01 and ba[2] <= 0.99 and ba[3] <= 0.99
    lab_clear = b1[0] >= 0.01 and b1[1] >= 0.01 and b2[0] >= 0.01 and b2[1] >= 0.01 \
                and b1[2] <= 0.99 and b2[2] <= 0.99
    print("      annotation inside mini frame: %s (ins bbox x%.3f-%.3f y%.3f-%.3f)"
          % ("OK" if ann_clear else "POKES OUT", ba[0], ba[2], ba[1], ba[3]))
    print("      labels inside mini frame: %s" % ("OK" if lab_clear else "POKES OUT"))

# ---------- 6. axes ranges unchanged ----------
print("\n[6] AXES RANGES (frozen)")
# ("b","x") is auto-expanded by matplotlib (no explicit xlim in the script; bar
# width 0.62 -> margins carry it to -0.541, 4.541), so its baseline is that
# measured frozen value; all others are set in code.
exp = {("a", "x"): (-4.5, -0.85), ("a", "y"): (0.0, 0.63),
       ("b", "x"): (-0.541, 4.541), ("b", "y"): (0.0, 0.40),
       ("c", "x"): (0.0, 0.19), ("c", "y"): (-0.6, 8.6),
       ("ins", "x"): (0.0, 1.3), ("ins", "y"): (-6.0, 33.0)}
TOL = 1e-6
for (key, axname), (lo, hi) in exp.items():
    if key == "ins":
        for k, ins in enumerate(insets):
            got = ins.get_xlim() if axname == "x" else ins.get_ylim()
            ok = abs(got[0] - lo) < TOL and abs(got[1] - hi) < TOL
            print("  ins%d %s range (%.2f, %.2f) -> %s"
                  % (k + 1, axname, got[0], got[1], "OK" if ok else "CHANGED"))
        continue
    ax = info["ax" + key]
    got = ax.get_xlim() if axname == "x" else ax.get_ylim()
    ok = abs(got[0] - lo) < TOL and abs(got[1] - hi) < TOL
    print("  panel %s %s range (%.2f, %.2f) -> %s"
          % (key, axname, got[0], got[1], "OK" if ok else "CHANGED"))

# ---------- 7. all text inside figure ----------
print("\n[7] ALL TEXT INSIDE FIGURE")
bad = 0
for ax in fig.axes:
    for t in ax.texts:
        bb = figbbox(t)
        if not (bb[0] >= -0.002 and bb[2] <= 1.002 and bb[1] >= -0.002 and bb[3] <= 1.002):
            bad += 1
            print("  CLIP: %r bbox %s" % (t.get_text()[:30], tuple(round(v, 3) for v in bb)))
for lg in fig.legends:
    if lg.get_visible():
        bb = lg.get_window_extent(renderer=renderer)
        inv = fig.transFigure.inverted()
        a, b = inv.transform((bb.x0, bb.y0)); c, d = inv.transform((bb.x1, bb.y1))
        if not (min(a, c) >= -0.002 and max(a, c) <= 1.002 and min(b, d) >= -0.002 and max(b, d) <= 1.002):
            bad += 1
            print("  CLIP legend")
print("  all-text inside-figure sweep: %s" % ("OK" if bad == 0 else "%d FAIL" % bad))

# ---------- 8. rendered files ----------
print("\n[8] RENDERED FILES")
from PIL import Image
for fn in ("Fig5_final_microfix2.png", "Fig5_final_microfix2_large.png"):
    path = os.path.join(os.path.dirname(fig5.OUT_DIR), "Fig5", fn)
    if os.path.exists(path):
        im = Image.open(path)
        print("  %s: %dx%d px" % (fn, im.size[0], im.size[1]))
    else:
        print("  MISSING %s" % path)
for ext in ("pdf", "svg"):
    p = os.path.join(fig5.OUT_DIR, "Fig5_final_microfix2." + ext)
    print("  microfix2.%s: %s" % (ext, "present" if os.path.exists(p) else "MISSING"))

print("\nQC DONE. clip fails: %d" % bad)
