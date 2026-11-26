"""
figure_style.py — unified style config for the FINAL figure package.

Frozen content applies: figures only visualize frozen result files; no
model, no COMSOL, no new analysis. This module standardizes fonts, sizes,
palette, panel labels, spine/ticks, and save options across Fig1–Fig6 + SI.

Style rules (per FINAL_FIGURE_PRODUCTION spec):
  - Font: Arial (primary), DejaVu Sans fallback; Helvetica/Liberation Sans ok.
  - Panel labels (a)(b)... 9–11 pt, upper-left, bold.
  - Axis labels 8–9 pt; ticks 7–8 pt; legends 7–8 pt; min text 6.5 pt.
  - Outward ticks; no top/right heavy spines; no grid except light grid for
    calibration / parity panels.
  - PNG @600 dpi + PDF (vector). Optional SVG.
  - Two size variants per main figure: journal width + large-review.
  - Okabe-Ito colorblind-safe categorical palette.
  - Unified parameter notation: mu_n, mu_p, tau_n, tau_p, Nc, Nv, tau_ETL,
    tau_HTL, rad_c (with proper sub/superscripts where needed).
"""

import os
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib import rcParams

# ---------------------------------------------------------------- fonts ----
FONT_PRIMARY = "Arial"
FONT_FALLBACK = "DejaVu Sans"

rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": [FONT_PRIMARY, FONT_FALLBACK],
    "mathtext.fontset": "dejavusans",     # full Unicode sub/superscript support
    "pdf.fonttype": 42,                    # TrueType text in PDFs (editable)
    "ps.fonttype": 42,
    "svg.fonttype": "none",                # text as text in SVG
})

# ---------------------------------------------------------------- palette --
# Okabe-Ito (colorblind-safe) categorical palette.
OKABE_ITO = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#56B4E9",
             "#CC79A7", "#F0E442", "#000000", "#999999"]
PALETTE = OKABE_ITO

INK = "#1a1a1a"          # primary axis/text ink
MUTED = "#555555"        # secondary text / grid
GRID = "#cccccc"         # light grid lines

# ---------------------------------------------------------------- sizes ----
# Two size variants per main figure (identical content).
SIZES = {
    # Solar RRL full width ~180 mm
    "journal": {"fig_width": 7.09, "fig_height": None},   # height set per fig
    "large":   {"fig_width": 9.5,  "fig_height": None},   # large-review version
}

# font sizes (pt)
FS_PANEL = 10.5     # panel labels 9–11 pt
FS_TITLE = 9.0      # subpanel titles (rarely used; prefer axis labels)
FS_AXIS = 8.5       # axis labels 8–9 pt
FS_TICK = 7.5       # ticks 7–8 pt
FS_LEGEND = 7.5     # legends 7–8 pt
FS_ANNOT = 7.0      # in-panel annotations
FS_CAPTION_TXT = 7.0

MIN_FS = 6.5        # hard floor for any text

# ----------------------------------------------------------------- params --
# Canonical order: mu_n, mu_p, tau_n, tau_p, Nc, Nv, tau_ETL, tau_HTL, rad_c
PARAM_NAMES = [
    "mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk",
    "Nc_eff_pvk", "Nv_eff_pvk", "tau_ETL", "tau_HTL", "rad_c",
]
# unified, journal-ready labels (mathtext)
PARAM_LABELS = [
    r"$\mu_n$", r"$\mu_p$", r"$\tau_n$", r"$\tau_p$",
    r"$N_c$", r"$N_v$", r"$\tau_\mathrm{ETL}$",
    r"$\tau_\mathrm{HTL}$", r"$r_\mathrm{ad}$",
]
# plain-text short names (legends/annotations where mathtext is noisy)
PARAM_SHORT = [
    "mu_n", "mu_p", "tau_n", "tau_p", "Nc", "Nv",
    "tau_ETL", "tau_HTL", "rad_c",
]

# -------------------------------------------------------------- helpers ----
def configure_axes(ax, grid=False, grid_axis="both", grid_style=":"):
    """Outward ticks, light spines, optional light grid, small tick labels."""
    ax.tick_params(axis="both", which="major", direction="out",
                   length=3.0, width=0.8, labelsize=FS_TICK,
                   colors=INK, top=False, right=False)
    for spine in ax.spines.values():
        spine.set_color(INK)
        spine.set_linewidth(0.8)
    if grid:
        ax.grid(True, axis=grid_axis, linestyle=grid_style,
                color=GRID, linewidth=0.5, alpha=0.6)


def set_labels(ax, xlabel=None, ylabel=None, fontsize=FS_AXIS):
    if xlabel is not None:
        ax.set_xlabel(xlabel, fontsize=fontsize)
    if ylabel is not None:
        ax.set_ylabel(ylabel, fontsize=fontsize)
    for lab in ax.get_xticklabels() + ax.get_yticklabels():
        lab.set_fontsize(FS_TICK)


def panel_label(ax, tag, fontsize=FS_PANEL, dx=-0.05, dy=1.06):
    """Upper-left panel label like (a), (b), ... with default offset."""
    ax.text(dx, dy, tag, transform=ax.transAxes,
            fontsize=fontsize, fontweight="bold", va="bottom",
            ha="left", color=INK)


def save_fig(fig, out_stem, dpi=600, pdf=True, svg=False,
             transparent=False):
    """Save PNG @600 dpi + optional PDF/SVG. Returns list of written files."""
    written = []
    fig.savefig(out_stem + ".png", dpi=dpi, bbox_inches="tight",
                facecolor="white", transparent=transparent)
    written.append(out_stem + ".png")
    if pdf:
        fig.savefig(out_stem + ".pdf", bbox_inches="tight",
                    facecolor="white", transparent=transparent)
        written.append(out_stem + ".pdf")
    if svg:
        fig.savefig(out_stem + ".svg", bbox_inches="tight",
                    facecolor="white", transparent=transparent)
        written.append(out_stem + ".svg")
    plt.close(fig)
    return written


def set_fig_width(size="journal", scale=1.0):
    """Return figure width (in) for a size variant."""
    return SIZES[size]["fig_width"] * scale
