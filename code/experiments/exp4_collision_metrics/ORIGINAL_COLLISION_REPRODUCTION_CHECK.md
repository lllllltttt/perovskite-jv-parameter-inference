# ORIGINAL COLLISION REPRODUCTION CHECK — EXP4 Phase 0

**Date:** 2026-08-25 · **Script:** `scripts/phase0.py` · **Result:** **PASS** (17/17)

Recomputed the frozen M1 nearest-neighbor analysis (per-column normalized full-curve RMSE, 131 points) from the frozen dataset `data/dataset_normalized.npz` using the exact original algorithm (`script/collision_analysis.py`), and compared every quantity against the frozen stored artifacts in `collision_analysis/`.

| Check | Result | Detail |
|---:|:---:|---|
| pair count N directed = 15307 | PASS | 15307 |
| deduplicated pairs = 7666 | PASS | got 7666 |
| deduplicated pair identities identical to frozen CSV | PASS |  |
| dJ_rmse matches frozen CSV (float64 rounding) | PASS | max|dev| = 1.08e-11 |
| dTheta matches frozen CSV (float64 rounding) | PASS | max|dev| = 9.71e-17 |
| Spearman(dJ,dTheta) ~ 0.158 | PASS | got 0.1576 (frozen 0.1576) |
| Pearson(dJ,dTheta) ~ 0.079 | PASS | got 0.0785 (frozen 0.0785) |
| random-pair dTheta median ~ 0.349 | PASS | got 0.3490 (frozen 0.3490) |
| NN-pair dTheta median ~ 0.200 | PASS | got 0.1999 (frozen 0.1999) |
| closest-1.0% median dTheta ~ 0.144 | PASS | got 0.1443 |
| closest-0.5% median dTheta ~ 0.134 | PASS | got 0.1337 |
| closest-0.1% median dTheta ~ 0.102 | PASS | got 0.1021 |
| closest-1% per-parameter median ambiguity matches frozen | PASS | worst dev = 0.0000 |
| representative tau_ETL pair (1010,2641) in frozen NN set | PASS |  |
| representative r_rad pair (8271,10258) in frozen NN set | PASS |  |
| representative tau_ETL pair passes 2x dominance (not 'pure' single-param) | PASS | top2 |d| = 0.611, 0.212 |
| representative r_rad pair passes 2x dominance (not 'pure' single-param) | PASS | top2 |d| = 0.619, 0.265 |

All quantities agree with the frozen reference to the required precision — the Phase 0 gate **passes** and the alternative metric analysis may proceed.
