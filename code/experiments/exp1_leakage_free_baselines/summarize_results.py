# -*- coding: utf-8 -*-
"""
Build results/multiseed_summary.csv and results/model_level_summary.csv from
results/per_seed_metrics.csv.
"""
import os, csv, json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, os.environ.get("EXP1_RESULTS_DIR", "results"))
CSV = os.path.join(RES, "per_seed_metrics.csv")
MODELS_DIR = os.path.join(HERE, os.environ.get("EXP1_MODELS_DIR", "models"))

PARAMS = ["mu_n", "mu_p", "tau_n", "tau_p", "Nc", "Nv", "tau_ETL", "tau_HTL", "rad_c"]
MODELS = ["vae", "det_ae", "mlp"]
SEEDS = [20260824, 20260825, 20260826, 20260827, 20260828]

rows = []
with open(CSV, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        rows.append(r)

def grab(model, param, col):
    vals = [float(r[col]) for r in rows if r["model"] == model and r["parameter"] == param]
    return vals

# ---- multiseed_summary.csv ----
MSUMMARY = os.path.join(RES, "multiseed_summary.csv")
cols = ["pearson_r", "mae_norm", "rmse_norm", "mae_decades", "gaussian_nll",
        "coverage_95", "spearman_sigma_error"]
with open(MSUMMARY, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    # interleaved (mean, sd) per column — MUST match the row-write order below
    header = ["model", "parameter"]
    for c in cols:
        header += [f"{c}_mean", f"{c}_sd"]
    w.writerow(header)
    for model in MODELS:
        for param in PARAMS + ["ALL"]:
            rec = [model, param]
            for c in cols:
                vals = grab(model, param, c)
                rec += [round(float(np.mean(vals)), 6), round(float(np.std(vals, ddof=1)), 6)]
            w.writerow(rec)
print("wrote", MSUMMARY)

# ---- model_level_summary.csv ----
MLSUMMARY = os.path.join(RES, "model_level_summary.csv")
with open(MLSUMMARY, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["model", "mean_parameter_r_mean", "mean_parameter_r_sd",
                "mean_test_nll", "mean_95coverage", "mean_sigma_error_spearman",
                "param_count", "mean_train_time_s", "mean_best_epoch", "mean_stop_epoch"])
    for model in MODELS:
        # per-seed ALL rows
        allr = [float(r["pearson_r"]) for r in rows if r["model"] == model and r["parameter"] == "ALL"]
        nll = [float(r["gaussian_nll"]) for r in rows if r["model"] == model and r["parameter"] == "ALL"]
        cov = [float(r["coverage_95"]) for r in rows if r["model"] == model and r["parameter"] == "ALL"]
        rho = [float(r["spearman_sigma_error"]) for r in rows if r["model"] == model and r["parameter"] == "ALL"]
        epochs = [int(r["stop_epoch"]) for r in rows if r["model"] == model and r["parameter"] == "ALL"]
        best = [int(r["best_epoch"]) for r in rows if r["model"] == model and r["parameter"] == "ALL"]
        # parameter count / train time from metadata
        pc = []
        tt = []
        for seed in SEEDS:
            md = os.path.join(MODELS_DIR, model, "seed%d" % seed, "metadata.json")
            if os.path.exists(md):
                with open(md) as fh:
                    m = json.load(fh)
                pc.append(m["param_count"]); tt.append(m.get("train_seconds", 0.0))
        w.writerow([model,
                    round(float(np.mean(allr)), 6), round(float(np.std(allr, ddof=1)), 6),
                    round(float(np.mean(nll)), 6), round(float(np.mean(cov)), 6),
                    round(float(np.mean(rho)), 6),
                    int(np.mean(pc)) if pc else "",
                    round(float(np.mean(tt)), 0) if tt else "",
                    round(float(np.mean(best)), 1), round(float(np.mean(epochs)), 1)])
print("wrote", MLSUMMARY)
