import os
import numpy as np
import pandas as pd
from scipy.io import loadmat
from tqdm import tqdm

# =====================================================
# 路径配置（请根据实际情况调整）
# =====================================================
MAT_DIR    = r"/home/student2/result-9D-interface-lifetimes-2"   # ← 改为新结果目录
OUTPUT_CSV = r"/home/student2/result-csv/JV_database_9D_interface_lifetimes-2.csv"  # ← 新文件名

# =====================================================
# 扫描 MAT 文件
# =====================================================
files = sorted([f for f in os.listdir(MAT_DIR) if f.endswith(".mat")])
print(f"MAT files found: {len(files)}")

# =====================================================
# 列名定义（更新为界面寿命版本）
# =====================================================
param_cols = [
    "Sample_ID",
    "mu_n_pvk",
    "mu_p_pvk",
    "tau_n_pvk",
    "tau_p_pvk",
    "Nc_eff_pvk",
    "Nv_eff_pvk",
    "tau_ETL",        # 替换 Nt_ETL_PVK
    "tau_HTL",        # 替换 Nt_HTL_PVK
    "rad_c",
]
J_cols   = [f"J_{i:03d}" for i in range(131)]
columns  = param_cols + J_cols

# =====================================================
# 读取所有 MAT 文件
# =====================================================
rows        = []
load_errors = []

for file in tqdm(files, desc="Loading MAT"):
    path = os.path.join(MAT_DIR, file)
    try:
        d = loadmat(path)

        # ── 参数（注意字段名与保存时一致） ──────────
        row = [
            int(np.squeeze(d["Index"])),
            float(np.squeeze(d["mu_n_pvk"])),
            float(np.squeeze(d["mu_p_pvk"])),
            float(np.squeeze(d["tau_n_pvk"])),
            float(np.squeeze(d["tau_p_pvk"])),
            float(np.squeeze(d["Nc_eff_pvk"])),
            float(np.squeeze(d["Nv_eff_pvk"])),
            float(np.squeeze(d["tau_ETL"])),       # 新字段
            float(np.squeeze(d["tau_HTL"])),       # 新字段
            float(np.squeeze(d["rad_c"])),
        ]

        # ── J-V 曲线：A/m² → mA/cm²（×0.1） ─────────
        J = np.squeeze(d["J"]) * 0.1
        assert len(J) == 131, f"J length {len(J)} != 131"
        row.extend(J.tolist())
        rows.append(row)

    except Exception as e:
        load_errors.append((file, str(e)))

if load_errors:
    print(f"\n[WARNING] {len(load_errors)} files failed to load:")
    for f, err in load_errors:
        print(f"  {f}: {err}")

# =====================================================
# 构建 DataFrame
# =====================================================
df = pd.DataFrame(rows, columns=columns)
df = df.sort_values("Sample_ID").reset_index(drop=True)
print(f"\nLoaded:  {len(df)} samples")

# =====================================================
# 物理合理性过滤
#   1. J_sc > 0        （第一点，短路端）
#   2. J_oc < 0        （最后一点，开路端附近）
#   3. 无异常大值       （通过后续判断，未显式过滤）
#   4. 单调递减         （稳态 J-V 的强约束，允许小幅上升≤0.2 mA/cm²）
# =====================================================
J_vals = df[J_cols].values

mask_jsc      = J_vals[:, 0]  >  0
# mask_joc      = J_vals[:, -1] <  0
# Voc是否存在于扫描范围内
sign_change = np.diff(np.sign(J_vals), axis=1)

mask_has_voc = (sign_change < 0).any(axis=1)
mask_valid    = np.all(np.isfinite(J_vals), axis=1)
mask_monotone = np.all(np.diff(J_vals, axis=1) <= 0.2, axis=1)  # 差分≤0.2容忍数值噪声
mask = mask_jsc & mask_has_voc & mask_valid & mask_monotone

df_clean = df[mask].reset_index(drop=True)

n_removed = len(df) - len(df_clean)
print(f"Physical filter: {len(df)} → {len(df_clean)} (removed {n_removed})")
print(f"  J_sc > 0   rejected: {(~mask_jsc).sum()}")
print(f"  J_oc < 0   rejected: {(~mask_has_voc).sum()}")
print(f"  NaN/Inf    rejected: {(~mask_valid).sum()}")
print(f"  monotone   rejected: {(~mask_monotone).sum()}")

# =====================================================
# 保存
# =====================================================
df_clean.to_csv(OUTPUT_CSV, index=False)
print(f"\nSaved: {OUTPUT_CSV}")
print(f"Shape: {df_clean.shape}")