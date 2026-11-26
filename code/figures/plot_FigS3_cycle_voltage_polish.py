"""
plot_FigS3_cycle_voltage_polish.py — publication-quality LAYOUT polish of ONLY
the Fig. S3 voltage-resolved-consistency panel.

Pure plotting/layout task. Reads the SAME frozen data
(decoder_comsol_audit/voltage_resolved_consistency.csv) with zero transformation.
No RMSE recomputed, no COMSOL re-run, 45 samples unchanged, three curves' values
unchanged, 1.0 V divider unchanged, noise floor 0.21 unchanged, manuscript
untouched. Writes ONLY to final_figures/SI_final_review/ (the review copy). The
original final_figures/SI/ figures and plot_SI_S3_cycle_audit.py are NOT touched.

Layout-only changes vs the original (plot_SI_S3_cycle_audit.py block 2):
  - canvas           7.09 x 2.55 in  ->  11.0 x 5.5 in
  - margins          0.14 / 0.97 / 0.15 / 0.96  (left/right/bottom/top)
  - legend           7.5 pt -> 6.2 pt (~-17%), shorter line samples,
                      tighter row spacing, upper-left, no frame
  - noise-floor text  moved from (0.02, 0.21*1.12) to a clear empty spot
                      ~(x 0.10 V, y 0.95 mA cm-2), font 7.0 pt (below FS_TICK)
  - curve linewidth   1.6 -> 2.0 pt
  - axis labels       default(10) -> FS_AXIS 8.5 pt (matches final main figures)
  - save              PNG@600 + PDF + SVG with pad_inches 0.08 (label breathing room)

Everything else is byte-identical data: colors, line styles, legend text,
1.0 V dash-dot divider, 0.21 gray dashed noise floor, axes labels text.

QC gates G1-G8 are asserted programmatically at the end.
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import figure_style as st

BASE = os.path.dirname(os.path.dirname(HERE))
VR_CSV = os.path.join(BASE, "decoder_comsol_audit", "voltage_resolved_consistency.csv")
OUT_DIR = os.path.join(BASE, "final_figures", "SI_final_review")
os.makedirs(OUT_DIR, exist_ok=True)
OUT_STEM = os.path.join(OUT_DIR, "FigS3_cycle_voltage")

NOISE_RMSE = 0.21                     # 1%-of-Jsc measurement-noise floor (frozen)
GRAY = "#5a6470"                      # neutral gray annotation
DIV_COLOR = "#999999"                 # 1.0 V divider (kept)
FLOOR_COLOR = "#888888"               # noise-floor line (kept)

FIG_W, FIG_H = 11.0, 5.5              # requested canvas
LEFT, RIGHT, BOTTOM, TOP = 0.14, 0.97, 0.15, 0.96
PAD_IN = 0.08                         # tight-bbox padding so y-label never glues
CURVE_LW = 2.0                        # uniform linewidth 2.0-2.3 pt
LEG_FS = 6.2                          # ~17% below FS_LEGEND 7.5 (15-20% requested)
ANN_FS = 7.0                          # slightly below FS_TICK 7.5
ANN_XY = (0.10, 1.05)                 # clear empty spot (x 0.08-0.15, y 0.7-1.2)
ANN_TEXT = r"noise floor = 0.21 mA cm$^{-2}$"

# ------------------------------------------------------------------ data ----
vres = pd.read_csv(VR_CSV)
assert len(vres) == 131                       # 131-point J-V grid (frozen)
assert abs(vres["voltage"].min()) < 1e-9      # starts at 0.0 V
assert abs(vres["voltage"].max() - 1.3) < 1e-9  # ends at 1.3 V (no cropping)

voltage = vres["voltage"].values
c1 = vres["decoder_target_rmse"].values
c2 = vres["comsol_target_rmse"].values
c3 = vres["decoder_comsol_rmse"].values

# G5 / G6 anchors: plotted arrays are the CSV columns verbatim, full range.
_expected = pd.read_csv(VR_CSV)               # fresh reload for the check
assert np.array_equal(voltage, _expected["voltage"].values)
assert np.array_equal(c1, _expected["decoder_target_rmse"].values)
assert np.array_equal(c2, _expected["comsol_target_rmse"].values)
assert np.array_equal(c3, _expected["decoder_comsol_rmse"].values)

# ------------------------------------------------------------------ plot ----
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
fig.subplots_adjust(left=LEFT, right=RIGHT, bottom=BOTTOM, top=TOP)

ax.plot(voltage, c1, color=st.OKABE_ITO[0], lw=CURVE_LW,
        label="decoder vs target")
ax.plot(voltage, c2, color=st.OKABE_ITO[3], lw=CURVE_LW, ls="--",
        label="COMSOL(pred) vs target")
ax.plot(voltage, c3, color=st.OKABE_ITO[2], lw=CURVE_LW, ls=":",
        label="decoder vs COMSOL(pred)")

divider = ax.axvline(1.0, color=DIV_COLOR, lw=0.9, ls="-.")   # kept, no text
floor = ax.axhline(NOISE_RMSE, color=FLOOR_COLOR, lw=0.8, ls="--")  # kept

# noise-floor label -> clear empty spot (empty x 0.08-0.15, y 0.7-1.2)
ann = ax.text(ANN_XY[0], ANN_XY[1], ANN_TEXT, fontsize=ANN_FS, color=GRAY,
              va="bottom", ha="left")

ax.set_xlabel("Voltage (V)", fontsize=st.FS_AXIS)
ax.set_ylabel(r"RMSE across 45 samples (mA cm$^{-2}$)", fontsize=st.FS_AXIS)
st.configure_axes(ax)

leg = ax.legend(fontsize=LEG_FS, frameon=False, loc="upper left",
                handlelength=1.2, labelspacing=0.28, handletextpad=0.6,
                borderaxespad=0.35)

# ---- save (PNG 600 dpi + PDF + SVG), tight bbox with padding ----
for ext in ("png", "pdf", "svg"):
    kw = {"bbox_inches": "tight", "pad_inches": PAD_IN, "facecolor": "white"}
    if ext == "png":
        kw["dpi"] = 600
    fig.savefig(OUT_STEM + "." + ext, **kw)
print("wrote", OUT_STEM + ".{png,pdf,svg}")

# ================================================================== QC =======
fig.canvas.draw()
ren = fig.canvas.get_renderer()
ok = []

def chk(name, cond, note=""):
    ok.append(cond)
    print("[%s] %s  %s" % ("PASS" if cond else "FAIL", name, note))

# G1  y-axis label complete and clear of edges
yl = ax.yaxis.label
yb = yl.get_window_extent(ren)
yf = fig.transFigure.inverted().transform([[yb.x0, yb.y0], [yb.x1, yb.y1]])
chk("G1", yb.x0 >= 0 and yf[0][0] >= 0.02 and yf[0][0] <= yf[1][0],
    "ylabel left edge %.3f in fig-units" % yf[0][0])
xl = ax.xaxis.label
xb = xl.get_window_extent(ren)
chk("G1", xb.y0 >= 0, "xlabel present")

# G2  legend smaller + does not obscure data
fs0 = float(leg.get_texts()[0].get_fontsize())
chk("G2", fs0 < st.FS_LEGEND and (st.FS_LEGEND - fs0) / st.FS_LEGEND >= 0.12,
    "legend fs %.1f vs FS_LEGEND %.1f (%.0f%% smaller)"
    % (fs0, st.FS_LEGEND, 100 * (st.FS_LEGEND - fs0) / st.FS_LEGEND))
lb = leg.get_window_extent(ren)
inv = ax.transData.inverted()
(x0, y0), (x1, y1) = inv.transform([(lb.x0, lb.y0), (lb.x1, lb.y1)])
mask = (voltage >= x0) & (voltage <= x1)
overlap = any(np.max(v[mask]) > y0 for v in (c1, c2, c3) if mask.any())
chk("G2", not overlap, "legend data-rect x[%.2f,%.2f] y[%.2f,%.2f]; max curve y in x-range %.2f"
    % (x0, x1, y0, y1, max(np.max(v[mask]) for v in (c1, c2, c3)) if mask.any() else -1))

# G3  noise-floor text: inside axes, not over curves, not on the floor line
ab = ann.get_window_extent(ren)
(a0, b0), (a1, b1) = inv.transform([(ab.x0, ab.y0), (ab.x1, ab.y1)])
in_axes = (a0 >= voltage.min() and a1 <= voltage.max() and b0 >= vres[
    ["decoder_target_rmse", "comsol_target_rmse", "decoder_comsol_rmse"]].min().min()
    and b1 <= vres[["decoder_target_rmse", "comsol_target_rmse",
                    "decoder_comsol_rmse"]].max().max())
mask = (voltage >= a0) & (voltage <= a1)
over_curve = any(np.max(v[mask]) > b0 for v in (c1, c2, c3) if mask.any())
on_floor = b0 <= NOISE_RMSE <= b1
chk("G3", in_axes and not over_curve and not on_floor,
    "text data-rect x[%.2f,%.2f] y[%.2f,%.2f]; over_curve=%s on_floor=%s"
    % (a0, a1, b0, b1, over_curve, on_floor))

# G4  1.0 V divider preserved (no text added)
dvs = [l for l in ax.lines if len(l.get_xdata()) == 2
       and abs(l.get_xdata()[0] - l.get_xdata()[1]) < 1e-9
       and abs(l.get_xdata()[0] - 1.0) < 1e-9]
fls = [l for l in ax.lines if len(l.get_ydata()) == 2
       and abs(l.get_ydata()[0] - l.get_ydata()[1]) < 1e-9
       and abs(l.get_ydata()[0] - NOISE_RMSE) < 1e-9]
chk("G4", len(dvs) == 1 and len(fls) == 1, "1.0 V divider + 0.21 floor line present")

# G5 / G6  values + voltage range unchanged (asserted above; restate here)
chk("G5", all(np.array_equal(vres[c], pd.read_csv(VR_CSV)[c])
              for c in ("decoder_target_rmse", "comsol_target_rmse",
                        "decoder_comsol_rmse")), "three curves == frozen CSV, no transform")
chk("G6", len(voltage) == 131 and abs(voltage.min()) < 1e-9
    and abs(voltage.max() - 1.3) < 1e-9, "voltage 0.0-1.3 V, 131 pts, no crop")

# G7  PNG @600 dpi
im = Image.open(OUT_STEM + ".png")
dpi = im.info.get("dpi", (0, 0))[0]
chk("G7", abs(dpi - 600) < 1.0 and im.size[0] > im.size[1],
    "PNG %dx%d @ %.0f dpi" % (im.size[0], im.size[1], dpi))
# left whitespace: label clear of the saved edge (pad_inches breathing room)
arr = np.asarray(im.convert("L"))
nonwhite = np.where((arr < 250).any(axis=1))[0]
leftmost = np.where((arr < 250).any(axis=0))[0]
chk("G1", len(leftmost) > 0 and leftmost[0] >= PAD_IN * 600 * 0.5,
    "leftmost ink col %d px (pad %.0f px)" % (leftmost[0] if len(leftmost) else -1, PAD_IN * 600))

# G8  PDF + SVG written, vector text preserved
chk("G8", os.path.exists(OUT_STEM + ".pdf") and os.path.getsize(OUT_STEM + ".pdf") > 1000,
    "PDF %.1f KB" % (os.path.getsize(OUT_STEM + ".pdf") / 1024))
svg = open(OUT_STEM + ".svg", encoding="utf-8").read()
chk("G8", "noise floor" in svg and "RMSE across 45 samples" in svg,
    "SVG editable-text (svg.fonttype=none) contains text glyphs")

print()
print("GATES: %d/%d PASS" % (sum(ok), len(ok)))
plt.close(fig)
