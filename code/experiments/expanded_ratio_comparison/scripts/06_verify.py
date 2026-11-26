# -*- coding: utf-8 -*-
"""Independent verification of the delivered experiment.

Recomputes every headline metric directly from the per-sample prediction CSVs
using the formulas (not the metric library) and compares with the reported
tables.  Also checks split integrity, train-only scaler fitting, run
completeness and figure artefacts.

Exit code is non-zero if any check fails.
"""
import json
import os
import pickle

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
MET = os.path.join(ROOT, "out", "metrics")
PRED = os.path.join(ROOT, "out", "predictions")
FIG = os.path.join(ROOT, "figures")

with open(os.path.join(ROOT, "config", "experiment_config.json"),
          encoding="utf-8") as f:
    CFG = json.load(f)
SEEDS = CFG["design"]["training_seeds"]
COORDS = ["a_mu", "r_mu", "a_tau", "r_tau", "a_D", "r_D"]

checks = []


def check(name, ok, detail=""):
    checks.append({"check": name, "status": "PASS" if ok else "FAIL",
                   "detail": str(detail)})
    print(("PASS " if ok else "FAIL ") + name + ("  " + str(detail) if detail else ""))


def formulas(y, yhat, ytrain):
    y, yhat, ytrain = map(lambda z: np.asarray(z, float), (y, yhat, ytrain))
    sse = float(np.sum((y - yhat) ** 2))
    sse_tr = float(np.sum((y - ytrain.mean()) ** 2))
    sse_te = float(np.sum((y - y.mean()) ** 2))
    mae = float(np.mean(np.abs(y - yhat)))
    mae_base = float(np.mean(np.abs(y - np.median(ytrain))))
    return {
        "rmse": float(np.sqrt(sse / y.size)),
        "mae": mae,
        "pearson": float(np.corrcoef(y, yhat)[0, 1]),
        "skill_mse": 1 - sse / sse_tr if sse_tr > 0 else np.nan,
        "r2_test": 1 - sse / sse_te if sse_te > 0 else np.nan,
        "mae_reduction": 1 - mae / mae_base if mae_base > 0 else np.nan,
    }


def main():
    # ---------------- splits -------------------------------------------
    arms = {}
    for arm in ("original", "expanded"):
        d = np.load(os.path.join(DATA, "arm_%s.npz" % arm), allow_pickle=True)
        tr, va, te = d["split_train"], d["split_val"], d["split_test"]
        arms[arm] = d
        check("%s: split sizes 16992/3641/3641" % arm,
              (len(tr), len(va), len(te)) == (16992, 3641, 3641),
              (len(tr), len(va), len(te)))
        s = [set(tr.tolist()), set(va.tolist()), set(te.tolist())]
        check("%s: train/val/test disjoint and cover all rows" % arm,
              len(s[0] & s[1]) == 0 and len(s[0] & s[2]) == 0 and
              len(s[1] & s[2]) == 0 and len(s[0] | s[1] | s[2]) == len(d["J"]))

        man = pd.read_csv(os.path.join(DATA, "split_manifest_%s.csv" % arm))
        check("%s: manifest has one row per sample with a split label" % arm,
              len(man) == len(d["J"]) and man["split"].isin(
                  ["train", "val", "test"]).all() and man["Sample_ID"].is_unique)
        # scalers fitted on train only: recompute from train rows
        with open(os.path.join(DATA, "param_scaler_%s.pkl" % arm), "rb") as f:
            psc = pickle.load(f)["scaler"]
        Ltr = np.log10(d["params"][tr])
        check("%s: parameter scaler equals MinMax fitted on TRAIN only" % arm,
              np.allclose(psc.data_min_, Ltr.min(axis=0)) and
              np.allclose(psc.data_max_, Ltr.max(axis=0)))
        with open(os.path.join(DATA, "current_scaler_%s.pkl" % arm), "rb") as f:
            jsc = pickle.load(f)["scaler"]
        Jtr = d["J"][tr]
        check("%s: current scaler equals MinMax fitted on TRAIN only" % arm,
              np.allclose(jsc.data_min_, Jtr.min(axis=0)) and
              np.allclose(jsc.data_max_, Jtr.max(axis=0)))

    # ---------------- predictions vs test split ------------------------
    tabB = pd.read_csv(os.path.join(MET, "table_B_common_tests.csv"))
    max_err = 0.0
    n_checked = 0
    for model_arm in ("original", "expanded"):
        for seed in SEEDS:
            for test_arm in ("original", "expanded"):
                pth = os.path.join(PRED, "pred_%s_%d__on_%s.csv"
                                   % (model_arm, seed, test_arm))
                check("prediction file exists %s" % os.path.basename(pth),
                      os.path.exists(pth))
                df = pd.read_csv(pth)
                te = arms[test_arm]["split_test"]
                exp_ids = arms[test_arm]["sample_id"][te]
                check("%s: rows equal the test split exactly"
                      % os.path.basename(pth),
                      len(df) == len(te) and
                      np.array_equal(df["Sample_ID"].to_numpy(), exp_ids))

                Ltr = arms[test_arm]["params_log10"][arms[test_arm]["split_train"]]
                L0, L1 = Ltr[:, 0], Ltr[:, 1]
                L2, L3 = Ltr[:, 2], Ltr[:, 3]
                L4, L5 = Ltr[:, 4], Ltr[:, 5]
                ytr = np.column_stack([(L0 + L1) / 2, L0 - L1,
                                       (L2 + L3) / 2, L2 - L3,
                                       (L4 + L5) / 2, L4 - L5])

                for j, c in enumerate(COORDS):
                    got = formulas(df["true_" + c], df["pred_" + c], ytr[:, j])
                    row = tabB[(tabB["test_arm"] == test_arm) &
                               (tabB["model_arm"] == model_arm) &
                               (tabB["seed"] == seed) &
                               (tabB["quantity"] == c)]
                    assert len(row) == 1
                    for k, v in got.items():
                        max_err = max(max_err, abs(float(row.iloc[0][k]) - v))
                        n_checked += 1
    check("all table-B coordinate metrics reproduce from prediction files",
          max_err < 1e-9, "max abs diff %.3e over %d values" % (max_err, n_checked))

    # ---------------- run completeness ---------------------------------
    status = {}
    for arm in ("original", "expanded"):
        for seed in SEEDS:
            rj = os.path.join(ROOT, "logs", "%s_%d" % (arm, seed), "run.json")
            if os.path.exists(rj):
                with open(rj, encoding="utf-8") as f:
                    r = json.load(f)
                status["%s_%d" % (arm, seed)] = r.get("status")
                check("run %s_%d completed" % (arm, seed),
                      r.get("status") == "completed",
                      "epochs=%s best=%s" % (r.get("epochs_run"),
                                             r.get("best_epoch")))
            else:
                check("run %s_%d has run.json" % (arm, seed), False)
    check("ten completed runs", sum(v == "completed" for v in status.values()) == 10,
          len(status))

    # same training seed -> same initial weights in both arms
    fp = {}
    for arm in ("original", "expanded"):
        for seed in SEEDS:
            rj = os.path.join(ROOT, "logs", "%s_%d" % (arm, seed), "run.json")
            with open(rj, encoding="utf-8") as f:
                fp[(arm, seed)] = json.load(f).get("initial_weight_sha256")
    for seed in SEEDS:
        check("seed %d: identical initial weights in both arms" % seed,
              fp[("original", seed)] is not None and
              fp[("original", seed)] == fp[("expanded", seed)],
              (fp[("original", seed)] or "")[:16])
    check("the five seeds give five distinct initial-weight fingerprints",
          len({fp[("original", s)] for s in SEEDS}) == len(SEEDS))

    # ---------------- figures -------------------------------------------
    for fn in ("fig02_skill_and_error.png", "fig03_common_test_paired.png"):
        p = os.path.join(FIG, fn)
        check("figure %s present and non-trivial" % fn,
              os.path.exists(p) and os.path.getsize(p) > 20000,
              os.path.getsize(p) if os.path.exists(p) else 0)

    n_fail = sum(c["status"] == "FAIL" for c in checks)
    os.makedirs(os.path.join(ROOT, "out", "qa"), exist_ok=True)
    with open(os.path.join(ROOT, "out", "qa", "verification.json"), "w",
              encoding="utf-8") as f:
        json.dump({"n_checks": len(checks), "n_fail": n_fail, "checks": checks},
                  f, indent=2)
    print("\n%d checks, %d FAIL" % (len(checks), n_fail))
    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
