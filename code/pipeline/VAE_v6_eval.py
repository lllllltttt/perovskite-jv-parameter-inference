"""
VAE v5 Evaluation
=================

Gaussian Parameter Head uncertainty evaluation

Output:
1. Reconstruction error
2. Pearson parameter prediction
3. Predicted sigma
4. Uncertainty-error correlation
5. 95% confidence coverage
6. Visualization
"""

import os
import numpy as np
import matplotlib.pyplot as plt
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


MODEL_DIR = (
    "/home/student2/result-9D-AE-interface-lifetimes-2/"
    "VAE_v6"
)


OUTPUT_DIR = MODEL_DIR + "/evaluation"

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# =====================================================
# Parameters
# =====================================================

INPUT_DIM = 131


PARAM_NAMES = [

    "mu_n_pvk",
    "mu_p_pvk",
    "tau_n_pvk",
    "tau_p_pvk",
    "Nc_eff_pvk",
    "Nv_eff_pvk",
    "tau_ETL",
    "tau_HTL",
    "rad_c",

]


N_PARAM=len(PARAM_NAMES)



# =====================================================
# Sampling layer
# =====================================================

class Sampling(layers.Layer):

    def call(self,inputs):

        z_mean,z_log_var=inputs

        eps=tf.random.normal(
            shape=tf.shape(z_mean)
        )

        return (
            z_mean+
            tf.exp(0.5*z_log_var)*eps
        )



# =====================================================
# Load data
# =====================================================


data=np.load(
    NPZ_PATH,
    allow_pickle=True
)


J_test=data["J_test"].astype(
    np.float32
)


params_test=data["params_test"].astype(
    np.float32
)


print(
    "Test:",
    J_test.shape,
    params_test.shape
)



# =====================================================
# Load models
# =====================================================


encoder=keras.models.load_model(
    MODEL_DIR+"/encoder.h5",
    custom_objects={
        "Sampling":Sampling
    }
)


decoder=keras.models.load_model(
    MODEL_DIR+"/decoder.h5"
)


param_head=keras.models.load_model(
    MODEL_DIR+"/param_head.h5"
)



print("Models loaded")



# =====================================================
# Prediction
# =====================================================


z_mean,z_log_var,z = encoder.predict(
    J_test,
    verbose=0
)



# reconstruction

recon_test=decoder.predict(
    z_mean,
    verbose=0
)



# Gaussian parameter prediction

param_mu,param_log_var=param_head.predict(
    z_mean,
    verbose=0
)



# sigma

param_sigma=np.exp(
    0.5*param_log_var
)



# =====================================================
# Reconstruction
# =====================================================


mse=np.mean(
    (J_test-recon_test)**2,
    axis=1
)


print("\n===== Reconstruction =====")

print(
    "Mean MSE:",
    mse.mean()
)

print(
    "Median MSE:",
    np.median(mse)
)



# =====================================================
# Pearson
# =====================================================


print(
    "\n===== Pearson r ====="
)


r_values=[]


for i,name in enumerate(PARAM_NAMES):

    r,_=pearsonr(
        params_test[:,i],
        param_mu[:,i]
    )

    r_values.append(r)


    print(
        f"{name:20s}: {r:.4f}"
    )


print(
    "Mean:",
    np.mean(r_values)
)



# =====================================================
# Sigma statistics
# =====================================================


print(
    "\n===== Predicted Sigma ====="
)


for i,name in enumerate(PARAM_NAMES):

    print(
        f"{name:20s}: "
        f"mean={param_sigma[:,i].mean():.5f}, "
        f"median={np.median(param_sigma[:,i]):.5f}"
    )



# =====================================================
# uncertainty-error correlation
# =====================================================


print(
    "\n===== Spearman sigma vs error ====="
)


error=np.abs(
    params_test-param_mu
)


spearman_values=[]


for i,name in enumerate(PARAM_NAMES):

    rho,p=spearmanr(
        param_sigma[:,i],
        error[:,i]
    )

    spearman_values.append(rho)


    print(
        f"{name:20s}: "
        f"rho={rho:.4f}, "
        f"p={p:.2e}"
    )



# =====================================================
# Coverage
# =====================================================


print(
    "\n===== 95% Coverage ====="
)


lower=(
    param_mu-
    1.96*param_sigma
)


upper=(
    param_mu+
    1.96*param_sigma
)



coverage=np.mean(
    (
        params_test>=lower
    )
    &
    (
        params_test<=upper
    ),
    axis=0
)



for i,name in enumerate(PARAM_NAMES):

    print(
        f"{name:20s}: {coverage[i]:.4f}"
    )



# =====================================================
# Visualization
# =====================================================


short_names=[

    "mu_n",
    "mu_p",
    "tau_n",
    "tau_p",
    "Nc",
    "Nv",
    "tau_ETL",
    "tau_HTL",
    "rad_c"

]



# Pearson

plt.figure(
    figsize=(8,4)
)

plt.bar(
    range(N_PARAM),
    r_values
)

plt.xticks(
    range(N_PARAM),
    short_names,
    rotation=45
)

plt.ylabel(
    "Pearson r"
)

plt.title(
    "Parameter Prediction"
)

plt.axhline(
    0.8,
    linestyle="--"
)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR+
    "/pearson.png",
    dpi=300
)

plt.close()



# Sigma


plt.figure(
    figsize=(8,4)
)

plt.bar(
    range(N_PARAM),
    np.mean(
        param_sigma,
        axis=0
    )
)


plt.xticks(
    range(N_PARAM),
    short_names,
    rotation=45
)


plt.ylabel(
    "Predicted sigma"
)


plt.title(
    "Parameter uncertainty"
)


plt.tight_layout()


plt.savefig(
    OUTPUT_DIR+
    "/sigma.png",
    dpi=300
)


plt.close()



# Spearman


plt.figure(
    figsize=(8,4)
)

plt.bar(
    range(N_PARAM),
    spearman_values
)


plt.xticks(
    range(N_PARAM),
    short_names,
    rotation=45
)


plt.ylabel(
    "Spearman rho"
)


plt.title(
    "Uncertainty-error correlation"
)


plt.axhline(
    0,
    linestyle="--"
)


plt.tight_layout()


plt.savefig(
    OUTPUT_DIR+
    "/spearman.png",
    dpi=300
)


plt.close()



print(
    "\nEvaluation finished."
)

# =====================================================
# Uncertainty vs Error scatter
# =====================================================

print(
    "\n===== Plot uncertainty vs error ====="
)


for i,name in enumerate(PARAM_NAMES):

    plt.figure(
        figsize=(5,4)
    )

    x = param_sigma[:,i]

    y = error[:,i]


    rho,_ = spearmanr(
        x,
        y
    )


    plt.scatter(
        x,
        y,
        s=5,
        alpha=0.3
    )


    plt.xlabel(
        "Predicted uncertainty σ"
    )

    plt.ylabel(
        "|Prediction error|"
    )


    plt.title(
        f"{name}\nSpearman r={rho:.3f}"
    )


    plt.tight_layout()


    plt.savefig(
        OUTPUT_DIR+
        f"/uncertainty_error_{name}.png",
        dpi=300
    )


    plt.close()