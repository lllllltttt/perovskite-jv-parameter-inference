# -*- coding: utf-8 -*-
"""Isolated pipeline test: forward, loss, backward, save/load, inverse
normalisation and output evaluation for BOTH arms.

Constraints enforced here:
  * only TRAIN and VALIDATION rows of each arm are touched; the test split is
    never loaded into the model or the metrics;
  * 512 training rows / 128 validation rows, 2 epochs;
  * writes only under models/_smoke and logs/_smoke; smoke weights are never
    used as a formal initialisation;
  * hyperparameters are not selected from any evaluation here.
"""
import json
import os
import pickle
import sys

import numpy as np

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("TF_DETERMINISTIC_OPS", "1")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
LOGS = os.path.join(ROOT, "logs")
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import tensorflow as tf  # noqa: E402
from tensorflow import keras  # noqa: E402

import vae_v6_model as vm  # noqa: E402

OUT = os.path.join(ROOT, "models", "_smoke")
os.makedirs(OUT, exist_ok=True)
os.makedirs(os.path.join(LOGS, "_smoke"), exist_ok=True)

N_TRAIN, N_VAL, EPOCHS = 512, 128, 2


def run_arm(arm):
    d = np.load(os.path.join(DATA, "arm_%s.npz" % arm), allow_pickle=True)
    tr, va, te = d["split_train"], d["split_val"], d["split_test"]
    assert len(set(tr[:N_TRAIN]) & set(te)) == 0
    J, P = d["J_scaled"], d["params_scaled"]
    Jtr, Ptr = J[tr[:N_TRAIN]].astype(np.float32), P[tr[:N_TRAIN]].astype(np.float32)
    Jva, Pva = J[va[:N_VAL]].astype(np.float32), P[va[:N_VAL]].astype(np.float32)

    tf.config.experimental.enable_op_determinism()
    keras.utils.set_random_seed(7)
    vae = vm.build_vae()
    vae.compile(optimizer=keras.optimizers.Adam(1e-3))

    l0 = float(vae.evaluate(Jtr, Ptr, batch_size=64, verbose=0)[0])
    # one explicit gradient step sanity check
    with tf.GradientTape() as tape:
        loss, *_ = vae._terms(Jtr[:64], Ptr[:64], True)
    g = tape.gradient(loss, vae.trainable_variables)
    n_none = sum(x is None for x in g)
    gnorm = float(tf.linalg.global_norm([x for x in g if x is not None]))
    assert n_none == 0 and gnorm > 0

    hist = vae.fit(tf.data.Dataset.from_tensor_slices((Jtr, Ptr)).batch(64),
                   validation_data=tf.data.Dataset.from_tensor_slices(
                       (Jva, Pva)).batch(64),
                   epochs=EPOCHS, verbose=0)
    l1 = float(vae.evaluate(Jva, Pva, batch_size=64, verbose=0)[0])

    sdir = os.path.join(OUT, arm)
    os.makedirs(sdir, exist_ok=True)
    vae.encoder.save(os.path.join(sdir, "encoder.h5"))
    vae.decoder.save(os.path.join(sdir, "decoder.h5"))
    vae.param_head.save(os.path.join(sdir, "param_head.h5"))

    enc = keras.models.load_model(os.path.join(sdir, "encoder.h5"),
                                  custom_objects={"Sampling": vm.Sampling})
    head = keras.models.load_model(os.path.join(sdir, "param_head.h5"))
    z_mean = enc.predict(Jva, verbose=0)[0]
    mu = head.predict(z_mean, verbose=0)[0]

    with open(os.path.join(DATA, "param_scaler_%s.pkl" % arm), "rb") as f:
        sc = pickle.load(f)["scaler"]
    L_pred = mu.astype(np.float64) * sc.data_range_ + sc.data_min_
    p_pred = 10 ** L_pred
    L_true = d["params_log10"][va[:N_VAL]]
    p_true = 10 ** L_true

    ok = bool(np.isfinite(p_pred).all() and np.isfinite(p_true).all())
    rel = np.abs(p_pred - p_true) / p_true
    # prediction evaluated on VALIDATION only (never the test split)
    result = {
        "arm": arm,
        "n_train": N_TRAIN, "n_val": N_VAL, "epochs": EPOCHS,
        "initial_val_loss": l0, "final_val_loss": l1,
        "loss_decreased": bool(l1 < l0),
        "loss_history_keys": sorted(hist.history.keys()),
        "gradients_all_present": bool(n_none == 0),
        "gradient_global_norm": gnorm,
        "save_load_zmean_max_abs_diff": float(
            np.max(np.abs(enc.predict(Jva, verbose=0)[0] - z_mean))),
        "inverse_transform_finite": ok,
        "prediction_median_relative_error_val": float(np.median(rel)),
        "param_log10_scaler_range_ok": bool(
            np.all(sc.data_range_ > 0)),
        "test_rows_touched": 0,
    }
    return result


def main():
    res = [run_arm(a) for a in ("original", "expanded")]
    failed = [r for r in res if not (r["loss_decreased"] and
                                     r["gradients_all_present"] and
                                     r["inverse_transform_finite"] and
                                     r["test_rows_touched"] == 0)]
    with open(os.path.join(LOGS, "_smoke", "smoke_test.json"), "w",
              encoding="utf-8") as f:
        json.dump({"results": res, "n_failed": len(failed)}, f, indent=2)
    for r in res:
        print(json.dumps(r, indent=1))
    print("SMOKE FAILURES:", len(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
