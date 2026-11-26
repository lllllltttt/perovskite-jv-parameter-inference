# MONTE-CARLO CONVERGENCE GATE

Fixed subset: 1000 test samples (seed 20260825), nested draws (first M of a 500-draw master, seed 20260825).
Reference: M = 500.  Quantities compared: mu_total, V_latent, V_head, V_total, f_latent, sigma_total.

## Convergence criterion (V_total, f_latent — principal nonzero cases)

| M | med-relerr V_total | q95-relerr V_total | med-relerr f_latent | q95-relerr f_latent | pass |
|---|---|---|---|---|---|
| 20 | 0.0012 | 0.0057 | 0.2140 | 0.5782 | - |
| 50 | 0.0008 | 0.0037 | 0.1320 | 0.3704 | - |
| 100 | 0.0005 | 0.0023 | 0.0852 | 0.2489 | - |
| 200 | 0.0003 | 0.0015 | 0.0532 | 0.1525 | - |

**Selected M = 500** (smallest passing, else M=500).

## Per-quantity error at selected M = 500  (relative / absolute)

| quantity | med-rel | q95-rel | med-abs | q95-abs | units of reference |
|---|---|---|---|---|---|
| mu_total   | 0.0000 | 0.0000 | 0.00e+00 | 0.00e+00 | ~5.39e-01 |
| V_latent   | 0.0000 | 0.0000 | 0.00e+00 | 0.00e+00 | ~6.59e-06 |
| V_head     | 0.0000 | 0.0000 | 0.00e+00 | 0.00e+00 | ~1.26e-02 |
| V_total    | 0.0000 | 0.0000 | 0.00e+00 | 0.00e+00 | ~1.26e-02 |
| f_latent   | 0.0000 | 0.0000 | 0.00e+00 | 0.00e+00 | ~5.52e-04 |
| sigma_total | 0.0000 | 0.0000 | 0.00e+00 | 0.00e+00 | ~1.12e-01 |

## Near-zero absolute check (quantities near zero should be judged by absolute error)

- V_latent   median |ref| = 6.591e-06 ; median abs err = 0.000e+00 ; q95 abs err = 0.000e+00
- V_head     median |ref| = 1.255e-02 ; median abs err = 0.000e+00 ; q95 abs err = 0.000e+00

## f_latent distribution (selected M vs M=500 reference)

| | selected M=500 | M=500 |
|---|---|---|
| mean | 0.0011 | 0.0011 |
| median | 0.0006 | 0.0006 |
| q25 | 0.0002 | 0.0002 |
| q75 | 0.0014 | 0.0014 |
| q90 | 0.0029 | 0.0029 |
| q95 | 0.0041 | 0.0041 |

## Decision

Selected M = **500** for the full-test decomposition.
