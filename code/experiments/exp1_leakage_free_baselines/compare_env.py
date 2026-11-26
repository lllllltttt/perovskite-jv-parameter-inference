# -*- coding: utf-8 -*-
"""
Cross-environment consistency: local (TF 2.20/Keras 3) vs server (TF 2.13/Keras 2)
15-run benchmark. Reads results/per_seed_metrics.csv and results_server/
per_seed_metrics.csv; prints and writes CROSS_ENV_COMPARISON.md.

Per-run ALL-mean Pearson r is the primary axis. Also reports per-family mean+/-SD,
per-family systematic bias (server-local), rank-order robustness of the family
hierarchy, and the preprocessing-leakage check per environment (frozen r=0.8069).
"""
import os, sys, csv
import numpy as np

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
LOCAL_CSV = os.path.join(HERE, "results", "per_seed_metrics.csv")
SERVER_CSV = os.path.join(HERE, "results_server", "per_seed_metrics.csv")

MODELS = ["vae", "det_ae", "mlp"]
SEEDS = [20260824, 20260825, 20260826, 20260827, 20260828]
FROZEN_MEAN = 0.8069

OUT = []
def P(*a):
    s = " ".join(str(x) for x in a)
    print(s); OUT.append(s)

def load(csv_path):
    """dict[model][seed] -> ALL-row pearson_r (None if missing)."""
    d = {m: {s: None for s in SEEDS} for m in MODELS}
    if not os.path.exists(csv_path):
        return d, False
    with open(csv_path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["parameter"] == "ALL" and r["model"] in d and int(r["seed"]) in d[r["model"]]:
                d[r["model"]][int(r["seed"])] = float(r["pearson_r"])
    return d, True

loc, ok_local = load(LOCAL_CSV)
srv, ok_server = load(SERVER_CSV)

P("# EXP1 跨环境一致性对比（CROSS-ENVIRONMENT CONSISTENCY）")
P("")
P("本地：TF 2.20.0 / Keras 3.13.2 / numpy 2.0.1（CPU）")
P("服务器：TF 2.13.1 / Keras 2 / numpy 1.x（CPU，无 GPU）；服务器 anchor 检查 PASS 精确复现")
P("冻结稿 mean r 0.8069（verify_frozen_eval_server.py）")
P("")
P("基准：逐 run ALL-mean Pearson r（跨 9 参数的测试集均值）。")
P("")

P("## 逐 run ALL-mean Pearson r")
P("")
P("%-8s %-10s %9s %9s %9s" % ("model", "seed", "local", "server", "server-local"))
for m in MODELS:
    for s in SEEDS:
        l, sv = loc[m][s], srv[m][s]
        if l is None or sv is None:
            dl = "-"
        else:
            dl = "%+.4f" % (sv - l)
        P("%-8s %-10d %9s %9s %9s" % (
            m, s,
            ("%.4f" % l) if l is not None else "(PEND)",
            ("%.4f" % sv) if sv is not None else "(NA)",
            dl))

P("")
P("## 每种子的 Δ 统计（server − local，重叠 run）")
deltas = []
for m in MODELS:
    for s in SEEDS:
        if loc[m][s] is not None and srv[m][s] is not None:
            deltas.append(srv[m][s] - loc[m][s])
if deltas:
    d = np.array(deltas)
    P("重叠 run 数：%d" % len(deltas))
    P("mean(Δ) = %+.4f  sd(Δ) = %.4f  min %+.4f  max %+.4f" %
      (d.mean(), d.std(ddof=1), d.min(), d.max()))
    P("|Δ| ≤ 0.01: %d/%d ; ≤ 0.02: %d/%d" %
      (int((np.abs(d) <= 0.01).sum()), len(d),
       int((np.abs(d) <= 0.02).sum()), len(d)))
P("")

P("## 各 family 5-seed mean ± SD")
P("")
P("%-8s %18s %18s" % ("model", "local", "server"))
fam = {}
for m in MODELS:
    lv = np.array([loc[m][s] for s in SEEDS if loc[m][s] is not None])
    sv = np.array([srv[m][s] for s in SEEDS if srv[m][s] is not None])
    fam[m] = (lv, sv)
    lstr = "%.4f ± %.4f (%d)" % (lv.mean(), lv.std(ddof=1), len(lv)) if len(lv) else "(PEND)"
    sstr = "%.4f ± %.4f (%d)" % (sv.mean(), sv.std(ddof=1), len(sv)) if len(sv) else "(NA)"
    P("%-8s %18s %18s" % (m, lstr, sstr))

P("")
P("## 架构名次（mean r 降序）在两环境的稳健性")
P("")
order_l = [m for m, (lv, _) in sorted(fam.items(), key=lambda kv: -kv[1][0].mean())] \
    if all(len(lv) for lv, _ in fam.values()) else []
order_s = [m for m, (_, sv) in sorted(fam.items(), key=lambda kv: -kv[1][1].mean())]
if order_l:
    P("本地：%s" % " > ".join(order_l))
P("服务器：%s" % " > ".join(order_s))
if order_l and order_l == order_s:
    P("⇒ 名次一致（两环境 family 排序相同）。")
elif order_l:
    P("⇒ 名次不一致（环境相关排序差异）。")

P("")
P("## 预处理泄漏检查（每环境无泄漏 VAE vs 冻结 mean r 0.8069）")
P("")
for name, f in [("本地", fam["vae"][0]), ("服务器", fam["vae"][1])]:
    if len(f):
        dlt = f.mean() - FROZEN_MEAN
        cls = "NEGLIGIBLE" if abs(dlt) < 0.01 else ("SMALL" if abs(dlt) < 0.05 else "MODERATE")
        P("%s：lf-VAE mean %.4f vs frozen %.4f → Δ %+.4f → %s" % (name, f.mean(), FROZEN_MEAN, dlt, cls))

P("")
P("## 解读")
P("")
P("- 若各 family 的 server−local Δ 有系统性同号偏移，属框架差异（Keras 2 vs 3 初始化 RNG、")
P("  采样层随机性、shuffle/oneDNN 动态），不影响同环境内 family 间相对比较。")
P("- 稳健结论的标准：名次一致性 + |Δ| 集中在小范围。")
if not ok_local or not ok_server:
    P("- 注：某一环境的 CSV 未找到（%s / %s），该环境列为占位。" % (ok_local, ok_server))

with open(os.path.join(HERE, "CROSS_ENV_COMPARISON.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(OUT) + "\n")
print("\nwrote", os.path.join(HERE, "CROSS_ENV_COMPARISON.md"))
