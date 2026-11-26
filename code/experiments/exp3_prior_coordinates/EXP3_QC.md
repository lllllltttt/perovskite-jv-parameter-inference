# EXP3 QC — Programmatic Assertions (§19)

**Date:** 2026-08-25 · **Script:** `scripts/qc.py` · **Result:** **PASS** (12/12)

| ID | Check | Result | Detail |
|---:|-------|:------:|--------|
| Q01 | Phase 0: frozen marginal Pearson == manuscript (test N=15307) | PASS | max |recomputed - manuscript| = 0.0004 |
| Q02 | log10 physical reconstruction exact (norm -> log10) | PASS | max |rec - log10(raw)| = 3.55e-15 |
| Q03 | population sizes: retained=102046, train=71432, test=15307 | PASS | retained=102046 train=71432 test=15307 |
| Q04 | prior geometry: SD(a)/SD(0.5r) >> 1 for all pairs | PASS | ratios = 5.4, 12.7, 4.3 |
| Q05 | r(a, r) ~ 0 across pairs (no filtering-induced dependence) | PASS | worst |r(a,r)| = 0.0077 |
| Q06 | marginal pair corr reproduced by shared-scale algebra (vs manuscript) | PASS | worst |algebra - manuscript| = 0.007 |
| Q07 | recoverability hierarchy: shared-scale r > 0.85 > ratio r | PASS | a r range [0.882, 0.925], ratio r max 0.429 |
| Q08 | info beyond prior: shared-scale skill > 0.75, ratio skill < 0.2 | PASS | a skill min 0.777, ratio skill max 0.184 |
| Q09 | prior-only baseline built from TRAINING data only (recomputed matches) | PASS | recomputed prior RMSE a_mu 0.870826 vs CSV 0.870826 |
| Q10 | ratio error 10^med_abs in (1.5, 1.7) for all three ratios | PASS | factors = 1.571, 1.614, 1.637 |
| Q11 | shuffled control: observed r >= 20 SD above pairing null for every coord | PASS | min (obs - null)/sd = 29 |
| Q12 | architecture-stable hierarchy (gap>0.4) + frozen model within 2SD of 5-seed vae | PASS | gaps = vae=0.45, det_ae=0.44, mlp=0.47; frozen-within-2SD=True |

All twelve assertions PASS — the EXP3 result files are internally consistent, reproduce the frozen manuscript values, and support the shared-scale-dominance reading of the prior-coordinate decomposition.