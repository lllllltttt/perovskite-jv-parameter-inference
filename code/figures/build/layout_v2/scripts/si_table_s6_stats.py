# -*- coding: utf-8 -*-
"""
si_table_s6_stats.py — Table S6 (nearest-neighbour collision statistics)
recomputed under the mentor's corrected deduplication rule.
========================================================================
Why this script exists
----------------------
The archived Table S6 block was produced by

    keep = np.arange(N) < nn_idx          # exp4_lib.dedup

which keeps a directed link only when it points upward (i < NN(i)). An
unordered edge {i, j} whose only directed link is the downward one is then
thrown away, so the archived table describes 7,666 pairs while the set of
distinct nearest-neighbour edges has 11,245 members. Every count, quantile
and tier size in the archived block is therefore a statistic of the wrong
pair set.

The corrected rule, applied uniformly (and already applied to Table S10):

    (lo, hi) = (min(i, nn[i]), max(i, nn[i]))   ->   unique unordered set
    key = lo * N + hi ; np.unique(key, return_index=True)

What is NOT changed
-------------------
The metric (M1, the paper metric), the parameter distance d_Theta, the
random-pair baseline, the tier rule and the ambiguity definitions are the
archived ones. Only the pair set, and therefore the statistics computed on
it, change. The directed nearest-neighbour search is imported from exp4_lib
and asserted against the archived `directed_nn_M1.csv`, so the metric cannot
drift while the dedup rule is fixed.

No p-value is reported anywhere in this table. The pairs share samples (a
curve may belong to up to 5 edges), so they are not independent observations
and a significance test on them would not be interpretable; the manuscript
withdraws those statistics for this analysis.

Read-only on the frozen project; writes only inside this delivery directory.
"""
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, pearsonr

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

BASE = r"E:\project\work1"
EXP4 = os.path.join(BASE, "reviewer_experiments", "exp4_collision_metric_robustness")
sys.path.insert(0, os.path.join(EXP4, "scripts"))
import exp4_lib as E4                                     # noqa: E402

import lib_v2 as L                                        # noqa: E402

OUT = os.path.dirname(HERE)
DATADIR = os.path.join(OUT, "data_used")
os.makedirs(DATADIR, exist_ok=True)

# the five representative cases tabulated by the archived Table S6 (T6.6)
ARCHIVED_CASES = [("A", 3416, 7166), ("B", 1010, 2641), ("C", 8271, 10258),
                  ("D", 6361, 12951), ("E", 2890, 5067)]
# the two cases Figure 3 actually draws, selected by the stated rule from the
# closest 1% of the corrected pair set
FIGURE_CASES = [("(a)", 2890, 5067, "mobility log-ratio"),
                ("(b)", 500, 4560, "lifetime log-ratio")]
SAME_SIGN_PAIRS = [("mu_n_pvk", "mu_p_pvk"), ("tau_n_pvk", "tau_p_pvk"),
                   ("Nc_eff_pvk", "Nv_eff_pvk"), ("tau_n_pvk", "tau_ETL"),
                   ("tau_n_pvk", "tau_HTL"), ("rad_c", "tau_n_pvk"),
                   ("rad_c", "tau_ETL")]
TIERS = [("closest 10%", 0.10), ("closest 5%", 0.05), ("closest 1%", 0.01),
         ("closest 0.5%", 0.005), ("closest 0.1%", 0.001)]


def dist_stats(v, name):
    """The archived T6.1/T6.2 row set: count, mean, std, min, quartiles."""
    q = np.percentile(v, [25, 50, 75, 90, 99])
    return pd.DataFrame(dict(statistic=["Count", "Mean", "Std", "Min",
                                        "25%", "50%", "75%", "90%", "99%",
                                        "Max"],
                             value=[v.size, v.mean(), v.std(ddof=1), v.min(),
                                    q[0], q[1], q[2], q[3], q[4], v.max()]),
                        ).assign(quantity=name)


def main():
    P = E4.P_test()                     # (N,9) normalized log parameters
    Xn = E4.J_test()                    # (N,131) normalized current
    N = P.shape[0]

    # ------------------------------------------------ directed NN + archive check
    nn, dJ_all = E4.nn_for_metric("M1")
    arch = np.genfromtxt(os.path.join(EXP4, "results", "directed_nn_M1.csv"),
                         delimiter=",", names=True, dtype=None, encoding="utf8")
    assert np.array_equal(nn, arch["nn_i"].astype(np.int64)), \
        "directed NN drifted from the archived analysis"
    print("[verify] directed nearest neighbour identical to the archived "
          "directed_nn_M1.csv for all %d test curves" % N)

    lo, hi, first = L.dedup_undirected(nn, N)
    n_archived = int(np.sum(np.arange(N) < nn))
    print("[verify] corrected unique undirected edges = %d "
          "(the archived i<NN(i) rule kept %d, so %d edges were dropped)"
          % (lo.size, n_archived, lo.size - n_archived))

    dJ = np.sqrt(np.mean((Xn[lo] - Xn[hi]) ** 2, axis=1))
    dTh = np.sqrt(np.mean((P[lo] - P[hi]) ** 2, axis=1))
    assert np.all(np.isfinite(dJ)) and np.all(np.isfinite(dTh))

    # ------------------------------------------------------------- sample counts
    ends = np.concatenate([lo, hi])
    uniq, cnt = np.unique(ends, return_counts=True)
    summary = dict(n_pairs=int(lo.size), n_test=int(N),
                   archived_pairs=n_archived,
                   archived_distinct_samples=12487,
                   distinct_samples=int(uniq.size),
                   samples_in_multiple_pairs=int(np.sum(cnt > 1)),
                   max_pairs_per_sample=int(cnt.max()),
                   median_dJ=float(np.median(dJ)),
                   median_dTheta=float(np.median(dTh)))
    print("[counts] %d pairs cover %d of %d test curves; %d curves lie in more "
          "than one pair (max %d)"
          % (summary["n_pairs"], summary["distinct_samples"], N,
             summary["samples_in_multiple_pairs"], summary["max_pairs_per_sample"]))

    # ------------------------------------------------------------ random baseline
    ra, rb, r_dTh = E4.random_pairs_seed42(P)
    r_dJ = np.sqrt(np.mean((Xn[ra] - Xn[rb]) ** 2, axis=1))
    print("[baseline] random pairs retained %d; median dTheta %.6f; median dJ "
          "%.6f" % (ra.size, np.median(r_dTh), np.median(r_dJ)))

    # ------------------------------------------------------- T6.1 / T6.2 columns
    d1 = dist_stats(dJ, "d_J (normalized RMSE, 131 points)")
    d2 = dist_stats(dTh, "d_Theta (RMSE over 9 normalized log parameters)")
    dist = pd.concat([d1, d2], ignore_index=True)
    dist.to_csv(os.path.join(DATADIR, "si_table_s6_1_dJ_distribution.csv"),
                index=False)
    d2.to_csv(os.path.join(DATADIR, "si_table_s6_2_dTheta_distribution.csv"),
              index=False)

    # --------------------------------------------------------------- T6.3 coupling
    sp = float(spearmanr(dJ, dTh)[0])
    pe = float(pearsonr(dJ, dTh)[0])
    coup = pd.DataFrame(dict(
        quantity=["Spearman(d_J, d_Theta)", "Pearson(d_J, d_Theta)",
                  "Random-pair d_Theta median", "Nearest-neighbour d_Theta median",
                  "Random-pair d_J median", "Nearest-neighbour d_J median"],
        value=[sp, pe, float(np.median(r_dTh)), float(np.median(dTh)),
               float(np.median(r_dJ)), float(np.median(dJ))],
        archived_value=[0.1576, 0.0785, 0.3490, 0.1999, 0.1172, 0.00267]))
    coup.to_csv(os.path.join(DATADIR, "si_table_s6_3_coupling.csv"), index=False)

    # ------------------------------------------------ T6.4 per-parameter ambiguity
    order = np.argsort(dJ, kind="stable")
    amb_rows = []
    for tier, frac in [("all NN", 1.0)] + TIERS:
        k = lo.size if tier == "all NN" else max(1, int(round(lo.size * frac)))
        sel = order[:k]
        A = np.abs(P[lo[sel]] - P[hi[sel]])
        for p, name in enumerate(L.PARAM_NAMES):
            amb_rows.append(dict(
                tier=tier, n_pairs=k, parameter=name,
                median=float(np.median(A[:, p])),
                mean=float(np.mean(A[:, p])),
                p90=float(np.percentile(A[:, p], 90))))
    amb = pd.DataFrame(amb_rows)
    amb.to_csv(os.path.join(DATADIR, "si_table_s6_4_ambiguity_by_tier.csv"),
               index=False)
    # the archived T6.4 subset: the closest-1% tier, ranked by median
    a1 = amb[amb["tier"] == "closest 1%"].copy()
    a1["rank"] = a1["median"].rank(ascending=False).astype(int)
    a1 = a1.sort_values("rank")
    a1.to_csv(os.path.join(DATADIR, "si_table_s6_4_ambiguity_closest1.csv"),
              index=False)
    print("\n[closest 1%% tier, n=%d] per-parameter |Delta| median:"
          % int(a1["n_pairs"].iloc[0]))
    for _, r in a1.iterrows():
        print("   %d. %-12s med=%.4f  mean=%.4f  p90=%.4f"
              % (r["rank"], r["parameter"], r["median"], r["mean"], r["p90"]))

    # ------------------------------------------------------ T6.5 same-sign pairs
    k1 = max(1, int(round(lo.size * 0.01)))
    sel1 = order[:k1]
    d_lo, d_hi = P[lo[sel1]], P[hi[sel1]]
    sign = {}
    for a, b in SAME_SIGN_PAIRS:
        ia, ib = L.PARAM_NAMES.index(a), L.PARAM_NAMES.index(b)
        da, db = d_lo[:, ia] - d_hi[:, ia], d_lo[:, ib] - d_hi[:, ib]
        sign[(a, b)] = float(np.mean(np.sign(da) == np.sign(db)))
    ss = pd.DataFrame([dict(parameter_1=a, parameter_2=b, same_sign_fraction=v)
                       for (a, b), v in sign.items()])
    ss.to_csv(os.path.join(DATADIR, "si_table_s6_5_same_sign.csv"), index=False)
    print("\n[same-sign fractions, closest 1%% tier, n=%d]" % k1)
    for (a, b), v in sign.items():
        print("   %-12s vs %-12s %.2f" % (a, b, v))

    # ------------------------------------------------- T6.6 representative cases
    pairset = set(zip(lo.tolist(), hi.tolist()))
    rows = []
    for tag, i, j in ARCHIVED_CASES:
        key = (min(i, j), max(i, j))
        pos = None
        if key in pairset:
            pos = int(np.where((lo == key[0]) & (hi == key[1]))[0][0])
        rows.append(dict(case=tag, i=i, j=j, pair=key,
                         still_a_nearest_neighbour_edge=key in pairset,
                         dJ=(float(dJ[pos]) if pos is not None else np.nan),
                         dTheta=(float(dTh[pos]) if pos is not None else np.nan),
                         dJ_percentile=(
                             float(100.0 * np.mean(dJ < dJ[pos]))
                             if pos is not None else np.nan),
                         dTheta_percentile=(
                             float(100.0 * np.mean(dTh < dTh[pos]))
                             if pos is not None else np.nan)))
    for tag, i, j, why in FIGURE_CASES:
        key = (min(i, j), max(i, j))
        pos = int(np.where((lo == key[0]) & (hi == key[1]))[0][0])
        rows.append(dict(case=tag, i=i, j=j, pair=key,
                         still_a_nearest_neighbour_edge=True,
                         dJ=float(dJ[pos]), dTheta=float(dTh[pos]),
                         dJ_percentile=float(100.0 * np.mean(dJ < dJ[pos])),
                         dTheta_percentile=float(100.0 * np.mean(dTh < dTh[pos])),
                         selection=why))
    cases = pd.DataFrame(rows)
    cases.to_csv(os.path.join(DATADIR, "si_table_s6_6_cases.csv"), index=False)
    print("\n[representative cases] archived case set, checked against the "
          "corrected pair set:")
    for _, r in cases.iterrows():
        print("   %-4s (%5d,%5d)  edge in corrected set: %-5s  dJ=%.5f  "
              "dTheta=%.4f" % (r["case"], r["i"], r["j"],
                               r["still_a_nearest_neighbour_edge"],
                               r["dJ"], r["dTheta"]))

    # ---------------------------------------------------------------- pair table
    out = pd.DataFrame(dict(i=lo, j=hi, dJ=dJ, dTheta=dTh))
    for cid, _fam, p, q in L.COORDS:
        col = (0.5 * (P[:, p] + P[:, q]) if cid.startswith("a")
               else P[:, p] - P[:, q])
        out["absd_" + cid] = np.abs(col[lo] - col[hi])
    out.to_csv(os.path.join(DATADIR, "si_table_s6_pairs.csv"), index=False)
    pd.DataFrame([summary]).to_csv(
        os.path.join(DATADIR, "si_table_s6_pair_summary.csv"), index=False)

    print("\nwrote si_table_s6_1_dJ_distribution.csv, _2_dTheta_distribution.csv,")
    print("      _3_coupling.csv, _4_ambiguity_by_tier.csv, "
          "_4_ambiguity_closest1.csv,")
    print("      _5_same_sign.csv, _6_cases.csv, _pairs.csv, _pair_summary.csv")


if __name__ == "__main__":
    main()
