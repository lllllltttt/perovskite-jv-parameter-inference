# -*- coding: utf-8 -*-
"""
CLI: evaluate_one.py <family> <seed> <outdir> [--tag pilot]

Loads eval_bundle.npz (+ metadata) for a trained model and computes the full
per-seed metric set on the untouched test cohort. Appends one row per parameter
(plus an 'ALL' mean row) to results/per_seed_metrics.csv. Returns the metric
dict (JSON on stdout) so a driver can collect it.
"""
import sys, os, json, csv
import numpy as np
from scipy.stats import pearsonr, spearmanr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exp1_lib import NOMINAL, PARAM_NAMES, SHORT_NAMES, load_scalers

RESULTS_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "per_seed_metrics.csv")
COLS = ["model", "seed", "parameter", "pearson_r", "mae_norm", "rmse_norm",
        "mae_decades", "median_abs_log_error", "median_multiplicative_factor",
        "gaussian_nll", "coverage_50", "coverage_80", "coverage_90", "coverage_95",
        "mean_sigma", "median_sigma", "spearman_sigma_error", "best_epoch", "stop_epoch"]


def gaussian_nll_per_param(y, mu, sigma):
    # single-parameter NLL term: 0.5*((y-mu)/sigma)^2 + log(sigma), mean over samples
    return np.mean(0.5 * ((y - mu) / sigma) ** 2 + np.log(sigma), axis=0)


def evaluate(family, seed, outdir):
    b = np.load(os.path.join(outdir, "eval_bundle.npz"), allow_pickle=True)
    with open(os.path.join(outdir, "metadata.json")) as f:
        meta = json.load(f)
    mu = b["param_mu"].astype(np.float64)
    sigma = b["param_sigma"].astype(np.float64)
    y = b["params_test"].astype(np.float64)
    recon = b["recon"] if b["recon"].size else None
    J = b["J_test"].astype(np.float64)

    scal = load_scalers()
    span = scal["param_max_log10"] - scal["param_min_log10"]

    err = np.abs(y - mu)
    rows = []
    for i in range(9):
        r, _ = pearsonr(y[:, i], mu[:, i])
        mae = float(np.mean(err[:, i]))
        rmse = float(np.sqrt(np.mean((y[:, i] - mu[:, i]) ** 2)))
        mae_dec = mae * span[i]
        med_log = float(np.median(err[:, i])) * span[i]
        med_mult = float(10.0 ** med_log)
        nll = float(gaussian_nll_per_param(y[:, i], mu[:, i], sigma[:, i]))
        cov = {}
        for lvl in NOMINAL:
            zz = NOMINAL[lvl]
            lo = mu[:, i] - zz * sigma[:, i]
            hi = mu[:, i] + zz * sigma[:, i]
            cov[lvl] = float(np.mean((y[:, i] >= lo) & (y[:, i] <= hi)))
        rho, _ = spearmanr(sigma[:, i], err[:, i])
        rows.append({
            "model": family, "seed": seed, "parameter": SHORT_NAMES[i],
            "pearson_r": round(r, 6), "mae_norm": round(mae, 6), "rmse_norm": round(rmse, 6),
            "mae_decades": round(mae_dec, 6), "median_abs_log_error": round(med_log, 6),
            "median_multiplicative_factor": round(med_mult, 6), "gaussian_nll": round(nll, 6),
            "coverage_50": round(cov[0.50], 6), "coverage_80": round(cov[0.80], 6),
            "coverage_90": round(cov[0.90], 6), "coverage_95": round(cov[0.95], 6),
            "mean_sigma": round(float(np.mean(sigma[:, i])), 6),
            "median_sigma": round(float(np.median(sigma[:, i])), 6),
            "spearman_sigma_error": round(float(rho), 6),
            "best_epoch": meta["best_epoch"], "stop_epoch": meta["stop_epoch"],
        })
    # ALL mean row
    rows.append({
        "model": family, "seed": seed, "parameter": "ALL",
        "pearson_r": round(float(np.mean([rows[j]["pearson_r"] for j in range(9)])), 6),
        "mae_norm": round(float(np.mean([rows[j]["mae_norm"] for j in range(9)])), 6),
        "rmse_norm": round(float(np.mean([rows[j]["rmse_norm"] for j in range(9)])), 6),
        "mae_decades": round(float(np.mean([rows[j]["mae_decades"] for j in range(9)])), 6),
        "median_abs_log_error": round(float(np.mean([rows[j]["median_abs_log_error"] for j in range(9)])), 6),
        "median_multiplicative_factor": round(float(np.mean([rows[j]["median_multiplicative_factor"] for j in range(9)])), 6),
        "gaussian_nll": round(float(np.sum([rows[j]["gaussian_nll"] for j in range(9)])), 6),
        "coverage_50": round(float(np.mean([rows[j]["coverage_50"] for j in range(9)])), 6),
        "coverage_80": round(float(np.mean([rows[j]["coverage_80"] for j in range(9)])), 6),
        "coverage_90": round(float(np.mean([rows[j]["coverage_90"] for j in range(9)])), 6),
        "coverage_95": round(float(np.mean([rows[j]["coverage_95"] for j in range(9)])), 6),
        "mean_sigma": round(float(np.mean([rows[j]["mean_sigma"] for j in range(9)])), 6),
        "median_sigma": round(float(np.mean([rows[j]["median_sigma"] for j in range(9)])), 6),
        "spearman_sigma_error": round(float(np.mean([rows[j]["spearman_sigma_error"] for j in range(9)])), 6),
        "best_epoch": meta["best_epoch"], "stop_epoch": meta["stop_epoch"],
    })

    os.makedirs(os.path.dirname(RESULTS_CSV), exist_ok=True)
    write_header = not os.path.exists(RESULTS_CSV)
    with open(RESULTS_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        if write_header:
            w.writeheader()
        for row in rows:
            w.writerow(row)

    # recon metrics for VAE / det_ae
    recon_report = None
    if recon is not None:
        mse = np.mean((J - recon) ** 2, axis=1)
        recon_report = {"mean": float(mse.mean()), "median": float(np.median(mse))}

    result = {"rows": rows, "recon": recon_report,
              "best_epoch": meta["best_epoch"], "stop_epoch": meta["stop_epoch"],
              "train_seconds": meta.get("train_seconds"), "param_count": meta.get("param_count")}
    return result


if __name__ == "__main__":
    family, seed, outdir = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    res = evaluate(family, seed, outdir)
    print(json.dumps({"seed": seed, "all_mean_r": res["rows"][-1]["pearson_r"],
                      "recon": res["recon"]}, ensure_ascii=False))
