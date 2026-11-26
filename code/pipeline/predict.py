import numpy as np
import matplotlib.pyplot as plt
from tensorflow import keras
from tensorflow.keras import layers
from scipy.stats import pearsonr
import os


# =====================================================
# 路径
# =====================================================

DATA_PATH = (
    "/home/student2/result-9D-AE-interface-lifetimes-2/"
    "dataset_normalized.npz"
)

MODEL_DIR = (
    "/home/student2/result-9D-AE-interface-lifetimes-2/"
    "VAE_v6"
)

os.makedirs(MODEL_DIR, exist_ok=True)



# =====================================================
# 参数名称
# =====================================================

PARAM_NAMES = [
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
# Sampling层
# =====================================================

class Sampling(layers.Layer):

    def call(self, inputs):

        z_mean, z_log_var = inputs

        epsilon = keras.backend.random_normal(
            shape=keras.backend.shape(z_mean)
        )

        return (
            z_mean
            +
            keras.backend.exp(0.5*z_log_var)
            *
            epsilon
        )



# =====================================================
# 加载模型
# =====================================================

print("Loading models...")


encoder = keras.models.load_model(
    MODEL_DIR + "/encoder.h5",
    custom_objects={
        "Sampling": Sampling
    }
)


param_head = keras.models.load_model(
    MODEL_DIR + "/param_head.h5"
)


print("Models loaded")



# =====================================================
# 加载数据
# =====================================================

data=np.load(DATA_PATH)


J_test=data["J_test"].astype(np.float32)

params_test=data["params_test"].astype(np.float32)



print("J_test:",J_test.shape)

print(
    "params_test:",
    params_test.shape
)



# =====================================================
# 参数预测
# =====================================================


z_mean,_,_=encoder.predict(
    J_test,
    verbose=0
)



# v6 uncertainty head:
# 输出:
# [mu, log_var]

params_pred_mu, params_pred_logvar = param_head.predict(
    z_mean,
    verbose=0
)


params_pred=params_pred_mu



print(
    "Prediction:",
    params_pred.shape
)



# =====================================================
# Pearson r
# =====================================================

print("\n===== Pearson r =====")


r_values=[]


for i,name in enumerate(PARAM_NAMES):

    r,_=pearsonr(
        params_test[:,i],
        params_pred[:,i]
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
# 图1
# 三参数可识别性展示
# =====================================================


plot_ids=[
    1,  # mu_p_pvk
    6,  # tau_ETL
    7   # tau_HTL
]


titles=[
    "Highly identifiable",
    "Moderately identifiable",
    "Poorly identifiable"
]


fig,axes=plt.subplots(
    1,
    3,
    figsize=(15,4)
)



for ax,idx,title in zip(
    axes,
    plot_ids,
    titles
):


    true=params_test[:,idx]

    pred=params_pred[:,idx]


    r,_=pearsonr(
        true,
        pred
    )


    ax.scatter(
        true,
        pred,
        s=5,
        alpha=0.25
    )


    # 理想线

    ax.plot(
        [0,1],
        [0,1],
        "--",
        linewidth=1
    )


    # 统一尺度

    ax.set_xlim(
        0,
        1
    )

    ax.set_ylim(
        0,
        1
    )

    ax.set_aspect('equal')


    ax.set_xlabel(
        "True normalized value"
    )

    ax.set_ylabel(
        "Predicted normalized value"
    )


    ax.set_title(
        f"{PARAM_NAMES[idx]}\nr={r:.3f}\n{title}"
    )



plt.tight_layout()


plt.savefig(
    MODEL_DIR+
    "/fig_parameter_scatter_3params.png",
    dpi=300
)


plt.close()



print(
    "Saved:",
    "fig_parameter_scatter_3params.png"
)




# =====================================================
# 图2
# 全9参数散点图
# =====================================================


fig,axes=plt.subplots(
    3,
    3,
    figsize=(12,12)
)


axes=axes.flatten()



for idx,ax in enumerate(axes):


    true=params_test[:,idx]

    pred=params_pred[:,idx]


    r,_=pearsonr(
        true,
        pred
    )


    ax.scatter(
        true,
        pred,
        s=3,
        alpha=0.25
    )


    ax.plot(
        [0,1],
        [0,1],
        "--",
        linewidth=0.8
    )


    ax.set_xlim(
        0,
        1
    )

    ax.set_ylim(
        0,
        1
    )


    ax.set_xlabel(
        "True"
    )

    ax.set_ylabel(
        "Pred"
    )


    ax.set_title(
        f"{PARAM_NAMES[idx]}\nr={r:.3f}"
    )



plt.tight_layout()


plt.savefig(
    MODEL_DIR+
    "/fig_parameter_scatter_all9.png",
    dpi=300
)


plt.close()



print(
    "Saved:",
    "fig_parameter_scatter_all9.png"
)


print("\nFinished.")