# -*- coding: utf-8 -*-
"""VAE-v6 architecture, transcribed from script/VAE-v6.py (frozen main model).

Only the path/IO parts of the original file are removed.  Layer sizes, the
Sampling layer, the sigma transform, the Gaussian NLL, the three loss terms and
the train/test steps are unchanged.
"""
import os

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

INPUT_DIM = 131
LATENT_DIM = 9
N_PARAM = 9

BETA = 0.001
LAMBDA = 1.0
SIGMA_MIN = 0.01
SIGMA_MAX = 1.0

PARAM_NAMES = ["mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk",
               "Nc_eff_pvk", "Nv_eff_pvk", "tau_ETL", "tau_HTL", "rad_c"]


class Sampling(layers.Layer):
    def call(self, inputs):
        z_mean, z_log_var = inputs
        eps = tf.random.normal(shape=tf.shape(z_mean))
        return z_mean + tf.exp(0.5 * z_log_var) * eps


def build_encoder():
    inp = keras.Input(shape=(INPUT_DIM,))
    x = layers.Dense(128, activation="relu")(inp)
    x = layers.Dense(64, activation="relu")(x)
    z_mean = layers.Dense(LATENT_DIM, name="z_mean")(x)
    z_log_var = layers.Dense(LATENT_DIM, name="z_log_var")(x)
    z = Sampling()([z_mean, z_log_var])
    return keras.Model(inp, [z_mean, z_log_var, z], name="encoder")


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


class VAE(keras.Model):
    def __init__(self, encoder, decoder, param_head):
        super().__init__()
        self.encoder = encoder
        self.decoder = decoder
        self.param_head = param_head
        self.loss_tracker = keras.metrics.Mean(name="loss")
        self.recon_tracker = keras.metrics.Mean(name="recon_loss")
        self.kl_tracker = keras.metrics.Mean(name="kl_loss")
        self.param_tracker = keras.metrics.Mean(name="param_loss")

    @property
    def metrics(self):
        return [self.loss_tracker, self.recon_tracker,
                self.kl_tracker, self.param_tracker]

    def sigma_transform(self, raw):
        sigma = tf.nn.softplus(raw)
        sigma = sigma + SIGMA_MIN
        return tf.clip_by_value(sigma, SIGMA_MIN, SIGMA_MAX)

    def gaussian_nll(self, y, mu, sigma):
        loss = 0.5 * (tf.square(y - mu) / tf.square(sigma) +
                      2 * tf.math.log(sigma))
        return tf.reduce_mean(tf.reduce_sum(loss, axis=1))

    def _terms(self, x, y, training):
        z_mean, z_log_var, z = self.encoder(x, training=training)
        recon = self.decoder(z, training=training)
        mu, raw_sigma = self.param_head(z, training=training)
        sigma = self.sigma_transform(raw_sigma)
        recon_loss = tf.reduce_mean(
            tf.reduce_sum(tf.square(x - recon), axis=1))
        kl = -0.5 * tf.reduce_mean(
            tf.reduce_sum(1 + z_log_var - tf.square(z_mean) - tf.exp(z_log_var),
                          axis=1))
        param_loss = self.gaussian_nll(y, mu, sigma)
        loss = recon_loss + BETA * kl + LAMBDA * param_loss
        return loss, recon_loss, kl, param_loss

    def train_step(self, data):
        x, y = data
        with tf.GradientTape() as tape:
            loss, recon_loss, kl, param_loss = self._terms(x, y, True)
        grads = tape.gradient(loss, self.trainable_variables)
        self.optimizer.apply_gradients(zip(grads, self.trainable_variables))
        self.loss_tracker.update_state(loss)
        self.recon_tracker.update_state(recon_loss)
        self.kl_tracker.update_state(kl)
        self.param_tracker.update_state(param_loss)
        return {m.name: m.result() for m in self.metrics}

    def test_step(self, data):
        x, y = data
        loss, recon_loss, kl, param_loss = self._terms(x, y, False)
        self.loss_tracker.update_state(loss)
        self.recon_tracker.update_state(recon_loss)
        self.kl_tracker.update_state(kl)
        self.param_tracker.update_state(param_loss)
        return {m.name: m.result() for m in self.metrics}


def build_vae():
    return VAE(build_encoder(), build_decoder(), build_param_head())
