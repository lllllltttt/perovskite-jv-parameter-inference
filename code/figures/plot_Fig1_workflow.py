"""
plot_Fig1_workflow.py — Fig. 1 of the FINAL figure package.
============================================================
Simulation-informed inversion workflow (4 panels), frozen content only:

  (a) Device physics: 1D drift–diffusion perovskite solar cell (COMSOL),
      inverted p-i-n stack FTO / NiOx / Perovskite / C60 / Ag. The nine
      inversion parameters are listed; bulk pairs (mu_n/mu_p, tau_n/tau_p,
      Nc/Nv) come from average-and-ratio latent construction, interface
      lifetimes tau_ETL / tau_HTL are pinned to their physical interfaces,
      and rad_c (r_rad) is a bulk radiative-recombination coefficient.
  (b) Physics-based database: Latin-hypercube sampling of the 9 latent
      variables -> COMSOL drift–diffusion forward model -> synthetic J-V
      ensemble (real COMSOL curve shapes).
  (c) Dataset construction: 200,000 simulated -> 102,046 retained (51.0%)
      by the frozen filter (finite J; J(V=0)>0; DeltaJ <= 0.2 mA/cm2;
      >=1 downward zero crossing) -> split 71,432 / 15,307 / 15,307
      (Train / Val / Test, seed 42).
  (d) Inverse workflow: normalized 131-point J-V -> Encoder (131->128->64)
      -> 9-D latent -> Gaussian ParamHead (9->64->32) -> 9 means + 9
      predictive scales sigma = clip(softplus+0.01, 0.01, 1.0). The decoder
      branch (9->64->128->131) reconstructs the J-V curve and is visually
      distinguished (outlined / hatched), consistent with the paper's
      statement that the decoder is NOT part of the parameter-prediction path.

Data source: real COMSOL curves from 9D-HTL-new/mat/Sample_*.mat (the same
local samples used by the project's own schematic). All numbers are frozen
manuscript values. No new analysis.

Outputs (journal width + large-review variant, PNG 600 dpi + PDF + SVG):
  final_figures/Fig1/Fig1_workflow.png / .pdf / .svg
  final_figures/Fig1/Fig1_workflow_large.png / .pdf / .svg
"""

import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle, FancyBboxPatch
from scipy.io import loadmat

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import figure_style as st

BASE = os.path.dirname(os.path.dirname(HERE))   # E:\project\work1
MATDIR = os.path.join(BASE, "9D-HTL-new", "mat")
OUT_DIR = os.path.join(BASE, "final_figures", "Fig1")
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------------------------------------------- palette --
INK = "#22262b"
GRAY = "#5a6470"
AXES = "#9aa1ad"
PHYS = "#4c6b8f"     # device / COMSOL blue
VAE = "#3f6f63"      # PI-VAE dark teal
VAE_BG = "#e9f1ee"
VAE_BRD = "#2e5c51"
DEC = "#b06a4a"      # decoder branch (distinguished, warm)
DEC_BG = "#f6ede6"
UNC = "#c07f45"      # uncertainty warm orange
PVK = "#e7cf96"; PVK_ED = "#b99a54"
ETL_C = "#8fb0c9"; HTL_C = "#9db9aa"
SUB_C = "#dde1e7"; EL_C = "#c6cbd3"
CHIP_B = "#eef3f8"; PAR_B = "#f4f6f8"


# ------------------------------------------------------------------ helpers
def arrow(ax, p0, p1, color=INK, lw=1.0, ms=9, ls="-", rad=0.0, shrinkA=0, shrinkB=0):
    ax.add_patch(FancyArrowPatch(
        p0, p1, arrowstyle="-|>", mutation_scale=ms, color=color, lw=lw,
        linestyle=ls, shrinkA=shrinkA, shrinkB=shrinkB,
        connectionstyle=f"arc3,rad={rad}", zorder=3))


def chip(ax, cx, cy, w, h, text, fs, tcy, tc, sub="", sfs=6.5, scy=None,
         fc=CHIP_B, ec=PHYS, lw=1.0):
    ax.add_patch(FancyBboxPatch(
        (cx - w / 2, cy - h / 2), w, h,
        boxstyle="round,pad=0.004,rounding_size=0.020",
        fc=fc, ec=ec, lw=lw, zorder=2))
    ax.text(cx, cy + h * (tcy - 0.5), text, ha="center", va="center",
            fontsize=fs, color=tc, fontweight="bold", zorder=4)
    if sub:
        ax.text(cx, cy + h * (scy - 0.5), sub, ha="center", va="center",
                fontsize=sfs, color=GRAY, zorder=4)


def mini(ax, x, y, w, h, xlim=(0, 1.3), ylim=(-0.30, 1.08)):
    ins = ax.inset_axes([x, y, w, h])
    ins.set_xlim(*xlim); ins.set_ylim(*ylim)
    ins.set_facecolor("white")
    for s in ("top", "right"):
        ins.spines[s].set_visible(False)
    for s in ("bottom", "left"):
        ins.spines[s].set_color(AXES); ins.spines[s].set_linewidth(0.5)
    ins.tick_params(length=0, width=0, labelbottom=False, labelleft=False)
    ins.axhline(0, color=AXES, lw=0.5, ls=(0, (2, 2)), alpha=0.6, zorder=1)
    return ins


def panel_tag(ax, x, y, tag, desc):
    ax.text(x, y, tag, fontsize=st.FS_PANEL, fontweight="bold", color=INK,
            va="baseline", zorder=5)
    ax.text(x + 0.042, y, desc, fontsize=st.FS_ANNOT, color=GRAY,
            va="baseline", zorder=5)


# ------------------------------------------------------------------ J-V data
V_REAL = np.linspace(0.0, 1.3, 131)
REAL = {}
for _n in ["00809", "00819", "01356", "06915", "07909"]:
    _d = loadmat(os.path.join(MATDIR, f"Sample_{_n}.mat"))
    _J = np.squeeze(_d["J"]) * 0.1
    REAL[_n] = _J / _J[0]


def curve_disp(name, voc_target, jend=-0.20):
    """Real-data-shaped normalized J-V with Voc placed at voc_target (PCHIP
    continuation beyond the real window; see the project's v7 schematic)."""
    V = np.linspace(0, 1.3, 200)
    Jn = REAL[name]
    vnat = None
    for i in range(len(V_REAL) - 1):
        if Jn[i] >= 0 > Jn[i + 1]:
            vnat = V_REAL[i] + (V_REAL[i + 1] - V_REAL[i]) * Jn[i] / (Jn[i] - Jn[i + 1])
            break
    if vnat is None:
        m = (Jn[-1] - Jn[-2]) / (V_REAL[-1] - V_REAL[-2])
        vnat = V_REAL[-1] + Jn[-1] / (-m) if m < 0 else 1.3
    s = vnat / voc_target
    Jd = np.interp(np.clip(V * s, 0, 1.3), V_REAL, Jn)
    V_end = min(voc_target, 1.3 / s)
    J_end = float(np.interp(min(V_end * s, 1.3), V_REAL, Jn))
    out = Jd.copy()
    m = V > V_end
    if np.any(m):
        if V_end < voc_target - 1e-9:
            px = [V_end, voc_target, 1.3]; py = [J_end, 0.0, jend]
            from scipy.interpolate import PchipInterpolator
            out[m] = PchipInterpolator(px, py)(V[m])
        else:
            px = [voc_target, 1.3]; py = [0.0, jend]
            from scipy.interpolate import PchipInterpolator
            out[m] = PchipInterpolator(px, py)(V[m])
    return V, out


def draw_fig(fig, ax):
    V = np.linspace(0, 1.3, 200)

    # ============================= (a) device physics =======================
    panel_tag(ax, 0.002, 0.955, "(a)", "device physics")
    X0, X1 = 0.014, 0.052
    layers = [
        (0.12, 0.20, SUB_C, "FTO", 6.5),
        (0.20, 0.31, HTL_C, "NiO$_x$", 6.5),
        (0.31, 0.66, PVK,   "Perovskite", 6.5),
        (0.66, 0.76, ETL_C, "C60", 6.5),
        (0.76, 0.86, EL_C,  "Ag", 6.5),
    ]
    for y0, y1, fc, name, fs in layers:
        ax.add_patch(Rectangle((X0, y0), X1 - X0, y1 - y0, fc=fc,
                               ec=PVK_ED if name == "Perovskite" else "#6d7480",
                               lw=1.1 if name == "Perovskite" else 0.6, zorder=2))
        ax.text((X0 + X1) / 2, (y0 + y1) / 2, name, fontsize=fs, color=INK,
                ha="center", va="center",
                fontweight="bold" if name == "Perovskite" else "normal", zorder=4)

    # interface lifetimes pinned to their interfaces (left of stack)
    ax.text(0.011, 0.31, r"$\tau_{\mathrm{HTL}}$", fontsize=st.FS_ANNOT,
            color=INK, ha="right", va="center", zorder=4)
    ax.text(0.011, 0.66, r"$\tau_{\mathrm{ETL}}$", fontsize=st.FS_ANNOT,
            color=INK, ha="right", va="center", zorder=4)
    ax.plot([0.0125, 0.014], [0.31, 0.31], color=GRAY, lw=0.6, zorder=3)
    ax.plot([0.0125, 0.014], [0.66, 0.66], color=GRAY, lw=0.6, zorder=3)

    # parameter box (right of stack)
    PB_L, PB_W = 0.062, 0.075
    ax.add_patch(FancyBboxPatch((PB_L, 0.30), PB_W, 0.44,
                                boxstyle="round,pad=0.004,rounding_size=0.012",
                                fc=PAR_B, ec=AXES, lw=0.5, zorder=1))
    PCX = PB_L + PB_W / 2
    ax.text(PCX, 0.715, "inversion parameters", fontsize=st.FS_CAPTION_TXT,
            color=GRAY, ha="center", va="center", zorder=4)
    rows = [
        (0.655, r"$\mu_n$", r"$\mu_p$"),
        (0.600, r"$\tau_n$", r"$\tau_p$"),
        (0.545, r"$N_c$", r"$N_v$"),
        (0.490, r"$r_{\mathrm{rad}}$", ""),
        (0.435, r"$\tau_{\mathrm{ETL}}$", ""),
        (0.380, r"$\tau_{\mathrm{HTL}}$", ""),
    ]
    for y, l1, l2 in rows:
        ax.text(PCX - 0.018, y, l1, fontsize=st.FS_ANNOT, color=INK, ha="center", va="center", zorder=4)
        if l2:
            ax.text(PCX + 0.018, y, l2, fontsize=st.FS_ANNOT, color=INK, ha="center", va="center", zorder=4)
    ax.text(PCX, 0.335, "bulk (paired) / interface", fontsize=st.FS_CAPTION_TXT,
            color=GRAY, ha="center", va="center", zorder=4)
    ax.plot([X1, PB_L - 0.001], [0.55, 0.55], color=GRAY, lw=0.6, zorder=3)
    ax.text(PCX, 0.235, "1D drift–diffusion\ndevice model (COMSOL)", fontsize=st.FS_ANNOT,
            color=GRAY, ha="center", va="center", style="italic", zorder=4)

    # ========================= (b) physics-based database ===================
    panel_tag(ax, 0.268, 0.955, "(b)", "physics-based database")
    rng = np.random.default_rng(7)
    for _ in range(10):
        px = 0.288 + rng.uniform(-0.024, 0.024)
        py = 0.50 + rng.uniform(-0.032, 0.032)
        ax.plot(px, py, marker="o", ms=3.6, color=PHYS, alpha=0.8, ls="none", zorder=3)
    ax.text(0.288, 0.565, r"$\theta$", fontsize=st.FS_ANNOT, color=INK, ha="center",
            va="center", style="italic", zorder=4)
    ax.text(0.288, 0.432, "Latin hypercube\n200,000 draws", fontsize=st.FS_CAPTION_TXT,
            color=GRAY, ha="center", va="center", zorder=4)
    arrow(ax, (0.312, 0.50), (0.334, 0.50))

    chip(ax, 0.370, 0.50, 0.062, 0.13, "COMSOL", fs=st.FS_TITLE, tcy=0.62,
         tc=PHYS, sub="drift–diffusion", sfs=st.FS_CAPTION_TXT, scy=0.34,
         fc=CHIP_B, ec=PHYS, lw=0.9)
    arrow(ax, (0.406, 0.50), (0.428, 0.50))

    ins_b = mini(ax, 0.430, 0.415, 0.155, 0.17)
    ens = [("06915", 1.053), ("01356", 1.100), ("00819", 1.150), ("07909", 1.200)]
    for name, voc in ens:
        _V, _J = curve_disp(name, voc)
        ins_b.plot(_V, _J, color=PHYS, lw=0.8, alpha=0.6, zorder=1)
    ax.text(0.432, 0.590, "J", fontsize=st.FS_CAPTION_TXT, color=GRAY, ha="center", va="center", zorder=4)
    ax.text(0.588, 0.428, "V", fontsize=st.FS_CAPTION_TXT, color=GRAY, ha="center", va="center", zorder=4)
    ax.text(0.507, 0.392, "synthetic J–V ensemble", fontsize=st.FS_CAPTION_TXT,
            color=GRAY, ha="center", va="center", zorder=4)

    # average-and-ratio prior callout
    ax.text(0.345, 0.285, "average-and-ratio prior:\n"
            r"$(\mu_n,\mu_p)\; (\tau_n,\tau_p)\; (N_c,N_v)$ paired,",
            fontsize=st.FS_ANNOT, color=INK, ha="center", va="center", zorder=4,
            linespacing=1.4)
    ax.text(0.345, 0.222, r"$\tau_{\mathrm{ETL}},\ \tau_{\mathrm{HTL}},\ r_{\mathrm{rad}}$ direct",
            fontsize=st.FS_ANNOT, color=INK, ha="center", va="center", zorder=4)

    # ========================= (c) dataset construction =====================
    panel_tag(ax, 0.540, 0.955, "(c)", "dataset construction")

    # 200k box
    ax.add_patch(FancyBboxPatch((0.546, 0.44), 0.055, 0.13,
                                boxstyle="round,pad=0.004,rounding_size=0.015",
                                fc="#f4f2ec", ec=AXES, lw=0.7, zorder=2))
    ax.text(0.5735, 0.555, "200,000", fontsize=st.FS_TITLE, color=INK, ha="center", va="center", fontweight="bold", zorder=4)
    ax.text(0.5735, 0.505, "simulated", fontsize=st.FS_CAPTION_TXT, color=GRAY, ha="center", va="center", zorder=4)
    arrow(ax, (0.603, 0.50), (0.622, 0.50))

    # filter box
    ax.add_patch(FancyBboxPatch((0.624, 0.27), 0.075, 0.46,
                                boxstyle="round,pad=0.004,rounding_size=0.015",
                                fc="#fbf7f0", ec="#b08a5a", lw=0.8, zorder=2))
    ax.text(0.6615, 0.675, "filter", fontsize=st.FS_TITLE, color="#8a6438",
            ha="center", va="center", fontweight="bold", zorder=4)
    flt = ["J finite (131 pts)",
           r"$J(V{=}0)>0$",
           r"$\Delta J \leq 0.2$ mA cm$^{-2}$",
           "$≥$1 downward zero crossing"]
    for i, t in enumerate(flt):
        ax.text(0.633, 0.625 - i * 0.083, t, fontsize=st.FS_CAPTION_TXT, color=INK,
                ha="left", va="center", zorder=4)
    arrow(ax, (0.701, 0.50), (0.716, 0.50))

    # retained + split
    ax.add_patch(FancyBboxPatch((0.718, 0.44), 0.052, 0.13,
                                boxstyle="round,pad=0.004,rounding_size=0.015",
                                fc="#eef3f8", ec=PHYS, lw=0.8, zorder=2))
    ax.text(0.744, 0.555, "102,046", fontsize=st.FS_TITLE, color=PHYS, ha="center", va="center", fontweight="bold", zorder=4)
    ax.text(0.744, 0.505, "(51.0%)", fontsize=st.FS_CAPTION_TXT, color=GRAY, ha="center", va="center", zorder=4)
    arrow(ax, (0.772, 0.50), (0.791, 0.50), color=GRAY, lw=0.8)

    ax.add_patch(FancyBboxPatch((0.793, 0.40), 0.056, 0.20,
                                boxstyle="round,pad=0.004,rounding_size=0.012",
                                fc=PAR_B, ec=AXES, lw=0.7, zorder=2))
    ax.text(0.821, 0.585, "split (seed 42)", fontsize=st.FS_CAPTION_TXT, color=GRAY, ha="center", va="center", zorder=4)
    for i, (lbl, n) in enumerate([("train", "71,432"), ("val", "15,307"), ("test", "15,307")]):
        ax.text(0.821, 0.545 - i * 0.05, f"{lbl} {n}", fontsize=st.FS_CAPTION_TXT,
                color=INK, ha="center", va="center", zorder=4)

    # ========================= (d) inverse workflow =========================
    panel_tag(ax, 0.860, 0.955, "(d)", "inverse workflow")

    # input J-V
    ins_d0 = mini(ax, 0.862, 0.505, 0.052, 0.12)
    _V, _J = curve_disp("06915", 1.053)
    ins_d0.plot(_V, _J, color=INK, lw=1.2, zorder=2)
    ax.text(0.865, 0.63, "J", fontsize=st.FS_CAPTION_TXT, color=GRAY, ha="center", va="center", zorder=4)
    ax.text(0.915, 0.513, "V", fontsize=st.FS_CAPTION_TXT, color=GRAY, ha="center", va="center", zorder=4)
    ax.text(0.888, 0.478, "J–V input", fontsize=st.FS_CAPTION_TXT, color=GRAY, ha="center", va="center", zorder=4)
    arrow(ax, (0.920, 0.565), (0.938, 0.565))

    # encoder
    chip(ax, 0.950, 0.565, 0.030, 0.10, "Enc", fs=st.FS_ANNOT, tcy=0.55, tc=VAE_BRD,
         sub="131→128→64", sfs=st.FS_CAPTION_TXT, scy=0.32, fc=VAE_BG, ec=VAE_BRD, lw=0.9)
    arrow(ax, (0.965, 0.565), (0.983, 0.565))

    # latent
    ax.add_patch(FancyBboxPatch((0.985, 0.525), 0.014, 0.08,
                                boxstyle="round,pad=0.002,rounding_size=0.008",
                                fc="white", ec=VAE_BRD, lw=0.9, zorder=2))
    ax.text(0.992, 0.545, r"$z$", fontsize=st.FS_ANNOT, color=VAE_BRD, ha="center", va="center", zorder=4)
    ax.text(0.992, 0.512, "(9)", fontsize=st.FS_CAPTION_TXT, color=GRAY, ha="center", va="center", zorder=4)

    # decoder branch (upward, visually distinguished)
    arrow(ax, (0.992, 0.525), (0.992, 0.42), color=DEC, lw=1.0, ms=8)
    chip(ax, 0.992, 0.355, 0.030, 0.11, "Dec", fs=st.FS_ANNOT, tcy=0.55, tc=DEC,
         sub="9→64→128→131", sfs=st.FS_CAPTION_TXT, scy=0.32, fc=DEC_BG, ec=DEC, lw=1.1)
    arrow(ax, (0.992, 0.30), (0.992, 0.255), color=DEC, lw=1.0, ms=8)
    ins_d1 = mini(ax, 0.962, 0.145, 0.062, 0.105, ylim=(-0.20, 1.0))
    _V, _J = curve_disp("06915", 1.053)
    ins_d1.plot(_V, _J, color=DEC, ls="--", lw=1.1, zorder=2)
    ax.text(0.962, 0.253, "reconstruction", fontsize=st.FS_CAPTION_TXT, color=DEC, ha="center", va="center", zorder=4)
    ax.text(0.993, 0.113, "decoder branch", fontsize=st.FS_CAPTION_TXT, color=DEC, ha="center", va="center", zorder=4)

    # param head (right of latent)
    arrow(ax, (1.001, 0.565), (1.019, 0.565))
    chip(ax, 1.033, 0.565, 0.032, 0.115, "ParamHead", fs=st.FS_ANNOT, tcy=0.58, tc=UNC,
         sub="9→64→32", sfs=st.FS_CAPTION_TXT, scy=0.32, fc="#fdf3e8", ec=UNC, lw=0.9)
    arrow(ax, (1.050, 0.565), (1.066, 0.565))

    # output
    ax.add_patch(FancyBboxPatch((1.069, 0.40), 0.032, 0.30,
                                boxstyle="round,pad=0.004,rounding_size=0.012",
                                fc="#fff8ee", ec=UNC, lw=0.9, zorder=2))
    ax.text(1.085, 0.665, r"9 means", fontsize=st.FS_CAPTION_TXT, color=INK, ha="center", va="center", fontweight="bold", zorder=4)
    ax.text(1.085, 0.620, r"$\mu_\theta$", fontsize=st.FS_ANNOT, color=INK, ha="center", va="center", zorder=4)
    ax.text(1.085, 0.555, r"9 scales", fontsize=st.FS_CAPTION_TXT, color=INK, ha="center", va="center", fontweight="bold", zorder=4)
    ax.text(1.085, 0.510, r"$\sigma_\theta$", fontsize=st.FS_ANNOT, color=UNC, ha="center", va="center", zorder=4)
    ax.text(1.085, 0.462, r"$\sigma=\mathrm{clip}$", fontsize=st.FS_CAPTION_TXT,
            color=GRAY, ha="center", va="center", zorder=4)
    ax.text(1.085, 0.428, r"$(\mathrm{softplus}+0.01,$", fontsize=st.FS_CAPTION_TXT,
            color=GRAY, ha="center", va="center", zorder=4)
    ax.text(1.085, 0.405, r"$0.01,\,1)$", fontsize=st.FS_CAPTION_TXT,
            color=GRAY, ha="center", va="center", zorder=4)

    # legend for solid/dashed
    ax.plot([0.862, 0.878], [0.178, 0.178], color=INK, lw=1.0, zorder=3)
    ax.plot([0.862, 0.878], [0.156, 0.156], color=DEC, lw=1.0, ls="--", zorder=3)
    ax.text(0.950, 0.178, "input", fontsize=st.FS_CAPTION_TXT, color=GRAY, ha="left", va="center", zorder=4)
    ax.text(0.950, 0.156, "recon.", fontsize=st.FS_CAPTION_TXT, color=GRAY, ha="left", va="center", zorder=4)


def make_fig(size="journal"):
    w = st.set_fig_width(size)
    h = w * 0.42
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1.12)
    ax.set_ylim(0, 1)
    ax.axis("off")
    draw_fig(fig, ax)
    stem = os.path.join(OUT_DIR, "Fig1_workflow" + ("_large" if size == "large" else ""))
    st.save_fig(fig, stem)
    return stem


if __name__ == "__main__":
    s1 = make_fig("journal")
    s2 = make_fig("large")
    print("wrote:", s1, "and", s2)
