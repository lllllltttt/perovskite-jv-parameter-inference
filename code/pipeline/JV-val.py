"""
重新筛选验证样本（9参数版）
================
策略：在物理空间（log尺度）对每个参数单独计算相对误差，
找所有参数误差都控制在阈值内的样本，避免某个参数预测
严重偏离导致COMSOL不收敛。

输出：
  - selected_true_params.csv    真实参数（对照组，必定收敛）
  - selected_pred_params.csv    预测参数（实验组）
  - selection_report.csv        各样本各参数误差详情
"""

import os
import numpy as np
import pandas as pd
import pickle

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

# =====================================================
# 路径配置
# =====================================================
NPZ_PATH        = "/home/student2/result-9D-AE-interface-lifetimes-2/dataset_normalized.npz"
SCALER_PATH     = "/home/student2/result-9D-AE-interface-lifetimes-2/param_scaler.pkl"
ENCODER_PATH    = "/home/student2/result-9D-AE-interface-lifetimes-2/VAE_v6/encoder.h5"
PARAM_HEAD_PATH = "/home/student2/result-9D-AE-interface-lifetimes-2/VAE_v6/param_head.h5"
OUTPUT_DIR      = "/home/student2/result-9D-AE-interface-lifetimes-2/forward_validation2"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# =====================================================
# 9个参数（完整参数集）
# =====================================================
PARAM_NAMES = [
    "mu_n_pvk", "mu_p_pvk",
    "tau_n_pvk", "tau_p_pvk",
    "Nc_eff_pvk", "Nv_eff_pvk",
    "tau_ETL",           # 界面寿命（取代 Nt_ETL_PVK）
    "tau_HTL",           # 界面寿命（取代 Nt_HTL_PVK）
    "rad_c",
]

# =====================================================
# 加载数据
# =====================================================
print("Loading data...")
data = np.load(NPZ_PATH, allow_pickle=True)
J_test          = data["J_test"].astype(np.float32)        # 归一化 J-V
J_test_raw      = data["J_test_raw"].astype(np.float32)    # 原始 J-V (mA/cm²)
params_test_raw = data["params_test_raw"].astype(np.float32)  # 物理单位 (N, 9)

print(f"Test set: {J_test.shape[0]} samples, {params_test_raw.shape[1]} params")

# =====================================================
# 加载scaler
# =====================================================
with open(SCALER_PATH, "rb") as f:
    scaler_dict = pickle.load(f)
param_scaler       = scaler_dict["scaler"]
log_transform_mask = scaler_dict["log_mask"]

def inverse_transform_params(params_scaled):
    params_transformed = param_scaler.inverse_transform(params_scaled)
    result = params_transformed.copy()
    result[:, log_transform_mask] = 10 ** params_transformed[:, log_transform_mask]
    return result

# =====================================================
# 加载模型
# =====================================================
print("Loading models...")

class Sampling(layers.Layer):
    def call(self, inputs):
        z_mean, z_log_var = inputs
        epsilon = tf.random.normal(shape=tf.shape(z_mean))
        return z_mean + tf.exp(0.5 * z_log_var) * epsilon

encoder    = keras.models.load_model(ENCODER_PATH,
                custom_objects={"Sampling": Sampling})
param_head = keras.models.load_model(PARAM_HEAD_PATH)

# =====================================================
# VAE推理
# =====================================================
print("Running VAE inference...")
z_mean, _, _ = encoder.predict(J_test, verbose=0)
param_head_outputs = param_head.predict(z_mean, verbose=0)
params_pred_scaled = param_head_outputs[0]   # 取均值 (N, 9)
params_pred_physical = inverse_transform_params(params_pred_scaled)

# params_test_raw全部9列
params_true_physical = params_test_raw[:, :len(PARAM_NAMES)]

# =====================================================
# 在log空间计算各参数相对误差
# =====================================================
eps = 1e-30
log_true = np.log10(np.abs(params_true_physical) + eps)
log_pred = np.log10(np.abs(params_pred_physical) + eps)
log_err  = np.abs(log_pred - log_true)   # (N, 9)

print("\n--- Log-space error statistics per parameter ---")
for i, name in enumerate(PARAM_NAMES):
    print(f"  {name:<16}: mean={log_err[:,i].mean():.3f}  "
          f"median={np.median(log_err[:,i]):.3f}  "
          f"max={log_err[:,i].max():.3f}")

# =====================================================
# 筛选：所有参数log误差 < threshold
# =====================================================
chosen_threshold = None
for threshold in [0.1, 0.15, 0.2, 0.3, 0.5]:
    mask = np.all(log_err < threshold, axis=1)
    n_pass = mask.sum()
    print(f"\nThreshold log_err < {threshold}: {n_pass} samples pass "
          f"({100*n_pass/len(mask):.1f}%)")
    if n_pass >= 20:
        chosen_threshold = threshold
        break

if chosen_threshold is None:
    chosen_threshold = 0.5
    mask = np.all(log_err < chosen_threshold, axis=1)
    print(f"\n[WARNING] Using fallback threshold = {chosen_threshold}")

print(f"\nUsing threshold = {chosen_threshold}")
candidate_idx = np.where(mask)[0]

# =====================================================
# 从候选里按总log误差排序，挑最好的5条
# =====================================================
total_log_err = log_err[candidate_idx].sum(axis=1)
sorted_within = np.argsort(total_log_err)

# 按Jsc分档覆盖不同性能水平
jsc_candidates = J_test_raw[candidate_idx, 0]   # V=0 处电流
jsc_sorted_idx = np.argsort(jsc_candidates)

n_cand = len(candidate_idx)
picks = []
# 最好误差的2条
picks.extend(sorted_within[:2].tolist())
# 低Jsc区1条（前1/3）
low_pool = [x for x in jsc_sorted_idx[:max(1, n_cand//3)] if x not in picks]
if low_pool:
    picks.append(low_pool[0])
# 高Jsc区1条（后1/3）
high_pool = [x for x in jsc_sorted_idx[2*n_cand//3:] if x not in picks]
if high_pool:
    picks.append(high_pool[0])
# 再补1条中间的
mid_pool = [x for x in sorted_within[2:10] if x not in picks]
if mid_pool:
    picks.append(mid_pool[0])

picks = picks[:5]
selected_in_candidate = np.array(picks)
selected_idx = candidate_idx[selected_in_candidate]

print(f"\nSelected {len(selected_idx)} samples: {selected_idx}")

# =====================================================
# 打印误差报告
# =====================================================
print("\n--- Error report for selected samples ---")
for idx in selected_idx:
    print(f"\n  [Sample {idx}]")
    print(f"  {'Parameter':<16} {'True':>14} {'Pred':>14} "
          f"{'LogErr':>8} {'RelErr%':>8}")
    print(f"  {'-'*68}")
    for j, name in enumerate(PARAM_NAMES):
        tv = params_true_physical[idx, j]
        pv = params_pred_physical[idx, j]
        le = log_err[idx, j]
        re = abs(tv - pv) / (abs(tv) + eps) * 100
        print(f"  {name:<16} {tv:>14.4e} {pv:>14.4e} {le:>8.3f} {re:>8.1f}%")

# =====================================================
# 输出CSV（9个参数，无固定Nt列）
# =====================================================
def make_csv(params_physical, idx_list, label):
    rows = []
    for rank, idx in enumerate(idx_list):
        row = {"sample_id": int(idx), "group": label}
        for j, name in enumerate(PARAM_NAMES):
            row[name] = params_physical[idx, j]
        rows.append(row)
    return pd.DataFrame(rows)

df_true = make_csv(params_true_physical, selected_idx, "true")
df_pred = make_csv(params_pred_physical, selected_idx, "pred")

true_csv = f"{OUTPUT_DIR}/selected_true_params.csv"
pred_csv = f"{OUTPUT_DIR}/selected_pred_params.csv"
df_true.to_csv(true_csv, index=False)
df_pred.to_csv(pred_csv, index=False)
print(f"\nSaved: {true_csv}")
print(f"Saved: {pred_csv}")

# =====================================================
# 误差汇总表
# =====================================================
report_rows = []
for idx in selected_idx:
    for j, name in enumerate(PARAM_NAMES):
        tv = params_true_physical[idx, j]
        pv = params_pred_physical[idx, j]
        report_rows.append({
            "sample_id": int(idx),
            "parameter": name,
            "true_value": tv,
            "pred_value": pv,
            "log_error":  log_err[idx, j],
            "rel_error_%": abs(tv-pv)/(abs(tv)+eps)*100,
        })

df_report = pd.DataFrame(report_rows)
report_csv = f"{OUTPUT_DIR}/selection_report.csv"
df_report.to_csv(report_csv, index=False)
print(f"Saved: {report_csv}")

# =====================================================
# 保存npz供后续画图
# =====================================================
np.savez(
    f"{OUTPUT_DIR}/selected_samples.npz",
    selected_idx      = selected_idx,
    J_raw_selected    = J_test_raw[selected_idx],
    params_true_phys  = params_true_physical[selected_idx],
    params_pred_phys  = params_pred_physical[selected_idx],
    log_err_selected  = log_err[selected_idx],
)
print(f"Saved: {OUTPUT_DIR}/selected_samples.npz")
print("\nDone. Next: run COMSOL with both CSV files.")