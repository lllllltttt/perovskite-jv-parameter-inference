# EXP1 服务器运行说明 (SERVER PACKAGE)

此包是实验 1（无泄漏多种子基线基准）在服务器上并行运行的独立副本。
**本地 15 轮与服务器 15 轮互不干扰**：本包不含本地 `models/`、`results/`、`pilot/`，
服务器跑出的结果写在服务器本目录下，两者各是一套完整 15 轮。

## 1. 环境要求
- Python 3.10+；`tensorflow`（含 Keras 3；若服务器是 TF 2.x 老 Keras，先跑第 4 步冒烟）
- `numpy`, `scipy`, `scikit-learn`；`matplotlib`（仅画图需要）

检查：
```bash
python -c "import tensorflow as tf, keras; print('tf', tf.__version__, 'keras', keras.__version__); print('gpu', [d.name for d in tf.config.list_physical_devices('GPU')])"
```

## 2. 解压
```bash
unzip exp1_server_package.zip
cd exp1_server_package
```

## 3. （推荐）先验证冻结基线能在本环境复现
```bash
python verify_frozen_eval_server.py
# 然后核对：cat phase0_frozen_eval_repro_server.txt
#   mean r 应 ≈ 0.8069；95% coverage 0.9464–0.9692；mean Spearman ≈ 0.4283
# 若偏差明显（>1e-3），说明环境/精度与冻结稿不一致，先排查再跑主基准。
```

## 4. 主基准（15 轮，约 1–4 小时 GPU）
```bash
python run_benchmark.py
```
- 顺序：vae×5种子 → det_ae×5 → mlp×5（种子 20260824–20260828）
- 断点续跑：每个 run 完成后写 `models/<family>/seed<seed>/DONE`，中断后重跑会自动跳过已完成的
- 日志：`benchmark_progress.log`；失败：`models/<family>/seed<seed>/FAILED`
- 结果：`results/per_seed_metrics.csv`（45 行参数 + 15 行 ALL）

## 5. （可选）生成汇总表与图
```bash
python summarize_results.py     # -> results/multiseed_summary.csv, model_level_summary.csv
python analyze_exp1.py          # -> results/PQ_analysis.md（Phase P/Q 判定）
python make_figures.py          # -> figures/EXP1_FigA–F.png
```

## 6. 老环境冒烟测试（Keras 2 或不确定时）
```bash
EXP1_MAX_EPOCHS=2 python train_one.py vae 20260824 smoke_test
```
能正常出 `smoke_test/eval_bundle.npz` 即可（Windows PowerShell 用
`$env:EXP1_MAX_EPOCHS=2; python ...`）。

## 7. numpy 版本兼容（重要）
`train_only_scalers.pkl` 是本地 numpy 2.0 写的（pickle 引用 `numpy._core`），在
numpy 1.x 环境 `pickle.load` 会报 `ModuleNotFoundError: No module named 'numpy._core'`。
已修复：本包新增 **`train_only_scalers.npz`**（纯数组、版本无关），`exp1_lib.load_scalers()`
会优先读 npz。**确认服务器上有 `train_only_scalers.npz` 且 `exp1_lib.py` 是最新版**
（含 `os.path.exists(npz_path)` 分支）即可，pkl 只是留档。
若你在旧包上直接覆盖这两个文件，同样生效。

## 8. 与本地对比
跑完后把服务器 `results/per_seed_metrics.csv`（和可选的
`phase0_frozen_eval_repro_server.txt`）取回，交给本地会话做环境一致性对比。
**预期**：两套数字有小幅数值差异（不同硬件/线程/浮点归约顺序），属正常；
对比的是多种子均值±SD 与分层结构是否一致，不要求逐位相同。
**注意**：不要在同一套 15 轮里混用两环境（每个种子只在单一环境跑一遍）。

---
本地参考：本地 TF-CPU 15 轮约 12–19 h（每轮 ~70–78 min）；服务器若 TF-GPU 快得多。
