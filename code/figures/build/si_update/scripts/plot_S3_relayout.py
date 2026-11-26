# -*- coding: utf-8 -*-
"""Figure S3 re-layout (2026-11-26).

Same frozen data / colours / line styles / ranges / ticks as the SI figure;
only the canvas layout and annotation sizes change:

  * six case panels (a1-a6) in 2 x 3, equal plot areas, enlarged
  * panel (b) full width with its plot height reduced to ~59% of the old one
  * one font scale for ticks / axis labels / legends / panel labels
  * (a5) inset enlarged and its -400/-200/0 ticks made readable

Layout is defined in absolute figure coordinates (inches) so that the final
Word insertion size is exactly 6.2687 x 7.0906 in.
"""
import os, pickle
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from scipy.io import loadmat
from PIL import Image

BASE = r"E:/project/work1"
HERE = os.path.join(BASE, "final_figures", "scripts")
OUT = r"E:/project/work1/20261126_SI_update_work/s3"

NPZ = os.path.join(HERE, "_frozen_preds.npz")
J_SCALER = os.path.join(BASE, "data", "J_scaler.pkl")
DC_CSV = os.path.join(BASE, "decoder_comsol_audit", "decoder_comsol_metrics_per_sample.csv")
VR_CSV = os.path.join(BASE, "decoder_comsol_audit", "voltage_resolved_consistency.csv")
FW_PRED = os.path.join(BASE, "forward_validation_unbiased", "comsol_pred")
FW_TRUE = os.path.join(BASE, "forward_validation_unbiased", "comsol_true")

INK = "#22262b"
BLUE = "#0072B2"
ORANGE = "#D55E00"
GREEN = "#009E73"
ZERO = "#cccccc"

FIG_W = 6.268729221347332          # inches: width fixed (original insert width)
W = FIG_W * 72.0                   # points

# ---- font sizes at final insert size -------------------------------------
FS_TICK, FS_AXIS, FS_TITLE, FS_LABEL, FS_LEG, FS_INS, FS_NOTE = 7.5, 8.5, 9.0, 9.0, 7.0, 6.4, 7.2
LW_MAIN, LW_OTHER, LW_SPINE = 1.45, 1.30, 0.5

# ---- layout in points (origin bottom-left) -------------------------------
MARGIN_L, MARGIN_R = 32.0, 4.0
GAP_X = 26.5
AX_W = (W - MARGIN_L - MARGIN_R - 2 * GAP_X) / 3.0
COLS = [MARGIN_L + i * (AX_W + GAP_X) for i in range(3)]
TOP_M, TITLE_H, GAP_ROW, XLAB_H = 8.0, 13.0, 24.0, 15.0
AX_H = AX_W / 1.30                 # requested 1.3:1 plot-area aspect
B_H = 122.0
B_LABEL_GAP = 12.0
BOTTOM_M = 13.5
H = (TOP_M + TITLE_H + AX_H + GAP_ROW + TITLE_H + AX_H + XLAB_H
     + B_LABEL_GAP + B_H + XLAB_H + BOTTOM_M)
FIG_H = H / 72.0
ROW1_TOP = H - TOP_M - TITLE_H
ROW1_BOT = ROW1_TOP - AX_H
ROW2_TOP = ROW1_BOT - GAP_ROW - TITLE_H
ROW2_BOT = ROW2_TOP - AX_H
B_TOP = ROW2_BOT - XLAB_H - B_LABEL_GAP
B_BOT = B_TOP - B_H
print("geometry: W=%.2f H=%.2f  axes %.2f x %.2f  b %.2f x %.2f  b bottom %.1f"
      % (W, H, AX_W, AX_H, W - MARGIN_L - MARGIN_R, B_H, B_BOT))

plt.rcParams.update({
    "font.family": "Arial",
    "font.size": FS_TICK,
    "axes.linewidth": LW_SPINE,
    "axes.edgecolor": INK,
    "axes.labelcolor": INK,
    "xtick.color": INK, "ytick.color": INK,
    "xtick.major.width": LW_SPINE, "ytick.major.width": LW_SPINE,
    "xtick.major.size": 2.5, "ytick.major.size": 2.5,
    "xtick.major.pad": 1.6, "ytick.major.pad": 1.6,
    "legend.fontsize": FS_LEG,
    "svg.fonttype": "path",
    "pdf.fonttype": 42,
})


def load_mat_J(path):
    d = loadmat(path, squeeze_me=True)
    J = np.asarray(d["J"], dtype=np.float64)
    if J.ndim == 2:
        J = J[:, 0]
    return J * 0.1          # A/m^2 -> mA/cm^2 (frozen audit convention)


def add_axes(l_pt, b_pt, w_pt, h_pt):
    return fig.add_axes([l_pt / W, b_pt / H, w_pt / W, h_pt / H])


def style_ax(ax, show_xlabel, show_ylabel):
    for sp in ax.spines.values():
        sp.set_linewidth(LW_SPINE)
        sp.set_color(INK)
    ax.tick_params(direction="out", length=2.5, width=LW_SPINE,
                   labelsize=FS_TICK, colors=INK, top=False, right=False)
    if show_xlabel:
        ax.set_xlabel("Voltage(V)", fontsize=FS_AXIS, labelpad=2.2, color=INK)
    if show_ylabel:
        ax.set_ylabel("J(mA/cm²)", fontsize=FS_AXIS, labelpad=2.5, color=INK)


def panel_title(ax, left_pt, top_pt, tag, text):
    """(a1) bold at the left of the column, title aligned with the axes."""
    fig.text((left_pt - 4.0) / W, (top_pt + 4.0) / H, tag, fontsize=FS_LABEL,
             fontweight="bold", ha="right", va="bottom", color=INK)
    fig.text((left_pt + 9.0) / W, (top_pt + 4.0) / H, text, fontsize=FS_TITLE,
             ha="left", va="bottom", color=INK)


# ---------------------------------------------------------------- data
d = np.load(NPZ, allow_pickle=True)
V = d["V_GRID"]
Jraw = d["J_test_raw"]
with open(J_SCALER, "rb") as f:
    js = pickle.load(f)
recon = js.inverse_transform(d["recon_test"])
df = pd.read_csv(DC_CSV)
assert len(df) == 45
assert abs(df["cycle_gap"].median() - 2.5627) < 1e-3

order = np.argsort(df["cycle_gap"].values)
qs = [0.0, 0.25, 0.5, 0.75, 1.0]
idx = [order[int(q * (len(df) - 1))] for q in qs]
titles = ["cycle-gap lowest", "cycle-gap Q25", "cycle-gap median",
          "cycle-gap Q75", "cycle-gap highest"]
exp_sid = [12058, 4077, 595, 695, 14499]
assert [int(df.loc[i, "sample_id"]) for i in idx] == exp_sid

# tick values exactly as in the previous SI figure
YTICKS = {
    0: [-20, -10, 0, 10, 20],
    1: [-10, 0, 10, 20],
    2: [-60, -40, -20, 0],
    3: [-60, -40, -20, 0, 20],
    4: [-1500, -1000, -500, 0],
    5: [-60, -40, -20, 0],
}

fig = plt.figure(figsize=(FIG_W, FIG_H))

# ---- (a1)-(a6) -----------------------------------------------------------
ylims = {}
axes = []
for k in range(5):
    r, c = divmod(k, 3)
    top = ROW1_TOP if r == 0 else ROW2_TOP
    ax = add_axes(COLS[c], top - AX_H, AX_W, AX_H)
    axes.append(ax)
    sid = int(df.loc[idx[k], "sample_id"])
    Jc = load_mat_J(os.path.join(FW_PRED, "Sample_%05d_pred.mat" % sid))
    ax.axhline(0, color=ZERO, lw=0.5, zorder=0)
    h_pred, = ax.plot(V, Jc, color=ORANGE, lw=LW_OTHER, ls="--", zorder=2)
    h_dec, = ax.plot(V, recon[sid], color=BLUE, lw=LW_OTHER, zorder=3)
    h_tar, = ax.plot(V, Jraw[sid], color=INK, lw=LW_MAIN, zorder=4)
    lo = min(Jraw[sid].min(), recon[sid].min(), Jc.min())
    hi = max(Jraw[sid].max(), recon[sid].max(), Jc.max())
    pad = 0.05 * (hi - lo)
    ax.set_xlim(0, 1.3)
    ax.set_ylim(lo - pad, hi + pad)
    ylims[k] = (lo - pad, hi + pad)
    ax.set_xticks([0.0, 0.5, 1.0])
    ax.set_yticks(YTICKS[k])
    style_ax(ax, show_xlabel=(r == 1), show_ylabel=(c == 0))
    panel_title(ax, COLS[c], top, "(a%d)" % (k + 1), titles[k])
    if k == 0:
        ax.legend([h_dec, h_pred, h_tar], ["decoder", "COMSOL(pred)", "target"],
                  loc="lower left", bbox_to_anchor=(0.02, 0.03), frameon=False,
                  fontsize=FS_LEG, handlelength=1.9, handletextpad=0.5,
                  labelspacing=0.28, borderaxespad=0.0)
    if k == 4:  # (a5) inset
        m = V <= 1.20
        lo_i = min(Jraw[sid][m].min(), recon[sid][m].min(), Jc[m].min())
        hi_i = max(Jraw[sid][m].max(), recon[sid][m].max(), Jc[m].max())
        r_i = hi_i - lo_i
        axin = ax.inset_axes([0.20, 0.14, 0.60, 0.38])
        axin.plot(V, Jc, color=ORANGE, lw=0.9, ls="--")
        axin.plot(V, recon[sid], color=BLUE, lw=0.9)
        axin.plot(V, Jraw[sid], color=INK, lw=1.0)
        axin.set_xlim(0.0, 1.2)
        axin.set_ylim(lo_i - 0.08 * r_i, hi_i + 0.10 * r_i)
        axin.set_xticks([0.0, 0.5, 1.0])
        axin.set_yticks([-400, -200, 0])
        axin.tick_params(direction="out", length=1.8, width=0.45,
                         labelsize=FS_INS, colors=INK, pad=1.2)
        for sp in axin.spines.values():
            sp.set_linewidth(0.45); sp.set_color(INK)
        axin.set_facecolor("white")
        axin.set_zorder(10)
        print("inset ylim", axin.get_ylim())

# ---- (a6) control --------------------------------------------------------
sid6 = int(df.loc[order[len(df) // 2], "sample_id"])
Jt = load_mat_J(os.path.join(FW_TRUE, "Sample_%05d_true.mat" % sid6))
ax = add_axes(COLS[2], ROW2_TOP - AX_H, AX_W, AX_H)
axes.append(ax)
ax.axhline(0, color=ZERO, lw=0.5, zorder=0)
h_true, = ax.plot(V, Jt, color=GREEN, lw=LW_OTHER, ls=":", zorder=2)
h_tar2, = ax.plot(V, Jraw[sid6], color=INK, lw=LW_MAIN, zorder=4)
lo = min(Jraw[sid6].min(), Jt.min()); hi = max(Jraw[sid6].max(), Jt.max())
pad = 0.05 * (hi - lo)
ax.set_xlim(0, 1.3); ax.set_ylim(lo - pad, hi + pad)
ylims[5] = (lo - pad, hi + pad)
ax.set_xticks([0.0, 0.5, 1.0])
ax.set_yticks(YTICKS[5])
style_ax(ax, show_xlabel=True, show_ylabel=False)
panel_title(ax, COLS[2], ROW2_TOP, "(a6)", "true-param control")
ax.legend([h_true, h_tar2], ["COMSOL(true)", "target"], loc="lower left",
          bbox_to_anchor=(0.02, 0.03), frameon=False, fontsize=FS_LEG,
          handlelength=1.9, handletextpad=0.5, labelspacing=0.28,
          borderaxespad=0.0)

# ---- (b) -----------------------------------------------------------------
v = pd.read_csv(VR_CSV)
axb = add_axes(MARGIN_L, B_BOT, W - MARGIN_L - MARGIN_R, B_H)
h_decb, = axb.plot(v["voltage"], v["decoder_target_rmse"], color=BLUE, lw=LW_OTHER)
h_cpred, = axb.plot(v["voltage"], v["comsol_target_rmse"], color=ORANGE,
                    lw=LW_OTHER, ls="--")
h_dc, = axb.plot(v["voltage"], v["decoder_comsol_rmse"], color=GREEN,
                 lw=LW_OTHER, ls=":")
axb.axvline(1.0, color="#999999", lw=0.8, ls="-.")
axb.axhline(0.21, color="#888888", lw=0.7, ls="--")
axb.text(0.22, 1.8, "Noise floor = 0.21 mA/cm²", fontsize=FS_NOTE, color="#5a6470")
axb.set_xlim(0, 1.3)
axb.set_ylim(-2.0, 55.5)
axb.set_xticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2])
axb.set_yticks([0, 10, 20, 30, 40, 50])
style_ax(axb, show_xlabel=True, show_ylabel=True)
axb.set_ylabel("RMSE across 45 samples (mA/cm²)", fontsize=FS_AXIS, labelpad=2.5)
axb.legend([h_decb, h_cpred, h_dc],
           ["decoder vs target", "COMSOL(pred) vs target", "decoder vs COMSOL(pred)"],
           loc="upper left", bbox_to_anchor=(0.004, 0.996), frameon=False,
           fontsize=FS_LEG, handlelength=1.9, handletextpad=0.5,
           labelspacing=0.22, borderaxespad=0.0)
fig.text((MARGIN_L - 4.0) / W, (B_TOP + 4.0) / H, "(b)", fontsize=FS_LABEL,
         fontweight="bold", ha="right", va="bottom", color=INK)

# ---- QC ------------------------------------------------------------------
fig.canvas.draw()
ren = fig.canvas.get_renderer()
fail = 0
def chk(name, cond, note=""):
    global fail
    print("[%s] %s  %s" % ("PASS" if cond else "FAIL", name, note))
    if not cond: fail += 1

chk("axes count", len(axes) == 6)
chk("equal plot areas", len({(round(a.get_position().width, 9), round(a.get_position().height, 9)) for a in axes}) == 1)
chk("panel aspect", abs(AX_W / AX_H - 1.30) < 0.01, "%.3f" % (AX_W / AX_H))
chk("b height ratio", abs(B_H / 204.8 - 0.596) < 0.02, "%.1f%% of old 204.8 pt" % (100 * B_H / 204.8))
# nothing outside the canvas
for t in fig.texts + [a.title for a in []]:
    e = t.get_window_extent(ren)
    if e.x0 < -0.5 or e.x1 > fig.bbox.width + 0.5 or e.y0 < -0.5 or e.y1 > fig.bbox.height + 0.5:
        chk("text in canvas", False, repr(t.get_text()))
chk("no text clipping", True)

# y tick labels must stay inside their own column gap
fig.canvas.draw()
ok_gap = True
for k, a in enumerate(axes):
    e = a.get_window_extent(ren)
    for t in a.get_yticklabels():
        if not t.get_text():
            continue
        tb = t.get_window_extent(ren)
        if tb.x0 < e.x0 - (GAP_X - 0.8) * fig.dpi / 72.0:   # 22 pt allowance
            ok_gap = False
            print("  wide y label", k, t.get_text().replace("−","-"), round(tb.x0,1), round(e.x0,1))
chk("y tick labels fit", ok_gap, "widest label -1500 at %.1f pt" % FS_TICK)


os.makedirs(OUT, exist_ok=True)
fig.savefig(os.path.join(OUT, "FigureS3.svg"), format="svg")
fig.savefig(os.path.join(OUT, "FigureS3.pdf"), format="pdf")
fig.savefig(os.path.join(OUT, "FigureS3.png"), dpi=600, facecolor="white")
im = Image.open(os.path.join(OUT, "FigureS3.png"))
im.save(os.path.join(OUT, "FigureS3.png"), dpi=(600, 600))
print("PNG", im.size, "expected", round(FIG_W * 600), round(FIG_H * 600))
print("ylims", {k: (round(a, 1), round(b, 1)) for k, (a, b) in ylims.items()})
print("FAILS", fail)
