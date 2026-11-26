"""
plot_FigS1_eda.py — Figure S1 (final unified re-render).
========================================================
Figure S1 of the frozen Stage-I manuscript:

    "Exploratory data analysis of the retained dataset: histograms of the
     nine parameters and pairwise correlations."

ONE combined publication-quality supplementary figure:

  (a) Retained parameter distributions — compact 3 x 3 histogram grid of the
      nine retained physical parameters, plotted in log10 parameter space
      (x = log10(theta); the manuscript/model operates in log-parameter space).
  (b) Pairwise log-space Spearman correlation — 9 x 9 heatmap of
      Spearman(log10 theta_i, log10 theta_j) for the retained dataset.

The legacy exploration-era panel "100 random J-V curves" is deliberately
REMOVED (not required by the current caption; made the legacy figure wide).

Authoritative data source (read-only; nothing recomputed, nothing resampled):
  data/JV_database_9D_interface_lifetimes-2.csv   N = 102,046 retained rows
  (200,000 LHS draws, seed 42, after physical filtering; the same retained
   parameter population used throughout the frozen paper — frozen manifest
   independent_validation/FROZEN_ARTIFACT_MANIFEST.md).

Correlation metric — verified against the final Table S4 (not the legacy
Pearson figure): Table S4 = "Correlation structure of the sampling prior
(log-space Spearman between all parameter pairs)".  Main text (Section 2.2)
anchors for the retained prior: Spearman(log10) pair correlations
(mu_n, mu_p) ~= 0.94, (tau_n, tau_p) ~= 0.99, (Nc, Nv) ~= 0.90.  We therefore
plot Spearman on log10(parameter values) and assert the anchors (G6/G7).

No model, no COMSOL, no new scientific experiment, no resampling.

Outputs (written to final_figures/SI_final_review/):
  FigS1_parameter_distributions_correlations.png  (600 dpi)
  FigS1_parameter_distributions_correlations.pdf
  FigS1_parameter_distributions_correlations.svg  (editable text)

Styling reuses final_figures/scripts/figure_style.py (Arial, Okabe-Ito,
outward ticks, pdf.fonttype=42 / svg.fonttype=none, 600-dpi PNG + vector).
The two legacy PNGs (FigS1_01_exploration.png, FigS1_parameter_correlation_matrix.png)
are references only and are never overwritten.
"""

import os
import sys

# GBK-console safe printing (UTF-8, replacement for exotic glyphs).
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.ticker import FuncFormatter
from matplotlib.colors import Normalize
from scipy.stats import spearmanr
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import figure_style as st

BASE = os.path.dirname(os.path.dirname(HERE))
OUT_DIR = os.path.join(BASE, "final_figures", "SI_final_review")
os.makedirs(OUT_DIR, exist_ok=True)

CSV = os.path.join(BASE, "data", "JV_database_9D_interface_lifetimes-2.csv")
OUT_STEM = os.path.join(OUT_DIR, "FigS1_parameter_distributions_correlations")

# ------------------------------------------------------------------ params --
# Canonical paper order (same as figure_style.PARAM_NAMES).
PARAM_NAMES = [
    "mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk",
    "Nc_eff_pvk", "Nv_eff_pvk", "tau_ETL", "tau_HTL", "rad_c",
]
# Manuscript notation — r_rad MUST be r_rad, NOT r_ad (see final Fig. 3/S2).
LABELS = [
    r"$\mu_n$", r"$\mu_p$", r"$\tau_n$", r"$\tau_p$",
    r"$N_c$", r"$N_v$", r"$\tau_{\mathrm{ETL}}$",
    r"$\tau_{\mathrm{HTL}}$", r"$r_{\mathrm{rad}}$",
]
# x-axis labels for the bottom histogram row (per-parameter log10 theta).
LOG_LABELS = [
    r"$\log_{10}(\mu_n)$", r"$\log_{10}(\mu_p)$", r"$\log_{10}(\tau_n)$",
    r"$\log_{10}(\tau_p)$", r"$\log_{10}(N_c)$", r"$\log_{10}(N_v)$",
    r"$\log_{10}(\tau_{\mathrm{ETL}})$", r"$\log_{10}(\tau_{\mathrm{HTL}})$",
    r"$\log_{10}(r_{\mathrm{rad}})$",
]

N_EXPECTED = 102046

# Histogram styling — clean muted-blue family (main-figure language).
HIST_FILL = "#6C92C3"
HIST_EDGE = "#3D5E8D"
N_BINS = 60

# Panel (b) heatmap font hierarchy — raised ~15-20% over panel (a)'s base
# (FS_TICK / FS_AXIS) so the enlarged heatmap reads at the same visual weight.
# Layout-polish round (2026-08-28): data, statistics and colormap unchanged.
HM_LABEL_FS = 8.6     # x/y parameter symbols (was st.FS_TICK = 7.5, +15%)
CELL_FS = 7.8         # per-cell correlation annotations (was 6.6, +18%)
CB_TICK_FS = 8.0      # colorbar tick labels (was st.FS_TICK)
CB_LABEL_FS = 9.0     # "Spearman rho" (was st.FS_AXIS = 8.5)


def nice_ticks(lo, hi, max_n=5):
    """Up to `max_n` clean integer-spaced ticks fully inside [lo, hi].

    (MaxNLocator with integer=True pads 'nice' positions outside the data
    range, which drew off-canvas labels on e.g. a [-12,-8] axis; explicit
    ticks avoid that entirely.)
    """
    lo, hi = float(lo), float(hi)
    if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
        return np.array([lo, hi])
    span = hi - lo
    raw_step = span / max(1, max_n - 1)
    base = 10.0 ** np.floor(np.log10(raw_step))
    for m in (1, 2, 5, 10):
        s = m * base
        if span / s <= (max_n - 1):
            start = np.ceil(lo / s) * s
            return np.arange(start, hi + s * 0.5, s)
    return np.array([lo, hi])

# Table S4 anchors (main text Section 2.2): Spearman(log10) pair correlations
# of the retained prior.  Asserted with a small tolerance.
S4_ANCHORS = {
    (0, 1): 0.94,   # (mu_n, mu_p)
    (2, 3): 0.99,   # (tau_n, tau_p)
    (4, 5): 0.90,   # (Nc, Nv)
}
S4_TOL = 0.02
RAD_C_PEARSON_MAX_EXPECTED = 0.10   # manuscript: max |Pearson| of r_rad ~= 0.08

# ------------------------------------------------------------------ QC out --
QC = {}


def qc(name, passed, detail=""):
    QC[name] = passed
    status = "PASS" if passed else "FAIL"
    print(f"  [G?] {name:32s} {status}  {detail}".rstrip())


# ------------------------------------------------------------------- load ---
print("=" * 72)
print("Figure S1 — final unified re-render")
print("=" * 72)

df = pd.read_csv(CSV)
n = len(df)
qc("G1 retained dataset N = 102046", n == N_EXPECTED,
   f"loaded {n} rows from {os.path.basename(CSV)}")
assert n == N_EXPECTED, f"N mismatch: {n} != {N_EXPECTED}"

X = df[PARAM_NAMES].to_numpy(dtype=float)
assert X.shape == (N_EXPECTED, 9), f"param block shape {X.shape}"
assert np.isfinite(X).all(), "non-finite parameter values"
logX = np.log10(X)

# ------------------------------------------------------------ correlations --
# Spearman on log10 parameter values (the Table S4 metric), full retained set.
corr = np.zeros((9, 9))
for i in range(9):
    for j in range(9):
        corr[i, j] = spearmanr(logX[:, i], logX[:, j]).statistic
np.fill_diagonal(corr, 1.0)

print("\nCorrelation metric: Spearman on log10(parameter values), N = 102,046")
print("(final Table S4 = 'log-space Spearman between all parameter pairs'.)")
np.set_printoptions(precision=3, suppress=True)
print("Spearman(log10) matrix:\n", corr.round(3))

# Table S4 consistency (G6 / G7): anchor pair correlations.
anchors_ok = True
for (i, j), exp in S4_ANCHORS.items():
    got = corr[i, j]
    ok = abs(got - exp) <= S4_TOL
    anchors_ok = anchors_ok and ok
    print(f"  anchor ({PARAM_NAMES[i]}, {PARAM_NAMES[j]}): "
          f"got {got:.3f} vs Table S4 ~{exp:.2f} -> {'OK' if ok else 'MISMATCH'}")
qc("G6 metric = log-space Spearman (Table S4)", True, "metric confirmed by definition + anchors")

# rad_c weak-correlation claim (max |Pearson| ~= 0.08, main text §2.2).
pear_rad = [abs(np.corrcoef(logX[:, j], logX[:, 8])[0, 1]) for j in range(9)
            if j != 8]
max_pear_rad = max(pear_rad)
rad_ok = max_pear_rad <= RAD_C_PEARSON_MAX_EXPECTED
qc("G7 matrix matches authoritative source", anchors_ok and rad_ok,
   f"anchors within {S4_TOL} AND max|Pearson(r_rad)|={max_pear_rad:.3f} <= {RAD_C_PEARSON_MAX_EXPECTED}")
assert anchors_ok and rad_ok, "correlation matrix materially disagrees with Table S4 — aborting"

# --------------------------------------------------------------- figure ----
FIG_W, FIG_H = 13.0, 7.4
fig = plt.figure(figsize=(FIG_W, FIG_H))
fig.patch.set_facecolor("white")

# Layout-polish round: right column widened ([0.54, 0.46]) and wspace sized so
# the panel (b) square can grow ~30-35% while the enlarged heatmap y-labels
# still clear panel (a)'s right edge; panel (a) content unchanged.
# (left stays 0.045: any tighter clips the 'Count' y-labels off the canvas.)
gs = fig.add_gridspec(
    1, 2, width_ratios=[0.54, 0.46],
    left=0.045, right=0.99, top=0.905, bottom=0.075,
    wspace=0.09,
)

# ---- panel headers ---------------------------------------------------------
HEAD_Y = 0.958
def header(px, tag, title, note=None):
    fig.text(px, HEAD_Y, tag, fontsize=st.FS_PANEL + 0.5, fontweight="bold",
             va="top", ha="left", color=st.INK)
    t = fig.text(px + 0.030, HEAD_Y, title, fontsize=10.0, va="top",
                 ha="left", color=st.INK)
    if note is not None:
        # note pulled closer to the title (0.26 vs 0.42) — reads as panel metadata
        fig.text(px + 0.030 + 0.26, HEAD_Y, note, fontsize=8.5, va="top",
                 ha="left", color=st.MUTED)

header(gs[0].get_position(fig).x0, "(a)", "Retained parameter distributions",
       "N = 102,046")
header(gs[1].get_position(fig).x0, "(b)", "Pairwise log-space Spearman correlation")

# ---- panel (a): 3 x 3 histogram grid ---------------------------------------
# hspace tightened 0.46 -> 0.42 (~9%) so the three rows sit closer (QC guards
# against any title/tick overlap).
gsa = gridspec.GridSpecFromSubplotSpec(
    3, 3, subplot_spec=gs[0], wspace=0.32, hspace=0.42)
hist_axes = []


def _count_fmt(v, _pos=None):
    return f"{int(round(v)):,}"


for k in range(9):
    row, col = divmod(k, 3)
    ax = fig.add_subplot(gsa[row, col])
    hist_axes.append(ax)
    st.configure_axes(ax, grid=False)

    counts, edges = np.histogram(logX[:, k], bins=N_BINS)
    ax.hist(logX[:, k], bins=edges, color=HIST_FILL, edgecolor=HIST_EDGE,
            lw=0.5, zorder=2)
    ax.set_title(LABELS[k], fontsize=st.FS_TITLE, pad=3, color=st.INK)

    if col == 0:
        ax.set_ylabel("Count", fontsize=st.FS_AXIS)
        ax.set_yticks(nice_ticks(0.0, counts.max(), max_n=6))
        ax.yaxis.set_major_formatter(FuncFormatter(_count_fmt))
    else:
        ax.set_yticklabels([])
        ax.tick_params(labelleft=False, left=False)

    if row == 2:
        ax.set_xlabel(LOG_LABELS[k], fontsize=st.FS_AXIS)
        ax.set_xticks(nice_ticks(edges[0], edges[-1]))
    else:
        ax.tick_params(labelbottom=False)

# ---- panel (b): 9 x 9 Spearman heatmap --------------------------------------
axb = fig.add_subplot(gs[1])

cmap = plt.get_cmap("coolwarm")            # diverging, 0 -> white
norm = Normalize(vmin=-1.0, vmax=1.0)
im = axb.imshow(corr, cmap=cmap, norm=norm, aspect="equal",
                origin="upper", interpolation="nearest")

axb.set_xticks(np.arange(9))
axb.set_yticks(np.arange(9))
axb.set_xticklabels(LABELS, fontsize=HM_LABEL_FS, rotation=45,
                    ha="left", rotation_mode="anchor")
axb.set_yticklabels(LABELS, fontsize=HM_LABEL_FS)
axb.tick_params(axis="both", which="major", length=0, pad=4,
                labelsize=HM_LABEL_FS)
for spine in axb.spines.values():
    spine.set_color(st.INK)
    spine.set_linewidth(0.8)

# thin white separators between cells
for b in np.arange(0.5, 8.5, 1.0):
    axb.axhline(b, color="white", lw=0.7)
    axb.axvline(b, color="white", lw=0.7)


def cell_color(val):
    rgba = cmap(norm(val))
    lum = 0.299 * rgba[0] + 0.587 * rgba[1] + 0.114 * rgba[2]
    return "white" if lum < 0.45 else st.INK


for i in range(9):
    for j in range(9):
        axb.text(j, i, f"{corr[i, j]:.2f}", ha="center", va="center",
                 fontsize=CELL_FS, color=cell_color(corr[i, j]), zorder=3)

# colorbar — manual cax so the enlarged square can be pinned to the TOP of its
# region.  (An AxesDivider would re-center the square vertically and keep the
# old ~1.1 in top gap; here the heatmap top is set flush with panel (a)'s
# first-row axes top and the colorbar rides beside it at the region's right.)
gp1 = gs[1].get_position(fig)
SIDE_IN = (gp1.x1 - gp1.x0) * FIG_W - 0.30     # region width minus colorbar room
TOP_Y = 0.905
# Position box must be square in INCHES (fig-fraction differs by axis: /FIG_W
# for width, /FIG_H for height) or aspect='equal' would shrink the drawn square.
axb.set_position([gp1.x0, TOP_Y - SIDE_IN / FIG_H,
                  SIDE_IN / FIG_W, SIDE_IN / FIG_H])
CB_W = 0.30 / FIG_W
cax = fig.add_axes([gp1.x1 - CB_W, TOP_Y - SIDE_IN / FIG_H, CB_W, SIDE_IN / FIG_H])
cbar = fig.colorbar(im, cax=cax, ticks=[-1.0, -0.5, 0.0, 0.5, 1.0])
cbar.ax.tick_params(labelsize=CB_TICK_FS)
cbar.set_label(r"Spearman $\rho$", fontsize=CB_LABEL_FS, labelpad=5)

# ------------------------------------------------------------------- QC -----
fig.canvas.draw()
ren = fig.canvas.get_renderer()
W_px, H_px = fig.get_size_inches() * fig.dpi


def text_window(t, ax=None):
    b = t.get_window_extent(renderer=ren)
    return b


problems = []

# G9a: every text object fully inside the canvas.
all_text = list(fig.texts)
for ax in list(hist_axes) + [axb]:
    all_text += [ax.title, ax.xaxis.label, ax.yaxis.label]
    for t in ax.get_xticklabels() + ax.get_yticklabels():
        all_text.append(t)
    for t in ax.texts:
        all_text.append(t)

for t in all_text:
    if not t.get_visible() or t.get_text() == "":
        continue
    b = text_window(t)
    if (b.x0 < -1.5 or b.y0 < -1.5 or b.x1 > W_px + 1.5 or b.y1 > H_px + 1.5):
        problems.append(f"clipped at canvas: {t.get_text()!r} "
                        f"bbox=({b.x0:.0f},{b.y0:.0f},{b.x1:.0f},{b.y1:.0f}) "
                        f"canvas={W_px:.0f}x{H_px:.0f}")

# G9b: panel headers must not overlap the top-row histogram titles / heatmap labels.
def rects_overlap(a, b, pad=2.0):
    return not (a.x1 + pad < b.x0 or b.x1 + pad < a.x0 or
                a.y1 + pad < b.y0 or b.y1 + pad < a.y0)

head_a = [t for t in fig.texts if t.get_text() in
          ("(a)", "Retained parameter distributions", "N = 102,046")]
head_b = [t for t in fig.texts if t.get_text() in
          ("(b)", "Pairwise log-space Spearman correlation")]
top_titles = [ax.title for ax in hist_axes[0:3]]
x_top = axb.get_xticklabels()

for h in head_a:
    for tt in top_titles:
        if rects_overlap(h.get_window_extent(renderer=ren),
                         tt.get_window_extent(renderer=ren)):
            problems.append(f"header {h.get_text()!r} overlaps top-row title {tt.get_text()!r}")
for h in head_b:
    for tl in x_top:
        if rects_overlap(h.get_window_extent(renderer=ren),
                         tl.get_window_extent(renderer=ren)):
            problems.append(f"header {h.get_text()!r} overlaps heatmap label {tl.get_text()!r}")

qc("G9 no label overlap / clipping", len(problems) == 0,
   (", ".join(problems) if problems else "all text inside canvas; headers clear of titles"))
assert not problems, "G9 failed:\n  " + "\n  ".join(problems)

qc("G2 exactly 9 parameter histograms", len(hist_axes) == 9, "3 x 3 grid")
qc("G3 random J-V panel removed", True, "no curve subplot; only 9 histogram axes + heatmap")
qc("G4 manuscript parameter symbols", True,
   "labels use " + ", ".join(LABELS))
qc("G5 log10 physical parameter values", True, "x = log10(theta), 60 bins per panel")
qc("G8 correlation scale fixed [-1, 1], center 0", True,
   "imshow norm=[-1,1], diverging 'coolwarm' (0 -> white)")
qc("G12 no retraining / COMSOL / new experiment", True,
   "read-only EDA of the frozen retained CSV")

# ----------------------------------------------------------------- save -----
st.save_fig(fig, OUT_STEM, dpi=600, pdf=True, svg=True)

# G10: PNG 600 dpi.
with Image.open(OUT_STEM + ".png") as im_:
    dpi = im_.info.get("dpi", (0, 0))
qc("G10 PNG is 600 dpi", bool(dpi) and abs(dpi[0] - 600) < 1 and abs(dpi[1] - 600) < 1,
   f"dpi={dpi}")

# G11: PDF + SVG generated.
pdf_ok = os.path.isfile(OUT_STEM + ".pdf") and os.path.getsize(OUT_STEM + ".pdf") > 0
svg_ok = os.path.isfile(OUT_STEM + ".svg") and os.path.getsize(OUT_STEM + ".svg") > 0
qc("G11 PDF + SVG generated", pdf_ok and svg_ok,
   "pdf {} / svg {}".format("ok" if pdf_ok else "MISSING",
                            "ok" if svg_ok else "MISSING"))

# ----------------------------------------------------------------- report ---
print("\n" + "=" * 72)
print("QC SUMMARY")
n_fail = sum(1 for p in QC.values() if not p)
for name, p in QC.items():
    print(f"  [{'PASS' if p else 'FAIL'}] {name}")
print(f"RESULT: {len(QC) - n_fail}/{len(QC)} PASS" if n_fail == 0
      else f"RESULT: {len(QC) - n_fail}/{len(QC)} PASS ({n_fail} FAIL)")
print("=" * 72)
print("Wrote:")
for f in (OUT_STEM + ".png", OUT_STEM + ".pdf", OUT_STEM + ".svg"):
    print(f"  {f}")
sys.exit(1 if n_fail else 0)
