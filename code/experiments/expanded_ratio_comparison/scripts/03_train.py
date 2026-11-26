# -*- coding: utf-8 -*-
"""Train one (arm, seed) VAE-v6 replica under the fixed experiment config.

Usage:
    python 03_train.py --arm original --seed 20261021
    python 03_train.py --arm expanded --seed 20261021 --epochs 3 --tag smoke

Every run writes a self-describing directory and never silently replaces a
finished run: an existing completed run is skipped unless --force is given, and
a forced re-run is recorded as a new attempt in runs.jsonl.
"""
import argparse
import hashlib
import json
import os
import platform
import shutil
import sys
import time
import traceback
from datetime import datetime, timezone

import numpy as np

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("TF_DETERMINISTIC_OPS", "1")
os.environ.setdefault("TF_CUDNN_DETERMINISTIC", "1")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
MODELS = os.path.join(ROOT, "models")
LOGS = os.path.join(ROOT, "logs")
CONFIG_PATH = os.path.join(ROOT, "config", "experiment_config.json")
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import tensorflow as tf  # noqa: E402
from tensorflow import keras  # noqa: E402

import vae_v6_model as vm  # noqa: E402


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class SubmodelCheckpoint(keras.callbacks.Callback):
    """Best-val_loss checkpoint of the three built submodels.

    Keras 3 refuses save_weights() on the subclassed VAE container (it has no
    build() of its own, because train_step drives the submodels directly), so
    the checkpoint is written from the functional submodels.  The monitored
    quantity and the save_best_only rule are those of the frozen script.
    """

    def __init__(self, outdir):
        super().__init__()
        self.outdir = outdir
        self.best = np.inf
        self.saved = False

    def on_epoch_end(self, epoch, logs=None):
        v = float((logs or {}).get("val_loss", np.inf))
        if v < self.best:
            self.best = v
            self.model.encoder.save_weights(
                os.path.join(self.outdir, "encoder.weights.h5"))
            self.model.decoder.save_weights(
                os.path.join(self.outdir, "decoder.weights.h5"))
            self.model.param_head.save_weights(
                os.path.join(self.outdir, "param_head.weights.h5"))
            self.saved = True


class EpochLogger(keras.callbacks.Callback):
    """Write one CSV row per finished epoch (train + validation)."""

    def __init__(self, path):
        super().__init__()
        self.path = path
        self.rows = []
        self.header = None

    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}
        if self.header is None:
            self.header = (["epoch"] + sorted(logs.keys()) + ["learning_rate"])
            with open(self.path, "w", newline="", encoding="utf-8") as f:
                f.write(",".join(self.header) + "\n")
        lr = float(self.model.optimizer.learning_rate.value)
        row = [epoch] + [logs.get(k, "") for k in self.header[1:-1]] + [lr]
        self.rows.append(row)
        with open(self.path, "a", newline="", encoding="utf-8") as f:
            f.write(",".join(str(v) for v in row) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=["original", "expanded"])
    ap.add_argument("--seed", required=True, type=int)
    ap.add_argument("--epochs", type=int, default=None,
                    help="override max epochs (smoke tests only)")
    ap.add_argument("--tag", default="", help="suffix for smoke-test output dirs")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    tf.config.experimental.enable_op_determinism()

    name = "%s_%d%s" % (args.arm, args.seed, ("_" + args.tag) if args.tag else "")
    outdir = os.path.join(MODELS, name)
    logdir = os.path.join(LOGS, name)
    os.makedirs(logdir, exist_ok=True)
    run_json = os.path.join(logdir, "run.json")
    runs_jsonl = os.path.join(LOGS, "runs.jsonl")

    status_prev = None
    if os.path.exists(run_json):
        with open(run_json, encoding="utf-8") as f:
            status_prev = json.load(f).get("status")
    if status_prev == "completed" and not args.force:
        print("[skip] %s already completed (use --force to retrain)" % name)
        return 0

    with open(CONFIG_PATH, encoding="utf-8") as f:
        cfg = json.load(f)
    cfg_sha = sha256(CONFIG_PATH)

    arm_npz = os.path.join(DATA, "arm_%s.npz" % args.arm)
    d = np.load(arm_npz, allow_pickle=True)
    J, P = d["J_scaled"], d["params_scaled"]
    tr, va, te = d["split_train"], d["split_val"], d["split_test"]
    Jtr, Ptr = J[tr].astype(np.float32), P[tr].astype(np.float32)
    Jva, Pva = J[va].astype(np.float32), P[va].astype(np.float32)

    n_train = len(Jtr)
    epochs = args.epochs if args.epochs is not None else cfg["training"]["max_epochs"]
    batch = cfg["training"]["batch_size"]

    started = datetime.now(timezone.utc)
    t0 = time.time()
    record = {
        "arm": args.arm, "seed": int(args.seed), "run_name": name,
        "started_utc": started.isoformat(),
        "config_sha256": cfg_sha,
        "arm_cache_sha256": sha256(arm_npz),
        "n_train": int(n_train), "n_val": int(len(Jva)), "n_test": int(len(te)),
        "batch_size": int(batch), "max_epochs": int(epochs),
        "previous_status": status_prev,
        "env": {
            "python": sys.version,
            "numpy": np.__version__,
            "tensorflow": tf.__version__,
            "keras": keras.__version__,
            "platform": platform.platform(),
            "deterministic_ops": True,
        },
    }

    try:
        if os.path.isdir(outdir) and args.force:
            shutil.rmtree(outdir)
        os.makedirs(outdir, exist_ok=True)

        # Identical initial weights for the same seed in both arms: the seed is
        # set immediately before model construction.
        keras.utils.set_random_seed(int(args.seed))
        vae = vm.build_vae()
        vae.compile(optimizer=keras.optimizers.Adam(1e-3))

        init_fp = hashlib.sha256()
        for w in vae.get_weights():
            init_fp.update(np.ascontiguousarray(w).tobytes())
        record["initial_weight_sha256"] = init_fp.hexdigest()

        train_ds = (tf.data.Dataset.from_tensor_slices((Jtr, Ptr))
                    .shuffle(n_train, seed=int(args.seed),
                             reshuffle_each_iteration=True)
                    .batch(batch))
        val_ds = (tf.data.Dataset.from_tensor_slices((Jva, Pva))
                  .batch(batch))

        epoch_csv = os.path.join(logdir, "epochs.csv")
        # mode="min" only states explicitly what Keras 2 inferred from the
        # "loss" suffix; the monitored quantities and stopping rules are those
        # of the frozen VAE-v6 script.
        early = keras.callbacks.EarlyStopping(
            monitor="val_param_loss", patience=50, restore_best_weights=True,
            mode="min")
        reduce = keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=15, min_lr=1e-6,
            mode="min")
        ckpt = SubmodelCheckpoint(outdir)
        logger = EpochLogger(epoch_csv)

        history = vae.fit(
            train_ds, validation_data=val_ds, epochs=epochs,
            callbacks=[early, reduce, ckpt, logger],
            verbose=0 if args.quiet else 2)

        hist = {k: [float(x) for x in v] for k, v in history.history.items()}
        with open(os.path.join(logdir, "history.json"), "w",
                  encoding="utf-8") as f:
            json.dump(hist, f, indent=1)

        vae.encoder.save(os.path.join(outdir, "encoder.h5"))
        vae.decoder.save(os.path.join(outdir, "decoder.h5"))
        vae.param_head.save(os.path.join(outdir, "param_head.h5"))

        # save/load check: reload the encoder with the custom Sampling layer
        enc2 = keras.models.load_model(os.path.join(outdir, "encoder.h5"),
                                       custom_objects={"Sampling": vm.Sampling})
        probe = Jva[:8].astype(np.float32)
        a = vae.encoder.predict(probe, verbose=0)[0]
        b = enc2.predict(probe, verbose=0)[0]
        record["reload_max_abs_diff_z_mean"] = float(np.max(np.abs(a - b)))

        record.update({
            "status": "completed",
            "finished_utc": datetime.now(timezone.utc).isoformat(),
            "wall_s": time.time() - t0,
            "epochs_run": int(len(hist["loss"])),
            "best_epoch": int(getattr(early, "best_epoch", -1)),
            "stopped_epoch": int(getattr(early, "stopped_epoch", -1)),
            "stop_reason": ("early_stopping" if getattr(early, "stopped_epoch", 0)
                            else "max_epochs"),
            "best_val_loss": float(np.min(hist["val_loss"])),
            "best_val_param_loss": float(np.min(hist["val_param_loss"])),
            "final_learning_rate": float(
                vae.optimizer.learning_rate.value),
            "model_files": {fn: {"sha256": sha256(os.path.join(outdir, fn)),
                                 "bytes": os.path.getsize(os.path.join(outdir, fn))}
                            for fn in ("encoder.h5", "decoder.h5",
                                       "param_head.h5", "encoder.weights.h5",
                                       "decoder.weights.h5",
                                       "param_head.weights.h5")},
        })
    except Exception as e:  # noqa: BLE001 - failures must be recorded verbatim
        record.update({
            "status": "failed",
            "finished_utc": datetime.now(timezone.utc).isoformat(),
            "wall_s": time.time() - t0,
            "error_type": type(e).__name__,
            "error": str(e),
            "traceback": traceback.format_exc(),
        })
        with open(run_json, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2)
        with open(runs_jsonl, "a", encoding="utf-8") as f:
            f.write(json.dumps({k: record[k] for k in
                                ("arm", "seed", "run_name", "status",
                                 "started_utc", "finished_utc", "wall_s")}) + "\n")
        print("FAILED:", e)
        return 1

    with open(run_json, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)
    with open(runs_jsonl, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "arm": record["arm"], "seed": record["seed"],
            "run_name": record["run_name"], "status": record["status"],
            "started_utc": record["started_utc"],
            "finished_utc": record["finished_utc"],
            "wall_s": record["wall_s"], "epochs_run": record["epochs_run"],
            "best_epoch": record["best_epoch"],
            "stop_reason": record["stop_reason"],
            "best_val_loss": record["best_val_loss"],
            "best_val_param_loss": record["best_val_param_loss"],
        }) + "\n")
    print("[done] %s  epochs=%d  best_epoch=%d  wall=%.1fs"
          % (name, record["epochs_run"], record["best_epoch"], record["wall_s"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
