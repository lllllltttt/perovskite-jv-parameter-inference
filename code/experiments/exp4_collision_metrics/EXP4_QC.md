# EXP4 QC — COLLISION-METRIC ROBUSTNESS

**Date:** 2026-08-25 · **Script:** `scripts/qc.py` · **Result:** **PASS** (70/70)

| Check | Result | Detail |
|---:|:---:|---|
| Q01 M1 Spearman(dJ,dTheta) reproduces frozen 0.1576 | PASS | got 0.1576 |
| Q02 M1 Pearson(dJ,dTheta) reproduces frozen 0.0785 | PASS | got 0.0785 |
| Q03 M1 NN-pair median dTheta reproduces frozen 0.1999 | PASS | got 0.1999 |
| Q04 M1 closest-1.0% median dTheta ~ 0.1443 | PASS | got 0.1443 |
| Q04 M1 closest-0.5% median dTheta ~ 0.1337 | PASS | got 0.1337 |
| Q04 M1 closest-0.1% median dTheta ~ 0.1021 | PASS | got 0.1021 |
| Q05 M1 closest-1% per-param ambiguity matches frozen | PASS | worst |dev| = 0.0000 |
| Q06 directed_nn_M1.csv exists (pre-dedup save) | PASS |  |
| Q06b M1 directed NN self-excluded | PASS | 15307 rows |
| Q06 directed_nn_M2.csv exists (pre-dedup save) | PASS |  |
| Q06b M2 directed NN self-excluded | PASS | 15307 rows |
| Q06 directed_nn_M3.csv exists (pre-dedup save) | PASS |  |
| Q06b M3 directed NN self-excluded | PASS | 15307 rows |
| Q06 directed_nn_M4.csv exists (pre-dedup save) | PASS |  |
| Q06b M4 directed NN self-excluded | PASS | 15307 rows |
| Q06 directed_nn_M5.csv exists (pre-dedup save) | PASS |  |
| Q06b M5 directed NN self-excluded | PASS | 15307 rows |
| Q06 directed_nn_M6.csv exists (pre-dedup save) | PASS |  |
| Q06b M6 directed NN self-excluded | PASS | 15307 rows |
| Q07 M1 dedup count = 7666 (not forced elsewhere) | PASS | M1=7666.000000 |
| Q07b per-metric dedup reported (not forced to 7666) | PASS | unique counts = {'M1': 7666, 'M2': 7635, 'M3': 7638, 'M4': 7666, 'M5': 7670} |
| Q08 random-pair baseline seed42 ~ 0.3490 | PASS | got 0.3490 |
| Q08b fixed baseline seed20260827 ~ 0.349 (100k unique pairs) | PASS | got 0.3489, pairs=100000 |
| Q09 M1 all-NN dTheta below random (R_NN<1) | PASS | R_NN=0.573 |
| Q10 M1 closest-1% dTheta below random (R_1pct<1) | PASS | R_1pct=0.413 |
| Q09 M2 all-NN dTheta below random (R_NN<1) | PASS | R_NN=0.620 |
| Q10 M2 closest-1% dTheta below random (R_1pct<1) | PASS | R_1pct=0.520 |
| Q09 M3 all-NN dTheta below random (R_NN<1) | PASS | R_NN=0.620 |
| Q10 M3 closest-1% dTheta below random (R_1pct<1) | PASS | R_1pct=0.481 |
| Q09 M4 all-NN dTheta below random (R_NN<1) | PASS | R_NN=0.594 |
| Q10 M4 closest-1% dTheta below random (R_1pct<1) | PASS | R_1pct=0.436 |
| Q09 M5 all-NN dTheta below random (R_NN<1) | PASS | R_NN=0.594 |
| Q10 M5 closest-1% dTheta below random (R_1pct<1) | PASS | R_1pct=0.436 |
| Q10b M1 every tier median < random 0.349 | PASS | max tier median = 0.1683 |
| Q10b M2 every tier median < random 0.349 | PASS | max tier median = 0.2044 |
| Q10b M3 every tier median < random 0.349 | PASS | max tier median = 0.1994 |
| Q10b M4 every tier median < random 0.349 | PASS | max tier median = 0.1749 |
| Q10b M5 every tier median < random 0.349 | PASS | max tier median = 0.1746 |
| Q11 M1 mutual-NN fraction in [0.5,0.6] | PASS | 0.5307 |
| Q11 M2 mutual-NN fraction in [0.5,0.6] | PASS | 0.5549 |
| Q11 M3 mutual-NN fraction in [0.5,0.6] | PASS | 0.5492 |
| Q11 M4 mutual-NN fraction in [0.5,0.6] | PASS | 0.5356 |
| Q11 M5 mutual-NN fraction in [0.5,0.6] | PASS | 0.5350 |
| Q12 M1 ambiguity ranks are a permutation of 1..9 | PASS | [1, 2, 3, 4, 5, 6, 7, 8, 9] |
| Q12 M2 ambiguity ranks are a permutation of 1..9 | PASS | [1, 2, 3, 4, 5, 6, 7, 8, 9] |
| Q12 M3 ambiguity ranks are a permutation of 1..9 | PASS | [1, 2, 3, 4, 5, 6, 7, 8, 9] |
| Q12 M4 ambiguity ranks are a permutation of 1..9 | PASS | [1, 2, 3, 4, 5, 6, 7, 8, 9] |
| Q12 M5 ambiguity ranks are a permutation of 1..9 | PASS | [1, 2, 3, 4, 5, 6, 7, 8, 9] |
| Q13 ambiguity-rank corr diagonal = 1 | PASS |  |
| Q13b ambiguity-rank corr matrix symmetric | PASS |  |
| Q14 pair-overlap diagonal = 1 | PASS |  |
| Q14b pair-overlap matrix symmetric | PASS |  |
| Q14c pair-overlap values in [0,1] | PASS |  |
| Q15 union pair count >= each metric's unique count | PASS | union=19182 |
| Q15b all cross-metric percentiles in [0,1] | PASS |  |
| Q15c every union row has 5 distances + 5 percentiles | PASS |  |
| Q16 tau_ETL_dominant pair identity in CSV | PASS |  |
| Q16b tau_ETL_dominant dTheta matches direct recompute (csv 4-dp) | PASS | csv=0.2205 dir=0.220516 |
| Q16c tau_ETL_dominant all 5 distances match direct recompute | PASS | worst dev=4.72e-07 |
| Q16d tau_ETL_dominant param |d| matches direct recompute (csv 4-dp) | PASS |  |
| Q16e tau_ETL_dominant labeled tau_ETL-dominant with >=2x dominance | PASS | top2 |d| = 0.611, 0.212 |
| Q16 r_rad_dominant pair identity in CSV | PASS |  |
| Q16b r_rad_dominant dTheta matches direct recompute (csv 4-dp) | PASS | csv=0.2394 dir=0.239371 |
| Q16c r_rad_dominant all 5 distances match direct recompute | PASS | worst dev=4.03e-07 |
| Q16d r_rad_dominant param |d| matches direct recompute (csv 4-dp) | PASS |  |
| Q16e r_rad_dominant labeled r_rad-dominant with >=2x dominance | PASS | top2 |d| = 0.619, 0.265 |
| Q17 robust pair meets predeclared criterion (>=3 metrics, bottom-1% + dTheta>tier med) | PASS | metrics=['M1', 'M4', 'M5'] (3) |
| Q18 M6 supplementary CSV present | PASS |  |
| Q18b M6 excluded from primary metric_level_summary | PASS |  |
| Q19 scripts write only inside exp4 directory | PASS | no external writes found |

All 17 assertions per the EXP4 specification §24 (plus reproducibility sub-checks) hold. The reported numbers are internally consistent with the frozen reference and the predeclared analysis protocol.
