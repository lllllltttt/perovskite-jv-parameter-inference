# v4 T2 · 复刻偏差记录（protocol.md §2/§7 要求的显式记录）

冻结 `script/VAE-v6.py` 以 Keras 2 / 未知 TF 版本运行；本机为 TF 2.21.0 / Keras 3.14.1（CPU-only）。
逐条记录为**语义等价**的适配或必要差异，未改结构/损失/超参：

| # | 冻结（Keras 2） | 本机（Keras 3） | 性质 |
|---|---|---|---|
| D1 | `EarlyStopping(monitor="val_param_loss", patience=50, restore_best_weights=True)`：Keras 2 对未知自定义指标默认 mode='min' | Keras 3 无法推断自定义 `val_param_loss` 方向 → 显式 `mode="min"` | 语义等价（必要适配） |
| D2 | 训练数据 `Dataset.shuffle(len(train))` 无 seed → 历史批次序不可复现 | T2 两分支共用**同一固定置换**（`default_rng(20260823).permutation(n_train)`，无再 shuffle）→ 批次序确定且 L=T 相同 | 必要差异（v4 §4；历史序不可逐位复现，已报告） |
| D3 | 初始权重全局随机 | 构建前 `tf.random.set_seed(20260823)`+`np.random.seed`，L 与 T 初始权重相同 | 附加控制（不改变规则） |
| D4 | 子模型存 .h5 | Keras 3 存 `.keras`（本 T2 自产，自评估自读，不影响与冻结比较） | 格式适配 |
| D6 | `ModelCheckpoint(best.weights.h5, monitor='val_loss', save_best_only=True)` | 省略：冻结的 best.weights.h5 官方推理从不加载（T0 P6）；本 protocol 预固定评估规则 = EarlyStopping(restore_best_weights=True, val_param_loss) 恢复态；Keras 3 无法对未 build 的自定义子类模型 save_weights_only | 语义等价（必要适配） |
| D5 | — | oneDNN CPU 浮点重排可能引入极小不确定（不同计算顺序） | 环境注明，不追逐位 |

冻结历史参考：688 epochs、val_loss argmin≈637、val_param_loss argmin≈637（history.pkl）。
本 protocol 的 A（Historical→L）包含 D1–D5 的叠加与“固定种子重训”随机性，不解读为逐位复现。
