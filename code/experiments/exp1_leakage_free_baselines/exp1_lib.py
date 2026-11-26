# -*- coding: utf-8 -*-
"""
Shared library for EXP1 — leakage-free multi-seed matched baseline benchmark.

CONVENTIONS (locked to frozen VAE-v6, script/VAE-v6.py):
  sigma      = clip(softplus(raw) + 0.01, 0.01, 1.0)          (SIGMA_MIN/MAX)
  recon_loss = mean_batch[ sum_{j=1..131} (x_j - recon_j)^2 ]  (per-sample SUM then batch mean)
  kl         = -0.5 * mean_batch[ sum_j (1 + z_log_var_j - z_mean_j^2 - exp(z_log_var_j)) ]
  nll        = mean_batch[ sum_{p=1..9} ( 0.5*((y_p-mu_p)/sigma_p)^2 + log(sigma_p) ) ]
  total      = recon + BETA*kl + LAMBDA*nll            (BETA=1e-3, LAMBDA=1.0)
  optimizer  = Adam(1e-3); batch 64; epochs 1000
  EarlyStopping  monitor=val_param_loss patience=50 restore_best_weights=True
  ReduceLROnPlateau monitor=val_loss factor=0.5 patience=15 min_lr=1e-6
  ModelCheckpoint  monitor=val_loss save_best_only (kept for provenance)
  Eval path: VAE uses z_mean; Det-AE uses encoded z; MLP direct.
"""
import os, time, pickle, random, json
import numpy as np

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

INPUT_DIM = 131
LATENT_DIM = 9
N_PARAM = 9
BETA = 1e-3
LAMBDA = 1.0
BATCH_SIZE = 64
SIGMA_MIN = 0.01
SIGMA_MAX = 1.0
EARLY_PATIENCE = 50
LR_PATIENCE = 15
LR_FACTOR = 0.5
MIN_LR = 1e-6
INIT_LR = 1e-3
EPOCHS = int(os.environ.get("EXP1_MAX_EPOCHS", "1000"))  # env override for smoke tests

PARAM_NAMES = ["mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk",
               "Nc_eff_pvk", "Nv_eff_pvk", "tau_ETL", "tau_HTL", "rad_c"]
SHORT_NAMES = ["mu_n", "mu_p", "tau_n", "tau_p", "Nc", "Nv",
               "tau_ETL", "tau_HTL", "rad_c"]
NOMINAL = {0.50: 0.67448975, 0.80: 1.28155157, 0.90: 1.64485363, 0.95: 1.95996398}


def seed_all(seed):
    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)


def load_lf_data():
    npz = np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "leakage_free_dataset.npz"), allow_pickle=True)
    return {k: npz[k] for k in npz.files}


def load_scalers():
    """Prefer the numpy-version-agnostic .npz (arrays only, no pickle bytecode);
    fall back to the legacy .pkl. Values are identical."""
    here = os.path.dirname(os.path.abspath(__file__))
    npz_path = os.path.join(here, "train_only_scalers.npz")
    if os.path.exists(npz_path):
        z = np.load(npz_path, allow_pickle=False)
        return {
            "log_mask": z["log_mask"],
            "param_names": z["param_names"],
            "param_min_log10": z["param_min_log10"],
            "param_max_log10": z["param_max_log10"],
            "param_scale": (z["param_scale_scale"], z["param_scale_min"]),
            "J_min": z["J_min"],
            "J_max": z["J_max"],
            "J_scale": (z["J_scale_scale"], z["J_scale_min"]),
            "N_train": int(z["N_train"]), "N_val": int(z["N_val"]), "N_test": int(z["N_test"]),
        }
    with open(os.path.join(here, "train_only_scalers.pkl"), "rb") as f:
        return pickle.load(f)


# ---------------- sigma / loss primitives ----------------

def sigma_transform(raw):
    s = tf.nn.softplus(raw) + SIGMA_MIN
    return tf.clip_by_value(s, SIGMA_MIN, SIGMA_MAX)


def gaussian_nll(y, mu, sigma):
    """mean_batch[ sum_p( 0.5*((y-mu)/sigma)^2 + log(sigma) ) ]  (frozen form)"""
    loss = 0.5 * (tf.square(y - mu) / tf.square(sigma) + 2 * tf.math.log(sigma))
    return tf.reduce_mean(tf.reduce_sum(loss, axis=1))


def kl_divergence(z_mean, z_log_var):
    return -0.5 * tf.reduce_mean(
        tf.reduce_sum(1 + z_log_var - tf.square(z_mean) - tf.exp(z_log_var), axis=1))


def recon_loss(x, recon):
    return tf.reduce_mean(tf.reduce_sum(tf.square(x - recon), axis=1))


# ---------------- model builders ----------------

def build_encoder(family):
    inp = keras.Input(shape=(INPUT_DIM,))
    x = layers.Dense(128, activation="relu")(inp)
    x = layers.Dense(64, activation="relu")(x)
    if family == "vae":
        z_mean = layers.Dense(LATENT_DIM, name="z_mean")(x)
        z_log_var = layers.Dense(LATENT_DIM, name="z_log_var")(x)
        z = _sampling()([z_mean, z_log_var])
        return keras.Model(inp, [z_mean, z_log_var, z], name="encoder")
    else:  # det_ae
        z = layers.Dense(LATENT_DIM, name="z")(x)
        return keras.Model(inp, z, name="encoder")


class _Sampling(layers.Layer):
    def call(self, inputs):
        z_mean, z_log_var = inputs
        eps = tf.random.normal(shape=tf.shape(z_mean))
        return z_mean + tf.exp(0.5 * z_log_var) * eps


_sampling_cache = None
def _sampling():
    global _sampling_cache
    if _sampling_cache is None:
        _sampling_cache = _Sampling()
    return _sampling_cache


def build_decoder():
    inp = keras.Input(shape=(LATENT_DIM,))
    x = layers.Dense(64, activation="relu")(inp)
    x = layers.Dense(128, activation="relu")(x)
    out = layers.Dense(INPUT_DIM, activation="sigmoid")(x)
    return keras.Model(inp, out, name="decoder")


def build_param_head():
    inp = keras.Input(shape=(LATENT_DIM,))
    x = layers.Dense(64, activation="relu")(inp)
    x = layers.Dense(32, activation="relu")(x)
    mu = layers.Dense(N_PARAM, name="param_mu")(x)
    sigma_raw = layers.Dense(N_PARAM,
                             bias_initializer=keras.initializers.Constant(-3.0),
                             name="sigma_raw")(x)
    return keras.Model(inp, [mu, sigma_raw], name="gaussian_parameter_head")


def build_mlp_trunk():
    inp = keras.Input(shape=(INPUT_DIM,))
    x = layers.Dense(128, activation="relu")(inp)
    x = layers.Dense(64, activation="relu")(x)
    h = layers.Dense(32, activation="relu", name="trunk_h")(x)
    mu = layers.Dense(N_PARAM, name="param_mu")(h)
    sigma_raw = layers.Dense(N_PARAM,
                             bias_initializer=keras.initializers.Constant(-3.0),
                             name="sigma_raw")(h)
    return keras.Model(inp, [h, mu, sigma_raw], name="mlp_trunk")


# ---------------- composite model ----------------

class ParamModel(keras.Model):
    """family in {'vae','det_ae','mlp'}"""

    def __init__(self, family, encoder=None, decoder=None, param_head=None, trunk=None):
        super().__init__()
        self.family = family
        self.encoder = encoder
        self.decoder = decoder
        self.param_head = param_head
        self.trunk = trunk
        self.loss_tracker = keras.metrics.Mean(name="loss")
        self.recon_tracker = keras.metrics.Mean(name="recon_loss")
        self.kl_tracker = keras.metrics.Mean(name="kl_loss")
        self.param_tracker = keras.metrics.Mean(name="param_loss")

    @property
    def metrics(self):
        return [self.loss_tracker, self.recon_tracker, self.kl_tracker, self.param_tracker]

    def call(self, inputs, training=False):
        return self.forward(inputs, training)

    def forward(self, x, training):
        if self.family == "vae":
            z_mean, z_log_var, z = self.encoder(x, training=training)
            recon = self.decoder(z, training=training)
            mu, raw_sigma = self.param_head(z, training=training)
            return dict(z_mean=z_mean, z_log_var=z_log_var, z=z, recon=recon,
                        mu=mu, sigma=sigma_transform(raw_sigma))
        elif self.family == "det_ae":
            z = self.encoder(x, training=training)
            recon = self.decoder(z, training=training)
            mu, raw_sigma = self.param_head(z, training=training)
            return dict(z=z, recon=recon, mu=mu, sigma=sigma_transform(raw_sigma))
        else:  # mlp
            h, mu, raw_sigma = self.trunk(x, training=training)
            return dict(h=h, mu=mu, sigma=sigma_transform(raw_sigma))

    def compute_losses(self, x, y, out):
        losses = {}
        losses["param_loss"] = gaussian_nll(y, out["mu"], out["sigma"])
        if self.family in ("vae", "det_ae"):
            losses["recon_loss"] = recon_loss(x, out["recon"])
        else:
            losses["recon_loss"] = tf.constant(0.0)
        if self.family == "vae":
            losses["kl"] = kl_divergence(out["z_mean"], out["z_log_var"])
        else:
            losses["kl"] = tf.constant(0.0)
        losses["loss"] = (losses["recon_loss"] + BETA * losses["kl"] + LAMBDA * losses["param_loss"])
        return losses

    def train_step(self, data):
        x, y = data
        with tf.GradientTape() as tape:
            out = self.forward(x, training=True)
            L = self.compute_losses(x, y, out)
        grads = tape.gradient(L["loss"], self.trainable_variables)
        self.optimizer.apply_gradients(zip(grads, self.trainable_variables))
        self.loss_tracker.update_state(L["loss"])
        self.recon_tracker.update_state(L["recon_loss"])
        self.kl_tracker.update_state(L["kl"])
        self.param_tracker.update_state(L["param_loss"])
        return {m.name: m.result() for m in self.metrics}

    def test_step(self, data):
        x, y = data
        out = self.forward(x, training=False)
        L = self.compute_losses(x, y, out)
        self.loss_tracker.update_state(L["loss"])
        self.recon_tracker.update_state(L["recon_loss"])
        self.kl_tracker.update_state(L["kl"])
        self.param_tracker.update_state(L["param_loss"])
        return {m.name: m.result() for m in self.metrics}

    def predict_eval(self, x_test):
        """Deterministic eval path (frozen convention: VAE uses z_mean)."""
        x = tf.constant(x_test, dtype=tf.float32)
        if self.family == "vae":
            z_mean, z_log_var, z = self.encoder(x, training=False)
            z_det = z_mean
            recon = self.decoder(z_det, training=False)
            mu, raw_sigma = self.param_head(z_det, training=False)
        elif self.family == "det_ae":
            z = self.encoder(x, training=False)
            recon = self.decoder(z, training=False)
            mu, raw_sigma = self.param_head(z, training=False)
        else:
            h, mu, raw_sigma = self.trunk(x, training=False)
            recon = None
        sigma = sigma_transform(raw_sigma)
        return mu.numpy(), sigma.numpy(), (recon.numpy() if recon is not None else None)


def build_model(family):
    if family == "vae":
        return ParamModel("vae", build_encoder("vae"), build_decoder(), build_param_head())
    if family == "det_ae":
        return ParamModel("det_ae", build_encoder("det_ae"), build_decoder(), build_param_head())
    if family == "mlp":
        return ParamModel("mlp", trunk=build_mlp_trunk())
    raise ValueError(family)


# ---------------- training ----------------

def train_one(family, seed, outdir):
    os.makedirs(outdir, exist_ok=True)
    seed_all(seed)
    data = load_lf_data()
    J_train = data["J_train"].astype(np.float32)
    J_val = data["J_val"].astype(np.float32)
    P_train = data["params_train"].astype(np.float32)
    P_val = data["params_val"].astype(np.float32)

    model = build_model(family)
    # build composite (needed for Keras-3 ModelCheckpoint save_weights)
    model(tf.zeros((1, INPUT_DIM), dtype=tf.float32), training=False)
    model.compile(optimizer=keras.optimizers.Adam(INIT_LR))

    train_ds = tf.data.Dataset.from_tensor_slices((J_train, P_train)) \
        .shuffle(len(J_train), seed=seed, reshuffle_each_iteration=False) \
        .batch(BATCH_SIZE).prefetch(2)
    val_ds = tf.data.Dataset.from_tensor_slices((J_val, P_val)).batch(BATCH_SIZE)

    callbacks = [
        keras.callbacks.EarlyStopping(monitor="val_param_loss", patience=EARLY_PATIENCE,
                                      restore_best_weights=True, mode="min"),
        keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=LR_FACTOR,
                                          patience=LR_PATIENCE, min_lr=MIN_LR, mode="min"),
        keras.callbacks.ModelCheckpoint(os.path.join(outdir, "best_val_loss.weights.h5"),
                                        save_best_only=True, save_weights_only=True,
                                        monitor="val_loss", mode="min"),
    ]

    t0 = time.time()
    history = model.fit(train_ds, validation_data=val_ds, epochs=EPOCHS,
                        callbacks=callbacks, verbose=0)
    train_seconds = time.time() - t0

    vp = np.asarray(history.history["val_param_loss"])
    best_epoch = int(np.argmin(vp)) + 1
    stop_epoch = len(vp)

    # save submodules (frozen convention: these carry the restore_best_weights state)
    if family in ("vae", "det_ae"):
        model.encoder.save(os.path.join(outdir, "encoder.h5"))
        model.decoder.save(os.path.join(outdir, "decoder.h5"))
        model.param_head.save(os.path.join(outdir, "param_head.h5"))
    else:
        model.trunk.save(os.path.join(outdir, "trunk.h5"))
    with open(os.path.join(outdir, "history.pkl"), "wb") as f:
        pickle.dump(history.history, f)

    # eval bundle on test
    data_t = load_lf_data()
    J_test = data_t["J_test"].astype(np.float32)
    P_test = data_t["params_test"].astype(np.float32)
    mu, sigma, recon = model.predict_eval(J_test)

    with open(os.path.join(outdir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump({"family": family, "seed": seed,
                   "best_epoch": best_epoch, "stop_epoch": stop_epoch,
                   "train_seconds": train_seconds,
                   "param_count": int(model.count_params())}, f)

    np.savez(os.path.join(outdir, "eval_bundle.npz"),
             family=family, seed=seed,
             param_mu=mu, param_sigma=sigma,
             recon=recon if recon is not None else np.zeros((0, 0)),
             params_test=P_test, J_test=J_test)
    return model, history, train_seconds
