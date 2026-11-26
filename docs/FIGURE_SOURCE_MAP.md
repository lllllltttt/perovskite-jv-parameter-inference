# Figure source map

Maps every figure of `Manuscript_20261126_final.docx` and
`Supplementary_Information_20261126_final.docx` to its scientific source data, the
script that computes it, and the composition file that places the panels.

**Read this first.** The figure numbering changed late in the project. Several
staging directories keep the *old* numbers: old S4 → current S5, old S5 → current S6,
old S6 → current S7, old S7 → current S8, old S8 → current S9, old S9 → current S10,
old S10 → current S11, old S3c → current S4. The table below uses the **current**
numbers from the final documents. Directory names such as
`build/s5_meanlines/` or `build/s9_arial/` follow that old numbering.

## How the figures were made

1. matplotlib panels, written by a script in `code/figures/` or
   `code/figures/build/<dir>/`.
2. Manual composition in PowerPoint:
   * main text — `figure_source/final_body_figs/正文_fig.pptx` (5 slides)
   * SI — `figure_source/final_si_figs/SI_fig.pptx` (11 slides)
3. Export to SVG (`图片1.svg` … `图片5.svg`, `SI1.svg` … `SI11.svg`).
4. A high-resolution / vector repair pass (`figure_source/highres/`), then embedding
   into the Word document.

The layout — panel placement, panel letters, titles and tick fonts — belongs to the
PowerPoint deck, **not** to the matplotlib script. Only Panel S3 is a direct
matplotlib export in the final version.

## Main text

| Figure | Content | Source data | Panel script | Composition / final artwork |
|---|---|---|---|---|
| **1** | Framework: device structure, VAE, three evaluations | schematic only; dimensional values in `build/layout_v2/data_used/Figure1_schematic_values.csv` | design source `build/…/fig1_simplified.py` (not the final artwork) | **drawn in PowerPoint** — `final_body_figs/正文_fig.pptx` slide 1 → `图片1.svg`. No numeric dataset. |
| **2** | Recovery of shared scales a and log-ratios r | `build/fig2_revision/data_used/fig2_coordinates.csv` (15,307 rows), `fig2_metrics.csv`; upstream `_frozen_preds.npz` | `build/fig2_revision/scripts/fig2_data.py` → `build/fig2_assets/scripts/fig2_final_assets.py` (panels a1–a3, b1–b3 + colourbars) | `正文_fig.pptx` slide 2. Panels (c) correlation summary and (d) MAE reduction are **native PowerPoint charts** whose values were entered from `fig2_metrics.csv`; no script reproduces them. |
| **3** | Parameter differences between neighbouring J–V curves | `build/fig345/data_used/fig3_case_*.csv`, `fig3_pairs_v2.csv` (11,245 pairs), `fig3_random_baseline_v2.csv` | `build/fig3ab/scripts/fig3ab_rebuild.py` (a,b); `build/fig345/scripts/fig3_rebuild.py` (c,d) | `正文_fig.pptx` slide 3 |
| **4** | Physical back-substitution of inferred parameters | `build/fig4_abc/data_used/Figure4ac_*.csv`, `build/fig4d/data_used/Figure4d_per_sample.csv`, `build/fig4_de/data_used/Figure4e_per_sample.csv`; upstream `code/analysis/forward_validation_unbiased/forward_metrics_per_sample.csv`, `code/analysis/decoder_comsol_audit/decoder_comsol_metrics_per_sample.csv` | `build/fig4_abc/scripts/fig4_abc_standalone.py` (a–c), `build/fig4d/scripts/fig4d_clean_half.py` (d), `build/fig4_de/scripts/fig4e_ff_pp.py` (e) | `正文_fig.pptx` slide 4 |
| **5** | Predictive-interval calibration and noise sensitivity | `build/fig5/data_used/Figure5_plotting_values.csv`; upstream `code/analysis/evaluation_fixed/calibration_fixed.csv`, `code/analysis/noise_robustness/*.csv`, `build/interval_repair_A1/outputs/tables/` | `build/fig5/scripts/fig5_standalone.py` (b–d), `build/fig345/scripts/fig5_rebuild.py` (a,e) | `正文_fig.pptx` slide 5 |

## Supplementary information

| Figure | Content | Source data | Panel script | Composition |
|---|---|---|---|---|
| **S1** | Parameter distributions + pairwise correlations | `JV_database_9D_interface_lifetimes-2.csv` (N = 102,046) | `code/figures/plot_FigS1_eda.py` | split by `build/split_s1/scripts/split_svg.py`; `SI_fig.pptx` slide 1; final user-edited `SI1.svg` |
| **S2** | Correlation-based J–V sensitivity vs recoverability | `code/analysis/sensitivity_recomputed/sensitivity_recomputed.csv`, `code/analysis/evaluation_fixed/parameter_metrics.csv` | `code/figures/plot_FigS2_sensitivity_recoverability.py` (asserts ρ = 0.533, p = 0.139 log-space; 0.683, p = 0.042 raw) | `build/split_s2`; `SI_fig.pptx` slide 2; `SI2.svg` |
| **S3** | Cycle cases + voltage-resolved forward error | `code/analysis/decoder_comsol_audit/decoder_comsol_metrics_per_sample.csv`, `voltage_resolved_consistency.csv`, `forward_validation_unbiased/comsol_{pred,true}/` | `build/si_update/scripts/plot_S3_relayout.py` | **direct matplotlib export** `s3/FigureS3.svg` — the only SI figure not composed in PowerPoint |
| **S4** | Distribution and correlates of cycle gaps | `code/analysis/decoder_comsol_audit/decoder_comsol_metrics_per_sample.csv` | `code/figures/plot_FigS3_cycle_gap_micropatch.py`; panels split by `build/split_s3` | `SI_fig.pptx` slide 3 → `SI4.svg` → `build/si_update` → vector patch `S4_vector.svg` |
| **S5** | Distributions of predictive scales σθ | `dataset_normalized.npz` + frozen model; `code/analysis/evaluation_fixed/sigma_statistics_fixed.csv` | `code/figures/plot_FigS4_fixed_sigma_distribution.py`; `build/split_s456`; Arial pass `build/s5_meanlines` | `SI_fig.pptx` slide 5; final uses the high-resolution rebuild `figure_source/highres/figs/FigureS5.svg` |
| **S6** | Predictive scale vs absolute parameter error | same as S5 plus `parameter_metrics.csv`, `uncertainty_error_fixed.csv` | `code/figures/plot_FigS5_fixed_uncertainty_error_polish.py`; `build/split_s456`; Arial pass `build/s6_arial` | `SI_fig.pptx` slide 6 → `SI6.svg` (68 MB). The Word document embeds a **600 dpi PNG re-render**, not the SVG. |
| **S7** | Recovery of the nine individual parameters | `_frozen_preds.npz`; `evaluation_fixed/parameter_metrics.csv` | `build/layout_v2/scripts/figS6_nineparam.py` (asserts the nine ρ) | `SI_fig.pptx` slide 7; final uses `figure_source/highres/figs/FigureS7.svg` |
| **S8** | ECDF: nearest-neighbour vs random pairs | `fig3_pairs_v2.csv` (11,245), `fig3_random_pairs.csv.gz` (199,985), `fig3_pair_summary_v2.csv` | `build/layout_v2/scripts/figs7_ecdf.py`; split by `build/split_s7` | `SI_fig.pptx` slide 8 → `SI8.svg`; panel (d) raster replaced by vector `build/split_s7/out/svg/S7b.svg` in `build/si_update/scripts/build_s8_dfix.py` |
| **S9** | Sampling-coordinate distributions, original vs expanded | `JV_database_9D_interface_lifetimes-newratio.csv` (24,274) + `JV_database_9D_interface_lifetimes-2.csv` (102,046) | `build/layout_v2` → `fig01_data_distributions`; split by `build/split_s8`; Arial pass `build/s9_arial` | `SI_fig.pptx` slide 9 |
| **S10** | Prediction performance on each model's own test set | `expanded_ratio_comparison/out/metrics/table_B_common_tests.csv`, `table_A_own_distribution.csv` | `build/s10_perf/scripts/performance_figures.py` | `SI_fig.pptx` slide 10; `SI10.svg` |
| **S11** | Paired comparison on common test sets | `expanded_ratio_comparison/out/metrics/paired_differences.csv` | `build/s11_common/scripts/common_test_figures.py`; labels `build/s11_labels/scripts/common_test_labels.py` | `SI_fig.pptx` slide 11; `SI11.svg` |

## What is *not* script-reproducible

* **Figure 1** — a PowerPoint schematic; no numeric dataset, no generating script.
* **Figure 2 (c) and (d)** — native PowerPoint charts. The values are in
  `fig2_metrics.csv`, but the chart objects were built by hand. This is the one
  scientific panel pair without a generating script.
* **Every panel layout** — panel letters, titles, annotation placement and font
  choices live in the `.pptx` decks.

## Shared library and the extractor

The figure-build scripts import two shared modules:

* `v2lib` — vendored at `code/comsol_validation/_tools/v2lib.py`.  The archived
  scripts add `<BASE>/supplementary_validation_v2/_tools` to `sys.path`; when
  running them from a clone, edit that line.  Its `device_metrics` is the
  published convention, now re-implemented and tested as
  `code/device_metrics.py` (the two agree to 1e-12).
* `_frozen_preds.npz` — produced by the single canonical extractor
  `code/pipeline/00_extract_frozen_predictions.py` (see
  `code/figures/README_EXTRACTOR.md`).  The figure scripts read it from their own
  directory.

## Panel-level source data

`code/figures/build/*/data_used/` holds the exact arrays each panel was drawn from,
so a figure can be checked without rerunning the analysis. The upstream per-sample
predictions for all 15,307 test curves are in
`figure_source/_frozen_preds.npz` (release asset).
