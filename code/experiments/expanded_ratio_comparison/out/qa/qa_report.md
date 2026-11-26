# QA report — v2 cross-arm evaluation repair (2026-10-21)

Scope: verify that (i) the repaired evaluation is correct, (ii) the repair did not touch any
training artefact, and (iii) the published numbers are reproducible from the delivered per-sample
CSVs. All commands were run on the delivery machine; exit codes and maxima are quoted from the
scripts' own JSON/log output, not from memory.

## 1. Scripts and outcomes

| script | what it checks | result |
|---|---|---|
| `01_data_qa.py` | filter rules re-applied, schema/ID/duplicate/unit checks, LHS provenance, distributions | PASS (`out/qa/qa_summary.json`); 0 rows rejected by re-applied rules in either delivered CSV |
| `06_verify.py` | splits, train-only scaler fitting, prediction/split row alignment, Table-B recomputation, run completion, initial-weight identity, figures present | **70 checks, 0 FAIL**; max recomputation difference **6.7e-16** over 720 coordinate values (`out/qa/verification.json`) |
| `11_validate_inference.py` | provenance ownership, independent reference path, model alignment, fault injection, metric/a–r algebra, hash invariance | **23 checks, 0 FAIL** (`out/qa/inference_validation.json`); exits non-zero if any check fails, any expected fault is missed, or a fault escapes its sandbox |
| `12_before_after.py` | diagonal reproduction of v1; cross-arm change table | diagonal max \|Δ\| = **1.6e-15** (< 1e-12 assert); cross-arm max \|Δ\| = 3.15 (Skill) |
| `09_report_numbers.py` | every number quoted in `RESULTS.md` printed from the CSVs | ran; its stdout is `out/qa/report_numbers.txt` |

## 2. Provenance checks (requirement 1)

`out/metrics/inference_provenance.csv` has 20 rows (2 model arms × 5 seeds × 2 test arms). For each
row:

- `input_scaler_owner == model_arm` and `output_scaler_owner == model_arm` — asserted for all 20.
- `encoder_sha256`, `decoder_sha256`, `param_head_sha256` recomputed from the files on disk and
  matched.
- `test_split_sha256` matches `data/split_manifest_<test_arm>.csv`.
- `test_sample_id_sha256` and `test_truth_sha256` recomputed from `arm_<test_arm>.npz`.

Additionally the evaluator asserts, for every same-arm combination, that
`current_scaler[arm].transform(J_physical) == J_scaled` exactly (max difference 0.0), which proves
that the archived physical currents are the ones the training pipeline normalised, i.e. that the
cross-arm input is built from the same physical representation and not from an inverse-transformed
array.

## 3. Independent reference path (requirement 2)

`11_validate_inference.py` does not import `04_evaluate.py` or its `predict` helper. It loads the
HDF5 submodels and the pickled scalers directly and recomputes, for a 64-row batch deliberately
enriched in extreme current values (32 smallest + 32 largest max-normalised current; the full test
set has only 0.00–0.03 % of inputs outside the training current range, so a uniform batch would
exercise the path weakly), all four (model_arm, test_arm) combinations at seed 20261021:

| combination | prediction max \|Δ\| | truth max \|Δ\| |
|---|---|---|
| original on original | 3.553e-15 | 3.553e-15 |
| original on expanded | 3.553e-15 | 3.553e-15 |
| expanded on original | 3.553e-15 | 3.553e-15 |
| expanded on expanded | 3.553e-15 | 3.553e-15 |

The difference is float32/float64 promotion in the reference implementation, not a logic
difference. The batch uses exactly the model arm's input scaler and inverse-transforms with the
model arm's parameter scaler.

## 4. Model alignment and shared baselines (requirement 3)

Within each common test set, the two models' prediction files have identical `Sample_ID` order
(max difference 0.0), identical `source_row` and identical truth columns (max 0.0). The Skill_MSE
and MAE-reduction baselines are computed once from the test arm's training partition and are
identical for both models; the evaluator writes them per row in `table_B_common_tests.csv`
(`train_mean`, `train_median`), and the validation compares them across model arms.

## 5. Fault injection (requirement 4)

Run on a 64-row copy with the evaluator's functions, in a sandbox; the official prediction CSVs
and the model files were re-hashed afterwards and are unchanged.

| fault | injected | outcome | magnitude |
|---|---|---|---|
| A | output inverse transform uses the **test** arm's parameter scaler (the v1 output error) | detected | 0.257 log10 max shift |
| B | input transform uses the **test** arm's current scaler (the v1 input error) | detected | 3.634 log10 max shift |
| C | a provenance row whose `input_scaler_owner` is forged to the other arm, scaler file unchanged | detected | ownership assertion fails |

v1 applied A and B together, which is why some v1 cells moved by more than either single fault.
Log: `out/qa/fault_injection_log.json`. A deliberately *unfaulted* control run through the same
harness reproduces the reference predictions, so the detector does not fire spuriously.

## 6. Metrics and algebra (requirement 6)

- All 300 coordinate metric rows in `table_B_common_tests.csv` were recomputed from the per-sample
  prediction CSVs with the formulas written out independently (not via `metrics_lib`): max
  absolute difference **6.7e-16**.
- 0 rows carry an `undefined` (zero-denominator) flag.
- `a = (L0+L1)/2` and `r = L0−L1` hold on both true and predicted columns: max \|Δ\| **1.1e-14**.
- No second log10: `10**true_log10` equals `true_phys` to 4.3e-13, and the coordinate magnitudes
  are physical log10 values (a_mu −6.58…−2.36, a_tau −9.48…−1.53, a_D 22.45…26.56, r −1.30…1.30).
- `06_verify.py` independently recomputes the same 720 values from the CSVs with a second formula
  implementation: max 6.7e-16.

## 7. Hash invariance (requirement 7)

| class | n | result |
|---|---|---|
| arm caches (`arm_*.npz`) | 2 | identical to v1 |
| param/current scalers (`*.pkl`) | 4 | identical |
| split manifests + split summary | 3 | identical |
| `config/experiment_config.json` | 1 | identical |
| model files (`encoder/decoder/param_head.h5`) | 60 | identical |
| **total** | **70** | **70/70 identical** |

Raw input CSVs still match the hashes frozen in `config/experiment_config.json`. Therefore no
data, split, scaler, model or config was changed; the only difference between v1 and v2 is the
evaluation code and everything computed from it.

## 8. Figures and visual QA (requirement: open every PNG, render every PDF)

| figure | PNG | PDF rendered | inspection |
|---|---|---|---|
| `fig01_data_distributions` | opened | yes (`out/qa/pdf_render/`) | three per-decade log10 density panels (g_mu, g_tau, g_D) and three linear-q panels with the old 0.2–5 band shaded; axes labelled with units; legend complete; nothing clipped |
| `fig02_skill_and_error` | opened | yes | panel (a) Skill_MSE per coordinate, panel (b) RMSE in log10 units; error bars are seed SD; Table-A values; bar labels legible; no overlap |
| `fig03_common_test_paired` | opened | yes | panel (a) paired ΔRMSE on the common original test (all positive), panel (b) on the common expanded test (all negative); zero line present; coordinate labels and axes legible |

`fig01` and `fig02` are byte-identical to the v1 files (sha256 match), which is expected because
they depend only on the data and on Table A. `fig03` changed, as it must: its cross-arm values are
the repaired ones. Renderings were produced with PyMuPDF at 2× and inspected visually; no
cropping, missing glyphs, wrong units or legend errors were found.

`figures/figure_values.csv` was regenerated with the figures and is consistent with
`summary_mean_sd.csv` and `paired_difference_summary.csv`.

## 9. Known residuals

- The 64-row extreme-heavy batch is not a random sample; it exists to stress the input path. The
  four combinations agree to 3.6e-15, but the check is a consistency check between two
  implementations, not an absolute ground truth.
- Fault C tests the provenance assertion, not a numerical path; it is a logic check.
- `09_report_numbers.py` prints to the console with the Windows code page; the `±` sign appears as
  a replacement glyph in a redirected log. This is a display artefact only; the CSV values are
  correct and are what the report quotes.
- No test-set minimum or maximum is used anywhere: cross-arm inputs can exceed the model arm's
  training current range (0.00–0.03 % of test inputs), and that is reported rather than clipped, as
  required.

## 10. Archive verification

`08_package.py` writes `deliverables/review_package_20261021_v2.zip` (152 files, 34.3 MB) and
`deliverables/models_20261021_v2.zip` (60 files, 4.3 MB) plus `MANIFEST.json` with per-file size
and sha256. `13_verify_archive.py` re-opens both archives, recomputes size and sha256 of every
member, compares them with the manifest, checks the member lists in both directions (no
unrecorded file) and checks a list of required members. Result: **0 failures**
(`out/qa/archive_verification.txt`). The superseded v1 predictions (71 MB) are not in the review
archive; the manifest points to the untouched v1 delivery for them, with the v1 archive's full
sha256.
