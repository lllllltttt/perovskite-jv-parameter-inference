"""
三模型 R² 对比图（自动适配 AE 和 VAE+param_head）
修正 param_head 输出为列表的处理，并打印诊断信息
"""

import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import os
from scipy.stats import pearsonr

# =====================================================
# 1. Sampling 层
# =====================================================
class Sampling(layers.Layer):
    def call(self, inputs):
        z_mean, z_log_var = inputs
        eps = tf.random.normal(shape=tf.shape(z_mean))
        return z_mean + tf.exp(0.5 * z_log_var) * eps

# =====================================================
# 2. 路径配置（请根据实际修改）
# =====================================================
DATA_PATH = "/home/student2/result-9D-AE-interface-lifetimes-2/dataset_normalized.npz"

MODEL_CONFIGS = {
    "AE_v1": {
        "encoder_path": "/home/student2/result-9D-AE-interface-lifetimes-2/AE-v1/ae_v1_encoder.h5",
        "head_path": None,
        "is_vae": False,
        "label": "AE v1 (Unsupervised)",
        "color": "#A8C8E8"
    },
    "AE_v2": {
        "encoder_path": "/home/student2/result-9D-AE-interface-lifetimes-2/AE-v2/ae_v2_encoder.h5",
        "head_path": None,
        "is_vae": False,
        "label": "AE v2 (Semi-supervised)",
        "color": "#4C72B0"
    },
    "VAE_v6": {
        "encoder_path": "/home/student2/result-9D-AE-interface-lifetimes-2/VAE_v6/encoder.h5",
        "head_path": "/home/student2/result-9D-AE-interface-lifetimes-2/VAE_v6/param_head.h5",
        "is_vae": True,
        "label": "VAE v4b (Probabilistic)",
        "color": "#C44E52"
    }
}

OUTPUT_DIR = "/home/student2/result-9D-AE-interface-lifetimes-2/compare"

# =====================================================
# 3. 加载测试数据
# =====================================================
data = np.load(DATA_PATH, allow_pickle=True)
J_test = data["J_test"].astype(np.float32)
params_test = data["params_test"].astype(np.float32)

print(f"测试集样本数: {J_test.shape[0]}")
print(f"真实参数均值: {params_test.mean(axis=0)}")
print(f"真实参数方差: {params_test.var(axis=0)}")

# =====================================================
# 4. 预测函数（处理 param_head 输出为列表的情况）
# =====================================================
def predict_params(config, J_test):
    try:
        encoder = keras.models.load_model(
            config["encoder_path"],
            custom_objects={"Sampling": Sampling}
        )
        # 先预测一小批判断输出结构
        test_out = encoder.predict(J_test[:5], verbose=0)

        if isinstance(test_out, list) and len(test_out) >= 3:
            # VAE 模式
            print(f"    检测到 VAE 架构")
            if config["head_path"] is None:
                raise ValueError(f" {config['label']} 是 VAE 但未提供 param_head 路径！")
            head = keras.models.load_model(config["head_path"])
            # 对整个测试集预测
            z_mean_full, _, _ = encoder.predict(J_test, verbose=0)
            head_out = head.predict(z_mean_full, verbose=0)
            # 若 head 输出为列表，取第一个元素（均值）
            if isinstance(head_out, list):
                param_mu = head_out[0]
            else:
                param_mu = head_out
            return param_mu
        else:
            # AE 模式：直接输出参数
            print(f"    检测到 AE 架构")
            full_out = encoder.predict(J_test, verbose=0)
            if isinstance(full_out, list):
                param_mu = full_out[0]
            else:
                param_mu = full_out
            if param_mu.shape[-1] == 9:
                return param_mu
            else:
                raise ValueError(f"输出维度 {param_mu.shape[-1]} 不是 9！")
    except Exception as e:
        print(f" 加载或预测失败: {config['encoder_path']}")
        print(f"   错误: {e}")
        return None

# =====================================================
# 5. 获取三个模型的预测
# =====================================================
print("\n===== 加载模型并预测 =====")
preds = {}
for key, config in MODEL_CONFIGS.items():
    print(f"正在加载 {key} ...")
    pred = predict_params(config, J_test)
    if pred is not None:
        preds[key] = pred
        print(f"    {key} 预测完成，形状: {pred.shape}, 均值: {pred.mean():.4f}, 方差: {pred.var():.4f}")
    else:
        raise RuntimeError(f" {key} 加载失败！")

# =====================================================
# 6. 计算 R² 和 Pearson r（便于诊断）
# =====================================================
def compute_r2(y_true, y_pred):
    tss = np.sum((y_true - y_true.mean(axis=0)) ** 2, axis=0)
    rss = np.sum((y_true - y_pred) ** 2, axis=0)
    return np.where(tss > 1e-12, 1 - rss / tss, 0.0)

param_names = ["mu_n", "mu_p", "tau_n", "tau_p", "Nc", "Nv", "tau_ETL", "tau_HTL", "rad_c"]

r2_dict = {}
pearson_dict = {}
for key, pred in preds.items():
    r2_dict[key] = compute_r2(params_test, pred)
    pearson_dict[key] = [pearsonr(params_test[:, i], pred[:, i])[0] for i in range(9)]

print("\n===== R² Scores =====")
print(f"{'Param':<10} {'AE_v1':>10} {'AE_v2':>10} {'VAE_v6':>10}")
print("-" * 42)
for i, name in enumerate(param_names):
    print(f"{name:<10} {r2_dict['AE_v1'][i]:>10.4f} {r2_dict['AE_v2'][i]:>10.4f} {r2_dict['VAE_v6'][i]:>10.4f}")

print("\n===== Pearson r (诊断) =====")
print(f"{'Param':<10} {'AE_v1':>10} {'AE_v2':>10} {'VAE_v6':>10}")
print("-" * 42)
for i, name in enumerate(param_names):
    print(f"{name:<10} {pearson_dict['AE_v1'][i]:>10.4f} {pearson_dict['AE_v2'][i]:>10.4f} {pearson_dict['VAE_v6'][i]:>10.4f}")

print(f"\nMean R²: AE_v1 = {np.mean(r2_dict['AE_v1']):.4f}, "
      f"AE_v2 = {np.mean(r2_dict['AE_v2']):.4f}, "
      f"VAE_v6 = {np.mean(r2_dict['VAE_v6']):.4f}")

# =====================================================
# 7. 绘图（与原 Pearson 图风格一致）
# =====================================================
x = np.arange(len(param_names))
width = 0.26

fig, ax = plt.subplots(figsize=(13, 6))

r2_list = [r2_dict["AE_v1"], r2_dict["AE_v2"], r2_dict["VAE_v6"]]
labels = [MODEL_CONFIGS["AE_v1"]["label"], MODEL_CONFIGS["AE_v2"]["label"], MODEL_CONFIGS["VAE_v6"]["label"]]
colors = [MODEL_CONFIGS["AE_v1"]["color"], MODEL_CONFIGS["AE_v2"]["color"], MODEL_CONFIGS["VAE_v6"]["color"]]

bars1 = ax.bar(x - width, r2_list[0], width, label=labels[0], color=colors[0], edgecolor="white", linewidth=0.5)
bars2 = ax.bar(x,         r2_list[1], width, label=labels[1], color=colors[1], edgecolor="white", linewidth=0.5)
bars3 = ax.bar(x + width, r2_list[2], width, label=labels[2], color=colors[2], edgecolor="white", linewidth=0.5)

ax.axhline(0.8, color="gray", linestyle="--", linewidth=1.0, alpha=0.7, label="R² = 0.8 threshold")
ax.axhline(0.0, color="black", linestyle="-", linewidth=0.5, alpha=0.4)
ax.axvline(5.5, color="gray", linestyle=":", linewidth=1.2, alpha=0.6)
ax.text(5.6, 0.92, "Low identifiability", fontsize=8.5, color="gray", style="italic")
ax.text(-0.5, 0.92, "High identifiability", fontsize=8.5, color="gray", style="italic")

# 数值标注（只标 VAE）
for bar in bars3:
    h = bar.get_height()
    if abs(h) > 0.01:
        ax.text(bar.get_x() + bar.get_width()/2, h + (0.02 if h>=0 else -0.05),
                f"{h:.2f}", ha="center", va="bottom" if h>=0 else "top",
                fontsize=7, color="#C44E52")

ax.set_xticks(x)
ax.set_xticklabels(param_names, fontsize=10)
ax.set_ylabel("R² Score", fontsize=11)
ax.set_title("Parameter Estimation Performance (R²): AE v1 → AE v2 → VAE v6\n"
             "(9-parameter dataset, p-i-n PSC, single steady-state J–V input)", fontsize=11)
ax.set_ylim(-0.5, 1.1)   # 允许显示负值
ax.legend(loc="upper right", fontsize=9, framealpha=0.9)

mean_v1, mean_v2, mean_vae = np.mean(r2_list[0]), np.mean(r2_list[1]), np.mean(r2_list[2])
mean_text = f"Mean R²:  AE v1={mean_v1:.3f}  |  AE v2={mean_v2:.3f}  |  VAE={mean_vae:.3f}"
ax.text(0.01, 0.02, mean_text, transform=ax.transAxes, fontsize=8.5, color="dimgray",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7))

ax.axvspan(-0.5, 5.5, alpha=0.03, color="blue")
ax.axvspan(5.5, 8.5, alpha=0.03, color="red")

plt.tight_layout()
os.makedirs(OUTPUT_DIR, exist_ok=True)
save_path = f"{OUTPUT_DIR}/fig_model_comparison_r2.png"
plt.savefig(save_path, dpi=150, bbox_inches="tight")
print(f"\n 图片已保存: {save_path}")
plt.show()