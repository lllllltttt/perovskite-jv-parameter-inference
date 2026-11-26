# -*- coding: utf-8 -*-
"""
si_table_s10_v2.py — Table S10 alternative metrics, unified dedup rule.
=======================================================================
The defect this fixes
---------------------
The archived EXP4 pair construction used

    keep = np.arange(N) < nn_idx          # exp4_lib.dedup

which keeps a directed link only when it points *upward*. An unordered edge
{i, j} whose only directed link is the downward one (i > NN(i) = j) is then
thrown away, so the pair set is smaller than the set of distinct
nearest-neighbour edges. For M1 that silently drops 3,579 of 11,245 edges.

The corrected rule, applied uniformly to M1-M6:

    (lo, hi) = (min(i, nn[i]), max(i, nn[i]))  ->  unique unordered set
    key = lo * N + hi ; np.unique(key, return_index=True)

What is deliberately NOT changed
--------------------------------
Each metric keeps its original definition, preprocessing, weights and random
baseline:
    M1  normalized full-curve (0-1.3 V) RMSE, 131 points   (the paper metric)
    M2  physical-current full-curve RMSE, 131 points (mA cm^-2)
    M3  M2 normalised by the pair-mean short-circuit current
    M4  physical-current 0-1.0 V window RMSE, 101 points
    M5  M4 normalised by the pair-mean short-circuit current
    M6  J/|Jsc| shape RMSE, 131 points (supplementary only)
d_Theta is the fixed RMSE over the nine normalized-log parameters for every
metric; the random baseline is the frozen seed-42 draw of 200,000 ordered
index pairs with self-pairs removed (199,985 retained).

The nearest-neighbour search itself is imported from exp4_lib, so the metric
implementations are the archived ones and cannot drift; the recomputed directed
links are checked against the archived directed_nn_M*.csv before use.

Nothing is presupposed about the outcome: if a metric does not reproduce the
paper's pattern after the fix, this script reports that.

Read-only on everything outside this v2 directory.
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
import exp4_lib as E4                                     # noqa: E402  (definitions)

import lib_v2 as L                                        # noqa: E402

OUT = os.path.dirname(HERE)
DATADIR = os.path.join(OUT, "source_data")
REPORTDIR = os.path.join(OUT, "report")
os.makedirs(DATADIR, exist_ok=True)
os.makedirs(REPORTDIR, exist_ok=True)

METRICS = ["M1", "M2", "M3", "M4", "M5", "M6"]
PRIMARY = ["M1", "M2", "M3", "M4", "M5"]
TIER_FRACS = [0.10, 0.05, 0.01, 0.005, 0.001]
TIER_NAMES = {0.10: "closest 10%", 0.05: "closest 5%", 0.01: "closest 1%",
              0.005: "closest 0.5%", 0.001: "closest 0.1%"}
# column names kept identical to the archived metric_level_summary.csv so the
# old and new tables can be compared row by row without a translation layer
TIER_COLS = {0.10: "median_dTheta_closest10", 0.05: "median_dTheta_closest5",
             0.01: "median_dTheta_closest1", 0.005: "median_dTheta_closest05",
             0.001: "median_dTheta_closest01"}


# ---------------------------------------------------------------- distances
def metric_distance(m, i, j, Xn, Xr, Xrl, jsc):
    """The metric's own distance for the pair (i, j). Symmetric by construction."""
    if m == "M1":
        return np.sqrt(np.mean((Xn[i] - Xn[j]) ** 2, axis=-1))
    if m == "M2":
        return np.sqrt(np.mean((Xr[i] - Xr[j]) ** 2, axis=-1))
    if m == "M3":
        return np.sqrt(np.mean((Xr[i] - Xr[j]) ** 2, axis=-1)) \
            / (0.5 * (jsc[i] + jsc[j]))
    if m == "M4":
        return np.sqrt(np.mean((Xrl[i] - Xrl[j]) ** 2, axis=-1))
    if m == "M5":
        return np.sqrt(np.mean((Xrl[i] - Xrl[j]) ** 2, axis=-1)) \
            / (0.5 * (jsc[i] + jsc[j]))
    if m == "M6":
        shp = Xr / np.abs(Xr[:, 0:1])
        return np.sqrt(np.mean((shp[i] - shp[j]) ** 2, axis=-1))
    raise ValueError(m)


def dedup_uniform(nn, N):
    """Mentor's rule: (min, max) -> unique. Returns (lo, hi, first)."""
    lo = np.minimum(np.arange(N), nn)
    hi = np.maximum(np.arange(N), nn)
    key = lo.astype(np.int64) * np.int64(N) + hi.astype(np.int64)
    _, first = np.unique(key, return_index=True)
    return lo[first], hi[first], np.sort(first)


def tiers(dJ, dTh, fracs=TIER_FRACS):
    order = np.argsort(dJ, kind="stable")
    M = len(dJ)
    out = {}
    for f in fracs:
        k = max(1, int(round(M * f)))
        sel = order[:k]
        out[f] = dict(n=k, med_dJ=float(np.median(dJ[sel])),
                      max_dJ=float(dJ[sel].max()),
                      med_dTh=float(np.median(dTh[sel])),
                      q25_dTh=float(np.percentile(dTh[sel], 25)),
                      q75_dTh=float(np.percentile(dTh[sel], 75)))
    return out


def main():
    P = E4.P_test()
    N = P.shape[0]
    Xn = E4.J_test()
    Xr = E4.J_raw()
    jsc = np.abs(Xr[:, 0])
    Xrl = Xr[:, E4.LOW_MASK]

    ra, rb, rd42 = E4.random_pairs_seed42(P)
    RAND_MED = float(np.median(rd42))
    print("[baseline] random pairs retained = %d   median dTheta = %.6f"
          % (ra.size, RAND_MED))

    # -------------------------------------------------- directed NN per metric
    D, D_buggy_kept, D_fixed = {}, {}, {}
    verify_rows = []
    for m in METRICS:
        nn, _d = E4.nn_for_metric(m)
        D[m] = nn
        arch = np.genfromtxt(os.path.join(EXP4, "results", "directed_nn_%s.csv" % m),
                             delimiter=",", names=True, dtype=None, encoding="utf8")
        same = bool(np.array_equal(nn, arch["nn_i"].astype(np.int64)))
        verify_rows.append(dict(metric=m, recomputed_matches_archive=same,
                                n_samples=int(N)))
        assert same, "directed NN drifted for %s" % m

        lo, hi, first = dedup_uniform(nn, N)
        D_fixed[m] = (lo, hi)
        D_buggy_kept[m] = int(np.sum(np.arange(N) < nn))     # the archived rule
    pd.DataFrame(verify_rows).to_csv(
        os.path.join(DATADIR, "si_table_s10_directed_nn_verify.csv"), index=False)
    print("[verify] recomputed directed NN identical to the archived CSVs "
          "for all six metrics (metric definitions therefore unchanged)")

    # -------------------------------------------------- old values, from disk
    old_sum = pd.read_csv(os.path.join(EXP4, "results", "metric_level_summary.csv")) \
        .set_index("metric")
    old_tier = pd.read_csv(os.path.join(EXP4, "results",
                                        "distance_tiers_by_metric.csv"))
    old_amb = pd.read_csv(os.path.join(EXP4, "results",
                                       "per_parameter_ambiguity_by_metric.csv"))
    old_over = pd.read_csv(os.path.join(EXP4, "results", "pair_set_overlap.csv"))
    old_amb_rank = pd.read_csv(os.path.join(EXP4, "results",
                                            "ambiguity_rank_correlations.csv"))

    # -------------------------------------------------- new statistics
    pair_rows, sum_rows, tier_rows, amb_rows = [], [], [], []
    dTh_all, pair_sets, pair_dJ, nn_ident, amb_vec = {}, {}, {}, {}, {}

    for m in METRICS:
        nn = D[m]
        lo, hi = D_fixed[m]
        dJ = np.asarray(metric_distance(m, lo, hi, Xn, Xr, Xrl, jsc), float)
        assert dJ.shape == lo.shape and np.all(np.isfinite(dJ))
        dTh = np.sqrt(np.mean((P[lo] - P[hi]) ** 2, axis=1))

        nn_ident[m] = nn
        pair_sets[m] = set(zip(lo.tolist(), hi.tolist()))
        pair_dJ[m], dTh_all[m] = dJ, dTh

        mutual = float(np.mean(nn[nn] == np.arange(N)))
        sp, pe = float(spearmanr(dJ, dTh)[0]), float(pearsonr(dJ, dTh)[0])
        ts = tiers(dJ, dTh)
        med_nn = float(np.median(dTh))
        order = np.argsort(dJ, kind="stable")
        k1 = max(1, int(round(len(dJ) * 0.01)))
        A1 = np.abs(P[lo[order[:k1]]] - P[hi[order[:k1]]])
        med = [float(np.median(A1[:, p])) for p in range(9)]
        rnk = sorted(range(9), key=lambda p: -med[p])
        rank_of = {p: r + 1 for r, p in enumerate(rnk)}
        amb_vec[m] = med
        for p in range(9):
            amb_rows.append(dict(metric=m, parameter=E4.PARAM_OUT[p],
                                 new_median_abs_delta_closest1pct=med[p],
                                 new_ambiguity_rank=rank_of[p]))

        # which directed link(s) gave rise to this edge: 1 = mutual, 0 = only
        # lo -> hi, 2 = only hi -> lo. Lets an auditor see which edges the
        # archived upward-only rule would have dropped.
        src = np.where((nn[lo] == hi) & (nn[hi] == lo), 1,
                       np.where(nn[lo] == hi, 0, 2))
        pair_rows.append(pd.DataFrame(dict(
            metric=m, i=lo, j=hi, dJ=dJ, dTheta=dTh, directed_link_source=src)))

        if m in PRIMARY:
            s = dict(metric=m, n_unique_pairs=len(dJ), mutual_nn_fraction=mutual,
                     spearman_dJ_dTheta=sp, pearson_dJ_dTheta=pe,
                     median_dTheta_allNN=med_nn, random_median_dTheta=RAND_MED,
                     R_NN=med_nn / RAND_MED)
            for f in TIER_FRACS:
                s[TIER_COLS[f]] = ts[f]["med_dTh"]
            s["R_1pct"] = ts[0.01]["med_dTh"] / RAND_MED
            s["R_05pct"] = ts[0.005]["med_dTh"] / RAND_MED
            s["R_01pct"] = ts[0.001]["med_dTh"] / RAND_MED
            sum_rows.append(s)

        for f in TIER_FRACS:
            t = ts[f]
            tier_rows.append(dict(metric=m, tier=TIER_NAMES[f], n_pairs=t["n"],
                                  median_dJ=t["med_dJ"], max_dJ=t["max_dJ"],
                                  median_dTheta=t["med_dTh"],
                                  q25_dTheta=t["q25_dTh"], q75_dTheta=t["q75_dTh"]))
        tier_rows.append(dict(metric=m, tier="all_NN", n_pairs=len(dJ),
                              median_dJ=float(np.median(dJ)),
                              max_dJ=float(dJ.max()), median_dTheta=med_nn,
                              q25_dTheta=float(np.percentile(dTh, 25)),
                              q75_dTheta=float(np.percentile(dTh, 75))))

        print("\n[%s] pairs %5d (archived rule kept %5d, so +%d recovered); "
              "mutual=%.3f Spearman=%.4f"
              % (m, len(dJ), D_buggy_kept[m], len(dJ) - D_buggy_kept[m],
                 mutual, sp))
        print("     median dTheta all-NN = %.4f (%.3f x random)   closest 1%% = %.4f"
              % (med_nn, med_nn / RAND_MED, ts[0.01]["med_dTh"]))

    SUM = pd.DataFrame(sum_rows)
    TIER = pd.DataFrame(tier_rows)
    AMB = pd.DataFrame(amb_rows)
    PAIRS = pd.concat(pair_rows, ignore_index=True)

    # -------------------------------------------------- old vs new comparison
    def num(df, key, col):
        return float(df.loc[key, col])

    cmp_rows = []
    for m in METRICS:
        n_new = len(pair_sets[m])
        n_old = int(old_sum.loc[m, "n_unique_pairs"]) if m in old_sum.index \
            else int(D_buggy_kept[m])
        cmp_rows.append(dict(metric=m, statistic="n_unique_pairs",
                             archived_value=n_old, corrected_value=n_new,
                             delta=n_new - n_old, affected_by_pair_set="yes",
                             note="archived rule kept only upward directed links"))
        if m not in PRIMARY:
            cmp_rows.append(dict(metric=m, statistic="(reporting only)",
                                 archived_value=np.nan, corrected_value=np.nan,
                                 delta=np.nan, affected_by_pair_set="n/a",
                                 note="M6 is supplementary-only in the archive"))
            continue
        new = SUM[SUM["metric"] == m].iloc[0]
        for col, lab in [("mutual_nn_fraction", "mutual_nn_fraction"),
                         ("spearman_dJ_dTheta", "spearman_dJ_dTheta"),
                         ("pearson_dJ_dTheta", "pearson_dJ_dTheta"),
                         ("median_dTheta_allNN", "median_dTheta_allNN"),
                         ("R_NN", "R_NN"),
                         ("median_dTheta_closest10", "median_dTheta_closest 10%"),
                         ("median_dTheta_closest5", "median_dTheta_closest 5%"),
                         ("median_dTheta_closest1", "median_dTheta_closest 1%"),
                         ("median_dTheta_closest05", "median_dTheta_closest 0.5%"),
                         ("median_dTheta_closest01", "median_dTheta_closest 0.1%"),
                         ("R_1pct", "R_1pct"), ("R_05pct", "R_05pct"),
                         ("R_01pct", "R_01pct")]:
            if col not in new:
                continue
            cmp_rows.append(dict(
                metric=m, statistic=lab,
                archived_value=num(old_sum, m, col),
                corrected_value=float(new[col]),
                delta=float(new[col]) - num(old_sum, m, col),
                affected_by_pair_set=("yes" if col != "mutual_nn_fraction"
                                      else "no (directed-graph property)"),
                note=""))
    CMP = pd.DataFrame(cmp_rows)

    # ---------------------------------------------- per-parameter ambiguity
    for _, r in AMB.iterrows():
        o = old_amb[(old_amb["metric"] == r["metric"])
                    & (old_amb["parameter"] == r["parameter"])].iloc[0]
        r_old = float(o["median_abs_delta_closest1pct"])
        r_new = float(r["new_median_abs_delta_closest1pct"])
        AMB.loc[(AMB["metric"] == r["metric"])
                & (AMB["parameter"] == r["parameter"]),
                "archived_median_abs_delta_closest1pct"] = r_old
        AMB.loc[(AMB["metric"] == r["metric"])
                & (AMB["parameter"] == r["parameter"]),
                "archived_ambiguity_rank"] = int(o["ambiguity_rank"])
        AMB.loc[(AMB["metric"] == r["metric"])
                & (AMB["parameter"] == r["parameter"]), "delta"] = r_new - r_old
    AMB = AMB[["metric", "parameter", "archived_median_abs_delta_closest1pct",
               "new_median_abs_delta_closest1pct", "delta",
               "archived_ambiguity_rank", "new_ambiguity_rank"]]

    # ------------------------------------------------------ pair-set overlap
    def jac(a, b):
        return len(a & b) / len(a | b) if (a or b) else 1.0

    def closest1(m):
        order = np.argsort(pair_dJ[m], kind="stable")
        k1 = max(1, int(round(len(pair_dJ[m]) * 0.01)))
        lst = sorted(pair_sets[m])
        return {lst[t] for t in order[:k1].tolist()}

    c1 = {m: closest1(m) for m in PRIMARY}
    over_rows = []
    for a in PRIMARY:
        for b in PRIMARY:
            over_rows.append(dict(
                metric_A=a, metric_B=b,
                nn_identity_agreement=float(np.mean(nn_ident[a] == nn_ident[b])),
                pair_jaccard_new=jac(pair_sets[a], pair_sets[b]),
                pair_jaccard_archived=float(old_over[(old_over["metric_A"] == a)
                                                     & (old_over["metric_B"] == b)]
                                            ["pair_jaccard"].iloc[0]),
                closest1pct_jaccard_new=jac(c1[a], c1[b]),
                closest1pct_jaccard_archived=float(
                    old_over[(old_over["metric_A"] == a)
                             & (old_over["metric_B"] == b)]
                    ["closest1pct_jaccard"].iloc[0])))
    OVER = pd.DataFrame(over_rows)

    rank_rows = []
    for a in PRIMARY:
        for b in PRIMARY:
            new_r = float(spearmanr(amb_vec[a], amb_vec[b])[0])
            old_r = float(old_amb_rank[(old_amb_rank["metric_A"] == a)
                                       & (old_amb_rank["metric_B"] == b)]
                          ["spearman_ambiguity_rank_corr"].iloc[0])
            rank_rows.append(dict(metric_A=a, metric_B=b, archived=old_r,
                                  corrected=new_r, delta=new_r - old_r))
    RANK = pd.DataFrame(rank_rows)

    # ------------------------------------------------------------ write out
    CMP.to_csv(os.path.join(DATADIR, "si_table_s10_old_vs_new.csv"), index=False)
    SUM.to_csv(os.path.join(DATADIR, "si_table_s10_metric_summary_v2.csv"),
               index=False)
    TIER.to_csv(os.path.join(DATADIR, "si_table_s10_tiers_v2.csv"), index=False)
    AMB.to_csv(os.path.join(DATADIR, "si_table_s10_ambiguity_v2.csv"), index=False)
    PAIRS.to_csv(os.path.join(DATADIR, "si_table_s10_pairs_v2.csv"), index=False)
    OVER.to_csv(os.path.join(DATADIR, "si_table_s10_overlap_v2.csv"), index=False)
    RANK.to_csv(os.path.join(DATADIR, "si_table_s10_ambiguity_rank_v2.csv"),
                index=False)

    # ------------------------------------------------------- console summary
    print("\n" + "=" * 100)
    print("UNIFIED DEDUP RULE APPLIED TO M1-M6 — pair counts")
    print("=" * 100)
    print("%-4s %10s %10s %10s" % ("", "archived", "corrected", "recovered"))
    for m in METRICS:
        print("%-4s %10d %10d %10d"
              % (m, D_buggy_kept[m], len(pair_sets[m]),
                 len(pair_sets[m]) - D_buggy_kept[m]))

    print("\n" + "=" * 100)
    print("KEY TABLE S10 QUANTITIES, archived vs corrected")
    print("=" * 100)
    print("%-4s | %-26s | %-26s | %-26s" % ("", "median dTheta all-NN",
                                            "median dTheta closest 1%",
                                            "median dTheta closest 0.1%"))
    print("%-4s | %9s %9s %6s | %9s %9s %6s | %9s %9s %6s"
          % ("", "old", "new", "delta", "old", "new", "delta",
             "old", "new", "delta"))
    def nm(m, tier, col):
        q = TIER[(TIER["metric"] == m) & (TIER["tier"] == tier)]
        return float(q[col].iloc[0])

    for m in METRICS:                     # M6 included: the rule applies to it too
        o = old_sum.loc[m] if m in old_sum.index else None
        a_old = float(o["median_dTheta_allNN"]) if o is not None else \
            float(old_tier[(old_tier["metric"] == m)
                           & (old_tier["tier"] == "all_NN")]["median_dTheta"].iloc[0])
        c1_old = float(o["median_dTheta_closest1"]) if o is not None else \
            float(old_tier[(old_tier["metric"] == m)
                           & (old_tier["tier"] == "closest_1")]["median_dTheta"].iloc[0])
        c01_old = float(o["median_dTheta_closest01"]) if o is not None else \
            float(old_tier[(old_tier["metric"] == m)
                           & (old_tier["tier"] == "closest_01")]["median_dTheta"].iloc[0])
        a_new = nm(m, "all_NN", "median_dTheta")
        c1_new = nm(m, "closest 1%", "median_dTheta")
        c01_new = nm(m, "closest 0.1%", "median_dTheta")
        print("%-4s | %9.4f %9.4f %+6.4f | %9.4f %9.4f %+6.4f | %9.4f %9.4f %+6.4f"
              % (m, a_old, a_new, a_new - a_old,
                 c1_old, c1_new, c1_new - c1_old,
                 c01_old, c01_new, c01_new - c01_old))
    print("%-4s   random-pair baseline median dTheta = %.4f (unchanged)"
          % ("--", RAND_MED))

    print("\nclosest-1%% ambiguity ranking per metric (corrected pair set):")
    for m in METRICS:
        s = AMB[AMB["metric"] == m].sort_values("new_ambiguity_rank")
        print("   %-3s %s" % (m, " > ".join(
            "%s(%.3f)" % (r["parameter"], r["new_median_abs_delta_closest1pct"])
            for _, r in s.iterrows())))

    print("\nwrote: si_table_s10_old_vs_new.csv, _metric_summary_v2.csv, "
          "_tiers_v2.csv, _ambiguity_v2.csv,")
    print("       _pairs_v2.csv, _overlap_v2.csv, _ambiguity_rank_v2.csv, "
          "_directed_nn_verify.csv")

    # ------------------------------------------------ markdown draft table
    lines = []
    lines.append("# Table S10 (draft v2) — collision robustness under "
                 "alternative J-V similarity metrics\n")
    lines.append("Pair construction: each sample's directed nearest neighbour "
                 "-> `(min(i,j), max(i,j))` -> unique unordered set, applied "
                 "identically to M1-M6.\n")
    lines.append("| metric | definition | unique pairs (archived -> corrected) "
                 "| median $d_\\Theta$ all-NN | random baseline | closest 1% | "
                 "closest 0.1% |")
    lines.append("|---|---|---|---|---|---|---|")
    DEFN = {
        "M1": "normalized-J full-curve RMSE, 131 pts (paper metric)",
        "M2": "physical-current full-curve RMSE, 131 pts (mA cm$^{-2}$)",
        "M3": "M2 / pair-mean $\\vert J_{sc}\\vert$",
        "M4": "physical-current 0-1.0 V RMSE, 101 pts",
        "M5": "M4 / pair-mean $\\vert J_{sc}\\vert$",
        "M6": "J/$\\vert J_{sc}\\vert$ shape RMSE, 131 pts (supplementary only)",
    }
    # TIER carries every metric (M6 included), so it is the lookup for the
    # three headline quantities
    def tierval(m, tier, col):
        q = TIER[(TIER["metric"] == m) & (TIER["tier"] == tier)]
        return float(q[col].iloc[0])

    for m in METRICS:
        lines.append("| %s | %s | %d $\\to$ %d | %.3f | %.3f | %.3f | %.3f |"
                     % (m, DEFN[m], D_buggy_kept[m], len(pair_sets[m]),
                        tierval(m, "all_NN", "median_dTheta"), RAND_MED,
                        tierval(m, "closest 1%", "median_dTheta"),
                        tierval(m, "closest 0.1%", "median_dTheta")))
    lines.append("")
    lines.append("$d_\\Theta$ is the fixed RMSE over the nine normalized-log "
                 "parameters and is identical by construction for every J "
                 "metric. Random baseline: frozen seed-42 draw of 200,000 "
                 "ordered index pairs, self-pairs removed (%d retained), median "
                 "$d_\\Theta$ = %.4f.\n" % (ra.size, RAND_MED))
    lines.append("Tier rounding: $k=\\max(1,\\mathrm{round}(M f))$ with "
                 "$M$ the number of unique pairs; tiers are the $k$ smallest "
                 "$d_J$ values, stable-sorted, so ties are kept in index order.\n")
    with open(os.path.join(REPORTDIR, "TABLE_S10_DRAFT_V2.md"), "w",
              encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print("wrote report/TABLE_S10_DRAFT_V2.md")


if __name__ == "__main__":
    main()
