# FROZEN PREDICTION REPRODUCTION CHECK (EXP3 Phase 0)

Frozen Stage-I VAE-v6 z_mean point evaluation on the frozen test set.
Reference: `evaluation_fixed/parameter_metrics.csv` (frozen evaluation pipeline).

Test N = 15307  (required 15307) -> PASS

| param | frozen ref | reproduced (log10 phys) | diff |
|---|---|---|---|
| mu_n     | 0.9063 | 0.9063 | -0.00000 | PASS |
| mu_p     | 0.9194 | 0.9194 | +0.00000 | PASS |
| tau_n    | 0.8783 | 0.8783 | +0.00000 | PASS |
| tau_p    | 0.8808 | 0.8808 | -0.00000 | PASS |
| Nc       | 0.9090 | 0.9090 | -0.00000 | PASS |
| Nv       | 0.8956 | 0.8956 | +0.00000 | PASS |
| tau_ETL  | 0.5936 | 0.5936 | -0.00000 | PASS |
| tau_HTL  | 0.7199 | 0.7199 | -0.00000 | PASS |
| rad_c    | 0.5592 | 0.5592 | +0.00000 | PASS |
| **mean** | **0.8069** | **0.8069** | -0.00000 | PASS |

## Spec reproduction targets

| param | target | reproduced | ok |
|---|---|---|---|
| mu_n     | 0.906 | 0.9063 | PASS |
| mu_p     | 0.919 | 0.9194 | PASS |
| tau_n    | 0.878 | 0.8783 | PASS |
| tau_p    | 0.881 | 0.8808 | PASS |
| Nc       | 0.909 | 0.9090 | PASS |
| Nv       | 0.896 | 0.8956 | PASS |
| tau_ETL  | 0.594 | 0.5936 | PASS |
| tau_HTL  | 0.720 | 0.7199 | PASS |
| rad_c    | 0.559 | 0.5592 | PASS |
| **mean** | **0.807** | **0.8069** | PASS |

## Inverse reconstruction QC ((a,r) -> paired log params)
max |reconstructed - original| over the 6 paired log10 parameters = 3.553e-15 -> PASS

## Verdict

**PASS — frozen predictions reproduced (all |Δ| < 0.0015). Proceeding to the prior-coordinate analysis.**
