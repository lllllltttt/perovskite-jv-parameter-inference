# -*- coding: utf-8 -*-
"""Fix the matched split, fit train-only scalers, write experiment_config.json.

Order of operations inside this script (deliberate):
  1. write experiment_config.json  -> design fixed before any training;
  2. draw the matched original-range subset;
  3. draw one seeded split per arm (shared by all five training seeds);
  4. fit parameter and current MinMaxScalers on each arm's TRAIN rows only;
  5. write split manifests, arm caches, scaler pickles and hashes.

Nothing here trains a network. No input CSV is modified.
"""
import csv
import hashlib
import json
import os
import pickle

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
CFG = os.path.join(ROOT, "config")
os.makedirs(DATA, exist_ok=True)
os.makedirs(CFG, exist_ok=True)

NEW_CSV = r"E:\project\work1\20261021\JV_database_9D_interface_lifetimes-newratio.csv"
OLD_CSV = r"E:\project\work1\data\JV_database_9D_interface_lifetimes-2.csv"
PARAM_COLS = ["mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk",
              "Nc_eff_pvk", "Nv_eff_pvk", "tau_ETL", "tau_HTL", "rad_c"]
J_COLS = ["J_%03d" % i for i in range(131)]

MASTER_SEED = 20261021
TRAIN_SEEDS = [20261021, 20261022, 20261023, 20261024, 20261025]
N_USED = 24274
COUNTS = {"train": 16992, "val": 3641, "test": 3641}
SPLIT_SEEDS = {"original": [20261021, 101], "expanded": [20261021, 102]}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


CONFIG = {
    "experiment_id": "20261021_expanded_ratio_comparison",
    "created_utc": "2026-10-21",
    "question": ("Under identical data volume, network, loss and training rules, "
                 "does widening the linear-uniform ratio prior from 0.2-5 to "
                 "0.05-20 change recovery of the shared scales and the ratio "
                 "coordinates?"),
    "design": {
        "arms": {
            "original": {
                "dataset_id": "orig200k",
                "ratio_prior": [0.2, 5.0],
                "n_available": 102046,
                "n_used": N_USED,
                "selection": ("random subset without replacement; "
                              "numpy.random.default_rng(20261021).choice(102046, "
                              "24274, replace=False), then sorted ascending"),
            },
            "expanded": {
                "dataset_id": "exp50k",
                "ratio_prior": [0.05, 20.0],
                "n_available": 24274,
                "n_used": N_USED,
                "selection": "all delivered valid rows",
            },
        },
        "shared_scale_priors_unchanged": {
            "mu_avg": [1e-6, 1e-3],
            "tau_avg": [1e-9, 1e-2],
            "DOS_avg": [1e22, 1e26],
            "tau_interface_ETL": [1e-12, 1e-8],
            "tau_interface_HTL": [1e-14, 1e-10],
            "rad_c": [1e-12, 1e-9],
        },
        "ratio_sampling": "linear uniform in q within the stated range",
        "split": {
            "counts": COUNTS,
            "ratios": [0.70, 0.15, 0.15],
            "rule": ("one seeded permutation per arm (numpy default_rng with the "
                     "recorded seed), first 16,992 train, next 3,641 validation, "
                     "last 3,641 test; identical counts in both arms"),
            "seeds": SPLIT_SEEDS,
            "shared_by_all_training_seeds": True,
            "leakage_control": ("no exact duplicate parameter vector or "
                                "byte-identical current curve exists within or "
                                "across the two arms, so no duplicate group "
                                "assignment is required; verified in data QA"),
        },
        "common_test_sets": {
            "original_range_test": "original-arm test rows (3,641)",
            "expanded_range_test": "expanded-arm test rows (3,641)",
        },
        "training_seeds": TRAIN_SEEDS,
        "n_training_runs": 2 * len(TRAIN_SEEDS),
    },
    "architecture": {
        "source": "script/VAE-v6.py (frozen main-paper model VAE-v6)",
        "input_dim": 131,
        "latent_dim": 9,
        "n_param": 9,
        "encoder": ["Dense128 relu", "Dense64 relu", "z_mean:9", "z_log_var:9",
                    "Sampling: z_mean + exp(0.5*z_log_var)*eps"],
        "decoder": ["Dense64 relu", "Dense128 relu", "Dense131 sigmoid"],
        "param_head": ["Dense64 relu", "Dense32 relu",
                       "mu:9", "sigma_raw:9 (bias initialiser -3.0)"],
        "sigma_transform": "clip(softplus(raw)+0.01, 0.01, 1.0)",
        "loss": ("recon_loss (mean of summed squared error over 131 points) + "
                 "0.001*KL + 1.0*GaussianNLL"),
    },
    "training": {
        "optimizer": "Adam(learning_rate=1e-3)",
        "batch_size": 64,
        "max_epochs": 1000,
        "early_stopping": {"monitor": "val_param_loss", "patience": 50,
                           "restore_best_weights": True,
                           "min_delta": "Keras default (0)"},
        "reduce_lr_on_plateau": {"monitor": "val_loss", "factor": 0.5,
                                 "patience": 15, "min_lr": 1e-6},
        "checkpoint": {"monitor": "val_loss", "save_best_only": True},
        "shuffle": "tf.data shuffle(buffer=n_train, seed=<training seed>, "
                   "reshuffle_each_iteration=True)",
        "init_and_order": ("keras.utils.set_random_seed(<training seed>) before "
                           "model construction in both arms; identical train-set "
                           "size and shuffle seed give the same batch order where "
                           "the framework permits it; residual framework "
                           "non-determinism is reported"),
        "no_hyperparameter_search": True,
    },
    "preprocessing": {
        "parameters": "log10 of all nine parameters (all nine had max/min > 100 "
                      "in the frozen pipeline), then MinMaxScaler fitted on the "
                      "arm's TRAIN partition only",
        "current": "per-voltage MinMaxScaler fitted on the arm's TRAIN partition "
                   "only",
        "val_test": "transform only; no clipping to [0,1]",
        "difference_from_frozen_main_model": (
            "the frozen main model's scalers were fitted on the full 102,046-row "
            "retained set before splitting; here both scalers are train-only, so "
            "normalisation and loss weighting differ from the frozen model. "
            "Conclusions are drawn between the two matched retrained models, not "
            "against the frozen model."),
    },
    "evaluation": {
        "point_prediction": "encoder z_mean -> param_head mu (no latent sampling), "
                            "identical for both arms",
        "space": "physical log10 parameter space after inverse transform",
        "coordinates": ["a_mu", "r_mu", "a_tau", "r_tau", "a_D", "r_D"],
        "metrics": ["pearson", "mae", "rmse", "r2_test", "skill_mse",
                    "mae_reduction"],
        "definitions_source": ("20261019_HC_revision_stage1_v2/scripts/"
                               "metrics_lib.py::metrics (archived, imported "
                               "verbatim)"),
        "table_A": "each arm's model on its own test set with its own train "
                   "baselines",
        "table_B": "same-test-set comparison with the test arm's train mean/"
                   "median baselines used for both models",
        "summary": "per-seed values, mean +/- sample SD across the five seeds, "
                   "and paired per-seed differences",
        "no_significance_tests": True,
    },
    "guardrails": [
        "no manuscript or SI edit",
        "no COMSOL run",
        "no overwrite of raw CSV, frozen model, frozen scalers or frozen split",
        "no claim of universal non-identifiability if no improvement is found",
        "out-of-distribution evaluations are labelled as such",
    ],
}


def main():
    # ---------------- 1. config first -------------------------------------
    CONFIG["inputs"] = {
        "expanded_csv": {"path": NEW_CSV, "sha256": sha256(NEW_CSV)},
        "original_csv": {"path": OLD_CSV, "sha256": sha256(OLD_CSV)},
        "frozen_main_model": {
            "dir": r"E:\project\work1\data\vae-v6\vae-v6",
            "note": "read for architecture provenance only; not used for fitting",
        },
        "metric_source": {
            "path": r"E:\project\work1\20261019_HC_revision_stage1_v2\scripts\metrics_lib.py",
            "sha256": sha256(r"E:\project\work1\20261019_HC_revision_stage1_v2\scripts\metrics_lib.py"),
        },
    }
    cfg_path = os.path.join(CFG, "experiment_config.json")
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(CONFIG, f, indent=2, ensure_ascii=False)
    print("wrote", cfg_path, "(design fixed before training)")

    # ---------------- 2. load ---------------------------------------------
    print("loading expanded CSV ...")
    new = pd.read_csv(NEW_CSV)
    print("loading original CSV ...")
    old = pd.read_csv(OLD_CSV)

    rng = np.random.default_rng(MASTER_SEED)
    sel = np.sort(rng.choice(len(old), size=N_USED, replace=False))
    assert len(np.unique(sel)) == N_USED

    arms = {
        "original": {"df": old.iloc[sel].reset_index(drop=True),
                     "source_row": sel,
                     "ids": old["Sample_ID"].to_numpy()[sel]},
        "expanded": {"df": new.reset_index(drop=True),
                     "source_row": np.arange(len(new)),
                     "ids": new["Sample_ID"].to_numpy()},
    }

    manifest_rows = []
    summary = {}
    for arm, a in arms.items():
        df = a["df"]
        n = len(df)
        assert n == N_USED, (arm, n)
        seed = SPLIT_SEEDS[arm]
        perm = np.random.default_rng(seed).permutation(n)
        a_i, b_i = COUNTS["train"], COUNTS["train"] + COUNTS["val"]
        idx = {"train": perm[:a_i], "val": perm[a_i:b_i], "test": perm[b_i:]}
        # hard assertions
        assert sum(len(v) for v in idx.values()) == n
        assert len(set(idx["train"]) & set(idx["val"])) == 0
        assert len(set(idx["train"]) & set(idx["test"])) == 0
        assert len(set(idx["val"]) & set(idx["test"])) == 0
        assert sorted(np.concatenate(list(idx.values())).tolist()) == list(range(n))
        for k, v in idx.items():
            assert len(v) == COUNTS[k], (arm, k, len(v))

        P = df[PARAM_COLS].to_numpy(np.float64)
        J = df[J_COLS].to_numpy(np.float64)

        # ---- scalers: TRAIN ONLY ----------------------------------------
        P_train = P[idx["train"]]
        L_train = np.log10(P_train)
        psc = MinMaxScaler().fit(L_train)
        Jsc = MinMaxScaler().fit(J[idx["train"]])

        L_all = np.log10(P)
        Pn = psc.transform(L_all)
        Jn = Jsc.transform(J)

        with open(os.path.join(DATA, "param_scaler_%s.pkl" % arm), "wb") as f:
            pickle.dump({"scaler": psc, "log10": True, "columns": PARAM_COLS,
                         "fit_partition": "train",
                         "n_fit": int(len(idx["train"]))}, f)
        with open(os.path.join(DATA, "current_scaler_%s.pkl" % arm), "wb") as f:
            pickle.dump({"scaler": Jsc, "columns": J_COLS, "units": "mA/cm2",
                         "fit_partition": "train",
                         "n_fit": int(len(idx["train"]))}, f)

        np.savez_compressed(
            os.path.join(DATA, "arm_%s.npz" % arm),
            J=J, params=P, params_log10=L_all,
            J_scaled=Jn, params_scaled=Pn,
            split_train=idx["train"], split_val=idx["val"],
            split_test=idx["test"],
            sample_id=a["ids"], source_row=a["source_row"],
            param_names=np.array(PARAM_COLS), j_cols=np.array(J_COLS),
        )

        split_label = np.empty(n, dtype=object)
        for k, v in idx.items():
            split_label[v] = k
        with open(os.path.join(DATA, "split_manifest_%s.csv" % arm), "w",
                  newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["dataset_id", "Sample_ID", "source_row", "split"])
            dsid = CONFIG["design"]["arms"][arm]["dataset_id"]
            for i in range(n):
                w.writerow([dsid, int(a["ids"][i]), int(a["source_row"][i]),
                            split_label[i]])

        summary[arm] = {
            "dataset_id": CONFIG["design"]["arms"][arm]["dataset_id"],
            "n": n,
            "split_sizes": {k: int(len(v)) for k, v in idx.items()},
            "param_scaler_min": psc.data_min_.tolist(),
            "param_scaler_max": psc.data_max_.tolist(),
            "param_scaler_range": psc.data_range_.tolist(),
            "current_scaler_min_range": float(np.min(Jsc.data_range_)),
            "current_scaler_max_range": float(np.max(Jsc.data_range_)),
            "train_truth_mean_log10": np.mean(L_all[idx["train"]], axis=0).tolist(),
            "train_truth_median_log10": np.median(L_all[idx["train"]], axis=0).tolist(),
            "test_truth_mean_log10": np.mean(L_all[idx["test"]], axis=0).tolist(),
            "split_sha256_of_manifest": sha256(
                os.path.join(DATA, "split_manifest_%s.csv" % arm)),
            "arm_cache_sha256": sha256(os.path.join(DATA, "arm_%s.npz" % arm)),
        }
        print(arm, summary[arm]["split_sizes"])

    with open(os.path.join(DATA, "split_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # fingerprint of the design actually realised
    CONFIG["realised"] = {
        "n_used": {k: v["n"] for k, v in summary.items()},
        "split_sizes": {k: v["split_sizes"] for k, v in summary.items()},
        "scaler_fit_partition": "train only",
        "train_seed_master": MASTER_SEED,
    }
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(CONFIG, f, indent=2, ensure_ascii=False)
    print("updated", cfg_path, "with realised sizes")


if __name__ == "__main__":
    main()
