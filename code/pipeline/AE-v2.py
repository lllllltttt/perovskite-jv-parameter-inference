"""
Step 02b: Autoencoder v2 — 半监督版本 (AE_v2)，9D数据集（界面寿命版）
===============================================
更新内容：
  1. 路径更新 → result-9D-AE-interface-lifetimes
  2. PARAM_NAMES 更新为当前项目的 9 个参数：
     mu_n_pvk, mu_p_pvk, tau_n_pvk, tau_p_pvk,
     Nc_eff_pvk, Nv_eff_pvk, tau_ETL, tau_HTL, rad_c
  3. 可视化标签同步更新
  4. 短名称生成逻辑适配新参数
"""

import numpy as np
import matplotlib.pyplot as plt
import pickle
import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from scipy.stats import pearsonr

# =====================================================
# 路径配置（适配当前项目）
# =====================================================
NPZ_PATH   = "/home/student2/result-9D-AE-interface-lifetimes-2/dataset_normalized.npz"
OUTPUT_DIR = "/home/student2/result-9D-AE-interface-lifetimes-2/AE-v2"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# =====================================================
# 超参数
# =====================================================
INPUT_DIM  = 131
LATENT_DIM = 9
DROPOUT_P  = 0.05
LAMBDA     = 1.0

# =====================================================
# 参数名称（与当前项目一致）
# =====================================================
PARAM_NAMES = [
    "mu_n_pvk",
    "mu_p_pvk",
    "tau_n_pvk",
    "tau_p_pvk",
    "Nc_eff_pvk",
    "Nv_eff_pvk",
    "tau_ETL",        # 界面寿命（取代 Nt_ETL_PVK）
    "tau_HTL",        # 界面寿命（取代 Nt_HTL_PVK）
    "rad_c",
]

# =====================================================
# 加载数据
# =====================================================
data = np.load(NPZ_PATH, allow_pickle=True)

J_train = data["J_train"].astype(np.float32)
J_val   = data["J_val"].astype(np.float32)
J_test  = data["J_test"].astype(np.float32)

params_train = data["params_train"].astype(np.float32)
params_val   = data["params_val"].astype(np.float32)
params_test  = data["params_test"].astype(np.float32)

if "param_names" in data:
    param_names = data["param_names"]
else:
    param_names = np.array(PARAM_NAMES)

print(f"Train: {J_train.shape}, Val: {J_val.shape}, Test: {J_test.shape}")
print(f"Lambda (supervision weight): {LAMBDA}")

# =====================================================
# 模型定义
# Encoder: 131 → 128 → 64 → 9
# Decoder: 9   → 64  → 128 → 131
# =====================================================
def build_ae_v2(input_dim=131, latent_dim=9, dropout_p=0.05):
    # ── Encoder ──────────────────────────────────
    encoder_input = keras.Input(shape=(input_dim,), name="encoder_input")
    x = layers.Dense(128, activation="relu", name="enc_dense1")(encoder_input)
    x = layers.Dropout(dropout_p, name="enc_drop1")(x)
    x = layers.Dense(64, activation="relu", name="enc_dense2")(x)
    x = layers.Dropout(dropout_p, name="enc_drop2")(x)
    latent = layers.Dense(latent_dim, activation="sigmoid", name="latent")(x)
    encoder = keras.Model(encoder_input, latent, name="encoder")

    # ── Decoder ──────────────────────────────────
    decoder_input = keras.Input(shape=(latent_dim,), name="decoder_input")
    x = layers.Dense(64, activation="relu", name="dec_dense1")(decoder_input)
    x = layers.Dense(128, activation="relu", name="dec_dense2")(x)
    recon = layers.Dense(input_dim, activation="sigmoid", name="recon_output")(x)
    decoder = keras.Model(decoder_input, recon, name="decoder")

    # ── Full AE：双输出 ───────────────────────────
    ae_input   = keras.Input(shape=(input_dim,), name="ae_input")
    latent_out = encoder(ae_input)
    recon_out  = decoder(latent_out)

    ae = keras.Model(
        inputs=ae_input,
        outputs=[recon_out, latent_out],
        name="autoencoder_v2"
    )

    return ae, encoder, decoder


ae, encoder, decoder = build_ae_v2(INPUT_DIM, LATENT_DIM, DROPOUT_P)
ae.summary()

# =====================================================
# 编译
# =====================================================
ae.compile(
    optimizer=keras.optimizers.Adam(learning_rate=1e-3),
    loss=["mse", "mse"],
    loss_weights=[1.0, LAMBDA],
)

# =====================================================
# 回调
# =====================================================
callbacks = [
    keras.callbacks.EarlyStopping(
        monitor="val_loss",
        patience=30,
        restore_best_weights=True,
        verbose=1,
    ),
    keras.callbacks.ReduceLROnPlateau(
        monitor="val_loss",
        factor=0.5,
        patience=10,
        min_lr=1e-6,
        verbose=1,
    ),
    keras.callbacks.ModelCheckpoint(
        filepath=f"{OUTPUT_DIR}/ae_v2_best.h5",
        monitor="val_loss",
        save_best_only=True,
        verbose=0,
    ),
]

# =====================================================
# 训练
# =====================================================
history = ae.fit(
    J_train,
    [J_train, params_train],
    validation_data=(
        J_val,
        [J_val, params_val],
    ),
    epochs=1000,
    batch_size=64,
    callbacks=callbacks,
    verbose=1,
)

# =====================================================
# 保存
# =====================================================
ae.save(f"{OUTPUT_DIR}/ae_v2_model.h5")
encoder.save(f"{OUTPUT_DIR}/ae_v2_encoder.h5")

with open(f"{OUTPUT_DIR}/ae_v2_history.pkl", "wb") as f:
    pickle.dump(history.history, f)

print(f"\nModels saved to {OUTPUT_DIR}")

# =====================================================
# 评估：重构误差
# =====================================================
recon_pred, params_pred = ae.predict(J_test, verbose=0)

mse_recon  = np.mean((J_test - recon_pred) ** 2, axis=1)
mse_params = np.mean((params_test - params_pred) ** 2, axis=1)

print(f"\n--- Test Reconstruction ---")
print(f"  MSE mean:   {mse_recon.mean():.6f}")
print(f"  MSE median: {np.median(mse_recon):.6f}")
print(f"  MSE std:    {mse_recon.std():.6f}")

# =====================================================
# 评估：参数估计 Pearson r
# =====================================================
print(f"\n--- Parameter Estimation (Pearson r) ---")
r_values = []
for i, name in enumerate(param_names):
    r, _ = pearsonr(params_test[:, i], params_pred[:, i])
    r_values.append(r)
    print(f"  {name:20s}: r = {r:.4f}")
print(f"  Mean r: {np.mean(r_values):.4f}")

# =====================================================
# 可视化（3×3布局，与AE v1对齐）
# =====================================================
fig, axes = plt.subplots(3, 3, figsize=(15, 12))
fig.suptitle(f"AE v2 (Semi-supervised, λ={LAMBDA}, 9D latent) — Interface Lifetimes", fontsize=12)
axes = axes.flatten()

# 损失曲线
ax = axes[0]
ax.plot(history.history["loss"],     label="Train total", color="#4C72B0")
ax.plot(history.history["val_loss"], label="Val total",   color="#DD8452")
if "recon_output_loss" in history.history:
    ax.plot(history.history["val_recon_output_loss"],
            label="Val recon", color="#4C72B0", linestyle="--", alpha=0.6)
    ax.plot(history.history["val_latent_loss"],
            label="Val param", color="#DD8452", linestyle="--", alpha=0.6)
ax.set_xlabel("Epoch")
ax.set_ylabel("Loss")
ax.set_title("Training History")
ax.legend(fontsize=8)
ax.set_yscale("log")

# 重构效果
V = np.linspace(0, 1.3, 131)
idx_plot = np.random.choice(len(J_test), 5, replace=False)
colors   = plt.cm.tab10(np.linspace(0, 1, 5))
ax = axes[1]
for k, idx in enumerate(idx_plot):
    ax.plot(V, J_test[idx],     color=colors[k], linewidth=1.5)
    ax.plot(V, recon_pred[idx], color=colors[k], linewidth=1.0, linestyle="--")
ax.set_xlabel("Voltage (V)")
ax.set_ylabel("J (normalized)")
ax.set_title("Reconstruction — solid: true, dashed: pred")

# 重构误差分布
ax = axes[2]
ax.hist(mse_recon, bins=50, color="#4C72B0", alpha=0.8)
ax.set_xlabel("Reconstruction MSE")
ax.set_ylabel("Count")
ax.set_title("Reconstruction Error Distribution")

# Pearson r条形图
ax = axes[3]
bar_colors = ["#4C72B0" if r > 0.8 else "#DD8452" for r in r_values]
ax.bar(range(len(param_names)), r_values, color=bar_colors)
ax.set_xticks(range(len(param_names)))
# 短名称：针对新参数优化显示
short_names = []
for n in param_names:
    n_short = n.replace("_pvk", "").replace("_eff", "")
    n_short = n_short.replace("Nc", "Nc").replace("Nv", "Nv")
    # 特别处理 tau_ETL 和 tau_HTL
    n_short = n_short.replace("tau_ETL", "τ_ETL").replace("tau_HTL", "τ_HTL")
    short_names.append(n_short)
ax.set_xticklabels(short_names, rotation=45, ha="right", fontsize=8)
ax.set_ylabel("Pearson r")
ax.set_title("Parameter Estimation Correlation")
ax.axhline(0.8, color="gray", linestyle="--", linewidth=0.8)
ax.set_ylim(-1, 1)

# Scatter: 最好参数
best_idx = int(np.argmax(r_values))
ax = axes[4]
ax.scatter(params_test[:, best_idx], params_pred[:, best_idx],
           alpha=0.3, s=5, color="#4C72B0")
ax.set_xlabel(f"True {param_names[best_idx]}")
ax.set_ylabel("Predicted")
ax.set_title(f"Best: {param_names[best_idx]}\nr={r_values[best_idx]:.4f}")

# Scatter: 最差参数
worst_idx = int(np.argmin(r_values))
ax = axes[5]
ax.scatter(params_test[:, worst_idx], params_pred[:, worst_idx],
           alpha=0.3, s=5, color="#DD8452")
ax.set_xlabel(f"True {param_names[worst_idx]}")
ax.set_ylabel("Predicted")
ax.set_title(f"Worst: {param_names[worst_idx]}\nr={r_values[worst_idx]:.4f}")

# 隐藏多余子图
for i in range(6, 9):
    axes[i].set_visible(False)

plt.tight_layout()
save_path = f"{OUTPUT_DIR}/02b_ae_v2_training.png"
plt.savefig(save_path, dpi=150)
print(f"\nPlot saved: {save_path}")
print("Done. Next step: 03_train_VAE.py")