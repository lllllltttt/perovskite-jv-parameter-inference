# EXP2 QC — 12 programmatic assertions

1  [PASS]  sigma transform matches frozen clip(softplus(raw)+0.01, 0.01, 1.0); max |stored - recomputed| = 1.04e-07
9a  [PASS]  z_mean point evaluation mu matches frozen (max |diff| = 2.38e-07)
9b  [PASS]  frozen mean Spearman(sigma,|err|) = 0.4283 (reference 0.4283)
9c  [PASS]  frozen 95% coverage range [0.9464, 0.9692] (reference [0.9464, 0.9692])
2  (internal check: stored decomposition was built with z = mu_z + exp(0.5 z_log_var) eps by construction; formula re-verified on a 4x50 draw, max |z - hand-computed| = 0.00e+00)
3  [PASS]  all V_head >= 0
4  [PASS]  all V_latent >= 0
5  [PASS]  V_total = V_head + V_latent (max |resid| = 0.00e+00)
6  [PASS]  f_head + f_latent = 1 where V_total nonzero (max |resid| = 0.00e+00)
7  [PASS]  no NaN/Inf in any stored decomposition array
8a  [PASS]  selected M = 500 == 500 (convergence gate)
8b  [PASS]  MC_CONVERGENCE.md documents M=500 selection
10  [PASS]  all frozen model/data/manuscript md5 unchanged (baseline recorded)
11  [PASS]  no training/optimizer calls in EXP2 scripts
12  [PASS]  frozen manuscript / evaluation_fixed / vae-v6 mtimes pre-date EXP2 (no overwrite)

## Summary: 15/15 assertions PASS
EXP2 QC: ALL PASS
