"""
figstyle.py — shared style module for the five reassembled main figures.

Adapted from final_figures/scripts/figure_style.py (the frozen figure-package
style) so that the five reassembled figures inherit exactly the same fonts,
palette, tick/spine conventions and export settings as the existing package.
Two deliberate changes only:

  1. the radiative-coefficient label is `r_rad` everywhere, matching the
     rewritten manuscript's prose symbol (code/CSV use `rad_c`);
  2. PARAM_ORDER is exposed explicitly so all five figures share one order.

Nothing here touches data. Style only.
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
    "mathtext.fontset": "dejavusans",
    "pdf.fonttype": 42,          # TrueType text in PDFs (editable)
    "ps.fonttype": 42,
    "svg.fonttype": "none",      # text stays text in SVG
})

# ---------------------------------------------------------------- palette --
OKABE_ITO = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#56B4E9",
             "#CC79A7", "#F0E442", "#000000", "#999999"]
PALETTE = OKABE_ITO

INK = "#1a1a1a"
MUTED = "#555555"
GRID = "#cccccc"

# ---------------------------------------------------------------- sizes ----
SIZES = {
    "journal": {"fig_width": 7.09},   # Solar RRL full width ~180 mm
    "large":   {"fig_width": 9.5},
}

FS_PANEL = 10.5
FS_TITLE = 9.0
FS_AXIS = 8.5
FS_TICK = 7.5
FS_LEGEND = 7.5
FS_ANNOT = 7.0
FS_CAPTION_TXT = 7.0
MIN_FS = 6.5

# ------------------------------------------------------- parameters/order --
# Canonical order used by every figure in this package.
PARAM_NAMES = [
    "mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk",
    "Nc_eff_pvk", "Nv_eff_pvk", "tau_ETL", "tau_HTL", "rad_c",
]
PARAM_LABELS = [
    r"$\mu_n$", r"$\mu_p$", r"$\tau_n$", r"$\tau_p$",
    r"$N_c$", r"$N_v$", r"$\tau_\mathrm{ETL}$",
    r"$\tau_\mathrm{HTL}$", r"$r_\mathrm{rad}$",
]
PARAM_SHORT = [
    "mu_n", "mu_p", "tau_n", "tau_p", "Nc", "Nv",
    "tau_ETL", "tau_HTL", "rad_c",
]

# Per-parameter colors. The archived package used OKABE_ITO[i] directly, whose
# entries 6-8 (yellow #F0E442, black, grey) are illegible or ambiguous on a
# white ground for thin lines. Replaced here by a nine-entry set that keeps
# OKABE_ITO for the first six and substitutes a dark brown / dark grey / dark
# goldenrod for the last three, so that all nine parameters keep one stable,
# legible color across the whole five-figure set.
PARAM_COLORS = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#56B4E9",
                "#CC79A7", "#8C564B", "#4D4D4D", "#B8860B"]

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
    """Upper-left panel label like (a), (b), ...

    Returns the Text artist so a caller can measure its extent and assert that
    it neither overflows its own axes nor collides with a neighbouring panel's
    labels. Added in the v2 round after three collisions that were visible only
    when the exported PDF was rendered back to an image.
    """
    return ax.text(dx, dy, tag, transform=ax.transAxes,
                   fontsize=fontsize, fontweight="bold", va="bottom",
                   ha="left", color=INK)


def save_fig(fig, out_stem, dpi=600, pdf=True, svg=True, transparent=False):
    """Save PNG @600 dpi + PDF + SVG. Returns list of written files.

    `dpi` is passed to ALL THREE formats, not only to the PNG. That matters
    for the two figures that carry `rasterized=True` scatter collections
    (Figure 2's six parity panels and Figure S6's nine-parameter grid: 15,307
    points per panel, which cannot be vectorised into anything a journal would
    accept as a file size). Every other artist is vector and ignores `dpi`
    entirely, so the page geometry and the text are untouched by this.

    Without it, savefig falls back to rcParams["savefig.dpi"] -> figure.dpi ->
    100, and the PDF embedded those scatter clouds at 100 dpi: measured, one
    Figure S6 panel was a 191 x 174 px bitmap stretched over 1.91 in. That is
    below the 300 dpi floor a journal applies to raster content, and it is the
    kind of thing no geometry check can see, because the panel is in the right
    place and the right size -- it is simply soft. At 600 dpi the same panel is
    1146 x 1044 px, matching the delivered PNG.
    """
    written = []
    fig.savefig(out_stem + ".png", dpi=dpi, bbox_inches="tight",
                facecolor="white", transparent=transparent)
    written.append(out_stem + ".png")
    if pdf:
        fig.savefig(out_stem + ".pdf", dpi=dpi, bbox_inches="tight",
                    facecolor="white", transparent=transparent)
        written.append(out_stem + ".pdf")
    if svg:
        fig.savefig(out_stem + ".svg", dpi=dpi, bbox_inches="tight",
                    facecolor="white", transparent=transparent)
        written.append(out_stem + ".svg")
    plt.close(fig)
    return written


def set_fig_width(size="journal", scale=1.0):
    return SIZES[size]["fig_width"] * scale


# ------------------------------------------------------------------ paths --
BASE = r"E:\project\work1"
HERE = os.path.dirname(os.path.abspath(__file__))
# The delivery root is the parent of this script's directory, so the same
# scripts write into work1_figures_reassembled_v2/ when run from the v2 copy.
# (Pinned to the v1 path in the first delivery; made relative in v2 so that the
# v1 package is never overwritten.)
OUT = os.path.dirname(HERE)
FIGDIR = os.path.join(OUT, "figures")
DATADIR = os.path.join(OUT, "data_used")
os.makedirs(FIGDIR, exist_ok=True)
os.makedirs(DATADIR, exist_ok=True)

# read-only frozen sources
NPZ = os.path.join(BASE, "final_figures", "scripts", "_frozen_preds.npz")
