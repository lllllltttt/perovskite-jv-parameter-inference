# 20261021 — expanded ratio-range matched comparison (v2, corrected evaluation)

Question: under identical data volume, network, loss and training rules, does widening the
linear-uniform prior of the three ratio coordinates from 0.2–5 to 0.05–20 change how well the
shared scales and the ratio coordinates are recovered from a 131-point J–V curve?

**v2 status.** The ten trained models, the splits, the scalers, the raw data and all training logs
are carried over unchanged from the first delivery (`..\20261021_expanded_ratio_comparison\`;
70/70 sha256 identical). What changed is the evaluation of a model on the *other* arm's test set:
v1 used the test arm's scalers for both the input normalisation and the output inverse transform;
v2 uses the model arm's scalers. Read `PATCH_NOTES.md` first — it states the root cause, the
affected artefacts and every conclusion that was withdrawn or retained. Table A is unchanged
(max |Δ| 1.6e-15); the cross-arm columns of Table B change materially.

Read `data_QA.md` (what the data is and what was verified), `EXPERIMENT_DESIGN.md` (the frozen
design and the architecture audit), `RESULTS.md` (findings, limitations, open items),
`PATCH_NOTES.md` (the repair) and `PARAGRAPHS_EN.md` (candidate manuscript / SI wording, **not**
written into any Word file).

Nothing in this directory writes to the manuscript, the SI, the raw CSVs, the frozen model, the
frozen scalers or the frozen split. No COMSOL run was made and nothing was retrained.

## Layout

```
config/experiment_config.json      frozen design + input hashes (written before training)
data/                              arm caches (regenerable), split manifests, scalers, split summary
scripts/01_data_qa.py              filter/schema/ID/duplicate/unit checks, distributions, LHS test
scripts/02_make_splits.py          writes the config first, then the subsample, splits and scalers
scripts/vae_v6_model.py            VAE-v6 architecture transcribed from script/VAE-v6.py
scripts/03a_smoke_test.py          isolated small-batch pipeline test (both arms, validation only)
scripts/03_train.py                one (arm, seed) run with full provenance
scripts/07_run_formal.py           driver for the ten formal runs (one worker per arm)
scripts/04_evaluate.py             v2 evaluation: model-arm scalers, test-arm rows/truth/baselines
scripts/11_validate_inference.py   independent reference path, provenance, fault injection, algebra
scripts/12_before_after.py         v1 -> v2 comparison tables and the diagonal reproduction assert
scripts/05_figures.py              comparison figures + figure_values.csv
scripts/10_slice_diagnostic.py     post-hoc overlap-band diagnostic (no retraining)
scripts/06_verify.py               independent recomputation of the tables from prediction files
scripts/09_report_numbers.py       prints every number quoted in RESULTS.md from out/metrics
scripts/08_package.py              light review ZIP + separate model ZIP + MANIFEST.json
scripts/13_verify_archive.py       re-opens both ZIPs and checks every member against MANIFEST.json
models/<arm>_<seed>/               encoder, decoder, param head (HDF5) + best-val-loss weights
logs/<arm>_<seed>/                 run.json, epochs.csv, history.json, stdout
out/qa/                            QA tables, verification.json, inference_validation.json,
                                   fault_injection_log.json, pdf_render/
out/metrics/                       v2 tables, inference_provenance.csv, before_after_*.csv
out/metrics_v1/                    the superseded v1 tables (read-only reference)
out/predictions/                   per-sample truth and prediction, 20 files (10 models x 2 tests)
out/predictions_v1/                the superseded v1 predictions (read-only reference)
figures/                           fig01 distributions, fig02 Skill+RMSE, fig03 paired ΔRMSE
figures_v1/                        the superseded v1 figure files
deliverables/                      review_package_<date>_v2.zip, models_<date>_v2.zip, MANIFEST.json
```

## Reproduce

Training is **not** re-run — the ten model directories are part of the delivery. To regenerate the
evaluation and everything downstream of it:

```
py -3 scripts\04_evaluate.py           # 20 predictions, all metric tables, inference_provenance.csv
py -3 scripts\11_validate_inference.py # 23 checks; must print FAILURES 0 and exit 0
py -3 scripts\12_before_after.py       # diagonal max |v2-v1| must be < 1e-12
py -3 scripts\05_figures.py
py -3 scripts\10_slice_diagnostic.py   # overlap-band diagnostic (post-hoc, no retraining)
py -3 scripts\06_verify.py             # 70 checks; exit 0 required
py -3 scripts\09_report_numbers.py     # numbers quoted in RESULTS.md
py -3 scripts\08_package.py
```

`04_evaluate.py` must be run **before** `11` and `12` (they read its outputs); `05` and `10` read
`out/predictions` and `out/metrics`.

From scratch the order is `01 → 02 → 03a → 07 → 04 → 11 → 12 → 05 → 10 → 06 → 09 → 08 → 13`.
`03_train.py` skips a run whose `run.json` says `completed`; use `--force` to retrain and note that
a forced rerun keeps the earlier attempt in `logs/runs.jsonl`. A failed run is written with
`status: "failed"` and its traceback; nothing is retried or substituted silently.

## Environment

Python 3.12.6, TensorFlow 2.20.0, Keras 3 (bundled), NumPy / pandas / scikit-learn / SciPy /
Matplotlib. The exact versions of each run are stored in its `run.json`. Deterministic ops are
enabled; oneDNN custom ops are disabled.
