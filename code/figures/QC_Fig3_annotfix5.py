# -*- coding: utf-8 -*-
"""QC for Fig3_recoverability_annotfix5 — geometry, mapping, panel-(b) fidelity."""
import io, sys, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import fitz
from PIL import Image

BASE = r"E:\project\work1\final_figures\Fig3"
NEW = os.path.join(BASE, "Fig3_recoverability_annotfix5.pdf")
OLD = os.path.join(BASE, "Fig3_recoverability_annotfix4.pdf")
ok = []
def chk(name, cond, note=""):
    ok.append(bool(cond)); print("[%s] %s  %s" % ("PASS" if cond else "FAIL", name, note))

doc = fitz.open(NEW); pg = doc[0]
PW, PH = pg.rect.width, pg.rect.height
blocks = [b[:5] for b in pg.get_text("blocks")]

# --- page bounds / no clipping ---
mx0 = min(b[0] for b in blocks); mx1 = max(b[2] for b in blocks)
my0 = min(b[1] for b in blocks); my1 = max(b[3] for b in blocks)
chk("no clip (blocks inside page)", mx0 > 0 and mx1 < PW and my0 > 0 and my1 < PH,
    "page %.0fx%.0f, text x %.1f..%.1f y %.1f..%.1f" % (PW, PH, mx0, mx1, my0, my1))

# --- shared axis labels ---
txt = "\n".join(b[4] for b in blocks)
chk("x-label 'True normalized log10 parameter'", "True normalized log10 parameter" in txt, "")
chk("y-label 'Predicted normalized log10 parameter'", "Predicted normalized log10 parameter" in txt, "")

# --- r mapping: expect 9 r annotations in canonical order (row-major) ---
r_blocks = [(b[1], b[0], b[4]) for b in blocks if re.search(r"r = \d\.\d{3}", b[4])]
r_blocks.sort()
rs = [m for (y, x, t) in r_blocks for m in re.findall(r"r = (\d\.\d{3})", t)]
EXP = ["0.906","0.919","0.878","0.881","0.909","0.896","0.594","0.720","0.559"]
chk("r-mapping 9/9 canonical order", rs == EXP, "got %s" % rs)
chk("r_rad token present", "rrad" in txt.replace("\n"," ") or "$r_\\mathrm{rad}$" in txt
    or re.search(r"r\s*rad", txt), "")

# --- shared x-label clear of bottom-row tick band ---
# (a) anchor -> offset: (a) text at data(0,1.06) fig-y = 27.6+1.06*220.5 = 261.3
xlab = [b for b in blocks if "True normalized log10 parameter" in b[4]][0]
# bottom-row x-tick labels = 0.0/0.5/1.0 words in the bottom region (y_from_top>215)
words = pg.get_text("words")
bot_ticks = [w for w in words if w[4] in ("0.0", "0.5", "1.0") and w[1] > 215
             and 30 < w[0] < 265]
# convert page-from-top to figure-from-bottom via (a)
a_blk = [b for b in blocks if b[4].strip() == "(a)"][0]
a_top = (a_blk[1] + a_blk[3]) / 2.0            # page-from-top
OFFSET = 261.3 - (PH - a_top)                  # fig_y = page_from_bottom + OFFSET
xl_fig_top = (PH - xlab[1]) + OFFSET           # block top in fig-from-bottom
xl_fig_bot = (PH - xlab[3]) + OFFSET
tick_bot_fig = min((PH - w[3]) + OFFSET for w in bot_ticks)
chk("x-label below tick labels", xl_fig_top < tick_bot_fig - 2.0,
    "label top fig-y %.1f < tick bottom fig-y %.1f (gap %.1f pt)"
    % (xl_fig_top, tick_bot_fig, tick_bot_fig - xl_fig_top))

# --- panel (b) unchanged: same text tokens as annotfix4 in the (b) region ---
docO = fitz.open(OLD); pgO = docO[0]
def b_tokens(pg, x0):
    toks = set()
    for b in pg.get_text("blocks"):
        if b[0] >= x0:
            for w in b[4].split():
                if len(w) > 1:
                    toks.add(w)
    return toks
# annotfix4: (b) region x>240 ; annotfix5: x>270
tok_new = b_tokens(pg, 270)
tok_old = b_tokens(pgO, 240)
missing = tok_old - tok_new
extra = tok_new - tok_old
# numeric tick tokens (0.1..0.9, 0.55..0.90) legitimately identical; ignore pure numbers
missing_txt = sorted(t for t in missing if not re.fullmatch(r"[0-9.\-]+", t))
extra_txt = sorted(t for t in extra if not re.fullmatch(r"[0-9.\-]+", t))
chk("panel (b) text tokens unchanged", not missing_txt and not extra_txt,
    "missing=%s extra=%s" % (missing_txt, extra_txt))

# --- exports ---
im = Image.open(os.path.join(BASE, "Fig3_recoverability_annotfix5.png"))
dpi = im.info.get("dpi", (0, 0))[0]
chk("exports PNG@600+PDF+SVG", abs(dpi - 600) < 1
    and os.path.exists(os.path.join(BASE, "Fig3_recoverability_annotfix5.svg"))
    and os.path.exists(os.path.join(BASE, "Fig3_recoverability_annotfix5_large.png"))
    and os.path.exists(os.path.join(BASE, "Fig3_recoverability_annotfix5_large.pdf")),
    "PNG %dx%d @%.0fdpi" % (im.size[0], im.size[1], dpi))

print()
print("QC GATES: %d/%d PASS" % (sum(ok), len(ok)))
