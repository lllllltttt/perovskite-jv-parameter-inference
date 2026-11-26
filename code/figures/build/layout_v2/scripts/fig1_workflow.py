# -*- coding: utf-8 -*-
"""
fig1_workflow.py — reassembled main Figure 1 (v3).
==================================================
"Physical model and evaluation framework for single J-V curve inversion"

v3 RESTRUCTURE (supervisor layout, three panels)
------------------------------------------------
The submitted Figure 1 had four panels (2x2): (a) device stack, (b) LHS prior,
(c) dataset construction, (d) inverse workflow. v3 merges them into the three
panels the supervisor's plan specifies:

    +--------------------------+--------------------------+
    | (a) Physical model and   | (b) Simulation data and  |
    |     parameterization     |     inference            |
    +--------------------------+--------------------------+
    | (c) Evaluation: three complementary evaluations     |
    +-----------------------------------------------------+

  (a) = old (a) device stack + old (b) sampling prior. The two magnified
      interface-slab INSETS are removed (the plan moves local interface
      geometry to Methods / supplementary material); the two 0.01 nm slabs stay
      visible in the stack itself. The stack keeps the v2 physical order and
      contact labelling (FTO at x = 0 abuts the HTL, Ag at x = 530 abuts the
      SnO2). The parameter list names the generation variables g and q, gives
      the sampling law of each (g log-uniform inside each pair's range, q
      uniform on 0.2-5), and states that g and q are GENERATION variables while
      a = log10 g and r = log10 q are the EVALUATION coordinates of Figure 2.
  (b) = old (c) dataset construction + old (d) network. Archived counts
      200,000 -> 102,046 (51.0%) -> 71,432 / 15,307 / 15,307 are preserved.
      The fact that the main model's scalers were fitted on the FULL retained
      set (not on the train split alone) is stated next to the split block, as
      the plan requires, instead of being drawn as train-only preprocessing.
  (c) = NEW panel. The three complementary evaluations are separated:
        1. parameter means -> inverse scaling -> shared scale / log ratio,
           compared against the training-median baseline;
        2. parameter means -> inverse scaling -> 10^x -> physical theta_hat
           -> COMSOL -> compared against the target curve;
        3. mean and scale -> marginal intervals -> compared against the
           training-quantile baseline, and subjected to the noise test.
      The decoder reconstruction path is drawn as a SEPARATE strip and is never
      connected to COMSOL, so the figure cannot be read as a single cycle in
      which the decoder produces the physical back-substitution.

This is a schematic: no data are plotted. The only numbers on it are the
archived sampling bounds, retention counts and split sizes, which are written
to `data_used/Figure1_schematic_values.csv` by this script so that the figure
and the source record cannot drift apart.

v5 EDITS (author feedback, 2026-09-28)
--------------------------------------
  (b) The Gaussian head's output is drawn as a NUMERIC ARRAY labelled
      "parameter vector / normalized log10", not as a J-V curve labelled
      "physical parameter vector". The old glyph read as
      Gaussian head -> curve -> physical parameter vector, although the head
      emits neither a curve nor physical values.
  (b) The network widths (131->128->64, 9->64->128->131) and the softplus/clip
      scale formula are removed to Methods / the SI, and the five-line
      full-data preprocessing note is compressed to one sentence: repeated
      sampling counts, layer sizes and a clipping expression made the main
      figure read as a methods page.
  (c) "three independent directions" -> "three complementary evaluations" (the
      three are not statistically independent evidence items); the interval
      formula's z is renamed z_{1-alpha/2} so that it no longer collides with
      the latent variable z shown above it.
  (c) The third column's footer cites Table S17b alongside S2 and S7: S17b is
      the training-set prior-baseline table the training-quantile comparison
      rests on.

Outputs: figures/Figure1{,_large}.{png,pdf,svg}
         data_used/Figure1_schematic_values.csv
"""

import os
import sys

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, FancyArrowPatch, Circle
from matplotlib.path import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import figstyle as st

# ---- local palette, inherited from the archived Figure 1 script -------------
BLACK = "#20252B"
TEXT = "#536273"
BLUE = "#5D80A8"
BLUE_FILL = "#E7EEF6"
GREEN = "#5E8D80"
GREEN_FILL = "#E4EFEB"
ORANGE = "#B96F42"
ORANGE_FILL = "#F8ECE5"
GOLD = "#B88943"
GOLD_FILL = "#F5E9D5"
GREY = "#9BA6B1"
GREY_FILL = "#F3F5F7"
AG = "#CCD0D6"
HTL = "#AEC4B5"
PVK = "#E4CB8B"
C60 = "#91B2CB"
SNO2 = "#D8DEE4"
FTO = "#E3E6EA"
IFACE = "#6E7B88"

# generation-variable colours: shared scale g and electron-hole ratio q
C_G = BLUE
C_Q = ORANGE

S = 1.0          # font scale, set per output size
FS_FLOOR = 7.0   # pt, in authoring units, before the S scale is applied


def fs(v):
    """Font size in points, floored so the figure satisfies the legibility law.

    The schematic is authored at 7.09 in and displayed in the manuscript's
    17.27 cm text column, so an authoring size v renders on the page at
    v * 17.27/18.01. The project's legibility law,

        f_internal >= 0.3886 pt/cm * W_display     (audit: figure_font_audit.py)

    puts the floor at 7.0 pt *internal* for this figure; a schematic that
    labelled its smallest notes at 5.2 pt rendered them at 5.0 pt on the page.
    Every sub-floor call is raised to the floor here rather than at ~60 call
    sites, so a future size can only move the floor, never miss a site.
    """
    return max(v, FS_FLOOR) * S


# ============================================================
# helpers
# ============================================================

def setup(ax, letter, title):
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.text(0.005, 0.990, "(%s)" % letter, fontsize=fs(10.5),
            fontweight="bold", va="top", color=BLACK)
    ax.text(0.060, 0.990, title, fontsize=fs(8.4), va="top", color=TEXT)


def box(ax, x, y, w, h, edge, face, radius=0.02, lw=1.2, ls="-"):
    p = FancyBboxPatch((x, y), w, h,
                       boxstyle="round,pad=0.004,rounding_size=%g" % radius,
                       linewidth=lw, edgecolor=edge, facecolor=face,
                       linestyle=ls)
    ax.add_patch(p)
    return p


def arrow(ax, x1, y1, x2, y2, color=BLACK, lw=1.2, size=7):
    p = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                        mutation_scale=size, linewidth=lw, color=color,
                        shrinkA=0, shrinkB=0)
    ax.add_patch(p)
    return p


def jv_frame(ax, x, y, w, h):
    ax.plot([x, x], [y, y + h], color="#AAB2BC", lw=0.9)
    ax.plot([x, x + w], [y, y], color="#AAB2BC", lw=0.9)


def draw_jv(ax, x, y, w, h, n=1, dashed=False, base_color=BLUE):
    jv_frame(ax, x, y, w, h)
    xx = np.linspace(0, 1.3, 240)
    for i in range(n):
        voc_shift = 1.03 + 0.025 * i
        jj = (1 - 0.05 * (xx / 1.3) - 0.08 * (xx / 1.3) ** 2
              - 1.08 / (1 + np.exp(-(xx - voc_shift) / 0.045)))
        X = x + (xx / 1.3) * w
        Y = y + h * (0.52 + 0.42 * jj)
        ax.plot(X, Y, lw=1.0, color=base_color,
                alpha=0.35 + 0.12 * i, ls="--" if dashed else "-")


def draw_param_vector(ax, x, y, w, h, color=BLUE, face=BLUE_FILL, ncol=3):
    """Numeric-array glyph for the Gaussian parameter head's output.

    Two rows of three filled cells stand for the nine means and the nine scales
    the head returns, in normalized log10 coordinates. This replaces the J-V
    curve glyph that used to sit in this slot: a curve labelled "physical
    parameter vector" read as Gaussian head -> curve -> physical parameter
    vector, but the head emits neither a curve nor physical values. The
    physical conversion (inverse scaling, then 10^x) is step 2 of panel (c).
    """
    box(ax, x, y, w, h, color, face, radius=0.010, lw=1.0)
    pad = 0.11 * w
    cw = (w - 2 * pad) / ncol
    ch = 0.19 * h
    for alpha, cy in ((0.90, y + 0.635 * h), (0.55, y + 0.275 * h)):
        for c in range(ncol):
            ax.add_patch(Rectangle(
                (x + pad + c * cw + 0.19 * cw, cy - ch / 2),
                0.62 * cw, ch, facecolor=color, edgecolor="none", alpha=alpha))


# ============================================================
# panel (a) — physical model and parameterization
# ============================================================

def panel_a(ax):
    setup(ax, "a", "Physical model and parameterization")

    # ---------------- left: 1D device cross-section -------------------------
    # sw 0.132 -> 0.150: at the 7 pt floor "Perovskite" (bold) is 49.3 px wide
    # and the band it sits in was 45.2 px, so the word crossed the band's border
    # on both sides (scripts/_fig_fit.py, "text out of the drawn box that holds
    # it"). The band is widened rather than the word shrunk, because the 7 pt
    # floor is not negotiable; the "0.01 nm" callouts move right with it and
    # still clear the parameter column at x = 0.350 by 4.8 px.
    sx, sw = 0.086, 0.150
    sy, sh = 0.185, 0.680

    # Drawn BOTTOM-UP, so the first entry sits at x = 0 nm and the last at
    # x = 530 nm. Physical order along +x:
    #   FTO | HTL | HTL&PVK | Perovskite | PVK&C60 | C60 | SnO2 | Ag
    # => FTO abuts the HTL and Ag abuts the SnO2.
    bands = [
        ("FTO", FTO, 0.060, True),
        ("HTL", HTL, 0.140, False),
        ("", IFACE, 0.030, False),          # HTL&PVK slab, x = 20-20.01 nm
        ("Perovskite", PVK, 0.420, False),
        ("", IFACE, 0.030, False),          # C60&PVK slab, x = 490-490.01 nm
        ("C60", C60, 0.140, False),
        ("SnO$_2$", SNO2, 0.110, False),
        ("Ag", AG, 0.070, True),
    ]
    yc = sy
    for name, col, frac, is_contact in bands:
        hh = frac * sh
        ax.add_patch(Rectangle((sx, yc), sw, hh, facecolor=col,
                               edgecolor="#5E6873" if is_contact else "#7C8792",
                               linewidth=0.9,
                               hatch="///" if is_contact else None,
                               linestyle="--" if is_contact else "-"))
        if name:
            ax.text(sx + sw / 2, yc + hh / 2, name, ha="center", va="center",
                    fontsize=fs(6.3),
                    fontweight="bold" if name == "Perovskite" else "normal",
                    color=BLACK)
        yc += hh
    y_top = yc

    # key the two 0.01 nm slabs to short brackets (no magnified insets here)
    # Bracket at +0.020 and label at +0.028, pulled in from +0.026/+0.034: with
    # the band widened to 0.150 the label (35.1 px at 7 pt) ended 0.1 px from
    # where "Density of states" begins, and the two read as one word.
    for frac_lo in (0.230, 0.680):
        ax.annotate("", xy=(sx + sw + 0.020, sy + frac_lo * sh),
                    xytext=(sx + sw + 0.020, sy + (frac_lo + 0.030) * sh),
                    arrowprops=dict(arrowstyle="<|-|>", lw=0.7, color=BLACK,
                                    mutation_scale=4))
        ax.text(sx + sw + 0.028, sy + (frac_lo + 0.015) * sh, "0.01 nm",
                ha="left", va="center", fontsize=fs(5.5), color=BLACK)

    # dimension arrow to the LEFT of the stack
    ax.annotate("", xy=(0.074, y_top), xytext=(0.074, sy),
                arrowprops=dict(arrowstyle="<|-|>", lw=0.9, color=GREY,
                                mutation_scale=6))
    ax.text(0.056, (sy + y_top) / 2, "x:  0 → 530 nm", rotation=90,
            ha="center", va="center", fontsize=fs(5.9), color=TEXT)
    # kept short enough to stop clear of the parameter column at x = 0.350
    ax.text(0.004, 0.168, "schematic, not to scale", fontsize=fs(5.6),
            color=TEXT, style="italic", va="top")
    ax.text(0.004, 0.130,
            "FTO and Ag: contacts,\nnot COMSOL volume domains.",
            fontsize=fs(5.6), color=C_Q, va="top", linespacing=1.35)

    # ---------------- right: parameterization ------------------------------
    # px 0.360 -> 0.370 and the generation-variables box 0.640 -> 0.630 (same
    # right edge, 0.990): the column has to start far enough right that the
    # "Density of states" row clears the "0.01 nm" callout on the stack. The
    # box's widest line, "one shared g and one q per electron-hole pair", is
    # 0.593 of this panel and still ends at 0.967 inside the box.
    px = 0.370
    ax.text(px, 0.900, "Nine inference targets", fontsize=fs(7.2),
            fontweight="bold", color=TEXT, va="top")

    ax.text(px, 0.840, "paired electron–hole parameters",
            fontsize=fs(6.0), color=TEXT, va="top")
    ax.text(px, 0.802,
            r"$p_n = g\sqrt{q}$        $p_p = g/\sqrt{q}$",
            fontsize=fs(6.6), color=BLACK, va="top")
    for i, (lab, sym) in enumerate([("Mobility", r"$\mu_n,\ \mu_p$"),
                                    ("Bulk lifetime", r"$\tau_n,\ \tau_p$"),
                                    ("Density of states",
                                     r"$N_c,\ N_v$")]):
        yy = 0.756 - 0.044 * i
        ax.text(px + 0.012, yy, lab, fontsize=fs(6.1), color=BLACK, va="top")
        # 0.265 rather than 0.215: at 7 pt "Density of states" is 83 px wide, so
        # the symbol column at 0.215 (which is 197 px into the panel) sat inside
        # it. The three symbols are 22-24 px wide, so they still clear the
        # panel's right edge at 0.265.
        ax.text(px + 0.265, yy, sym, fontsize=fs(6.4), color=BLACK, va="top")

    ax.text(px, 0.596, "directly sampled parameters", fontsize=fs(6.0),
            color=TEXT, va="top")
    direct = [(r"$\tau_\mathrm{ETL}$",
               r"$1\times10^{-12} - 1\times10^{-8}$ s"),
              (r"$\tau_\mathrm{HTL}$",
               r"$1\times10^{-14} - 1\times10^{-10}$ s"),
              (r"$r_\mathrm{rad}$",
               r"$1\times10^{-12} - 1\times10^{-9}$ cm$^3$ s$^{-1}$")]
    for i, (sym, rng) in enumerate(direct):
        yy = 0.554 - 0.044 * i
        ax.text(px + 0.012, yy, sym, fontsize=fs(6.4), color=BLACK, va="top")
        ax.text(px + 0.105, yy, rng, fontsize=fs(5.9), color=BLACK, va="top")

    # generation variables vs evaluation coordinates
    # box bottom 0.262 (not 0.278) and height 0.178: the box's last line of
    # text sits at 0.302 and was measured below the drawn bottom edge. The line
    # cannot simply move up — the q annotation above it would be crossed — so
    # the box grows downward instead; the top edge is unchanged at 0.440.
    box(ax, px - 0.010, 0.262, 0.630, 0.178, "#C8CED4", "#FAFBFC",
        radius=0.014, lw=0.9)
    # The draw count is not repeated here: at 7 pt the fuller string measured
    # 273 px and ran 45 px past this panel's right edge. It is stated once, in
    # panel (b)'s archive strip, which is where the reader meets the counts.
    ax.text(px + 0.004, 0.418, "generation variables  (Latin hypercube)",
            fontsize=fs(5.9), color=TEXT, va="top")
    ax.text(px + 0.004, 0.374, "$g$", fontsize=fs(6.8), color=C_G, va="top")
    ax.text(px + 0.032, 0.376, "log-uniform, inside each pair's range",
            fontsize=fs(5.9), color=BLACK, va="top")
    ax.text(px + 0.004, 0.332, "$q$", fontsize=fs(6.8), color=C_Q, va="top")
    ax.text(px + 0.032, 0.334, "uniform on 0.2 – 5",
            fontsize=fs(5.9), color=BLACK, va="top")
    # 0.302 rather than 0.294: the last line of the box was measured 3.67 pt
    # below the box's drawn bottom edge, so its descenders were cut by the
    # border (qa_text_overlap.py, check 5 TEXT_OUT_OF_BOX). Raising it clears
    # the border by ~1.5 pt while keeping clear of the q line above.
    ax.text(px + 0.004, 0.302,
            "one shared $g$ and one $q$ per electron–hole pair",
            fontsize=fs(5.7), color=TEXT, va="top")

    ax.text(px - 0.010, 0.246,
            "$g$ and $q$ are the generation variables;",
            fontsize=fs(5.8), color=TEXT, va="top")
    ax.text(px - 0.010, 0.208,
            "$a=\\log_{10}g$ and $r=\\log_{10}q$ are the evaluation",
            fontsize=fs(5.8), color=TEXT, va="top")
    ax.text(px - 0.010, 0.170, "coordinates of Figure 2.",
            fontsize=fs(5.8), color=TEXT, va="top")

    # both footnotes are stacked in the free band UNDER the stack (x < 0.79 at
    # this height is clear), rather than one sitting at x = 0.350 where the
    # two would run into each other at every wrapping
    ax.text(0.004, 0.066,
            "Interface lifetimes are effective slab\n"
            "parameters of the thin-slab model.",
            fontsize=fs(5.6), color=TEXT, va="top", style="italic",
            linespacing=1.35)


# ============================================================
# panel (b) — simulation data and inference
# ============================================================

def panel_b(ax):
    setup(ax, "b", "Inference network (autoencoder)")

    # ---------------- archived data: one compact strip ---------------------
    # The five-node database-construction chain (Latin hypercube -> COMSOL ->
    # synthetic ensemble -> physical filter -> retained set) and the four
    # filter criteria were removed from the MAIN figure this round. They are
    # procedural and belong to Methods and the supplementary material, and on
    # the main figure they made panel (b) read as a methods page. Only the two
    # facts a reader needs in order to place the network are kept, on one
    # strip: how many curves the archive holds, and that the split is fixed.
    # Three lines, not two: at the 7 pt floor the two old lines measured 422
    # and 511 px against the 340 px the strip offers (scripts/_measure_strings.py),
    # so they ran 0.46 in past the canvas and the delivered PNG grew. The same
    # facts are now spread over three lines that each fit, and the strip box
    # grew downward by 0.031 to hold them.
    box(ax, 0.004, 0.830, 0.992, 0.125, "#C8CED4", "#FAFBFC",
        radius=0.012, lw=0.9)
    ax.text(0.5, 0.941,
            "archived data:  200,000 draws  "
            r"$\rightarrow$  102,046 retained (51.0%)",
            ha="center", va="top", fontsize=fs(7.0), color=BLACK)
    ax.text(0.5, 0.906,
            "fixed split:  71,432 train   ·   15,307 validation   ·   "
            "15,307 test",
            ha="center", va="top", fontsize=fs(7.0), color=TEXT)
    ax.text(0.5, 0.871, "normalization fitted on the retained set",
            ha="center", va="top", fontsize=fs(7.0), color=TEXT)

    # ---------------- the network ------------------------------------------
    # YC is the vertical centre of the input -> encoder -> latent line. The
    # head and the decoder branch off it, so the panel reads left to right and
    # then splits, rather than as a single cycle.
    YC = 0.530

    draw_jv(ax, 0.008, YC - 0.078, 0.110, 0.156, n=1, base_color=BLACK)
    # Left-aligned on the glyph's own left edge, not centred under it: at 7 pt
    # "131 currents" is 62 px wide and a centred caption started 5.7 px outside
    # this panel, where panel (a)'s parameter column sits.
    ax.text(0.008, YC - 0.092, "J–V input", ha="left", va="top",
            fontsize=fs(7.0), color=TEXT)
    ax.text(0.008, YC - 0.126, "131 currents", ha="left", va="top",
            fontsize=fs(7.0), color=TEXT)
    ax.text(0.008, YC - 0.160, "0 – 1.3 V", ha="left", va="top",
            fontsize=fs(7.0), color=TEXT)
    arrow(ax, 0.120, YC, 0.136, YC, size=6)

    # The encoder layer sizes (131 -> 128 -> 64) are deliberately not drawn:
    # they belong in Methods / the SI.
    box(ax, 0.140, YC - 0.078, 0.126, 0.156, GREEN, GREEN_FILL, radius=0.012)
    ax.text(0.203, YC + 0.090, "Encoder", ha="center", va="bottom",
            fontsize=fs(6.6), fontweight="bold", color=GREEN)
    arrow(ax, 0.268, YC, 0.284, YC, size=6)

    ax.add_patch(Circle((0.312, YC), 0.027, facecolor=GREY_FILL,
                        edgecolor="#7F8994", linewidth=1.0))
    ax.text(0.312, YC, r"$z$", ha="center", va="center", fontsize=fs(6.6))
    # the latent label sits on the z -> head connector and breaks it with a
    # white backing box, so the vertical arrow does not run through the glyphs
    ax.text(0.312, YC - 0.040, "latent (9)", ha="center", va="top",
            fontsize=fs(5.2), color=TEXT, zorder=6,
            bbox=dict(boxstyle="square,pad=0.14", fc="white", ec="none"))

    # ---- Gaussian parameter head ------------------------------------------
    # The scale formula (softplus, clipped to [0.01, 1.0]) and the layer sizes
    # went to Methods / the SI.
    # hw 0.310 -> 0.360. At the 7 pt floor the box's own labels measure 119.4 px
    # (bold title) and 123.4 px against a 106.2 px interior, so all three lines
    # crossed the border. The extra width comes out of the gap to the output
    # glyph, which moves right with it; the input arrow into the box's left edge
    # is unaffected.
    HY = 0.705
    hx0, hy0, hw, hhh = 0.350, HY - 0.070, 0.360, 0.140
    box(ax, hx0, hy0, hw, hhh, ORANGE, ORANGE_FILL, radius=0.012)
    hc = hx0 + hw / 2
    ax.text(hc, hy0 + hhh - 0.012, "Gaussian parameter head", ha="center",
            va="top", fontsize=fs(6.1), fontweight="bold", color=ORANGE)
    # single spaces around the plus: the three-space version measured 123.4 px
    # and was the widest line in the box
    ax.text(hc, hy0 + hhh - 0.048,
            r"9 means $\mu_\theta$ + 9 scales $\sigma_\theta$",
            ha="center", va="top", fontsize=fs(5.4))
    ax.text(hc, hy0 + hhh - 0.084, "in normalized log$_{10}$ space",
            ha="center", va="top", fontsize=fs(5.4), color=BLACK)
    ax.add_patch(FancyArrowPatch(
        path=Path([(0.312, YC + 0.027), (0.312, HY), (0.346, HY)]),
        arrowstyle="-|>", mutation_scale=6, linewidth=1.2, color=ORANGE))

    # ---- decoder -----------------------------------------------------------
    # The decoder layer sizes (9 -> 64 -> 128 -> 131) went to Methods / the SI.
    DY = 0.360
    dx0, dy0, dw, dh = 0.350, DY - 0.060, 0.360, 0.120
    box(ax, dx0, dy0, dw, dh, ORANGE, "#FBF4F0", radius=0.012)
    dc = dx0 + dw / 2
    ax.text(dc, dy0 + dh - 0.014, "Decoder", ha="center", va="top",
            fontsize=fs(6.6), fontweight="bold", color=ORANGE)
    # Two lines, not one. "reconstructs the J-V curve from z" is 147.1 px at
    # 7 pt and the box interior is 123.3 px, so the single line ran 19.1 px out
    # of the box. Wrapped, the longest line is 116.2 px and both fit.
    ax.text(dc, dy0 + dh - 0.048, "reconstructs the J–V curve",
            ha="center", va="top", fontsize=fs(5.2), color=TEXT)
    ax.text(dc, dy0 + dh - 0.074, "from $z$",
            ha="center", va="top", fontsize=fs(5.2), color=TEXT)
    ax.add_patch(FancyArrowPatch(
        path=Path([(0.312, YC - 0.027), (0.312, DY), (0.346, DY)]),
        arrowstyle="-|>", mutation_scale=6, linewidth=1.2, color=ORANGE))

    # ---- the two outputs ---------------------------------------------------
    # Upper output: the head returns 9 means and 9 scales in normalized log10
    # coordinates, so it is drawn as a NUMERIC ARRAY. A J-V curve here read as
    # "Gaussian head -> curve -> physical parameter vector", which is wrong
    # twice over: the head emits no curve, and what it emits is not yet
    # physical. The inverse scaling and 10^x conversion are step 2 of (c).
    # The glyphs moved from x = 0.700 to 0.752 to make room for the widened
    # head and decoder boxes, and their captions are now CENTRED under each
    # glyph rather than left-aligned on it: "decoder reconstruction" is 0.257 of
    # this panel wide and left-aligned at 0.752 it would end at 1.009, past the
    # panel edge. Centred at 0.808 it spans 0.680-0.937 and fits.
    GX, GC = 0.752, 0.752 + 0.056
    draw_param_vector(ax, GX, HY - 0.054, 0.112, 0.108, color=BLUE,
                      face=BLUE_FILL)
    ax.text(GC, HY - 0.066, "parameter vector", ha="center", va="top",
            fontsize=fs(5.4), color=BLUE)
    ax.text(GC, HY - 0.092, "normalized log$_{10}$", ha="center", va="top",
            fontsize=fs(5.4), color=BLUE)
    # the label rides ABOVE the glyph's top edge (HY + 0.054), not beside it:
    # at HY + 0.016 the string sat inside the drawn array box
    ax.text(GC, HY + 0.062, r"$\mu_\theta$, $\sigma_\theta$", ha="center",
            va="bottom", fontsize=fs(5.6), color=ORANGE)
    arrow(ax, 0.718, HY, 0.746, HY, color=BLUE, size=6)

    # Lower output: a curve glyph is correct here — the decoder really does
    # emit a J-V curve, and it is drawn dashed so the two paths never merge.
    draw_jv(ax, GX, DY - 0.054, 0.112, 0.108, n=1, dashed=True,
            base_color=ORANGE)
    ax.text(GC, DY - 0.066, "decoder reconstruction", ha="center", va="top",
            fontsize=fs(5.4), color=ORANGE)
    arrow(ax, 0.718, DY, 0.746, DY, color=ORANGE, size=6)

    # one line of scope for the whole panel, anchored at the foot so the panel
    # does not end in empty space now that the data chain is gone
    ax.plot([0.004, 0.996], [0.196, 0.196], color="#C8CED4", lw=0.8)
    # Three lines, not two: the two-line version was 371 px wide inside a
    # 342 px panel, so it overhung the figure's right edge by 0.10 in at
    # journal width and 0.14 in at large width, and savefig's tight bbox
    # silently widened the delivered PNG. Each line now fits the panel width
    # and the block still clears the axes bottom.
    ax.text(0.5, 0.156,
            "one J–V curve in: the parameter head returns the nine "
            "inference targets,\n"
            "the decoder returns a curve. The decoder is never fed to "
            "COMSOL —\n"
            "physical back-substitution uses $\\hat{\\theta}$ (panel c).",
            ha="center", va="top", fontsize=fs(5.5), color=TEXT,
            linespacing=1.55)


# ============================================================
# panel (c) — evaluation
# ============================================================

# vertical slots inside a direction column (axes fraction)
C_TOP = 0.806
C_BOT = 0.150


# All the vertical steps below are fractions of the PANEL height, so they have
# to be re-derived whenever the type size changes. They were tuned for 5.4-6.6
# pt labels; at the 7 pt floor a line of text is 0.0304 of panel (c) at journal
# width, and any step below that made consecutive lines overlap. Each step is
# now at least 0.032, and the two header steps grew to 0.042/0.044.
def _col_header(ax, x0, w, lines, color, y):
    for t in lines:
        ax.text(x0 + w / 2, y, t, ha="center", va="top", fontsize=fs(6.6),
                fontweight="bold", color=color)
        y -= 0.042
    return y - 0.010


def _col_step(ax, x0, w, y, lines, color=BLACK):
    # 0.044 rather than a tight 0.030: mathtext with subscripts and
    # superscripts has a taller extent than its nominal font size
    for t in lines:
        ax.text(x0 + w / 2, y, t, ha="center", va="top", fontsize=fs(5.8),
                color=color)
        y -= 0.044
    return y - 0.010


def _col_down(ax, x0, w, y):
    ax.text(x0 + w / 2, y, r"$\downarrow$", ha="center", va="top",
            fontsize=fs(6.2), color=TEXT)
    return y - 0.044


def _col_cmp(ax, x0, w, y, title, sub):
    """A comparison block: one titled line plus its qualifier lines.

    The separate italic "compared with" line that used to sit above the title
    is gone. At the 7 pt floor it cost 0.032 of the panel height in each of the
    four blocks, and column 3 - which holds two of them - then pushed its last
    arrow through the bottom-anchored "reported as" block. The relation is now
    carried by the title itself ("vs. training-median baseline"), which is
    shorter than the two lines it replaces and reads the same.
    """
    ax.text(x0 + w / 2, y, title, ha="center", va="top",
            fontsize=fs(6.0), color=BLACK)
    for i, t in enumerate(sub):
        ax.text(x0 + w / 2, y - 0.032 - 0.032 * i, t, ha="center", va="top",
                fontsize=fs(5.4), color=TEXT)
    return y - 0.032 - 0.032 * len(sub) - 0.008


def _col_box(ax, x0, w, y, title, sub, edge, face):
    h = 0.030 + 0.032 * len(sub) + 0.018
    box(ax, x0 + 0.014, y - h, w - 0.028, h, edge, face, radius=0.012, lw=1.0)
    ax.text(x0 + w / 2, y - 0.014, title, ha="center", va="top",
            fontsize=fs(6.0), fontweight="bold", color=edge)
    for i, t in enumerate(sub):
        ax.text(x0 + w / 2, y - 0.048 - 0.032 * i, t, ha="center", va="top",
                fontsize=fs(5.4), color=TEXT)
    return y - h - 0.012


def _col_out(ax, x0, w, items, tail):
    """Bottom-anchored 'reported as' block."""
    n = len(items)
    y_tail = C_BOT + 0.020
    y_bul = y_tail + 0.036 * n
    y_head = y_bul + 0.032
    ax.plot([x0 + 0.022, x0 + w - 0.022], [y_head + 0.012] * 2,
            color="#C8CED4", lw=0.8)
    ax.text(x0 + w / 2, y_head, "reported as", ha="center", va="top",
            fontsize=fs(5.4), color=TEXT, style="italic")
    for i, t in enumerate(items):
        ax.text(x0 + w / 2, y_bul - 0.036 * i, "•  " + t, ha="center",
                va="top", fontsize=fs(5.6), color=BLACK)
    ax.text(x0 + w / 2, y_tail, tail, ha="center", va="top",
            fontsize=fs(5.4), color=TEXT)
    return y_head + 0.012


def panel_c(ax):
    setup(ax, "c", "Evaluation: three complementary evaluations")

    # ---------------- shared prediction bar ---------------------------------
    box(ax, 0.004, 0.856, 0.992, 0.088, "#A9B4C1", GREY_FILL, radius=0.012)
    ax.text(0.500, 0.932,
            "prediction per test curve:   9 means $\\mu_\\theta$   +   "
            "9 scales $\\sigma_\\theta$    in normalized log$_{10}$ space",
            ha="center", va="top", fontsize=fs(6.4), color=BLACK)

    cols = [(0.004, 0.322, C_G, "#F4F8FC"),
            (0.339, 0.322, BLUE, "#F2F6FA"),
            (0.674, 0.322, C_Q, "#FBF4F0")]

    for x0, w, color, face in cols:
        # bottom 0.026 below C_BOT (not 0.014): at 7 pt the "reported as" tail
        # line's descenders were clipped by the box border
        box(ax, x0, C_BOT - 0.026, w, C_TOP - C_BOT + 0.038, color, face,
            radius=0.014, lw=1.1)
        arrow(ax, x0 + w / 2, 0.852, x0 + w / 2, 0.836, color=color)

    # ---------------- 1: paired coordinates vs training median -------------
    x0, w, color, _ = cols[0]
    y = _col_header(ax, x0, w, ["1  Recovery of paired", "coordinates"], color,
                    C_TOP)
    y = _col_step(ax, x0, w, y,
                  [r"$\mu_\theta$  $\rightarrow$  inverse scaling",
                   r"$a = \log_{10}g$,   $r = \log_{10}q$"])
    y = _col_down(ax, x0, w, y)
    y = _col_cmp(ax, x0, w, y, "vs. training-median baseline",
                 ["fixed constant, computed from the", "training partition, "
                  "no curve input"])
    y = _col_down(ax, x0, w, y)
    # Figure 2g / 2h, not 2b / 2c: the reassembled Figure 2 carries the
    # correlation comparison in panel (g) and the baseline-relative MAE
    # reduction in panel (h). The old two-panel Figure 2 put them in (b)/(c),
    # and those letters were left behind in the first assembly.
    _col_out(ax, x0, w, ["coordinate prediction correlation",
                         "MAE reduction vs baseline"],
             "Figure 2g, 2h   ·   Table S11")

    # ---------------- 2: physical back-substitution ------------------------
    x0, w, color, _ = cols[1]
    y = _col_header(ax, x0, w, ["2  Physical", "back-substitution"], color,
                    C_TOP)
    y = _col_step(ax, x0, w, y,
                  [r"$\mu_\theta$  $\rightarrow$  inverse scaling  "
                   r"$\rightarrow$  $10^{x}$",
                   r"$\hat{\theta}$   (physical units)"])
    y = _col_down(ax, x0, w, y)
    y = _col_box(ax, x0, w, y, "COMSOL  drift–diffusion",
                 ["1D,  x = 0 – 530 nm"], BLUE, GREY_FILL)
    y = _col_down(ax, x0, w, y)
    y = _col_cmp(ax, x0, w, y, "vs. target curve",
                 ["and target device metrics"])
    y = _col_down(ax, x0, w, y)
    ax.text(x0 + w / 2, y - 0.006,
            "the decoder curve is not used here",
            ha="center", va="top", fontsize=fs(5.4), color=C_Q,
            style="italic")
    _col_out(ax, x0, w, ["curve RMSE by voltage window",
                         "device-metric deviations"],
             "Figure 4   ·   Table S8")

    # ---------------- 3: predictive intervals ------------------------------
    x0, w, color, _ = cols[2]
    y = _col_header(ax, x0, w, ["3  Predictive", "intervals"], color, C_TOP)
    y = _col_step(ax, x0, w, y,
                  ["marginal intervals",
                   r"$\mu_\theta \pm z_{1-\alpha/2}\,\sigma_\theta$"])
    y = _col_down(ax, x0, w, y)
    y = _col_cmp(ax, x0, w, y, "vs. training-quantile baseline",
                 ["fixed empirical quantiles, from the", "training partition"])
    y = _col_down(ax, x0, w, y)
    y = _col_cmp(ax, x0, w, y, "clean vs. noisy input",
                 ["Gaussian current noise,",
                  r"0 – 2% of each curve's $|J_\mathrm{sc}|$"])
    y = _col_down(ax, x0, w, y)
    _col_out(ax, x0, w, ["empirical coverage, interval score",
                         "change in predicted scale"],
             "Figure 5   ·   Tables S2, S7, S17b")

    # ---------------- separate decoder strip --------------------------------
    # Three rows now. At the 7 pt floor the flow line alone is 400 px wide
    # against this panel's 699 px, so the scoping caveat could no longer share
    # its row: it started at x = 0.480 and the two overlapped by 77 px. The row
    # it freed is used to give the caveat its own line, and the strip grew
    # upward to the underside of the three column boxes.
    box(ax, 0.004, 0.000, 0.992, 0.131, "#B7C0C9", "#FCFCFD", radius=0.010,
        lw=0.9, ls=(0, (4, 2)))
    ax.text(0.018, 0.125, "separate path — decoder reconstruction",
            fontsize=fs(6.1), fontweight="bold", color=TEXT, va="top")
    ax.text(0.018, 0.082,
            "decoder curve (from $z$)   $\\rightarrow$   compared with the "
            "target curve   $\\rightarrow$   reconstruction error",
            fontsize=fs(7.0), color=BLACK, va="top")
    # Left at 0.036. Raising it to 0.044 to clear the strip's bottom border
    # (measured 3.4 px) put it 0.9 px into the flow line above instead, and the
    # strip cannot grow upward without crossing the (c) container's lower edge.
    # The remaining 3.4 px is the descender of $\hat{\theta}$ against a border
    # drawn with pad=0.004, i.e. below the border's own footing.
    ax.text(0.018, 0.036,
            "Never fed to COMSOL: back-substitution uses $\\hat{\\theta}$.",
            fontsize=fs(7.0), color=C_Q, va="top")


# ============================================================
# build
# ============================================================

def build(size):
    global S
    w = st.set_fig_width(size)
    S = w / 7.09
    # 1.010 rather than 0.940: with every label floored at 7 pt (see fs()), the
    # old canvas gave panel (c) 297 px for a 14-line column and the bottom
    # "reported as" block no longer cleared the last arrow. The canvas is a
    # little taller instead; the displayed height is 6.9 in, well inside the
    # manuscript's 9.4 in text height together with the caption.
    fig = plt.figure(figsize=(w, w * 1.010))
    gs = fig.add_gridspec(2, 2, left=0.008, right=0.994, bottom=0.006,
                          top=0.994, wspace=0.040, hspace=0.050,
                          height_ratios=[1.16, 1.0])
    panel_a(fig.add_subplot(gs[0, 0]))
    panel_b(fig.add_subplot(gs[0, 1]))
    panel_c(fig.add_subplot(gs[1, :]))
    stem = os.path.join(st.FIGDIR, "Figure1"
                        + ("_large" if size == "large" else ""))
    st.save_fig(fig, stem)
    print("wrote:", stem)


def main():
    for sz in ("journal", "large"):
        build(sz)

    rows = [
        dict(item="LHS draws", value=200000, unit="draws",
             source="script/LHS.py (qmc.LatinHypercube, seed 42)"),
        dict(item="g sampling law", value=np.nan, unit="-",
             source="script/LHS.py: log-uniform per pair "
                    "(mu 1e-6-1e-3, tau 1e-9-1e-2, DOS 1e22-1e26)"),
        dict(item="q sampling law", value=np.nan, unit="-",
             source="script/LHS.py: uniform on 0.2-5"),
        dict(item="tau_ETL range", value=np.nan, unit="s",
             source="script/LHS.py: log-uniform 1e-12-1e-8"),
        dict(item="tau_HTL range", value=np.nan, unit="s",
             source="script/LHS.py: log-uniform 1e-14-1e-10"),
        dict(item="r_rad range", value=np.nan, unit="cm3 s-1",
             source="script/LHS.py: log-uniform 1e-12-1e-9"),
        dict(item="retained curves", value=102046, unit="curves",
             source="archived retention (51.0% of 200,000)"),
        dict(item="train / val / test", value=np.nan, unit="curves",
             source="archived split: 71,432 / 15,307 / 15,307"),
        dict(item="x domain", value=530.0, unit="nm",
             source="COMSOL 1D model: x = 0-530 nm, six volume domains"),
    ]
    pd.DataFrame(rows).to_csv(
        os.path.join(st.DATADIR, "Figure1_schematic_values.csv"), index=False)
    print("wrote schematic value table")


if __name__ == "__main__":
    main()
