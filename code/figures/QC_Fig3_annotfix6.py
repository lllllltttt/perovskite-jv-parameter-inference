# -*- coding: utf-8 -*-
"""QC for Fig3_recoverability_annotfix6 — grid spacing, tick-label subsetting,
square+lidger panels, width split, r mapping, panel-(b) fidelity, exports."""
import io, sys, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import fitz
from PIL import Image

BASE = r"E:\project\work1\final_figures\Fig3"
NEW = os.path.join(BASE, "Fig3_recoverability_annotfix6.pdf")
PREV = os.path.join(BASE, "Fig3_recoverability_annotfix5.pdf")
ok = []
def chk(name, cond, note=""):
    ok.append(bool(cond)); print("[%s] %s  %s" % ("PASS" if cond else "FAIL", name, note))

# ------------------------------------------------------------- matplotlib geom
import os as _os
sys.path.insert(0, _os.getcwd())
import figure_style as st
_cap = []
_orig = st.save_fig
def _capfn(fig, stem, **kw): _cap.append((fig, str(stem)))
st.save_fig = _capfn
import plot_Fig3_recoverability_annotfix6 as M
M.main()
import matplotlib
fig, stem = _cap[0]
fig.canvas.draw(); ren = fig.canvas.get_renderer()
fw, fh = fig.get_size_inches(); dp = fig.dpi
pt = 72.0 / dp
def bb(ax):
    b = ax.get_window_extent(ren); return (b.x0 * pt, b.y0 * pt, b.x1 * pt, b.y1 * pt)
def W(a): return bb(a)[2] - bb(a)[0]
def H(a): return bb(a)[3] - bb(a)[1]
panels = [a for a in fig.axes if a.get_subplotspec() is not None
          and a.get_subplotspec().get_gridspec().nrows == 3]
axb = [a for a in fig.axes if a is not panels[0] and a.get_subplotspec() is not None
       and a.get_subplotspec().get_gridspec().ncols == 2][0]
assert len(panels) == 9, len(panels)
pws = [W(a) for a in panels]; phs = [H(a) for a in panels]
asp = sum(pws) / sum(phs)
chk("panels square (aspect ~1.2)", 1.0 <= asp <= 1.35,
    "mean %.3f (w %.1f..%.1f, h %.1f..%.1f)" % (asp, min(pws), max(pws), min(phs), max(phs)))
import numpy as _np
xs = sorted(set(round(bb(a)[0], 1) for a in panels))
ys = sorted(set(round(bb(a)[3], 1) for a in panels), reverse=True)   # row tops, top row first
gap_col = [round(xs[k+1] - xs[k] - pws[0], 1) for k in range(len(xs) - 1)]
gap_row = [round(ys[k] - ys[k+1] - phs[0], 1) for k in range(len(ys) - 1)]
aw = sum(pws) / 9.0; ah = sum(phs) / 9.0
chk("real spacing present (wspace/hspace 0.08-0.12)",
    all(0.08 <= g / aw <= 0.12 for g in gap_col)
    and all(0.08 <= g / ah <= 0.12 for g in gap_row),
    "x gaps %s (frac %.3f), y gaps %s (frac %.3f)"
    % (gap_col, gap_col[0] / aw, gap_row, gap_row[0] / ah))
chk("(a) wider than (b)", W(axb) < W(panels[0]) * 3,
    "(a) grid %.0f pt vs (b) %.0f pt" % (sum(pws) + sum(gap_col), W(axb)))

# panel area vs annotfix5 (measured earlier: 65.3 x 52.5)
area6 = pws[0] * phs[0]
chk("panels larger than annotfix5", area6 > 3429 * 1.30,
    "area %.0f pt^2 vs annotfix5 3429 (%.0f%% of it)" % (area6, 100*area6/3429))

# ------------------------------------------------------------- PDF text checks
doc = fitz.open(NEW); pg = doc[0]
PW, PH = pg.rect.width, pg.rect.height
blocks = [b[:5] for b in pg.get_text("blocks")]
txt = "\n".join(b[4] for b in blocks)
chk("no clip (blocks inside page)", min(b[0] for b in blocks) > 0
    and max(b[2] for b in blocks) < PW and min(b[1] for b in blocks) > 0
    and max(b[3] for b in blocks) < PH,
    "text x %.1f..%.1f y %.1f..%.1f in %.0fx%.0f page"
    % (min(b[0] for b in blocks), max(b[2] for b in blocks),
       min(b[1] for b in blocks), max(b[3] for b in blocks), PW, PH))
chk("x-label present", "True normalized log10 parameter" in txt, "")
chk("y-label present", "Predicted normalized log10 parameter" in txt, "")

r_blocks = sorted([(b[1], b[0], b[4]) for b in blocks if re.search(r"r = \d\.\d{3}", b[4])])
rs = [m for (y, x, t) in r_blocks for m in re.findall(r"r = (\d\.\d{3})", t)]
EXP = ["0.906","0.919","0.878","0.881","0.909","0.896","0.594","0.720","0.559"]
chk("r-mapping 9/9 canonical order", rs == EXP, "got %s" % rs)
chk("r_rad token", bool(re.search(r"r\s*rad", txt)), "")

# ---- tick-label collision scan: every numeric tick word in (a) region ----
words = pg.get_text("words")
A = [w for w in words if w[0] < 270 and w[4] in ("0.0", "0.5", "1.0")]
def ov(a, b):
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])
coll = []
for i in range(len(A)):
    for j in range(i + 1, len(A)):
        if ov(A[i], A[j]):
            coll.append((A[i][4], A[j][4], A[i][:4], A[j][:4]))
chk("no overlapping numeric tick labels", len(coll) == 0,
    "n_tick_words=%d, collisions=%d" % (len(A), len(coll)))
if coll:
    for c in coll[:8]: print("      ", c)

# ---- shared labels clear of tick bands (exact figure coords via renderer) ----
axg = [a for a in fig.axes if a.get_subplotspec() is None][0]
bot = [a for a in panels if a.get_subplotspec().rowspan.start == 2]
lft = [a for a in panels if a.get_subplotspec().colspan.start == 0]
def wb(o):
    e = o.get_window_extent(ren); return (e.x0 * pt, e.y0 * pt, e.x1 * pt, e.y1 * pt)
xt_lo = min(wb(w)[1] for a in bot for w in a.get_xticklabels() if w.get_text())
yt_lo = min(wb(w)[0] for a in lft for w in a.get_yticklabels() if w.get_text())
xl = [t for t in axg.texts if "True normalized log10" in t.get_text()][0]
yl = [t for t in axg.texts if "Predicted normalized" in t.get_text()][0]
gx = xt_lo - wb(xl)[3]
gy = yt_lo - wb(yl)[2]
chk("x-label below bottom ticks", gx >= 3.0,
    "gap %.1f pt (tick bottom %.1f, label top %.1f)" % (gx, xt_lo, wb(xl)[3]))
chk("y-label left of y ticks", gy >= 3.0,
    "gap %.1f pt (tick left %.1f, label right %.1f)" % (gy, yt_lo, wb(yl)[2]))

# ---- panel (b) tokens unchanged vs annotfix5 ----
docO = fitz.open(PREV); pgO = docO[0]
def b_toks(pg, x0):
    s = set()
    for b in pg.get_text("blocks"):
        if b[0] >= x0:
            for w in b[4].split():
                if len(w) > 1:
                    s.add(w)
    return s
mt = sorted(t for t in b_toks(pgO, 270) - b_toks(pg, 270) if not re.fullmatch(r"[0-9.\-]+", t))
ex = sorted(t for t in b_toks(pg, 270) - b_toks(pgO, 270) if not re.fullmatch(r"[0-9.\-]+", t))
chk("panel (b) tokens unchanged vs annotfix5", not mt and not ex, "missing=%s extra=%s" % (mt, ex))

# ---- exports ----
im = Image.open(os.path.join(BASE, "Fig3_recoverability_annotfix6.png"))
dpi = im.info.get("dpi", (0, 0))[0]
chk("exports PNG@600+PDF+SVG", abs(dpi - 600) < 1
    and os.path.exists(os.path.join(BASE, "Fig3_recoverability_annotfix6.svg"))
    and os.path.exists(os.path.join(BASE, "Fig3_recoverability_annotfix6_large.png"))
    and os.path.exists(os.path.join(BASE, "Fig3_recoverability_annotfix6_large.pdf")),
    "PNG %dx%d @%.0fdpi" % (im.size[0], im.size[1], dpi))

print()
print("QC GATES: %d/%d PASS" % (sum(ok), len(ok)))
