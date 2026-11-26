"""
VAE v6 — Gaussian Uncertainty Parameter Head
================================================

Physics-informed VAE

Input:
    J-V curve (131 points)

Output:
    parameter mean μ
    parameter uncertainty σ


Stable Gaussian NLL:
    sigma = softplus(raw_sigma)+sigma_min


Purpose:
    Identify parameter uncertainty
    for J-V inverse problem
"""


import numpy as np
import matplotlib.pyplot as plt
import pickle
import os


os.environ["TF_CPP_MIN_LOG_LEVEL"]="2"


import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

from scipy.stats import pearsonr, spearmanr



# =====================================================
# Path
# =====================================================


NPZ_PATH = (
"/home/student2/result-9D-AE-interface-lifetimes-2/"
"dataset_normalized.npz"
)


OUTPUT_DIR = (
"/home/student2/result-9D-AE-interface-lifetimes-2/"
"VAE_v6"
)


os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)



# =====================================================
# Hyper parameters
# =====================================================


INPUT_DIM = 131

LATENT_DIM = 9

N_PARAM = 9


BETA = 0.001

LAMBDA = 1.0


BATCH_SIZE = 64

EPOCHS = 1000



SIGMA_MIN = 0.01

SIGMA_MAX = 1.0



PARAM_NAMES=[

"mu_n_pvk",
"mu_p_pvk",
"tau_n_pvk",
"tau_p_pvk",
"Nc_eff_pvk",
"Nv_eff_pvk",
"tau_ETL",
"tau_HTL",
"rad_c"

]



# =====================================================
# Load data
# =====================================================


data=np.load(
    NPZ_PATH,
    allow_pickle=True
)


J_train=data["J_train"].astype(np.float32)

J_val=data["J_val"].astype(np.float32)

J_test=data["J_test"].astype(np.float32)



params_train=data["params_train"].astype(np.float32)

params_val=data["params_val"].astype(np.float32)

params_test=data["params_test"].astype(np.float32)



print(
J_train.shape,
params_train.shape
)




# =====================================================
# Sampling
# =====================================================


class Sampling(layers.Layer):

    def call(self,inputs):

        z_mean,z_log_var=inputs


        eps=tf.random.normal(
            shape=tf.shape(z_mean)
        )


        return (
            z_mean
            +
            tf.exp(
                0.5*z_log_var
            )
            *
            eps
        )



# =====================================================
# Encoder
# =====================================================


def build_encoder():


    inp=keras.Input(
        shape=(INPUT_DIM,)
    )


    x=layers.Dense(
        128,
        activation="relu"
    )(inp)


    x=layers.Dense(
        64,
        activation="relu"
    )(x)



    z_mean=layers.Dense(
        LATENT_DIM,
        name="z_mean"
    )(x)



    z_log_var=layers.Dense(
        LATENT_DIM,
        name="z_log_var"
    )(x)



    z=Sampling()(
        [
            z_mean,
            z_log_var
        ]
    )



    return keras.Model(
        inp,
        [
            z_mean,
            z_log_var,
            z
        ],
        name="encoder"
    )





# =====================================================
# Decoder
# =====================================================


def build_decoder():


    inp=keras.Input(
        shape=(LATENT_DIM,)
    )


    x=layers.Dense(
        64,
        activation="relu"
    )(inp)


    x=layers.Dense(
        128,
        activation="relu"
    )(x)


    out=layers.Dense(
        INPUT_DIM,
        activation="sigmoid"
    )(x)



    return keras.Model(
        inp,
        out,
        name="decoder"
    )





# =====================================================
# Gaussian parameter head
# =====================================================


def build_param_head():


    inp=keras.Input(
        shape=(LATENT_DIM,)
    )


    x=layers.Dense(
        64,
        activation="relu"
    )(inp)


    x=layers.Dense(
        32,
        activation="relu"
    )(x)



    mu=layers.Dense(
        N_PARAM,
        name="param_mu"
    )(x)



    sigma_raw=layers.Dense(
        N_PARAM,
        bias_initializer=
        keras.initializers.Constant(-3.0),
        name="sigma_raw"
    )(x)



    return keras.Model(
        inp,
        [
            mu,
            sigma_raw
        ],
        name="gaussian_parameter_head"
    )




encoder=build_encoder()

decoder=build_decoder()

param_head=build_param_head()




# =====================================================
# VAE
# =====================================================


class VAE(keras.Model):


    def __init__(
        self,
        encoder,
        decoder,
        param_head
    ):

        super().__init__()


        self.encoder=encoder

        self.decoder=decoder

        self.param_head=param_head



        self.loss_tracker=keras.metrics.Mean(
            name="loss"
        )

        self.recon_tracker=keras.metrics.Mean(
            name="recon_loss"
        )

        self.kl_tracker=keras.metrics.Mean(
            name="kl_loss"
        )

        self.param_tracker=keras.metrics.Mean(
            name="param_loss"
        )



    @property
    def metrics(self):

        return [

        self.loss_tracker,
        self.recon_tracker,
        self.kl_tracker,
        self.param_tracker

        ]



    def sigma_transform(
        self,
        raw
    ):


        sigma=tf.nn.softplus(raw)


        sigma=sigma+SIGMA_MIN


        sigma=tf.clip_by_value(
            sigma,
            SIGMA_MIN,
            SIGMA_MAX
        )


        return sigma




    def gaussian_nll(
        self,
        y,
        mu,
        sigma
    ):


        loss=0.5*(

            tf.square(
                y-mu
            )
            /
            tf.square(
                sigma
            )

            +

            2*tf.math.log(
                sigma
            )

        )


        return tf.reduce_mean(

            tf.reduce_sum(
                loss,
                axis=1
            )

        )




    def train_step(
        self,
        data
    ):


        x,y=data


        with tf.GradientTape() as tape:


            z_mean,z_log_var,z=\
            self.encoder(
                x,
                training=True
            )


            recon=self.decoder(
                z,
                training=True
            )


            mu,raw_sigma=\
            self.param_head(
                z,
                training=True
            )


            sigma=self.sigma_transform(
                raw_sigma
            )



            recon_loss=tf.reduce_mean(

                tf.reduce_sum(
                    tf.square(
                        x-recon
                    ),
                    axis=1
                )

            )



            kl=-0.5*tf.reduce_mean(

                tf.reduce_sum(
                    1+
                    z_log_var-
                    tf.square(z_mean)-
                    tf.exp(z_log_var),
                    axis=1
                )

            )



            param_loss=self.gaussian_nll(
                y,
                mu,
                sigma
            )



            loss=(

                recon_loss

                +

                BETA*kl

                +

                LAMBDA*param_loss

            )



        grads=tape.gradient(
            loss,
            self.trainable_variables
        )


        self.optimizer.apply_gradients(
            zip(
                grads,
                self.trainable_variables
            )
        )



        self.loss_tracker.update_state(loss)

        self.recon_tracker.update_state(recon_loss)

        self.kl_tracker.update_state(kl)

        self.param_tracker.update_state(param_loss)



        return {
            m.name:m.result()
            for m in self.metrics
        }



    def test_step(
        self,
        data
    ):


        x,y=data


        z_mean,z_log_var,z=\
        self.encoder(
            x,
            training=False
        )


        recon=self.decoder(
            z,
            training=False
        )


        mu,raw_sigma=\
        self.param_head(
            z,
            training=False
        )


        sigma=self.sigma_transform(
            raw_sigma
        )



        recon_loss=tf.reduce_mean(

            tf.reduce_sum(
                tf.square(
                    x-recon
                ),
                axis=1
            )

        )


        kl=-0.5*tf.reduce_mean(

            tf.reduce_sum(
                1+
                z_log_var-
                tf.square(z_mean)-
                tf.exp(z_log_var),
                axis=1
            )

        )


        param_loss=self.gaussian_nll(
            y,
            mu,
            sigma
        )


        loss=(

        recon_loss
        +
        BETA*kl
        +
        LAMBDA*param_loss

        )



        self.loss_tracker.update_state(loss)

        self.recon_tracker.update_state(recon_loss)

        self.kl_tracker.update_state(kl)

        self.param_tracker.update_state(param_loss)



        return {
            m.name:m.result()
            for m in self.metrics
        }



# =====================================================
# Train
# =====================================================


vae=VAE(
    encoder,
    decoder,
    param_head
)


vae.compile(
    optimizer=keras.optimizers.Adam(
        1e-3
    )
)



train_ds=tf.data.Dataset.from_tensor_slices(
(
J_train,
params_train
)
).shuffle(
len(J_train)
).batch(
BATCH_SIZE
)



val_ds=tf.data.Dataset.from_tensor_slices(
(
J_val,
params_val
)
).batch(
BATCH_SIZE
)



callbacks=[

keras.callbacks.EarlyStopping(
monitor="val_param_loss",
patience=50,
restore_best_weights=True
),


keras.callbacks.ReduceLROnPlateau(
monitor="val_loss",
factor=0.5,
patience=15,
min_lr=1e-6
),


keras.callbacks.ModelCheckpoint(
f"{OUTPUT_DIR}/best.weights.h5",
save_best_only=True,
save_weights_only=True,
monitor="val_loss"
)

]



history=vae.fit(

train_ds,

validation_data=val_ds,

epochs=EPOCHS,

callbacks=callbacks

)



encoder.save(
f"{OUTPUT_DIR}/encoder.h5"
)

decoder.save(
f"{OUTPUT_DIR}/decoder.h5"
)

param_head.save(
f"{OUTPUT_DIR}/param_head.h5"
)


with open(
f"{OUTPUT_DIR}/history.pkl",
"wb"
) as f:

    pickle.dump(
        history.history,
        f
    )



print("Training finished")