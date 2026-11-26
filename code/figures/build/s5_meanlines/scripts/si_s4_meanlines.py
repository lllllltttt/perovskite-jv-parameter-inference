# -*- coding: utf-8 -*-
"""SI Figure S4 - nine predictive-scale histograms, each with a vertical
dashed line at the mean of sigma_theta.

Baseline (unchanged in every respect except the new line):
  20261117_si_s4_s5_s8/out/S4_01..09  --  the approved nine standalone panels
  (same frozen data, 40 bins, bar colour/alpha, xlim 0-0.5, auto y, four-sided
  frame #000000 0.8 pt, ticks left+bottom, Arial tick numbers as outlines,
  canvas 243.24 x 169.32 pt, plot area 210.997 x 152.851 pt).

The only addition:
  one axvline per panel at x = np.mean(sigma[:, i]) computed in float64 from
  the frozen 15,307-row test sigma array (full precision, no rounding),
  colour #CA7241, linewidth 1.2 pt, dashed, spanning the full plot height,
  drawn above the bars, no legend, no text.

QC gates asserted at the end:
  G1  every mean reproduces evaluation_fixed/sigma_statistics_fixed.csv
      (|diff| < 2e-5) and rounds to the supervisor's 3-dp list
  G2  canvas / plot area identical to the approved panels (<= 1e-3 pt)
  G3  x/y limits and all 40 bar rectangles identical with and without the line
  G4  the line is at the full-precision mean, not the 3-dp value
  G5  Arial resolves to arial.ttf; SVG contains no <text> (outlines only)
  G6  every panel keeps >= 0.8 pt clearance (nothing clipped)
"""
import os

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

BASE = r"E:\project\work1"
ROOT = os.path.join(BASE, "20261119_si_s4_meanlines")
OUT = os.path.join(ROOT, "out")
WORK = os.path.join(ROOT, "work")
os.makedirs(OUT, exist_ok=True)
os.makedirs(WORK, exist_ok=True)

NPZ_PATH = os.path.join(BASE, "data", "dataset_normalized.npz")
MODEL_DIR = os.path.join(BASE, "data", "vae-v6", "vae-v6")
SIG_CSV = os.path.join(BASE, "evaluation_fixed", "sigma_statistics_fixed.csv")

PARAMS = ["mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk",
          "Nc_eff_pvk", "Nv_eff_pvk", "tau_ETL", "tau_HTL", "rad_c"]
SHORT = ["mu_n", "mu_p", "tau_n", "tau_p", "Nc", "Nv",
         "tau_ETL", "tau_HTL", "rad_c"]
SYMBOL = ["\u03bc_n", "\u03bc_p", "\u03c4_n", "\u03c4_p", "N_c", "N_v",
          "\u03c4_ETL", "\u03c4_HTL", "r_rad"]
QUOTED_3DP = [0.093, 0.087, 0.109, 0.109, 0.075, 0.081, 0.229, 0.191, 0.228]

C_BLUE = "#0072B2"      # unchanged bar colour
C_MEAN = "#CA7241"      # new mean line
FRAME = "#000000"       # spines / ticks exactly as in the approved panels
LINE_LW = 1.2
LINE_DASH = (0, (4.0, 2.0))   # 4 pt dash / 2 pt gap, scaled by lw -> 4.8/2.4
LINE_ZORDER = 2.4       # above bars (patches = 1), below spines/ticks (2.5)

# plot area of one panel in the approved grid (pt) + tick font size
W_PT, H_PT, FS = 210.997, 152.851, 8.0
CANVAS_PT = (243.24, 169.32)          # approved canvas, pt
AXES_BOX_PT = (25.42, 2.14, 236.417, 154.991)   # left, top, right, bottom (SVG)
N_BINS = 40
X_MAX = 0.5


# --------------------------------------------------------------- font check --
def require_arial():
    path = font_manager.findfont(font_manager.FontProperties(family="Arial"))
    print("Arial resolves to:", path)
    if "arial" not in os.path.basename(path).lower():
        raise SystemExit("FATAL: Arial not available (resolved to %s)." % path)
    return path


# ------------------------------------------------------------------ data ----
def load_sigma():
    """The frozen predictive scale array, exactly as used for the approved
    S4_01..09 panels (validated against the frozen statistics CSV)."""
    cache = os.path.join(WORK, "sigma_error.npz")
    if os.path.exists(cache):
        sigma = np.load(cache)["sigma"]
        print("cached sigma:", sigma.shape)
    else:
        import tensorflow as tf
        from tensorflow import keras
        from tensorflow.keras import layers

        class Sampling(layers.Layer):
            def call(self, inputs):
                z_mean, z_log_var = inputs
                eps = tf.random.normal(shape=tf.shape(z_mean))
                return z_mean + tf.exp(0.5 * z_log_var) * eps

        data = np.load(NPZ_PATH, allow_pickle=True)
        J_test = data["J_test"].astype(np.float32)
        encoder = keras.models.load_model(
            os.path.join(MODEL_DIR, "encoder.h5"),
            custom_objects={"Sampling": Sampling})
        head = keras.models.load_model(os.path.join(MODEL_DIR, "param_head.h5"))
        z_mean, _, _ = encoder.predict(J_test, verbose=0)
        _, sigma_raw = head.predict(z_mean, verbose=0)
        s = tf.nn.softplus(sigma_raw).numpy() + 0.01
        sigma = np.clip(s, 0.01, 1.0).astype(np.float64)
        np.savez(cache, sigma=sigma)
        print("computed sigma:", sigma.shape)

    fs = pd.read_csv(SIG_CSV)
    assert list(fs["parameter"]) == PARAMS
    for i, p in enumerate(PARAMS):
        s = sigma[:, i]
        row = fs.iloc[i]
        for got, key in ((np.mean(s), "mean"), (np.median(s), "median"),
                         (np.percentile(s, 25), "q25"),
                         (np.percentile(s, 75), "q75"),
                         (s.min(), "min"), (s.max(), "max")):
            assert abs(got - row[key]) < 2e-5, (p, key, got, row[key])
    print("  cross-check vs frozen sigma_statistics_fixed.csv: PASS")
    return sigma


# --------------------------------------------------------------- renderer ---
def style(ax):
    ax.tick_params(axis="both", which="both", direction="out", length=3.5,
                   width=0.8, color=FRAME, labelcolor="#1a1a1a",
                   top=False, right=False, labelsize=FS)
    for s in ax.spines.values():
        s.set_visible(True)
        s.set_color(FRAME)
        s.set_linewidth(0.8)      # approved panels: #000000, 0.8 pt


def draw_s4(ax, i, means, with_line):
    """The approved S4 panel drawing; `with_line` only adds the mean marker."""
    ax.hist(SIGMA[:, i], bins=N_BINS, color=C_BLUE, alpha=0.7,
            edgecolor="white", linewidth=0.4)
    ax.set_xlim(0.0, X_MAX)
    if with_line:
        ax.axvline(means[i], color=C_MEAN, linewidth=LINE_LW,
                   linestyle=LINE_DASH, zorder=LINE_ZORDER,
                   solid_capstyle="butt", dash_capstyle="butt")


def make_figure(margins, i, means, with_line):
    L, R, T, B = margins
    fig = plt.figure(figsize=((W_PT + L + R) / 72.0, (H_PT + T + B) / 72.0))
    ax = fig.add_axes([L / (W_PT + L + R), B / (H_PT + T + B),
                       W_PT / (W_PT + L + R), H_PT / (H_PT + T + B)])
    draw_s4(ax, i, means, with_line)
    style(ax)
    fig.patch.set_facecolor("white")
    return fig, ax


def probe_margins(i, means):
    """Render once with generous margins and report what the labels need."""
    L0 = R0 = T0 = B0 = 40.0
    fig, ax = make_figure((L0, R0, T0, B0), i, means, True)
    tmp = os.path.join(WORK, "_probe_S4_%02d.png" % (i + 1))
    fig.savefig(tmp, dpi=300, facecolor="white")
    plt.close(fig)
    a = np.asarray(plt.imread(tmp))
    g255 = (a[..., :3].mean(axis=2) * 255).astype(int)
    mk = (255 - g255) > 8
    rows = np.where(mk.any(axis=1))[0]
    cols = np.where(mk.any(axis=0))[0]
    s = 300 / 72.0
    pad = 1.5
    return (max(1.0, L0 - cols[0] / s + pad),
            max(1.0, (cols[-1] + 1) / s - (L0 + W_PT) + pad),
            max(1.0, T0 - rows[0] / s + pad),
            max(1.0, (rows[-1] + 1) / s - (T0 + H_PT) + pad))


def patch_rects(ax):
    return [(round(p.get_x(), 12), round(p.get_y(), 12),
             round(p.get_width(), 12), round(p.get_height(), 12))
            for p in ax.patches]


def main():
    require_arial()
    plt.rcParams.update({
        "font.family": "Arial",
        "font.size": 8,
        "axes.linewidth": 0.5,
        "svg.fonttype": "path",     # tick numbers become outlines
        "pdf.fonttype": 42,
        "axes.unicode_minus": True,
    })

    global SIGMA
    SIGMA = load_sigma()

    # ---- G1: full-precision arithmetic means ------------------------------
    means = [float(np.mean(SIGMA[:, i])) for i in range(9)]
    frozen = pd.read_csv(SIG_CSV)
    print("\n%-8s %-18s %-8s %-8s %-8s" %
          ("panel", "mean (full precision)", "3 dp", "quoted", "|diff|"))
    for i in range(9):
        csv_mean = float(frozen.iloc[i]["mean"])
        assert abs(means[i] - csv_mean) < 2e-5
        assert round(means[i], 3) == QUOTED_3DP[i], (SHORT[i], means[i])
        print("%-8s %-18.10f %-8.3f %-8.3f %.1e" %
              ("S4_%02d" % (i + 1), means[i], round(means[i], 3),
               QUOTED_3DP[i], abs(means[i] - csv_mean)))

    # ---- margins -----------------------------------------------------------
    need = [probe_margins(i, means) for i in range(9)]
    L = max(n[0] for n in need)
    R = max(n[1] for n in need)
    T = max(n[2] for n in need)
    B = max(n[3] for n in need)
    print("\nS4 margins L%.2f R%.2f T%.2f B%.2f" % (L, R, T, B))
    cw, ch = W_PT + L + R, H_PT + T + B
    assert abs(cw - CANVAS_PT[0]) < 1e-3 and abs(ch - CANVAS_PT[1]) < 1e-3, \
        ("canvas changed", (cw, ch), CANVAS_PT)

    # ---- render ------------------------------------------------------------
    ok = []
    detail = []

    def gate(name, cond):
        ok.append(bool(cond))
        detail.append((name, bool(cond)))

    for i in range(9):
        fig, ax = make_figure((L, R, T, B), i, means, True)
        l, t, r, b = ax.get_position().x0 * cw, (1 - ax.get_position().y1) * ch, \
            ax.get_position().x1 * cw, (1 - ax.get_position().y0) * ch
        assert max(abs(l - AXES_BOX_PT[0]), abs(t - AXES_BOX_PT[1]),
                   abs(r - AXES_BOX_PT[2]), abs(b - AXES_BOX_PT[3])) < 1e-3

        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        rects = patch_rects(ax)
        line = ax.lines[-1]
        gate("S4_%02d mean x exact" % (i + 1),
             line.get_xdata()[0] == means[i])               # exact, no rounding
        gate("S4_%02d colour" % (i + 1),
             matplotlib.colors.to_rgba(line.get_color())
             == matplotlib.colors.to_rgba(C_MEAN))
        gate("S4_%02d lw" % (i + 1),
             abs(line.get_linewidth() - LINE_LW) < 1e-12)
        gate("S4_%02d dashed" % (i + 1),
             line.get_linestyle() == "--"
             and line._unscaled_dash_pattern == (0.0, (4.0, 2.0)))
        gate("S4_%02d above bars" % (i + 1),
             line.get_zorder() > ax.patches[0].get_zorder())
        gate("S4_%02d 40 bars" % (i + 1), len(ax.patches) == N_BINS == len(rects))
        gate("S4_%02d no legend" % (i + 1),
             ax.get_legend_handles_labels() == ([], []))

        stem = os.path.join(OUT, "S4_%02d" % (i + 1))
        fig.savefig(stem + ".svg", dpi=600, facecolor="white")
        fig.savefig(stem + "_600dpi.png", dpi=600, facecolor="white")
        plt.close(fig)

        # same panel without the line, same margins -> geometry must not move
        figr, axr = make_figure((L, R, T, B), i, means, False)
        assert axr.get_xlim() == xlim and axr.get_ylim() == ylim, i
        assert patch_rects(axr) == rects, i
        figr.savefig(os.path.join(WORK, "_ref_S4_%02d.png" % (i + 1)),
                     dpi=600, facecolor="white")
        plt.close(figr)

    print("\npanels written to", OUT)
    for name, cond in detail:
        if not cond:
            print("  FAIL", name)
    print("QC gates: %d/%d PASS" % (sum(ok), len(ok)))
    if not all(ok):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
