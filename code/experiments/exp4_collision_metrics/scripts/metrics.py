# -*- coding: utf-8 -*-
"""
EXP4 §4-14 — full M1-M5 computation + all result CSVs (M6 optional).

For each metric: exact directed NN (saved pre-dedup), dedup to unordered pairs,
distance coupling, NN parameter-distance distribution, distance tiers,
per-parameter closest-1% ambiguity, pair-set overlap, cross-metric union
distances, and representative-collision metric checks. d_Theta is FIXED (RMSE
over the nine normalized-log parameters) for every metric.

Outputs in results/ (all listed in §23):
  directed_nn_{M1..M6}.csv, metric_level_summary.csv, distance_tiers_by_metric.csv,
  per_parameter_ambiguity_by_metric.csv, ambiguity_rank_correlations.csv,
  pair_set_overlap.csv, cross_metric_pair_distances.csv,
  representative_collision_metric_check.csv, metric_M6_supplementary.csv
"""
import os, sys, csv
import numpy as np
from scipy.stats import spearmanr, pearsonr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exp4_lib import (EXP4, PARAM_NAMES, PARAM_OUT, REP_TAUETL, REP_RRAD,
                      J_test, P_test, J_raw, LOW_MASK,
                      nn_for_metric, dedup, coupling, tier_stats,
                      random_pairs_seed42, random_pairs_fixed)

RES = os.path.join(EXP4, "results")
os.makedirs(RES, exist_ok=True)

PRIMARY = ["M1", "M2", "M3", "M4", "M5"]
ALL_M = PRIMARY + ["M6"]

P = P_test()
N = P.shape[0]
Xnorm = J_test()                 # (N,131) normalized
Xraw = J_raw()                   # (N,131) physical mA/cm^2
Xraw_low = Xraw[:, LOW_MASK]     # (N,101)
JSC = np.abs(Xraw[:, 0])         # |J at V=0| ~ |Jsc| in mA/cm^2

# ---------------------------------------------------------------- directed NN
print("computing directed exact NN per metric ...")
directed = {}
for m in ALL_M:
    nn_idx, dJ = nn_for_metric(m)
    directed[m] = (nn_idx, dJ)
    with open(os.path.join(RES, "directed_nn_%s.csv" % m), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["i", "nn_i", "dJ"])
        for k in range(N):
            w.writerow([k, int(nn_idx[k]), "%.12e" % dJ[k]])
    print("  %s directed NN saved" % m)

# ---------------------------------------------------------------- exact-NN subset verification
# independent brute-force check of the chunked implementation (seed 20260827, §6)
rng = np.random.default_rng(20260827)
sub = rng.choice(N, 150, replace=False)
Xm = {"M1": Xnorm, "M2": Xraw, "M4": Xraw_low, "M6": Xraw / JSC[:, None]}
for m in ("M1", "M2", "M4", "M6"):
    nn_idx = directed[m][0]
    X = Xm[m]
    ok = True
    for k in sub:
        oth = np.arange(N) != k
        d = np.sqrt(np.mean((X[k] - X[oth]) ** 2, axis=1))
        if np.arange(N)[oth][np.argmin(d)] != nn_idx[k]:
            ok = False; break
    print("  %s brute-force subset verify: %s" % (m, "OK" if ok else "MISMATCH"))
for m in ("M3", "M5"):
    nn_idx = directed[m][0]
    X = Xraw_low if m == "M5" else Xraw
    ok = True
    for k in sub:
        oth = np.arange(N) != k
        d = np.sqrt(np.mean((X[k] - X[oth]) ** 2, axis=1))
        d = d / (0.5 * (JSC[k] + JSC[oth]))
        if np.arange(N)[oth][np.argmin(d)] != nn_idx[k]:
            ok = False; break
    print("  %s pair-scaled brute-force subset verify: %s" % (m, "OK" if ok else "MISMATCH"))

# ---------------------------------------------------------------- random baselines
ra, rb, rd42 = random_pairs_seed42(P)          # frozen (original draw, primary)
ra27, rb27, rd27 = random_pairs_fixed(P)       # spec fixed set (seed 20260827)
RAND_MED = float(np.median(rd42))
print("\nrandom baseline medians: seed42=%.4f (frozen 0.3490)  20260827=%.4f"
      % (RAND_MED, np.median(rd27)))
with open(os.path.join(RES, "random_pairs_seed20260827.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["i", "j"])
    for a, b in zip(ra27, rb27):
        w.writerow([int(a), int(b)])

# ---------------------------------------------------------------- per metric tables
TIER_FRACS = [0.10, 0.05, 0.01, 0.005, 0.001]
TIER_NAMES = {0.10: "closest_10", 0.05: "closest_5", 0.01: "closest_1",
              0.005: "closest_05", 0.001: "closest_01"}
TIER_COLS = {0.10: "median_dTheta_closest10", 0.05: "median_dTheta_closest5",
             0.01: "median_dTheta_closest1", 0.005: "median_dTheta_closest05",
             0.001: "median_dTheta_closest01"}

pair_sets, pair_dJ, pair_dTh, nn_identity = {}, {}, {}, {}
amb_vec = {}
summary, tier_rows, amb_rows = [], [], []

for m in ALL_M:
    nn_idx, dJ = directed[m]
    nn_identity[m] = nn_idx
    I, J = dedup(nn_idx)
    dJp = dJ[I]                      # dedup-pair distances (directed masked to kept)
    dTh = np.sqrt(np.mean((P[I] - P[J]) ** 2, axis=1))
    pair_sets[m] = set(zip(I.tolist(), J.tolist()))
    pair_dJ[m], pair_dTh[m] = dJp, dTh

    mutual = float(np.mean(nn_idx[nn_idx] == np.arange(N)))
    sp, pe = coupling(dJp, dTh)
    ts = tier_stats(dJp, dTh, TIER_FRACS)
    med_nn = float(np.median(dTh))
    print("\n[%s] unique=%d mutual=%.4f  Spearman=%.4f Pearson=%.4f  NN med=%.4f"
          % (m, len(I), mutual, sp, pe, med_nn))

    order = np.argsort(dJp, kind="stable")
    k1 = max(1, int(round(len(I) * 0.01)))
    sel1 = order[:k1]
    A1 = np.abs(P[I[sel1]] - P[J[sel1]])
    med = [float(np.median(A1[:, p])) for p in range(9)]
    rnk = sorted(range(9), key=lambda p: -med[p])
    rank_of = {p: r + 1 for r, p in enumerate(rnk)}
    amb_vec[m] = med
    for p in range(9):
        amb_rows.append([m, PARAM_OUT[p], med[p], rank_of[p]])
    print("      closest-1%% ambiguity rank: %s" %
          ", ".join("%s(%.3f)" % (PARAM_OUT[p], med[p]) for p in rnk))

    if m in PRIMARY:
        s = dict(metric=m, n_unique_pairs=len(I), mutual_nn_fraction=mutual,
                 spearman_dJ_dTheta=sp, pearson_dJ_dTheta=pe,
                 median_dTheta_allNN=med_nn, random_median_dTheta=RAND_MED,
                 R_NN=med_nn / RAND_MED)
        for f in TIER_FRACS:
            s[TIER_COLS[f]] = ts[f]["med_dTh"]
        s["R_1pct"] = ts[0.01]["med_dTh"] / RAND_MED
        s["R_05pct"] = ts[0.005]["med_dTh"] / RAND_MED
        s["R_01pct"] = ts[0.001]["med_dTh"] / RAND_MED
        summary.append(s)

    for f in TIER_FRACS:
        t = ts[f]
        tier_rows.append([m, TIER_NAMES[f], t["n"], t["med_dJ"],
                          t["max_dJ"], t["med_dTh"], t["q25_dTh"], t["q75_dTh"]])
    tier_rows.append([m, "all_NN", len(I), float(np.median(dJp)), float(dJp.max()),
                      med_nn, float(np.percentile(dTh, 25)),
                      float(np.percentile(dTh, 75))])

if "M1" in summary:
    t1 = next(r for r in tier_rows if r[0] == "M1" and r[1] == "closest_1")
    print("\n  M1 frozen-tier check: closest_1 med_dTheta=%.4f (frozen 0.1443)"
          % t1[5])

with open(os.path.join(RES, "metric_level_summary.csv"), "w", newline="") as f:
    cols = ["metric", "n_unique_pairs", "mutual_nn_fraction",
            "spearman_dJ_dTheta", "pearson_dJ_dTheta", "median_dTheta_allNN",
            "random_median_dTheta", "R_NN"] + [TIER_COLS[f] for f in TIER_FRACS] + \
           ["R_1pct", "R_05pct", "R_01pct"]
    w = csv.writer(f); w.writerow(cols)
    for s in summary:
        w.writerow([s[c] if isinstance(s[c], str) else "%.6f" % s[c] for c in cols])
print("\nsaved metric_level_summary.csv")

with open(os.path.join(RES, "distance_tiers_by_metric.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["metric", "tier", "n_pairs", "median_dJ", "max_dJ",
                "median_dTheta", "q25_dTheta", "q75_dTheta"])
    for r in tier_rows:
        w.writerow([r[0], r[1]] + ["%.6f" % v for v in r[2:]])
print("saved distance_tiers_by_metric.csv")

with open(os.path.join(RES, "per_parameter_ambiguity_by_metric.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["metric", "parameter", "median_abs_delta_closest1pct", "ambiguity_rank"])
    for r in amb_rows:
        w.writerow([r[0], r[1], "%.6f" % r[2], r[3]])
print("saved per_parameter_ambiguity_by_metric.csv")

with open(os.path.join(RES, "ambiguity_rank_correlations.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["metric_A", "metric_B", "spearman_ambiguity_rank_corr"])
    for a in PRIMARY:
        for b in PRIMARY:
            w.writerow([a, b, "%.4f" % spearmanr(amb_vec[a], amb_vec[b])[0]])
print("saved ambiguity_rank_correlations.csv")

# ---------------------------------------------------------------- cross-metric union
union_set = set()
for m in PRIMARY:
    union_set |= pair_sets[m]
U = sorted(union_set)
Ui = np.array([t[0] for t in U], np.int64)
Uj = np.array([t[1] for t in U], np.int64)
NU = len(U)
print("\ncross-metric union size = %d pairs" % NU)

dJ_u = {}
for m in PRIMARY:
    sr = np.sort(pair_dJ[m])
    if m == "M1":
        d = np.sqrt(np.mean((Xnorm[Ui] - Xnorm[Uj]) ** 2, axis=1))
    elif m == "M2":
        d = np.sqrt(np.mean((Xraw[Ui] - Xraw[Uj]) ** 2, axis=1))
    elif m == "M3":
        d = np.sqrt(np.mean((Xraw[Ui] - Xraw[Uj]) ** 2, axis=1)) \
            / (0.5 * (JSC[Ui] + JSC[Uj]))
    elif m == "M4":
        d = np.sqrt(np.mean((Xraw_low[Ui] - Xraw_low[Uj]) ** 2, axis=1))
    elif m == "M5":
        d = np.sqrt(np.mean((Xraw_low[Ui] - Xraw_low[Uj]) ** 2, axis=1)) \
            / (0.5 * (JSC[Ui] + JSC[Uj]))
    dJ_u[m] = d
    dJ_u[m + "_pct"] = np.searchsorted(sr, d, side="right") / float(len(sr))

dTh_u = np.sqrt(np.mean((P[Ui] - P[Uj]) ** 2, axis=1))

with open(os.path.join(RES, "cross_metric_pair_distances.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["i", "j", "dTheta"] +
               ["dJ_" + m for m in PRIMARY] + ["pct_" + m for m in PRIMARY])
    for k in range(NU):
        row = [U[k][0], U[k][1], "%.6f" % dTh_u[k]]
        row += ["%.6f" % dJ_u[m][k] for m in PRIMARY]
        row += ["%.6f" % dJ_u[m + "_pct"][k] for m in PRIMARY]
        w.writerow(row)
print("saved cross_metric_pair_distances.csv")

# ---------------------------------------------------------------- pair-set overlap
def jaccard(sa, sb):
    return len(sa & sb) / len(sa | sb) if (sa or sb) else 1.0

def closest1_set(m):
    order = np.argsort(pair_dJ[m], kind="stable")
    k1 = max(1, int(round(len(order) * 0.01)))
    lst = sorted(pair_sets[m])
    return {lst[i] for i in order[:k1].tolist()}

with open(os.path.join(RES, "pair_set_overlap.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["metric_A", "metric_B", "nn_identity_agreement", "pair_jaccard",
                "closest1pct_jaccard"])
    c1 = {m: closest1_set(m) for m in PRIMARY}
    for a in PRIMARY:
        for b in PRIMARY:
            agree = float(np.mean(nn_identity[a] == nn_identity[b]))
            w.writerow([a, b, "%.4f" % agree, "%.4f" % jaccard(pair_sets[a], pair_sets[b]),
                        "%.4f" % jaccard(c1[a], c1[b])])
print("saved pair_set_overlap.csv")

# ---------------------------------------------------------------- representative collisions + robust pair
def pair_dist_full(i, j):
    """All five distances for one pair (scalars)."""
    dp = float(np.sqrt(np.mean((Xraw[i] - Xraw[j]) ** 2)))
    dpl = float(np.sqrt(np.mean((Xraw_low[i] - Xraw_low[j]) ** 2)))
    return {"M1": float(np.sqrt(np.mean((Xnorm[i] - Xnorm[j]) ** 2))),
            "M2": dp,
            "M3": dp / (0.5 * (JSC[i] + JSC[j])),
            "M4": dpl,
            "M5": dpl / (0.5 * (JSC[i] + JSC[j]))}

# robust-pair selection (§14), predeclared:
#   bottom-1% NN tail under >= 3 of M1-M5 AND dTheta > that metric's closest-1% median
thr, tier_med = {}, {}
for m in PRIMARY:
    order = np.argsort(pair_dJ[m], kind="stable")
    k1 = max(1, int(round(len(order) * 0.01)))
    thr[m] = pair_dJ[m][order[:k1]].max()       # bottom-1% boundary
    tier_med[m] = float(np.median(pair_dTh[m][order[:k1]]))

hits = np.zeros(NU, dtype=int)
for m in PRIMARY:
    hits += ((dJ_u[m] <= thr[m]) & (dTh_u > tier_med[m])).astype(int)
cand = np.where(hits >= 3)[0]
robust_pair = None
if len(cand):
    order = cand[np.argsort(dTh_u[cand])[::-1]]
    robust_pair = (int(Ui[order[0]]), int(Uj[order[0]]))
    print("\nrobust cross-metric candidate: (%d,%d) metrics=%d dTheta=%.4f"
          % (robust_pair[0], robust_pair[1], int(hits[order[0]]), dTh_u[order[0]]))
else:
    print("\nrobust cross-metric candidate: NONE (criterion not relaxed)")

rep_cases = [("tau_ETL_dominant", REP_TAUETL), ("r_rad_dominant", REP_RRAD)]
if robust_pair:
    rep_cases.append(("cross_metric_robust", robust_pair))

with open(os.path.join(RES, "representative_collision_metric_check.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["case", "i", "j", "dTheta"] + ["dJ_" + m for m in PRIMARY] +
               ["pct_" + m for m in PRIMARY] + ["absd_" + p for p in PARAM_OUT])
    for name, (i, j) in rep_cases:
        dd = pair_dist_full(i, j)
        pct = {}
        for m in PRIMARY:
            pct[m] = np.searchsorted(np.sort(pair_dJ[m]), dd[m], side="right") \
                / float(len(pair_dJ[m]))
        ad = np.abs(P[i] - P[j])
        dth = float(np.sqrt(np.mean((P[i] - P[j]) ** 2)))
        row = [name, i, j, "%.4f" % dth]
        row += ["%.6f" % dd[m] for m in PRIMARY]
        row += ["%.4f" % pct[m] for m in PRIMARY]
        row += ["%.4f" % ad[p] for p in range(9)]
        w.writerow(row)
        print("\n[%s] (%d,%d) dTheta=%.4f" % (name, i, j, dth))
        for m in PRIMARY:
            print("   %s dJ=%.5f  pct=%.1f%%" % (m, dd[m], pct[m] * 100))
        print("   param |d|: " + ", ".join("%s=%.3f" % (PARAM_OUT[p], ad[p])
                                           for p in range(9)))
print("\nsaved representative_collision_metric_check.csv")

# ---------------------------------------------------------------- M6 supplementary
m = "M6"
nn_idx, dJ = directed[m]
I, J = dedup(nn_idx)
dJp = dJ[I]
dTh = np.sqrt(np.mean((P[I] - P[J]) ** 2, axis=1))
sp, pe = coupling(dJp, dTh)
order = np.argsort(dJp, kind="stable")
k1 = max(1, int(round(len(I) * 0.01)))
with open(os.path.join(RES, "metric_M6_supplementary.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["metric", "n_unique_pairs", "spearman_dJ_dTheta", "pearson_dJ_dTheta",
                "median_dTheta_allNN", "median_dTheta_closest1",
                "median_dTheta_closest1_over_random"])
    w.writerow(["M6", len(I), "%.4f" % sp, "%.4f" % pe, "%.4f" % np.median(dTh),
                "%.4f" % np.median(dTh[order[:k1]]),
                "%.4f" % (np.median(dTh[order[:k1]]) / RAND_MED)])
print("\nM6 (optional shape metric) supplementary saved")

print("\nEXP4 metrics computation complete.")
