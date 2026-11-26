# -*- coding: utf-8 -*-
"""
fig3_pair_analysis_v2.py — corrected nearest-neighbour pair analysis, DESCRIPTIVE.
==================================================================================
Changes from the phase-1 version, per the review:

  * The paired Wilcoxon signed-rank tests and the per-pair percentile bootstrap
    intervals are WITHDRAWN. They treated the tier pairs as independent draws,
    but the pairs share samples (closest 1%: 112 pairs over 196 distinct
    samples; closest 0.5%: 56 over 99; closest 0.1%: 11 over 21). Both are
    therefore invalid as stated and are not reported anywhere in v2. No
    replacement significance test or resampling scheme is introduced.
  * The distribution preview is an ECDF over the FULL range instead of a
    histogram truncated at 2.0. The truncation silently dropped 16.9%, 19.0%
    and 20.3% of the mobility / lifetime / DOS ratio values and re-normalised
    the density on the retained part.
  * Dependence inside each tier is measured and reported explicitly.

Kept, as instructed: distributions, medians, quartiles, pair counts, distinct
sample counts, and the per-pair fraction whose shared-scale difference is
smaller than its matching log-ratio difference.

Read-only on the frozen project; writes only inside this v2 directory.
"""
import gzip
import os
import sys

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lib_v2 as L
import figstyle as st

OUT = os.path.dirname(HERE)
DATADIR = os.path.join(OUT, "data_used")
FIGDIR = os.path.join(OUT, "figures")
os.makedirs(DATADIR, exist_ok=True)
os.makedirs(FIGDIR, exist_ok=True)

C_SHARED = st.OKABE_ITO[0]      # blue
C_RATIO = st.OKABE_ITO[3]       # orange
C_RAND = "#9a9a9a"              # grey


def pair_frame(C, i, j):
    """Signed and absolute coordinate differences for one pair set."""
    d = {}
    for cid, fam, p, q in L.COORDS:
        col = L.COORD_IDS.index(cid)
        d[cid] = C[i, col] - C[j, col]
    return d


# panel titles: the coordinate symbol, then the parameter family it belongs to
COORD_TITLE = {
    "a_mu":  r"(a)  $a_{\mu}$   mobility",
    "r_mu":  r"(b)  $r_{\mu}$   mobility",
    "a_tau": r"(c)  $a_{\tau}$   lifetime",
    "r_tau": r"(d)  $r_{\tau}$   lifetime",
    # The DOS pair is the one coordinate the SI names with a D rather than by
    # its parameters: Tables S11 and S14 both write a_D and r_D, so the panels
    # use those letters too. (a_N / r_N appeared only here.)
    "a_D":   r"(e)  $a_{D}$   DOS",
    "r_D":   r"(f)  $r_{D}$   DOS",
}


def build_ecdf(size, P, RD, n_random):
    """Supplementary Figure S7 — full-range ECDF, nearest-neighbour vs random.

    One panel per paired coordinate. Each panel is scaled to the complete range
    of BOTH groups, so no value is off-canvas and both curves reach 1; the six
    coordinates have different dispersions in this normalisation, so the panels
    deliberately do not share an x range and the caption says so.
    """
    w = st.set_fig_width(size)
    # 0.700 rather than 0.660, and gridspec bottom 0.235 rather than 0.215:
    # the footnote is four lines at the 7 pt floor, and the band between the
    # bottom row's x-axis label and the canvas edge has to hold all four.
    fig = plt.figure(figsize=(w, w * 0.740))
    gs = fig.add_gridspec(2, 3, left=0.088, right=0.988, top=0.910,
                          bottom=0.245, wspace=0.30, hspace=0.55)
    for c, cid in enumerate(L.COORD_IDS):
        ax = fig.add_subplot(gs[c // 3, c % 3])
        col = C_SHARED if cid.startswith("a_") else C_RATIO
        nnv = np.sort(P["norm_" + cid].values)
        rnv = np.sort(RD["norm_" + cid].values)
        ax.plot(rnv, np.arange(1, rnv.size + 1) / rnv.size, color=C_RAND,
                lw=1.3, zorder=2, label="random pairs")
        ax.plot(nnv, np.arange(1, nnv.size + 1) / nnv.size, color=col,
                lw=1.6, zorder=3, label="nearest-neighbour pairs")
        ax.axvline(1.0, color=st.MUTED, ls=":", lw=1.0, zorder=1)
        # The dotted line is the random-pair median. It used to carry its own
        # grey "1" at the foot of the line, but that label sat inside panel
        # (a)'s legend box and was half covered by the frame -- a 27 px^2
        # glyph-on-glyph overlap that neither qa_layout (text-on-text, but the
        # legend's text is a separate artist) nor any fit check could see. A
        # unit x locator says the same thing in all six panels with no text
        # inside the axes at all: every panel then has a tick exactly under the
        # dotted line. It also replaces the 0/2/4 spacing of the three
        # log-ratio panels with 0..n, so "1" is labelled there too.
        ax.xaxis.set_major_locator(MultipleLocator(1.0))
        hi = max(nnv.max(), rnv.max())
        ax.set_xlim(0.0, hi * 1.02)      # whole range of BOTH groups
        ax.set_ylim(0.0, 1.0)            # every ECDF accumulates to 1
        ax.set_title(COORD_TITLE[cid], fontsize=st.FS_ANNOT, loc="left",
                     color=col, pad=3.0)
        ax.set_xlabel(r"$|\Delta\mathrm{coord}|$ / random median",
                      fontsize=st.FS_ANNOT)
        if c % 3 == 0:
            ax.set_ylabel("cumulative fraction", fontsize=st.FS_ANNOT)
        ax.tick_params(labelsize=st.FS_TICK - 1)
        if c == 0:
            # The pair counts moved out of the labels and into the caption.
            # With them the two entries render 189 px against this panel's
            # 177 px, so loc="lower right" pushed the box 16.5 px out through
            # the left spine, where its translucent patch sat over the y tick
            # label "0.2"; the counts are in the caption now and the box is
            # 130 px, inside the panel with room to spare. The frame is opaque
            # (alpha 1.0) rather than the 0.92 it used to be: at 0.92 the
            # dotted line showed through the legend text as a ghost instead of
            # being cleanly masked.
            ax.legend(fontsize=st.FS_ANNOT, loc="lower right",
                      frameon=True, facecolor="white", edgecolor="none",
                      framealpha=1.0, handlelength=1.5, handletextpad=0.5,
                      borderpad=0.3)
        st.configure_axes(ax)

    # Four lines, not two. At the 7 pt floor the two-line version measured
    # 866 px against this figure's 709 px canvas: the string is centred, so it
    # ran 0.79 in past BOTH edges and savefig(bbox_inches="tight") grew the
    # delivered PNG by 1.6 in. The same sentence is re-wrapped, not shortened.
    fig.text(0.5, 0.160,
             "x axis: absolute difference in the coordinate, divided by the "
             "median absolute difference of the same coordinate\n"
             "over the %s random pairs (seed %d); 1 (dotted) is therefore the "
             "random-pair median.\n"
             "Every value of both sets is drawn — no truncation, no dropped "
             "points — and each panel is scaled to the full\n"
             "range of its own two groups, so the six x ranges differ."
             % ("{:,}".format(n_random), L.RANDOM_SEED),
             ha="center", va="top", fontsize=st.FS_ANNOT, color=st.MUTED,
             linespacing=1.50)

    stem = os.path.join(FIGDIR, "FigureS7_ecdf"
                        + ("_large" if size == "large" else ""))
    st.save_fig(fig, stem)
    print("wrote:", stem)


def main():
    F = L.load_frozen()
    Lg, Jn = F["L"], F["Jn"]
    C = L.coordinates(Lg)
    N = Lg.shape[0]

    # ---------------------------------------------------- 1. link structure --
    nn, dJ_dir = L.nearest_neighbours(Jn)
    ni, nj, first = L.dedup_undirected(nn, N)
    print("[links] test curves (directed links)          : %d" % N)
    print("[links] mutually-nearest pairs                : %d"
          % int(np.sum(nn[nn] == np.arange(N))))
    print("[links] unique undirected edges after dedup   : %d" % ni.size)
    print("[links] distinct samples touched by the edges : %d"
          % np.unique(np.concatenate([ni, nj])).size)
    deg = np.bincount(np.concatenate([ni, nj]), minlength=N)
    print("[links] samples in >1 edge                    : %d"
          % int(np.sum(deg > 1)))
    print("[links] max edges on one sample               : %d" % int(deg.max()))

    # independent re-check against the phase-1 pair set
    v1 = L.read_v1_pairs()
    v1_keys = set(zip(v1["i"].astype(int), v1["j"].astype(int)))
    new_keys = set(zip(ni.tolist(), nj.tolist()))
    print("[links] pair set identical to phase 1         : %s"
          % (v1_keys == new_keys))

    # ------------------------------------------------- 2. per-pair values ----
    DD = pair_frame(C, ni, nj)                     # signed differences
    P = pd.DataFrame({"i": ni, "j": nj,
                      "dJ_rmse": np.sqrt(np.sum((Jn[ni] - Jn[nj]) ** 2,
                                                axis=1) / Jn.shape[1])})
    for cid in L.COORD_IDS:
        P["d_" + cid] = DD[cid]
        P["absd_" + cid] = np.abs(DD[cid])

    # ------------------------------------------------- 3. random baseline ----
    ra, rb = L.random_pairs(N)
    print("\n[random] rng=np.random.default_rng(%d); %d ordered index pairs "
          "drawn uniformly, self-pairs dropped -> %d retained"
          % (L.RANDOM_SEED, L.N_RANDOM, ra.size))
    DR = pair_frame(C, ra, rb)
    RD = pd.DataFrame({"i": ra, "j": rb})
    for cid in L.COORD_IDS:
        RD["absd_" + cid] = np.abs(DR[cid])
    RD["dJ_rmse"] = np.sqrt(np.sum((Jn[ra] - Jn[rb]) ** 2, axis=1) / Jn.shape[1])

    rand_med = {cid: float(np.median(RD["absd_" + cid])) for cid in L.COORD_IDS}
    for cid in L.COORD_IDS:
        P["norm_" + cid] = P["absd_" + cid] / rand_med[cid]
    for cid in L.COORD_IDS:
        RD["norm_" + cid] = RD["absd_" + cid] / rand_med[cid]
    print("[random] normalisation denominators (median |d| of random pairs):")
    for cid in L.COORD_IDS:
        print("   %-6s %.4f" % (cid, rand_med[cid]))

    # ------------------------------------- 4. descriptive tier summaries ----
    order = np.argsort(P["dJ_rmse"].values, kind="stable")
    rows = []

    def describe(tag, sel):
        i_arr, j_arr = P["i"].values[sel], P["j"].values[sel]
        cnt = np.bincount(np.concatenate([i_arr, j_arr]), minlength=N)
        touched = cnt[cnt > 0]
        r = dict(set=tag, n_pairs=int(sel.size),
                 distinct_samples=int(touched.size),
                 samples_in_multiple_pairs=int(np.sum(cnt > 1)),
                 max_pairs_per_sample=int(touched.max()) if touched.size else 0,
                 median_dJ=float(np.median(P["dJ_rmse"].values[sel])))
        for cid in L.COORD_IDS:
            v = P["absd_" + cid].values[sel]
            r["median_absd_" + cid] = float(np.median(v))
            r["q25_absd_" + cid] = float(np.percentile(v, 25))
            r["q75_absd_" + cid] = float(np.percentile(v, 75))
            r["median_norm_" + cid] = float(np.median(v) / rand_med[cid])
        return r

    rows.append(describe("all corrected pairs", order))
    for name, frac in L.TIERS:
        k = L.tier_k(len(P), frac)
        rows.append(describe(name, order[:k]))
    S = pd.DataFrame(rows)
    S.to_csv(os.path.join(DATADIR, "fig3_pair_summary_v2.csv"), index=False)

    print("\n" + "=" * 104)
    print("DESCRIPTIVE SUMMARY — median |dcoord| / median |dcoord| of random pairs")
    print("(a value < 1 means the nearest-neighbour pairs are closer than random "
          "pairs on that coordinate)")
    print("=" * 104)
    print("%-20s %6s %8s %8s | %-17s | %-17s | %-17s"
          % ("set", "pairs", "samples", "rep.", "mobility a | r",
             "lifetime a | r", "DOS a | r"))
    for _, r in S.iterrows():
        print("%-20s %6d %8d %8d | %6.3f |%6.3f   | %6.3f |%6.3f   | "
              "%6.3f |%6.3f" % (
                  r["set"], r["n_pairs"], r["distinct_samples"],
                  r["samples_in_multiple_pairs"],
                  r["median_norm_a_mu"], r["median_norm_r_mu"],
                  r["median_norm_a_tau"], r["median_norm_r_tau"],
                  r["median_norm_a_D"], r["median_norm_r_D"]))
    print("\nraw medians in physical log10 units (unit-basis dependent for a only):")
    print("%-20s %6s | %-17s | %-17s | %-17s"
          % ("set", "pairs", "mobility a | r", "lifetime a | r", "DOS a | r"))
    for _, r in S.iterrows():
        print("%-20s %6d | %6.3f |%6.3f   | %6.3f |%6.3f   | %6.3f |%6.3f"
              % (r["set"], r["n_pairs"], r["median_absd_a_mu"],
                 r["median_absd_r_mu"], r["median_absd_a_tau"],
                 r["median_absd_r_tau"], r["median_absd_a_D"],
                 r["median_absd_r_D"]))

    print("\ndependence inside the tiers (the reason the v1 tests were withdrawn):")
    for _, r in S.iterrows():
        if r["set"] == "all corrected pairs":
            continue
        print("   %-16s %4d pairs over %4d distinct samples; %3d samples sit in "
              ">1 pair (max %d)"
              % (r["set"], r["n_pairs"], r["distinct_samples"],
                 r["samples_in_multiple_pairs"], r["max_pairs_per_sample"]))

    # ------------------------------- 5. per-pair fraction, common scale -----
    print("\nper-pair fraction whose shared-scale difference is smaller than its "
          "matching log-ratio difference (baseline-normalised):")
    frows = []
    for fam, ca, cr in (("mobility", "a_mu", "r_mu"),
                        ("lifetime", "a_tau", "r_tau"), ("DOS", "a_D", "r_D")):
        fr = float(np.mean(P["norm_" + ca] < P["norm_" + cr]))
        frows.append(dict(family=fam, frac_a_lt_r=fr, n_pairs=int(len(P))))
        print("   %-9s %.4f   (n = %d pairs)" % (fam, fr, len(P)))
    pd.DataFrame(frows).to_csv(
        os.path.join(DATADIR, "fig3_per_pair_fraction_v2.csv"), index=False)

    # ---------------------------------------------- 6. affected statistics --
    from scipy.stats import spearmanr, pearsonr
    aff = []
    for name, frac in [("all corrected pairs", None)] + L.TIERS:
        sel = order if frac is None else order[:L.tier_k(len(P), frac)]
        dJ = P["dJ_rmse"].values[sel]
        dTh = np.sqrt(np.mean(
            (F["params_test"][P["i"].values[sel]]
             - F["params_test"][P["j"].values[sel]]) ** 2, axis=1))
        aff.append(dict(set=name, n_pairs=int(sel.size),
                        median_dJ=float(np.median(dJ)),
                        median_dTheta=float(np.median(dTh)),
                        spearman_dJ_dTheta=float(spearmanr(dJ, dTh)[0]),
                        pearson_dJ_dTheta=float(pearsonr(dJ, dTh)[0])))
    A = pd.DataFrame(aff)
    A.to_csv(os.path.join(DATADIR, "fig3_affected_statistics_v2.csv"), index=False)

    # ---------------------------------------------------- 7. write sources --
    P.to_csv(os.path.join(DATADIR, "fig3_pairs_v2.csv"), index=False)
    pd.DataFrame([dict(coordinate=c, median_absd_random=rand_med[c],
                       n_random_pairs=int(ra.size),
                       random_seed=L.RANDOM_SEED)
                  for c in L.COORD_IDS]).to_csv(
        os.path.join(DATADIR, "fig3_random_baseline_v2.csv"), index=False)

    # (8.2) the random pairs actually used, so the baseline can be re-run
    cols = ["i", "j"] + ["absd_" + c for c in L.COORD_IDS] \
        + ["norm_" + c for c in L.COORD_IDS]
    RD[cols].to_csv(os.path.join(DATADIR, "fig3_random_pairs.csv.gz"),
                    index=False, compression="gzip")

    # (8.6) directed links so the directed -> undirected dedup is auditable
    rep = np.zeros(N, dtype=bool)
    rep[first] = True
    pd.DataFrame(dict(
        test_index=np.arange(N), nn_index=nn, dJ_rmse_directed=dJ_dir,
        is_mutual=(nn[nn] == np.arange(N)),
        edge_lo=np.minimum(np.arange(N), nn),
        edge_hi=np.maximum(np.arange(N), nn),
        is_dedup_representative=rep)).to_csv(
        os.path.join(DATADIR, "nearest_neighbour_links.csv"), index=False)

    S.to_csv(os.path.join(DATADIR, "fig3_tier_samples_v2.csv"), index=False)

    # ============================================ 8. Figure S7: ECDF ========
    # This replaced a histogram of the nearest-neighbour ratio coordinates that
    # was truncated at 2.0. The truncation silently dropped 16.9%, 19.0% and
    # 20.3% of the three ratio values and re-normalised the density on what was
    # left, which made the nearest-neighbour and random distributions look
    # closer than they are. An ECDF over the full range of both groups shows
    # every point and is the honest replacement.
    for size in ("journal", "large"):
        build_ecdf(size, P, RD, int(ra.size))
    print("\nwrote: figures/FigureS7_ecdf{,_large}.{png,pdf,svg}")
    print("wrote 8 source tables + fig3_random_pairs.csv.gz")


if __name__ == "__main__":
    main()
