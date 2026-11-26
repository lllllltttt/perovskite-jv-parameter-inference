# Status of `forward_metrics_summary.csv`

**The `device_mae` block in this file is superseded.  Do not use it as a
verification input and do not quote it.**

| field | value here | published value | source of the published value |
|---|---|---|---|
| `MAE_Voc.median` | 0.030 V | **0.022439 V** (n = 44) | Figure 4e / Table S8 |
| `MAE_FF.median` | 0.0141 | **0.015533** = 1.5533 pp (n = 44) | Figure 4e / Table S8 |
| `MAE_Jsc.median` | 0.1119 | 0.111897 (n = 45) | agrees |
| `MAE_PCE.median` | 0.4714 | 0.471401 pp (n = 44) | agrees |

Reason: `forward_validation_postprocess.py` (which writes the per-sample table
this summary is built from) rounds Voc to 0.01 V before differencing and keeps
the one case with an undefined FF/PCE in the sample.  The manuscript uses the
interpolated zero crossing on all 45 curves, with NaN for the undefined case —
that is `code/device_metrics.py`, and the per-sample values are in
`code/figures/build/fig4_de/data_used/Figure4e_per_sample.csv` and in the SI's
`T8.2_per_sample_full_precision.csv`.

Still valid in this file: `rmse_full_median` (2.6926 mA cm⁻²) and the other
curve-RMSE summaries, which come from `forward_metrics_per_sample.csv` and agree
with the paper.

Kept unchanged for provenance; the file is a record of what that extraction
script produced, not a statement about the paper.
