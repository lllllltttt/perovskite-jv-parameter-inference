# EXP1 跨环境一致性对比（CROSS-ENVIRONMENT CONSISTENCY）

本地：TF 2.20.0 / Keras 3.13.2 / numpy 2.0.1（CPU）
服务器：TF 2.13.1 / Keras 2 / numpy 1.x（CPU，无 GPU）；服务器 anchor 检查 PASS 精确复现
冻结稿 mean r 0.8069（verify_frozen_eval_server.py）

基准：逐 run ALL-mean Pearson r（跨 9 参数的测试集均值）。

## 逐 run ALL-mean Pearson r

model    seed           local    server server-local
vae      20260824      0.7823    0.7966   +0.0143
vae      20260825      0.7900    0.8025   +0.0125
vae      20260826      0.7977    0.8105   +0.0129
vae      20260827      0.8090    0.8137   +0.0047
vae      20260828      0.7979    0.8049   +0.0070
det_ae   20260824      0.8098    0.7988   -0.0110
det_ae   20260825      0.8093    0.8060   -0.0033
det_ae   20260826      0.8147    0.8065   -0.0081
det_ae   20260827      0.8238    0.8073   -0.0165
det_ae   20260828      0.8067    0.8085   +0.0018
mlp      20260824      0.7810    0.7850   +0.0040
mlp      20260825      0.7860    0.7974   +0.0113
mlp      20260826      0.7822    0.7836   +0.0014
mlp      20260827      0.7998    0.8002   +0.0003
mlp      20260828      0.7977    0.8013   +0.0036

## 每种子的 Δ 统计（server − local，重叠 run）
重叠 run 数：15
mean(Δ) = +0.0023  sd(Δ) = 0.0091  min -0.0165  max +0.0143
|Δ| ≤ 0.01: 9/15 ; ≤ 0.02: 15/15

## 各 family 5-seed mean ± SD

model                 local             server
vae      0.7954 ± 0.0100 (5) 0.8056 ± 0.0067 (5)
det_ae   0.8128 ± 0.0068 (5) 0.8054 ± 0.0038 (5)
mlp      0.7894 ± 0.0088 (5) 0.7935 ± 0.0085 (5)

## 架构名次（mean r 降序）在两环境的稳健性

本地：det_ae > vae > mlp
服务器：vae > det_ae > mlp
⇒ 名次不一致（环境相关排序差异）。

## 预处理泄漏检查（每环境无泄漏 VAE vs 冻结 mean r 0.8069）

本地：lf-VAE mean 0.7954 vs frozen 0.8069 → Δ -0.0115 → SMALL
服务器：lf-VAE mean 0.8056 vs frozen 0.8069 → Δ -0.0013 → NEGLIGIBLE

## 解读

- 若各 family 的 server−local Δ 有系统性同号偏移，属框架差异（Keras 2 vs 3 初始化 RNG、
  采样层随机性、shuffle/oneDNN 动态），不影响同环境内 family 间相对比较。
- 稳健结论的标准：名次一致性 + |Δ| 集中在小范围。
