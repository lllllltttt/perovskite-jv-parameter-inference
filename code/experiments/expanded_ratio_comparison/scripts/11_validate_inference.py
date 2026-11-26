# -*- coding: utf-8 -*-
"""Independent validation of the v2 prediction pipeline.

This script does NOT import the evaluator's prediction wrapper.  It rebuilds
the inference path for a fixed small batch directly from the archived arm
cache, the archived scaler pickles and the archived Keras models, and compares
the result with the CSV written by scripts/04_evaluate.py.

Checks
  1. provenance: every combination's input/output scaler belongs to model_arm,
     all recorded hashes match the files on disk, test identifiers/truth match;
  2. alignment: both models see the same samples, order, truth and baselines;
  3. independent reference recomputation (4 combinations x 64 rows);
  4. fault injection: wrong-arm scalers must be detected (in memory only);
  5. metric recomputation from the final prediction CSVs;
  6. algebraic a/r definition and no double log10;
  7. models, scalers, splits, arm caches, config and raw inputs unchanged
     relative to v1.

Any failure increments the counter and the process exits non-zero.
"""
import hashlib
import json
import os
import pickle
import sys

import numpy as np
import pandas as pd

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V1 = r"E:\project\work1\20261021_expanded_ratio_comparison"
DATA = os.path.join(ROOT, "data")
MODELS = os.path.join(ROOT, "models")
PRED = os.path.join(ROOT, "out", "predictions")
MET = os.path.join(ROOT, "out", "metrics")
QA = os.path.join(ROOT, "out", "qa")
os.makedirs(QA, exist_ok=True)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import tensorflow as tf  # noqa: E402
from tensorflow import keras  # noqa: E402
import vae_v6_model as vm  # noqa: E402

ARMS = ["original", "expanded"]
PARAMS = ["mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk",
          "Nc_eff_pvk", "Nv_eff_pvk", "tau_ETL", "tau_HTL", "rad_c"]
SHORT = ["mu_n", "mu_p", "tau_n", "tau_p", "Nc", "Nv", "tau_ETL",
         "tau_HTL", "rad_c"]
COORDS = ["a_mu", "r_mu", "a_tau", "r_tau", "a_D", "r_D"]
PAIR_IDX = [(0, 1), (2, 3), (4, 5)]

with open(os.path.join(ROOT, "config", "experiment_config.json"),
          encoding="utf-8") as f:
    CFG = json.load(f)
SEEDS = CFG["design"]["training_seeds"]

CHECKS = []
FAILURES = [0]
FAULT_LOG = []


def check(name, ok, detail=""):
    status = "PASS" if ok else "FAIL"
    if not ok:
        FAILURES[0] += 1
    CHECKS.append({"check": name, "status": status, "detail": str(detail)})
    print("%-4s %-72s %s" % (status, name, detail))
    return ok


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def arr_sha(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def load_arm(arm):
    d = np.load(os.path.join(DATA, "arm_%s.npz" % arm), allow_pickle=True)
    with open(os.path.join(DATA, "param_scaler_%s.pkl" % arm), "rb") as f:
        psc = pickle.load(f)
    with open(os.path.join(DATA, "current_scaler_%s.pkl" % arm), "rb") as f:
        csc = pickle.load(f)
    return d, psc, csc


ARMS_D = {}
for a in ARMS:
    ARMS_D[a] = load_arm(a)

PRED_DF = {}
for ma in ARMS:
    for seed in SEEDS:
        for ta in ARMS:
            p = os.path.join(PRED, "pred_%s_%d__on_%s.csv" % (ma, seed, ta))
            PRED_DF[(ma, seed, ta)] = pd.read_csv(p)
METRICS = pd.read_csv(os.path.join(MET, "metrics_long.csv"))
PROV = pd.read_csv(os.path.join(MET, "inference_provenance.csv"))


def main():
    # ---------------------------------------------------------------- 1
    check("provenance has 20 rows (2 models x 5 seeds x 2 tests)",
          len(PROV) == 20, len(PROV))
    keys = set(zip(PROV.model_arm, PROV.seed, PROV.test_arm))
    check("provenance covers every combination exactly once",
          len(keys) == 20 == len(PROV), len(keys))

    owner_ok = True
    hash_ok = True
    for r in PROV.itertuples():
        d, psc, csc = ARMS_D[r.model_arm]
        mdir = os.path.join(MODELS, "%s_%d" % (r.model_arm, r.seed))
        ok_owner = (r.input_scaler_owner == r.model_arm and
                    r.output_scaler_owner == r.model_arm)
        ok_hash = (
            r.input_scaler_sha256 == sha256(os.path.join(
                DATA, "current_scaler_%s.pkl" % r.model_arm)) and
            r.output_scaler_sha256 == sha256(os.path.join(
                DATA, "param_scaler_%s.pkl" % r.model_arm)) and
            r.encoder_sha256 == sha256(os.path.join(mdir, "encoder.h5")) and
            r.decoder_sha256 == sha256(os.path.join(mdir, "decoder.h5")) and
            r.param_head_sha256 == sha256(os.path.join(mdir, "param_head.h5")))
        ta_d = ARMS_D[r.test_arm][0]
        idx = ta_d["split_test"]
        ok_test = (
            r.test_split_sha256 == sha256(os.path.join(
                DATA, "split_manifest_%s.csv" % r.test_arm)) and
            r.test_sample_id_sha256 == arr_sha(ta_d["sample_id"][idx]) and
            r.test_truth_sha256 == arr_sha(ta_d["params_log10"][idx]) and
            r.n_test == len(idx))
        owner_ok &= ok_owner
        hash_ok &= (ok_hash and ok_test)
    check("input and output scalers belong to model_arm (all 20)", owner_ok)
    check("recorded model/scaler/split/truth hashes match files on disk", hash_ok)

    # scaler round-trip of the archived physical currents (all rows)
    rt = []
    for a in ARMS:
        d, psc, csc = ARMS_D[a]
        rec = csc["scaler"].transform(d["J"])
        rt.append(float(np.max(np.abs(rec - d["J_scaled"]))))
    check("archived J_scaled equals transform(archived physical J)",
          max(rt) <= 1e-12, "max |diff| = %.3e" % max(rt))

    # ---------------------------------------------------------------- 2
    align_ok = True
    base_ok = True
    truth_max = 0.0
    for ta in ARMS:
        for seed in SEEDS:
            o = PRED_DF[("original", seed, ta)]
            e = PRED_DF[("expanded", seed, ta)]
            align_ok &= list(o.Sample_ID) == list(e.Sample_ID)
            align_ok &= list(o.source_row) == list(e.source_row)
            tcols = [c for c in o.columns if c.startswith("true_")]
            truth_max = max(truth_max, float(np.max(np.abs(
                o[tcols].to_numpy() - e[tcols].to_numpy()))))
            g = METRICS[(METRICS.test_arm == ta) & (METRICS.seed == seed)]
            for q in g.quantity.unique():
                h = g[g.quantity == q]
                if len(h) == 2:
                    base_ok &= (
                        abs(h.train_mean.iloc[0] - h.train_mean.iloc[1]) < 1e-12 and
                        abs(h.train_median.iloc[0] - h.train_median.iloc[1]) < 1e-12 and
                        abs(h.sse_train_mean.iloc[0] - h.sse_train_mean.iloc[1]) < 1e-9 and
                        abs(h.test_mean.iloc[0] - h.test_mean.iloc[1]) < 1e-12)
    check("both models see identical Sample_ID/source_row order", align_ok)
    check("both models see identical truth values", truth_max == 0.0,
          "max |diff| = %.3e" % truth_max)
    check("baselines identical across models within each common test", base_ok)

    # ---------------------------------------------------------------- 3
    ref_rows = []
    combos = [("original", 20261021, "expanded"),
              ("expanded", 20261021, "original"),
              ("original", 20261021, "original"),
              ("expanded", 20261021, "expanded")]
    NB = 64
    for model_arm, seed, test_arm in combos:
        ta_d, _, ta_csc = ARMS_D[test_arm]
        ma_d, ma_psc, ma_csc = ARMS_D[model_arm]
        test_idx = ta_d["split_test"]
        Jin_all = ma_csc["scaler"].transform(ta_d["J"][test_idx])
        outside = float(np.mean((Jin_all < 0.0) | (Jin_all > 1.0)))
        # deterministic extreme-heavy batch: 32 rows with the smallest and 32
        # with the largest maximum transformed current
        order = np.argsort(Jin_all.max(axis=1))
        sel = np.concatenate([order[:NB // 2], order[-(NB // 2):]])
        idx = test_idx[sel]
        J_phys = ta_d["J"][idx]
        Jin = ma_csc["scaler"].transform(J_phys)
        mdir = os.path.join(MODELS, "%s_%d" % (model_arm, seed))
        enc = keras.models.load_model(os.path.join(mdir, "encoder.h5"),
                                      custom_objects={"Sampling": vm.Sampling})
        head = keras.models.load_model(os.path.join(mdir, "param_head.h5"))
        out = enc(Jin.astype(np.float32))
        zmean = np.asarray(out[0], dtype=np.float64)
        mu = np.asarray(head(zmean.astype(np.float32))[0], dtype=np.float64)
        L_ref = ma_psc["scaler"].inverse_transform(mu)
        df = PRED_DF[(model_arm, seed, test_arm)].set_index("Sample_ID")
        ids = ta_d["sample_id"][idx]
        L_csv = df.loc[ids, ["pred_log10_" + s for s in SHORT]].to_numpy()
        t_csv = df.loc[ids, ["true_log10_" + s for s in SHORT]].to_numpy()
        dmax = float(np.max(np.abs(L_ref - L_csv)))
        tmax = float(np.max(np.abs(
            ta_d["params_log10"][idx] - t_csv)))
        inside = float(np.mean((Jin >= 0.0) & (Jin <= 1.0)))
        ref_rows.append({
            "model_arm": model_arm, "seed": seed, "test_arm": test_arm,
            "n_rows": NB, "max_abs_pred_diff": dmax,
            "max_abs_truth_diff": tmax,
            "frac_input_inside_0_1_batch": inside,
            "frac_input_outside_0_1_full_test": outside,
        })
        check("independent reference matches CSV: %s/%s on %s"
              % (model_arm, seed, test_arm), dmax < 1e-5 and tmax < 1e-12,
              "pred %.3e, truth %.3e, full-test out-of-range inputs %.2f%%"
              % (dmax, tmax, 100 * outside))

    # ---------------------------------------------------------------- 4
    model_arm, seed, test_arm = "expanded", 20261021, "original"
    ta_d, ta_psc, ta_csc = ARMS_D[test_arm]
    ma_d, ma_psc, ma_csc = ARMS_D[model_arm]
    idx = ta_d["split_test"][:NB]
    J_phys = ta_d["J"][idx]
    mdir = os.path.join(MODELS, "%s_%d" % (model_arm, seed))
    enc = keras.models.load_model(os.path.join(mdir, "encoder.h5"),
                                  custom_objects={"Sampling": vm.Sampling})
    head = keras.models.load_model(os.path.join(mdir, "param_head.h5"))

    def forward(Jin, psc):
        o = enc(Jin.astype(np.float32))
        m = head(np.asarray(o[0], dtype=np.float32))
        return psc["scaler"].inverse_transform(
            np.asarray(m[0], dtype=np.float64))

    L_correct = forward(ma_csc["scaler"].transform(J_phys), ma_psc)
    # fault A: test arm's parameter scaler on the output
    L_wrong_out = forward(ma_csc["scaler"].transform(J_phys), ta_psc)
    dA = float(np.max(np.abs(L_wrong_out - L_correct)))
    FAULT_LOG.append({"fault": "output scaler swapped to test_arm",
                      "model_arm": model_arm, "test_arm": test_arm,
                      "max_abs_shift": dA, "detected": dA > 0.01})
    check("fault injection A detected (wrong output scaler)", dA > 0.01,
          "max shift %.3f log10" % dA)

    # fault B: test arm's current scaler on the input
    L_wrong_in = forward(ta_csc["scaler"].transform(J_phys), ma_psc)
    dB = float(np.max(np.abs(L_wrong_in - L_correct)))
    FAULT_LOG.append({"fault": "input scaler swapped to test_arm",
                      "model_arm": model_arm, "test_arm": test_arm,
                      "max_abs_shift": dB, "detected": dB > 1e-3})
    check("fault injection B detected (wrong input scaler)", dB > 1e-3,
          "max shift %.4f log10" % dB)

    # fault C: provenance checker must reject a forged owner
    def provenance_ok(row):
        return (row["input_scaler_owner"] == row["model_arm"] and
                row["output_scaler_owner"] == row["model_arm"])

    good = PROV.iloc[0].to_dict()
    other = "expanded" if good["model_arm"] == "original" else "original"
    forged = dict(good, output_scaler_owner=other)
    caught = (provenance_ok(good) is True and provenance_ok(forged) is False)
    FAULT_LOG.append({"fault": "forged provenance row with wrong owner",
                      "detected": caught})
    check("fault injection C detected (forged scaler owner)", caught)

    # explicit expected-exception pattern
    try:
        if dA <= 0.01:
            raise AssertionError("wrong output scaler not detectable")
        ok_exc = True
    except AssertionError:
        ok_exc = False
    check("fault A handled by expected-exception rule", ok_exc)

    # ---------------------------------------------------------------- 5
    def recompute(y, yhat, ytr):
        n = len(y)
        sse = float(np.sum((y - yhat) ** 2))
        btm = float(np.mean(ytr))
        bte = float(np.mean(y))
        bmed = float(np.median(ytr))
        sse_tr = float(np.sum((y - btm) ** 2))
        sse_te = float(np.sum((y - bte) ** 2))
        mae = float(np.mean(np.abs(y - yhat)))
        mae_base = float(np.mean(np.abs(y - bmed)))
        return dict(n=n, rmse=float(np.sqrt(sse / n)), mae=mae,
                    pearson=float(np.corrcoef(y, yhat)[0, 1]),
                    skill_mse=1 - sse / sse_tr, r2_test=1 - sse / sse_te,
                    mae_reduction=1 - mae / mae_base)

    metric_max = 0.0
    bad_row = None
    for r in METRICS.itertuples():
        ta_d2, _, _ = ARMS_D[r.test_arm]
        idx2 = ta_d2["split_test"]
        ytr_full = ta_d2["params_log10"][ta_d2["split_train"]]
        Ltr = ytr_full  # already physical log10
        df = PRED_DF[(r.model_arm, r.seed, r.test_arm)]
        if r.family == "coordinate":
            y = df["true_" + r.quantity].to_numpy()
            yh = df["pred_" + r.quantity].to_numpy()
            kk = COORDS.index(r.quantity)
            m = PAIR_IDX[kk // 2]
            a = 0.5 * (Ltr[:, m[0]] + Ltr[:, m[1]])
            b = Ltr[:, m[0]] - Ltr[:, m[1]]
            ytr = a if kk % 2 == 0 else b
        else:
            j = PARAMS.index(r.quantity)
            y = df["true_log10_" + SHORT[j]].to_numpy()
            yh = df["pred_log10_" + SHORT[j]].to_numpy()
            ytr = Ltr[:, j]
        got = recompute(y, yh, ytr)
        for key in ("rmse", "mae", "pearson", "skill_mse", "r2_test",
                    "mae_reduction"):
            dv = abs(got[key] - getattr(r, key))
            if dv > metric_max:
                metric_max = dv
                if dv > 1e-9:
                    bad_row = (r.test_arm, r.model_arm, r.seed, r.quantity, key, dv)
    check("all 300 metric rows recomputed from prediction CSVs",
          metric_max < 1e-9, "max abs diff %.3e %s"
          % (metric_max, bad_row or ""))

    und = METRICS["undefined"].fillna("").astype(str)
    check("no undefined (zero-denominator) metrics",
          int((und.str.len() > 0).sum()) == 0,
          "%d flagged rows" % int((und.str.len() > 0).sum()))

    # ---------------------------------------------------------------- 6
    amax = 0.0
    for (ma, seed, ta), df in PRED_DF.items():
        for k, (i, j) in enumerate(PAIR_IDX):
            amax = max(amax, float(np.max(np.abs(
                df["true_" + COORDS[2 * k]].to_numpy()
                - 0.5 * (df["true_log10_" + SHORT[i]].to_numpy()
                         + df["true_log10_" + SHORT[j]].to_numpy())))))
            amax = max(amax, float(np.max(np.abs(
                df["pred_" + COORDS[2 * k + 1]].to_numpy()
                - (df["pred_log10_" + SHORT[i]].to_numpy()
                   - df["pred_log10_" + SHORT[j]].to_numpy())))))
    check("a/r algebra holds on true and predicted columns", amax < 1e-12,
          "max |diff| %.3e" % amax)

    # no double log10: log10(true_phys) must equal true_log10 and the
    # coordinate magnitudes must stay in physical log10 units
    lmax = 0.0
    for (ma, seed, ta), df in PRED_DF.items():
        for j, s in enumerate(SHORT):
            lmax = max(lmax, float(np.max(np.abs(
                np.log10(df["true_phys_" + s].to_numpy())
                - df["true_log10_" + s].to_numpy()))))
    coord_ok = (PRED_DF[("original", 20261021, "original")]
                [["true_" + c for c in COORDS]].abs().max().max() < 40)
    check("no second log10 applied (true_phys vs true_log10)", lmax < 1e-12,
          "max |diff| %.3e" % lmax)
    check("coordinate magnitudes are physical log10 values", bool(coord_ok))

    # ---------------------------------------------------------------- 7
    rels = ["data/arm_original.npz", "data/arm_expanded.npz",
            "data/param_scaler_original.pkl", "data/param_scaler_expanded.pkl",
            "data/current_scaler_original.pkl", "data/current_scaler_expanded.pkl",
            "data/split_manifest_original.csv", "data/split_manifest_expanded.csv",
            "data/split_summary.json", "config/experiment_config.json"]
    same = 0
    total = 0
    diffs = []
    for rel in rels:
        total += 1
        a = sha256(os.path.join(V1, rel))
        b = sha256(os.path.join(ROOT, rel))
        if a == b:
            same += 1
        else:
            diffs.append(rel)
    import glob
    for d in sorted(glob.glob(os.path.join(V1, "models", "*_2026*"))):
        rel = os.path.relpath(d, V1)
        for f in sorted(os.listdir(d)):
            total += 1
            if sha256(os.path.join(V1, rel, f)) == sha256(os.path.join(ROOT, rel, f)):
                same += 1
            else:
                diffs.append(os.path.join(rel, f))
    check("inputs/models/scalers/splits/config unchanged vs v1",
          same == total, "%d/%d identical; diffs %s" % (same, total, diffs))

    raw_ok = True
    for key, entry in CFG["inputs"].items():
        if "path" in entry and "sha256" in entry:
            raw_ok &= (sha256(entry["path"]) == entry["sha256"])
    check("raw input CSVs still match the hashes frozen in the config", raw_ok)

    # ---------------------------------------------------------------- out
    out = {"checks": CHECKS, "n_checks": len(CHECKS),
           "n_failures": FAILURES[0],
           "reference_batch": ref_rows,
           "metric_recompute_max_abs_diff": metric_max,
           "coordinate_algebra_max_abs_diff": amax,
           "log10_consistency_max_abs_diff": lmax,
           "hash_invariance": {"identical": same, "total": total,
                               "diffs": diffs}}
    with open(os.path.join(QA, "inference_validation.json"), "w",
              encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    with open(os.path.join(QA, "fault_injection_log.json"), "w",
              encoding="utf-8") as f:
        json.dump(FAULT_LOG, f, indent=2)

    print("\n%d checks, %d FAIL" % (len(CHECKS), FAILURES[0]))
    return 0 if FAILURES[0] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
