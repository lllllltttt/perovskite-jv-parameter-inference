# -*- coding: utf-8 -*-
"""
EXP4 §2 — Phase 0: exact original collision reproduction.

Recompute the frozen M1 nearest-neighbor analysis (per-column normalized
full-curve RMSE, 131 pts) from the frozen dataset using the exact original
algorithm, and compare every quantity against the frozen stored artifacts
(collision_analysis/nearest_neighbor_pairs.csv, parameter_ambiguity_summary.csv,
collision_summary.txt). STOP if anything disagrees materially.

Writes ORIGINAL_COLLISION_REPRODUCTION_CHECK.md in the exp4 root.
"""
import os, sys, csv
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, pearsonr, percentileofscore

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exp4_lib import (BASE, EXP4, COLL_DIR, PARAM_NAMES, PARAM_OUT, REF_DEDUP,
                      REF_SPEARMAN, REF_PEARSON, REF_MED_NN, REF_MED_RAND,
                      REF_TIER_MED, REF_PARM_AMB, REP_TAUETL, REP_RRAD,
                      J_test, P_test, J_raw, exact_nn_rmse, dedup, coupling,
                      tier_stats, random_pairs_seed42)

V = np.linspace(0.0, 1.3, J_test().shape[1])
N, JD = J_test().shape

checks = []   # (desc, ok, detail)
def check(desc, ok, detail=""):
    checks.append((desc, bool(ok), detail))
    print("%s  %s%s" % ("PASS" if ok else "**FAIL**", desc,
                        ("  -> " + detail) if detail else ""))

# ---------------------------------------------------------------- recompute M1
X = J_test()
nn_idx, dJ = exact_nn_rmse(X, JD)
P = P_test()
dTh = np.sqrt(np.mean((P - P[nn_idx]) ** 2, axis=1))
absd = np.abs(P - P[nn_idx])

keep = np.arange(N) < nn_idx
I, Jn = np.arange(N)[keep], nn_idx[keep]
dJ_k, dTh_k = dJ[keep], dTh[keep]
A_k = absd[keep]
M = len(I)
check("pair count N directed = 15307", len(nn_idx) == 15307, str(len(nn_idx)))
check("deduplicated pairs = 7666", M == REF_DEDUP, "got %d" % M)

# ---------------------------------------------------------------- frozen stored
pairs = pd.read_csv(os.path.join(COLL_DIR, "nearest_neighbor_pairs.csv"))
amb = pd.read_csv(os.path.join(COLL_DIR, "parameter_ambiguity_summary.csv"))

same_ids = (np.array(pairs["i"]) == I).all() and (np.array(pairs["j"]) == Jn).all()
check("deduplicated pair identities identical to frozen CSV", same_ids)

ddJ = float(np.max(np.abs(np.array(pairs["dJ_rmse"], float) - dJ_k)))
ddTh = float(np.max(np.abs(np.array(pairs["dTheta"], float) - dTh_k)))
# tolerance = stored-rounding precision (float64 CSV round-trip / BLAS order)
check("dJ_rmse matches frozen CSV (float64 rounding)", ddJ < 1e-9,
      "max|dev| = %.2e" % ddJ)
check("dTheta matches frozen CSV (float64 rounding)", ddTh < 1e-9,
      "max|dev| = %.2e" % ddTh)

# ---------------------------------------------------------------- aggregates
sp, p_sp = spearmanr(dJ_k, dTh_k)
pe, p_pe = pearsonr(dJ_k, dTh_k)
check("Spearman(dJ,dTheta) ~ 0.158", abs(sp - REF_SPEARMAN) < 0.001,
      "got %.4f (frozen 0.1576)" % sp)
check("Pearson(dJ,dTheta) ~ 0.079", abs(pe - REF_PEARSON) < 0.001,
      "got %.4f (frozen 0.0785)" % pe)

# random baseline (frozen draw, seed 42)
ra, rb, rd = random_pairs_seed42(P)
check("random-pair dTheta median ~ 0.349", abs(np.median(rd) - REF_MED_RAND) < 0.001,
      "got %.4f (frozen 0.3490)" % np.median(rd))
check("NN-pair dTheta median ~ 0.200", abs(np.median(dTh_k) - REF_MED_NN) < 0.001,
      "got %.4f (frozen 0.1999)" % np.median(dTh_k))

# tiers
ts = tier_stats(dJ_k, dTh_k)
for f, ref in REF_TIER_MED.items():
    got = ts[f]["med_dTh"]
    pct = "%.1f%%" % (f * 100)
    check("closest-%s median dTheta ~ %.3f" % (pct, ref), abs(got - ref) < 0.002,
          "got %.4f" % got)

# per-parameter ambiguity closest 1% (map frozen names -> spec names)
order = np.argsort(dJ_k, kind="stable")
k1 = max(1, int(round(M * 0.01)))
sel = order[:k1]
subA = A_k[sel]
name_map = dict(zip(PARAM_NAMES, PARAM_OUT))
worst = 0.0
for p, frozen_name in enumerate(PARAM_NAMES):
    out_name = name_map[frozen_name]
    got = float(np.median(subA[:, p]))
    ref = REF_PARM_AMB[out_name]
    worst = max(worst, abs(got - ref))
check("closest-1% per-parameter median ambiguity matches frozen",
      worst < 0.002, "worst dev = %.4f" % worst)

# representative pairs present in the dedup set
for (i, j), label in [(REP_TAUETL, "tau_ETL"), (REP_RRAD, "r_rad")]:
    hit = np.any((I == i) & (Jn == j))
    check("representative %s pair (%d,%d) in frozen NN set" % (label, i, j), hit)

# single-parameter dominance criterion (largest >= 2x second-largest)
for (i, j), label in [(REP_TAUETL, "tau_ETL"), (REP_RRAD, "r_rad")]:
    kk = int(np.where((I == i) & (Jn == j))[0][0])
    ad = np.sort(A_k[kk])[::-1]
    dom = ad[0] >= 2.0 * ad[1]
    check("representative %s pair passes 2x dominance (not 'pure' single-param)" % label,
          dom, "top2 |d| = %.3f, %.3f" % (ad[0], ad[1]))

allok = all(ok for _, ok, _ in checks)
# ---------------------------------------------------------------- write md
md = []
md.append("# ORIGINAL COLLISION REPRODUCTION CHECK — EXP4 Phase 0")
md.append("")
md.append("**Date:** 2026-08-25 · **Script:** `scripts/phase0.py` · "
          "**Result:** **%s** (%d/%d)" % ("PASS" if allok else "FAIL",
                                          sum(ok for _, ok, _ in checks), len(checks)))
md.append("")
md.append("Recomputed the frozen M1 nearest-neighbor analysis (per-column "
          "normalized full-curve RMSE, 131 points) from the frozen dataset "
          "`data/dataset_normalized.npz` using the exact original algorithm "
          "(`script/collision_analysis.py`), and compared every quantity "
          "against the frozen stored artifacts in `collision_analysis/`.")
md.append("")
md.append("| Check | Result | Detail |")
md.append("|---:|:---:|---|")
for desc, ok, detail in checks:
    md.append("| %s | %s | %s |" % (desc, "PASS" if ok else "**FAIL**", detail))
md.append("")
if allok:
    md.append("All quantities agree with the frozen reference to the required "
              "precision — the Phase 0 gate **passes** and the alternative "
              "metric analysis may proceed.")
else:
    md.append("**Disagreement detected — STOP.** Do not run alternative metrics "
              "until this is resolved.")
with open(os.path.join(EXP4, "ORIGINAL_COLLISION_REPRODUCTION_CHECK.md"), "w",
          encoding="utf-8") as f:
    f.write("\n".join(md) + "\n")

print("\nPhase 0 verdict: %s" % ("PASS" if allok else "FAIL"))
