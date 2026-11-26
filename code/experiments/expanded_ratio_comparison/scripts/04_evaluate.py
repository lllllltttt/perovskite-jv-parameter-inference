# -*- coding: utf-8 -*-
"""Deterministic evaluation of the ten trained runs -- v2 (cross-arm fix).

v1 bug: for a model evaluated on the other arm's test set, both the input
normalisation and the output inverse transform used the *test* arm's scalers.
The correct rule implemented here is:

    J_input   = current_scaler[model_arm].transform(J_physical[test_arm][idx])
    mu_norm   = model(model_arm, seed)(J_input)
    L_pred    = param_scaler[model_arm].inverse_transform(mu_norm)
    L_true    = params_log10[test_arm][idx]

The physical currents are read from the archived arm cache (`arm_<arm>.npz`,
key `J`, mA/cm^2, 131 voltage columns in acquisition order); they are not
reconstructed by inverting J_scaled.  The evaluation baselines still come from
the TEST arm's training partition: Skill_MSE against the test arm's training
mean, MAE reduction against its training median, R^2 against the test mean.

Point prediction is unchanged: encoder z_mean -> parameter head mu, no latent
sampling, no clipping, no checkpoint reselection.

Outputs are the same tables as v1 plus `inference_provenance.csv`, which
records for every (model_arm, seed, test_arm) combination the exact model
files, scalers (with owner arm) and test split actually used.
"""
import hashlib
import importlib.util
import json
import os
import pickle
import sys

import numpy as np
import pandas as pd

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
MODELS = os.path.join(ROOT, "models")
OUT = os.path.join(ROOT, "out")
PRED = os.path.join(OUT, "predictions")
MET = os.path.join(OUT, "metrics")
for d in (PRED, MET):
    os.makedirs(d, exist_ok=True)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import tensorflow as tf  # noqa: E402
from tensorflow import keras  # noqa: E402
import vae_v6_model as vm  # noqa: E402

CONFIG_PATH = os.path.join(ROOT, "config", "experiment_config.json")
with open(CONFIG_PATH, encoding="utf-8") as f:
    CFG = json.load(f)

ARMS = ["original", "expanded"]
SEEDS = CFG["design"]["training_seeds"]

# archived metric implementation, imported verbatim
MLIB = r"E:\project\work1\20261019_HC_revision_stage1_v2\scripts\metrics_lib.py"
spec = importlib.util.spec_from_file_location("archived_metrics_lib", MLIB)
mlib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mlib)
metrics = mlib.metrics
coords = mlib.coords
PARAM_NAMES = mlib.PARAM_NAMES
COORD_NAMES = mlib.COORD_NAMES

SHORT = {"mu_n_pvk": "mu_n", "mu_p_pvk": "mu_p", "tau_n_pvk": "tau_n",
         "tau_p_pvk": "tau_p", "Nc_eff_pvk": "Nc", "Nv_eff_pvk": "Nv",
         "tau_ETL": "tau_ETL", "tau_HTL": "tau_HTL", "rad_c": "rad_c"}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_arm(arm):
    d = np.load(os.path.join(DATA, "arm_%s.npz" % arm), allow_pickle=True)
    with open(os.path.join(DATA, "param_scaler_%s.pkl" % arm), "rb") as f:
        psc = pickle.load(f)
    with open(os.path.join(DATA, "current_scaler_%s.pkl" % arm), "rb") as f:
        csc = pickle.load(f)
    return {
        "J": d["J"],                          # physical mA/cm^2, 131 points
        "J_scaled": d["J_scaled"],            # archived normalised copy
        "L": d["params_log10"],               # physical log10 truth
        "train": d["split_train"], "val": d["split_val"], "test": d["split_test"],
        "sample_id": d["sample_id"], "source_row": d["source_row"],
        "param_scaler": psc["scaler"], "param_scaler_meta": psc,
        "current_scaler": csc["scaler"], "current_scaler_meta": csc,
        "dataset_id": CFG["design"]["arms"][arm]["dataset_id"],
    }


_MODEL_CACHE = {}


def load_model(model_arm, seed):
    """Load the three archived submodels for one (arm, seed) once."""
    key = (model_arm, seed)
    if key in _MODEL_CACHE:
        return _MODEL_CACHE[key]
    mdir = os.path.join(MODELS, "%s_%d" % (model_arm, seed))
    enc = keras.models.load_model(os.path.join(mdir, "encoder.h5"),
                                  custom_objects={"Sampling": vm.Sampling})
    head = keras.models.load_model(os.path.join(mdir, "param_head.h5"))
    _MODEL_CACHE[key] = (enc, head)
    return enc, head


def predict(model_arm, seed, J_in):
    enc, head = load_model(model_arm, seed)
    z_mean = enc.predict(J_in.astype(np.float32), verbose=0, batch_size=512)[0]
    mu = head.predict(z_mean, verbose=0, batch_size=512)[0]
    return np.asarray(mu, dtype=np.float64)


def main():
    arms = {a: load_arm(a) for a in ARMS}
    train_coords = {a: coords(arms[a]["L"][arms[a]["train"]]) for a in ARMS}

    # scaler ownership, recorded once
    scaler_info = {}
    for a in ARMS:
        scaler_info[a] = {
            "param": {"path": os.path.join(DATA, "param_scaler_%s.pkl" % a),
                      "sha256": sha256(os.path.join(DATA, "param_scaler_%s.pkl" % a)),
                      "owner_arm": a},
            "current": {"path": os.path.join(DATA, "current_scaler_%s.pkl" % a),
                        "sha256": sha256(os.path.join(DATA, "current_scaler_%s.pkl" % a)),
                        "owner_arm": a},
        }

    model_info = {}
    for ma in ARMS:
        for seed in SEEDS:
            mdir = os.path.join(MODELS, "%s_%d" % (ma, seed))
            model_info[(ma, seed)] = {
                f: {"path": os.path.join(mdir, f), "sha256": sha256(os.path.join(mdir, f))}
                for f in ("encoder.h5", "decoder.h5", "param_head.h5")
            }

    long_rows = []
    prov_rows = []
    manifest = {
        "evaluator": os.path.abspath(__file__),
        "evaluator_sha256": sha256(os.path.abspath(__file__)),
        "config_sha256": sha256(CONFIG_PATH),
        "metric_source": {"path": MLIB, "sha256": sha256(MLIB)},
        "prediction_rule": "encoder z_mean -> param_head mu; no latent sampling",
        "baseline_rule": ("Skill_MSE baseline = test arm's TRAIN mean; MAE "
                          "reduction baseline = test arm's TRAIN median; "
                          "R2_test = test mean; identical for both models"),
        "scaler_roundtrip": {},
        "models": {"%s_%d" % (ma, s): model_info[(ma, s)] for ma in ARMS for s in SEEDS},
        "scalers": scaler_info,
        "predictions": {},
    }

    for model_arm in ARMS:
        for seed in SEEDS:
            for test_arm in ARMS:
                a = arms[test_arm]
                idx = a["test"]
                J_phys = a["J"][idx]                       # archived physical
                cur_sc = arms[model_arm]["current_scaler"]
                par_sc = arms[model_arm]["param_scaler"]

                J_input = cur_sc.transform(J_phys)
                # same-arm check: must equal the archived J_scaled slice
                if model_arm == test_arm:
                    dmax = float(np.max(np.abs(J_input - a["J_scaled"][idx])))
                    manifest.setdefault("scaler_roundtrip", {})[
                        "%s_%d__on_%s" % (model_arm, seed, test_arm)] = dmax
                    if dmax > 1e-12:
                        raise RuntimeError("current-scaler round trip %.3e" % dmax)
                else:
                    manifest.setdefault("scaler_roundtrip", {})[
                        "%s_%d__on_%s" % (model_arm, seed, test_arm)] = None

                mu_norm = predict(model_arm, seed, J_input)
                L_pred = par_sc.inverse_transform(mu_norm)   # model arm's scaler
                L_true = a["L"][idx]
                if not np.isfinite(L_pred).all():
                    raise RuntimeError("non-finite prediction %s %s %s"
                                       % (model_arm, seed, test_arm))

                C_true, C_pred = coords(L_true), coords(L_pred)
                # ---- per-sample prediction file -----------------------
                out = pd.DataFrame({
                    "dataset_id": a["dataset_id"],
                    "Sample_ID": a["sample_id"][idx],
                    "source_row": a["source_row"][idx],
                    "test_arm": test_arm,
                    "model_arm": model_arm,
                    "seed": seed,
                    "input_scaler_arm": model_arm,
                    "output_scaler_arm": model_arm,
                })
                for i, p in enumerate(PARAM_NAMES):
                    out["true_log10_" + SHORT[p]] = L_true[:, i]
                    out["pred_log10_" + SHORT[p]] = L_pred[:, i]
                    out["true_phys_" + SHORT[p]] = 10 ** L_true[:, i]
                    out["pred_phys_" + SHORT[p]] = 10 ** L_pred[:, i]
                for i, c in enumerate(COORD_NAMES):
                    out["true_" + c] = C_true[:, i]
                    out["pred_" + c] = C_pred[:, i]
                pth = os.path.join(PRED, "pred_%s_%d__on_%s.csv"
                                   % (model_arm, seed, test_arm))
                out.to_csv(pth, index=False)
                manifest["predictions"][os.path.basename(pth)] = sha256(pth)

                prov_rows.append({
                    "model_arm": model_arm, "test_arm": test_arm, "seed": seed,
                    "n_test": int(len(idx)),
                    "encoder_sha256": model_info[(model_arm, seed)]["encoder.h5"]["sha256"],
                    "decoder_sha256": model_info[(model_arm, seed)]["decoder.h5"]["sha256"],
                    "param_head_sha256": model_info[(model_arm, seed)]["param_head.h5"]["sha256"],
                    "input_scaler_owner": model_arm,
                    "input_scaler_sha256": scaler_info[model_arm]["current"]["sha256"],
                    "output_scaler_owner": model_arm,
                    "output_scaler_sha256": scaler_info[model_arm]["param"]["sha256"],
                    "test_arm": test_arm,
                    "test_split_sha256": sha256(
                        os.path.join(DATA, "split_manifest_%s.csv" % test_arm)),
                    "test_sample_id_sha256": hashlib.sha256(
                        np.ascontiguousarray(a["sample_id"][idx]).tobytes()).hexdigest(),
                    "test_truth_sha256": hashlib.sha256(
                        np.ascontiguousarray(L_true).tobytes()).hexdigest(),
                })

                # ---- metrics ------------------------------------------
                y_train_C = train_coords[test_arm]
                y_train_L = arms[test_arm]["L"][arms[test_arm]["train"]]
                for j, c in enumerate(COORD_NAMES):
                    m = metrics(C_true[:, j], C_pred[:, j], y_train_C[:, j])
                    long_rows.append(dict(test_arm=test_arm, model_arm=model_arm,
                                          seed=seed, family="coordinate",
                                          quantity=c, **m))
                for j, p in enumerate(PARAM_NAMES):
                    m = metrics(L_true[:, j], L_pred[:, j], y_train_L[:, j])
                    long_rows.append(dict(test_arm=test_arm, model_arm=model_arm,
                                          seed=seed, family="parameter",
                                          quantity=p, **m))

    long = pd.DataFrame(long_rows)
    long["model"] = long["model_arm"] + "_" + long["seed"].astype(str)
    long.to_csv(os.path.join(MET, "metrics_long.csv"), index=False)

    metric_cols = ["n", "pearson", "mae", "rmse", "r2_test", "skill_mse",
                   "mae_reduction", "train_mean", "train_median", "test_mean",
                   "sse_model", "sse_train_mean", "sse_test_mean",
                   "mae_train_median_baseline", "undefined"]

    # ---- Table A: each arm's model on its own test set ----------------
    A = long[long["test_arm"] == long["model_arm"]].copy()
    A = A[["model_arm", "seed", "family", "quantity"] + metric_cols]
    A.to_csv(os.path.join(MET, "table_A_own_distribution.csv"), index=False)

    # ---- Table B: same test set, both models, common baselines --------
    B = long.copy()
    B.to_csv(os.path.join(MET, "table_B_common_tests.csv"), index=False)

    # ---- paired differences (expanded model - original model) ---------
    prows = []
    keys = ["test_arm", "family", "quantity"]
    for k, g in long.groupby(keys):
        g = g.set_index(["model_arm", "seed"])
        for seed in SEEDS:
            o = g.loc[("original", seed)]
            e = g.loc[("expanded", seed)]
            row = {"test_arm": k[0], "family": k[1], "quantity": k[2],
                   "seed": seed}
            for c in ["pearson", "mae", "rmse", "r2_test", "skill_mse",
                      "mae_reduction", "sse_model"]:
                row["old_" + c] = o[c]
                row["new_" + c] = e[c]
                row["diff_new_minus_old_" + c] = e[c] - o[c]
            prows.append(row)
    P = pd.DataFrame(prows)
    P.to_csv(os.path.join(MET, "paired_differences.csv"), index=False)

    # ---- mean +/- sample SD across the five seeds ---------------------
    srows = []
    for k, g in long.groupby(["test_arm", "model_arm", "family", "quantity"]):
        for c in ["pearson", "mae", "rmse", "r2_test", "skill_mse",
                  "mae_reduction"]:
            v = g[c].astype(float).to_numpy()
            srows.append({"test_arm": k[0], "model_arm": k[1], "family": k[2],
                          "quantity": k[3], "metric": c,
                          "mean": float(np.nanmean(v)),
                          "sd": float(np.nanstd(v, ddof=1)),
                          "n_seeds": int(np.isfinite(v).sum()),
                          "min": float(np.nanmin(v)),
                          "max": float(np.nanmax(v))})
    S = pd.DataFrame(srows)
    S.to_csv(os.path.join(MET, "summary_mean_sd.csv"), index=False)

    # paired summary
    qrows = []
    for k, g in P.groupby(["test_arm", "family", "quantity"]):
        for c in ["pearson", "mae", "rmse", "r2_test", "skill_mse",
                  "mae_reduction"]:
            v = g["diff_new_minus_old_" + c].astype(float).to_numpy()
            qrows.append({"test_arm": k[0], "family": k[1], "quantity": k[2],
                          "metric": c, "mean_diff": float(np.nanmean(v)),
                          "sd_diff": float(np.nanstd(v, ddof=1)),
                          "n_positive": int(np.sum(v > 0)),
                          "n_negative": int(np.sum(v < 0)),
                          "n_seeds": int(len(v))})
    pd.DataFrame(qrows).to_csv(
        os.path.join(MET, "paired_difference_summary.csv"), index=False)

    # ---- provenance, one row per prediction combination ----------------
    pd.DataFrame(prov_rows).to_csv(
        os.path.join(MET, "inference_provenance.csv"), index=False)

    # ---- zero-denominator audit --------------------------------------
    und = long[long["undefined"].astype(str).str.len() > 0]
    manifest["n_rows_with_undefined_metric"] = int(len(und))
    manifest["undefined_detail"] = und[["test_arm", "model_arm", "seed",
                                        "quantity", "undefined"]].to_dict(
        orient="records")
    manifest["n_runs"] = len(SEEDS) * len(ARMS)
    manifest["seeds"] = SEEDS
    with open(os.path.join(MET, "eval_manifest.json"), "w",
              encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print("wrote tables:", len(long), "metric rows")
    print("undefined metric rows:", len(und))
    print("provenance rows:", len(prov_rows))


if __name__ == "__main__":
    sys.exit(main())
