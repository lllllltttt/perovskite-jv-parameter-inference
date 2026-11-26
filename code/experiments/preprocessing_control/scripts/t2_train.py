"""v4 T2: run one Branch (L legacy full-fit scalers | T train-only scalers)
under protocol.md. Same architecture/loss/opt/callbacks as frozen VAE-v6.py;
deterministic seeded batch order shared by both branches; pre-fixed eval rule =
early-stop (val_param_loss) restored weights. --dry N: run N epochs, print
timing, do not save weights (for budget estimate). Read-only on frozen."""
import argparse, json, os, sys, time, pickle
import numpy as np
import tensorflow as tf
from tensorflow import keras
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t2_model as M

def seed_all(s):
    np.random.seed(s)
    tf.random.set_seed(s)
    os.environ["PYTHONHASHSEED"] = str(s)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--branch", choices=["L", "T"], required=True)
    ap.add_argument("--seed", type=int, default=20260823)
    ap.add_argument("--dry", type=int, default=0, help="run N epochs as timing probe")
    ap.add_argument("--out", default=r"E:\project\work1\supplementary_validation_v4\T2_control\runs")
    args = ap.parse_args()
    S0 = args.seed
    seed_all(S0)
    tag = f"{args.branch}_seed{S0}" + ("_dry" if args.dry else "")
    run_dir = os.path.join(args.out, tag)
    os.makedirs(run_dir, exist_ok=True)

    ROOT = r"E:\project\work1"
    NPZ = os.path.join(ROOT, r"data\dataset_normalized.npz")
    PHYS = r"E:\project\work1\supplementary_validation_v4\T2_control\_data_physical.npz"
    d = np.load(NPZ, allow_pickle=True)
    p = np.load(PHYS, allow_pickle=True)
    params_phys = p["params_phys"]; J_phys = p["J_phys"]
    idx_tr, idx_va, idx_te = p["idx_train"], p["idx_val"], p["idx_test"]

    if args.branch == "L":
        J_train = d["J_train"].astype(np.float32); params_train = d["params_train"].astype(np.float32)
        J_val   = d["J_val"].astype(np.float32);   params_val   = d["params_val"].astype(np.float32)
        J_testN = d["J_test"].astype(np.float32);   params_testN = d["params_test"].astype(np.float32)
        # frozen full-fit scalers (physical log10 params / physical mA cm-2 J)
        pkl = pickle.load(open(os.path.join(ROOT, r"data\param_scaler.pkl"), "rb"))
        log_mask = np.asarray(pkl["log_mask"], bool)
        pmin = pkl["scaler"].data_min_; prange = pkl["scaler"].data_max_ - pmin
        jsc = pickle.load(open(os.path.join(ROOT, r"data\J_scaler.pkl"), "rb"))
        jmin = jsc.data_min_; jrange = jsc.data_max_ - jmin
        meta_scaler = dict(log_mask=log_mask.tolist(), pmin=pmin.tolist(), prange=prange.tolist(),
                           jmin=jmin.tolist(), jrange=jrange.tolist(), scope="L: full-data fit (frozen rule)")
    else:  # T
        from sklearn.preprocessing import MinMaxScaler
        # log10 decision + MinMax fit ONLY on train
        ptrain = params_phys[idx_tr]
        colmin = ptrain.min(0); colmax = ptrain.max(0)
        log_mask = (colmin > 0) & (colmax / np.maximum(colmin, 1e-300) > 100.0)
        Xtr = np.where(log_mask, np.log10(ptrain), ptrain)
        psT = MinMaxScaler(); psT.fit(Xtr)
        def transform_params(X):
            Xt = np.where(log_mask, np.log10(X), X)
            return psT.transform(Xt)
        jsT = MinMaxScaler(); jsT.fit(J_phys[idx_tr])
        params_all = np.concatenate([params_phys[idx_tr], params_phys[idx_va], params_phys[idx_te]], 0)
        J_all = np.concatenate([J_phys[idx_tr], J_phys[idx_va], J_phys[idx_te]], 0)
        Pn = transform_params(params_all).astype(np.float32); Jn = jsT.transform(J_all).astype(np.float32)
        n = len(idx_tr)
        params_train, params_val, params_testN = Pn[:n], Pn[n:n+len(idx_va)], Pn[n+len(idx_va):]
        J_train, J_val, J_testN = Jn[:n], Jn[n:n+len(idx_va)], Jn[n+len(idx_va):]
        pmin = psT.data_min_; prange = psT.data_max_ - pmin
        jmin = jsT.data_min_; jrange = jsT.data_max_ - jmin
        meta_scaler = dict(log_mask=log_mask.tolist(), pmin=pmin.tolist(), prange=prange.tolist(),
                           jmin=jmin.tolist(), jrange=jrange.tolist(), scope="T: train-only fit")

    n_train = len(J_train)
    rng = np.random.default_rng(S0)
    perm = rng.permutation(n_train)          # SAME fixed order for L and T
    train_ds = tf.data.Dataset.from_tensor_slices((J_train[perm], params_train[perm])).batch(M.BATCH_SIZE)
    val_ds = tf.data.Dataset.from_tensor_slices((J_val, params_val)).batch(M.BATCH_SIZE)

    seed_all(S0)  # re-seed so L and T build with identical init
    vae = M.build_vae()
    vae.compile(optimizer=keras.optimizers.Adam(1e-3))
    if args.dry:
        t0 = time.perf_counter()
        hist = vae.fit(train_ds, validation_data=val_ds, epochs=args.dry, verbose=1)
        dt = time.perf_counter() - t0
        print(f"[dry] {args.dry} epochs in {dt:.1f}s -> {dt/args.dry:.2f} s/epoch")
        json.dump({"s_per_epoch": dt / args.dry, "n_train": n_train},
                  open(os.path.join(run_dir, "dry_timing.json"), "w"), indent=1)
        sys.exit(0)

    callbacks = [
        # (D1) Keras3 cannot auto-infer direction for the custom 'val_param_loss'
        # metric (frozen ran under Keras 2 where unknown metrics defaulted to 'min').
        # (D6) ModelCheckpoint of the subclassed VAE is omitted: frozen best.weights.h5
        # was never loaded by official inference (T0 P6) and the pre-fixed eval rule is
        # the EarlyStopping(restore_best_weights=True) state -> checkpoint redundant.
        keras.callbacks.EarlyStopping(monitor="val_param_loss", mode="min",
                                      patience=50, restore_best_weights=True),
        keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=15, min_lr=1e-6),
    ]
    t0 = time.perf_counter()
    hist = vae.fit(train_ds, validation_data=val_ds, epochs=M.EPOCHS, callbacks=callbacks, verbose=1)
    dt = time.perf_counter() - t0
    vae.encoder.save(os.path.join(run_dir, "encoder.keras"))
    vae.decoder.save(os.path.join(run_dir, "decoder.keras"))
    vae.param_head.save(os.path.join(run_dir, "param_head.keras"))
    n_ep = len(hist.history["loss"])
    json.dump(hist.history, open(os.path.join(run_dir, "history.json"), "w"))
    json.dump({"branch": args.branch, "seed": S0, "n_epochs": n_ep,
               "best_epoch_idx": int(np.argmin(hist.history["val_param_loss"])),
               "val_param_loss_min": float(np.min(hist.history["val_param_loss"])),
               "val_loss_min": float(np.min(hist.history["val_loss"])),
               "wall_s": dt, "s_per_epoch": dt / n_ep,
               "perm_seed": S0, "n_train": n_train,
               "frozen_reference": "data/vae-v6/vae-v6/*.h5 (untouched)",
               "tf": tf.__version__, "keras": keras.__version__},
              open(os.path.join(run_dir, "meta.json"), "w"), indent=1)
    np.savez(os.path.join(run_dir, "scaler_meta.npz"), **{k: np.asarray(v) for k, v in meta_scaler.items()})
    print(f"[{tag}] done: {n_ep} epochs, best val_param_loss idx {int(np.argmin(hist.history['val_param_loss']))}, "
          f"{dt:.1f}s ({dt/n_ep:.2f} s/epoch)")

if __name__ == "__main__":
    main()
