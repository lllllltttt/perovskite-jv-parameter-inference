"""
J-V collision / inverse-ambiguity analysis (VAE v6 project, test set only).

Question: under the predefined COMSOL drift-diffusion domain and the physically
constrained LHS sampling prior, do near-identical J-V curves exist that correspond
to clearly different parameter combinations?

Constraints honored:
  * no training            * no COMSOL
  * no modification of npz * no overwrite of existing artifacts (new dir)

Outputs (collision_analysis/):
  nearest_neighbor_pairs.csv   all deduplicated nearest-neighbor pairs
  top_collision_pairs.csv      high-scoring collision pairs + representative cases
  parameter_ambiguity_summary.csv  per-param abs diff by J-distance tier
  collision_summary.txt        narrative statistics
  collision_analysis.png       2x2 publication-style figure

Primary metric: RMSE J-V distance in normalized space; parameter distance is
RMSE over the 9 normalized log-parameters.
"""
import os
import numpy as np
import pandas as pd
import scipy.stats as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA = r"E:\project\work1\data\dataset_normalized.npz"
OUT = r"E:\project\work1\collision_analysis"
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- load
d = np.load(DATA, allow_pickle=True)
names = [str(x) for x in d["param_names"]]
J_test  = d["J_test"].astype(np.float64)        # (N,131) normalized
P_test  = d["params_test"].astype(np.float64)   # (N,9)   normalized log space
J_raw   = d["J_test_raw"].astype(np.float64)    # raw J (mA/cm2) for plotting
V       = np.linspace(0.0, 1.3, J_test.shape[1])

N, JD = J_test.shape
ND = P_test.shape[1]
assert ND == 9
print(f"[data] test set: N={N}, J-dim={JD}, param-dim={ND}")

# ---------------------------------------------------------------- NN search (chunked brute force, Euclidean in normalized J space)
q2 = np.einsum("ij,ij->i", J_test, J_test)
CH = 1024
nn_idx = np.empty(N, dtype=np.int64)
nn_d2  = np.empty(N)
for s in range(0, N, CH):
    e = min(s + CH, N)
    q = J_test[s:e]
    d2 = q2[s:e, None] + q2[None, :] - 2.0 * (q @ J_test.T)   # (e-s, N)
    # exclude self: for query k (absolute index s+k), zero out column s+k
    d2[np.arange(e - s), np.arange(s, e)] = np.inf
    idx = np.argmin(d2, axis=1)
    nn_idx[s:e] = idx
    nn_d2[s:e] = d2[np.arange(e - s), idx]

dJ_full  = np.sqrt(nn_d2 / JD)                        # RMSE over 131 points
dTh_full = np.sqrt(np.mean((P_test - P_test[nn_idx]) ** 2, axis=1))
absd_full = np.abs(P_test - P_test[nn_idx])           # (N,9)

# ---- deduplicate (i,j) / (j,i): keep i < nn_idx[i] ----
keep = np.arange(N) < nn_idx
I, Jn = np.arange(N)[keep], nn_idx[keep]
dJ, dTh = dJ_full[keep], dTh_full[keep]
A = absd_full[keep]
M = len(I)
print(f"[nn] deduplicated nearest-neighbor pairs: {M}")

# ---- random-pair baselines (parameter space) for context ----
rng = np.random.default_rng(42)
n_rand = 200000
ra, rb = rng.integers(0, N, n_rand), rng.integers(0, N, n_rand)
ok = ra != rb
rd = np.sqrt(np.mean((P_test[ra[ok]] - P_test[rb[ok]]) ** 2, axis=1))
# random-pair J distance (full) for context (dJ is trivially minimized by NN)
rj = np.sqrt(np.mean((J_test[ra[ok]] - J_test[rb[ok]]) ** 2, axis=1))

# ---------------------------------------------------------------- percentiles / collision score
def pct(x, v):
    return float(st.percentileofscore(x, v)) / 100.0

dJ_p  = np.array([pct(dJ, v) for v in dJ])
dTh_p = np.array([pct(dTh, v) for v in dTh])
coll = dTh / (dJ + 1e-9)

rho_sp, p_sp = st.spearmanr(dJ, dTh)
r_pe, p_pe = st.pearsonr(dJ, dTh)

print("\n[stats] nearest-neighbor d_J (normalized RMSE):")
print(pd.Series(dJ).describe(percentiles=[.25,.5,.75,.9,.99]).round(5).to_string())
print("\n[stats] corresponding d_theta (normalized RMSE over 9 params):")
print(pd.Series(dTh).describe(percentiles=[.25,.5,.75,.9,.99]).round(4).to_string())
print(f"\n[stats] Spearman(dJ, dTheta) = {rho_sp:.4f} (p={p_sp:.3e})")
print(f"[stats] Pearson (dJ, dTheta)  = {r_pe:.4f} (p={p_pe:.3e})")
print(f"[stats] random-pair dTheta  median={np.median(rd):.4f} mean={rd.mean():.4f}")
print(f"[stats] NN-pair dTheta      median={np.median(dTh):.4f} mean={dTh.mean():.4f}")
print(f"[stats] random-pair dJ      median={np.median(rj):.4f} mean={rj.mean():.4f}")
print(f"[stats] NN-pair dJ          median={np.median(dJ):.4f} mean={dJ.mean():.4f}")

# ---------------------------------------------------------------- tiers (closest by dJ)
tier_defs = {"closest 1%": 0.01, "closest 0.5%": 0.005, "closest 0.1%": 0.001}
order = np.argsort(dJ, kind="stable")
tier_stats = {}
for tname, frac in tier_defs.items():
    k = max(1, int(round(M * frac)))
    sel = order[:k]
    subA = A[sel]
    rows = []
    for p in range(ND):
        rows.append({
            "tier": tname, "n_pairs": k,
            "parameter": names[p],
            "median_abs_diff": float(np.median(subA[:, p])),
            "mean_abs_diff": float(subA[:, p].mean()),
            "p90_abs_diff": float(np.percentile(subA[:, p], 90)),
            "max_abs_diff": float(subA[:, p].max()),
        })
    rows.append({
        "tier": tname, "n_pairs": k, "parameter": "dTheta",
        "median_abs_diff": float(np.median(dTh[sel])),
        "mean_abs_diff": float(dTh[sel].mean()),
        "p90_abs_diff": float(np.percentile(dTh[sel], 90)),
        "max_abs_diff": float(dTh[sel].max()),
    })
    tier_stats[tname] = pd.DataFrame(rows)
    # ranking per tier
    med = [float(np.median(subA[:, p])) for p in range(ND)]
    rnk = sorted(range(ND), key=lambda p: -med[p])
    print(f"\n[tier {tname}] k={k}  median dTheta={np.median(dTh[sel]):.4f}")
    print("   ambiguity ranking (param: median |diff|):")
    for p in rnk:
        print(f"     {names[p]:<10} {med[p]:.4f}")

# ---------------------------------------------------------------- compensation directions (closest 1%)
k1 = max(1, int(round(M * 0.01)))
sel = order[:k1]
def sign_frac(a, b, mask):
    da = A[mask, names.index(a)]
    db = A[mask, names.index(b)]
    # sign of difference, need signed diff not abs
    return da, db
signed = (P_test[I] - P_test[Jn])   # (M,9) signed differences
def same_sign(a, b):
    ia, ib = names.index(a), names.index(b)
    return float(np.mean(np.sign(signed[sel, ia]) == np.sign(signed[sel, ib])))
def opp_sign(a, b):
    return 1.0 - same_sign(a, b)
print("\n[compensation] closest-1% pairs, fraction of same-sign / opposite-sign parameter shifts:")
for a, b in [("mu_n_pvk","mu_p_pvk"), ("tau_n_pvk","tau_p_pvk"), ("Nc_eff_pvk","Nv_eff_pvk"),
             ("tau_n_pvk","tau_ETL"), ("tau_n_pvk","tau_HTL"), ("rad_c","tau_n_pvk"), ("rad_c","tau_ETL")]:
    print(f"   {a:<12} vs {b:<12}  same={same_sign(a,b):.2f}  opp={opp_sign(a,b):.2f}")

# ---------------------------------------------------------------- representative cases
pool = order[:max(50, int(M*0.01))]   # candidate pool: closest 1%
def pick(idx, criterion, used):
    """pick best pair in pool by criterion, not already used"""
    best = None
    for k in idx:
        if k in used:
            continue
        v = criterion(k)
        if best is None or v > best[1]:
            best = (k, v)
    return best

used = set()
def case(name, crit):
    res = pick(pool, crit, used)
    if res is None:
        print(f"[case] {name}: none found"); return None
    k = res[0]; used.add(k)
    i, j = int(I[k]), int(Jn[k])
    print(f"[case] {name}: i={i} j={j} dJ={dJ[k]:.5f} (p{dJ_p[k]*100:.2f}%) dTh={dTh[k]:.4f} (p{dTh_p[k]*100:.1f}%)")
    for p in range(ND):
        print(f"         {names[p]:<10} {P_test[i,p]:.3f} -> {P_test[j,p]:.3f}  |d|={A[k,p]:.3f}")
    return (k, i, j, name)

case_specs = [
    ("A: very-close J, large total param diff", lambda k: dTh[k]),
    ("B: interface-lifetime ambiguity",          lambda k: max(A[k, names.index("tau_ETL")], A[k, names.index("tau_HTL")])),
    ("C: rad_c ambiguity",                       lambda k: A[k, names.index("rad_c")]),
    ("D: bulk transport <-> recombination compensation",
        lambda k: min(abs(signed[k, names.index("mu_n_pvk")]), abs(signed[k, names.index("tau_n_pvk")]))
                  if np.sign(signed[k, names.index("mu_n_pvk")]) != np.sign(signed[k, names.index("tau_n_pvk")]) else -1.0),
    ("E: paired-parameter compensation (mu_n vs mu_p)",
        lambda k: min(abs(signed[k, names.index("mu_n_pvk")]), abs(signed[k, names.index("mu_p_pvk")]))
                  if np.sign(signed[k, names.index("mu_n_pvk")]) != np.sign(signed[k, names.index("mu_p_pvk")]) else -1.0),
]
rep = [c for c in (case(*cs) for cs in case_specs) if c is not None]
print(f"[case] {len(rep)} representative cases selected")

# ---------------------------------------------------------------- CSVs
df_pairs = pd.DataFrame({
    "i": I, "j": Jn,
    "dJ_rmse": dJ, "dJ_percentile": dJ_p,
    "dTheta": dTh, "dTheta_percentile": dTh_p,
    "collision_score": coll,
})
for p in range(ND):
    df_pairs[f"absd_{names[p]}"] = A[:, p]
    df_pairs[f"signedd_{names[p]}"] = signed[:, p]
df_pairs.to_csv(os.path.join(OUT, "nearest_neighbor_pairs.csv"), index=False)

# top collision pairs by score (require non-trivially-close J to avoid numerical ties)
score_order = np.argsort(-coll, kind="stable")[:100]
top = df_pairs.iloc[score_order].head(40).copy()
top.insert(0, "case_label", [("REPRESENTATIVE" if int(r.i) in {int(I[k]) for k,_,_,_ in rep} else "") for r in top.itertuples()])
top.to_csv(os.path.join(OUT, "top_collision_pairs.csv"), index=False)

param_amb = pd.concat([tier_stats[t] for t in tier_defs], ignore_index=True)
param_amb.to_csv(os.path.join(OUT, "parameter_ambiguity_summary.csv"), index=False)

# ---------------------------------------------------------------- summary text
L = []
L.append("J-V COLLISION / INVERSE-AMBIGUITY ANALYSIS")
L.append("dataset: dataset_normalized.npz | domain: predefined COMSOL drift-diffusion")
L.append(f"test set: N={N}, J-dim={JD}, param-dim={ND} (normalized log-param space)")
L.append(f"deduplicated nearest-neighbor pairs: {M}")
L.append("")
L.append("=== 1. Nearest-neighbor d_J (normalized RMSE over 131 pts) ===")
L.append(pd.Series(dJ).describe(percentiles=[.25,.5,.75,.9,.99]).round(5).to_string())
L.append("")
L.append("=== 2. Corresponding d_theta (RMSE over 9 normalized log-params) ===")
L.append(pd.Series(dTh).describe(percentiles=[.25,.5,.75,.9,.99]).round(4).to_string())
L.append("")
L.append("=== 3. d_J vs d_theta coupling ===")
L.append(f"Spearman(dJ,dTheta) = {rho_sp:.4f} (p={p_sp:.3e})")
L.append(f"Pearson (dJ,dTheta) = {r_pe:.4f} (p={p_pe:.3e})")
L.append(f"random-pair dTheta median={np.median(rd):.4f}  NN-pair dTheta median={np.median(dTh):.4f}")
L.append(f"random-pair dJ median={np.median(rj):.4f}      NN-pair dJ median={np.median(dJ):.5f}")
L.append("")
L.append("=== 4. Parameter-level ambiguity by J-distance tier ===")
L.append("(median / mean / p90 absolute difference in normalized log space; closest-N pairs)")
for tname in tier_defs:
    k = max(1, int(round(M * tier_defs[tname])))
    sel = order[:k]; subA = A[sel]
    L.append(f"-- {tname}: n_pairs={k}, median dTheta={np.median(dTh[sel]):.4f} --")
    med = [float(np.median(subA[:, p])) for p in range(ND)]
    rnk = sorted(range(ND), key=lambda p: -med[p])
    for rank, p in enumerate(rnk, 1):
        L.append(f"   {rank:>2}. {names[p]:<10} med={med[p]:.4f}  mean={subA[:,p].mean():.4f}  p90={np.percentile(subA[:,p],90):.4f}")
L.append("")
L.append("=== 5. Compensation directions (closest 1% pairs, signed-diff sign agreement) ===")
L.append("fraction of pairs where the two parameters shift in the SAME direction (1 = always together):")
for a, b in [("mu_n_pvk","mu_p_pvk"), ("tau_n_pvk","tau_p_pvk"), ("Nc_eff_pvk","Nv_eff_pvk"),
             ("tau_n_pvk","tau_ETL"), ("tau_n_pvk","tau_HTL"), ("rad_c","tau_n_pvk"), ("rad_c","tau_ETL")]:
    L.append(f"   {a:<12} vs {b:<12}  same_sign_frac={same_sign(a,b):.2f}")
L.append("")
L.append("=== 6. Representative collision cases ===")
for k, i, j, name in rep:
    L.append(f"-- {name} --")
    L.append(f"   pair (i={i}, j={j})  dJ={dJ[k]:.5f} (pct {dJ_p[k]*100:.2f}%)  dTheta={dTh[k]:.4f} (pct {dTh_p[k]*100:.1f}%)")
    for p in range(ND):
        L.append(f"     {names[p]:<10} {P_test[i,p]:.3f} -> {P_test[j,p]:.3f}   |d|={A[k,p]:.3f}")
L.append("")
L.append("=== 7. Caveat ===")
L.append("Collision behavior is conditional on the predefined sampling prior; the paired")
L.append("construction of mu_n/mu_p, tau_n/tau_p, Nc/Nv is an intentional physically")
L.append("constrained prior, not a defect. Directional claims are data-observational only.")
open(os.path.join(OUT, "collision_summary.txt"), "w", encoding="utf-8").write("\n".join(L))
print("\n".join(L[-40:]))

# ---------------------------------------------------------------- figure (2x2)
case_main = rep[0]  # representative pair for panels a/b
k0, i0, j0, _ = case_main
plt.rcParams.update({
    "font.size": 9, "font.family": "sans-serif",
    "axes.linewidth": 0.8, "axes.edgecolor": "#222222",
    "xtick.direction": "in", "ytick.direction": "in",
    "axes.grid": True, "grid.linewidth": 0.4, "grid.alpha": 0.5, "grid.color": "#cccccc",
})
fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.6))
labels = "abcd"
colors = ["#1f77b4", "#d62728"]

# (a) raw J-V curves of the representative pair
ax = axes[0, 0]
ax.plot(V, J_raw[i0], color=colors[0], lw=1.4, label=f"sample {i0}")
ax.plot(V, J_raw[j0], color=colors[1], lw=1.4, ls="--", label=f"sample {j0}")
ax.set_xlabel("Voltage (V)"); ax.set_ylabel("J (mA cm$^{-2}$)")
ax.legend(fontsize=7.5, frameon=False, loc="lower left")
ax.set_ylim(min(J_raw[i0].min(), J_raw[j0].min()) - 0.5, max(J_raw[i0].max(), J_raw[j0].max()) + 0.5)

# (b) dumbbell of 9 normalized-log params for that pair
ax = axes[0, 1]
y = np.arange(ND)[::-1]
x1 = P_test[i0]; x2 = P_test[j0]
for p, (a_, b_) in enumerate(zip(x1, x2)):
    yy = ND - 1 - p
    ax.plot([a_, b_], [yy, yy], color="#999999", lw=1.0, zorder=1)
    ax.scatter([a_, b_], [yy, yy], s=26, c=colors, zorder=2)
ax.set_yticks(y, [names[ND-1-p] for p in range(ND)])
ax.set_xlabel("normalized log parameter value")
ax.set_xlim(-0.02, 1.02)

# (c) all NN pairs, dJ vs dTheta
ax = axes[1, 0]
ax.scatter(dJ, dTh, s=4, alpha=0.25, color="#888888", linewidths=0)
for k, i, j, name in rep:
    ax.scatter([dJ[k]], [dTh[k]], s=30, facecolors="none", edgecolors="#d62728", linewidths=1.2)
ax.set_xlabel("$d_J$ (normalized RMSE)"); ax.set_ylabel("$d_\\theta$ (normalized RMSE)")
ax.text(0.04, 0.96, f"Spearman = {rho_sp:.2f}\np = {p_sp:.1e}", transform=ax.transAxes,
        fontsize=7.5, va="top", ha="left", bbox=dict(fc="white", ec="none", alpha=0.8))
ax.set_xscale("log"); ax.set_yscale("log")

# (d) ambiguity ranking: median abs param diff at closest 1%
ax = axes[1, 1]
k1 = max(1, int(round(M * 0.01)))
sel = order[:k1]; subA = A[sel]
med = [float(np.median(subA[:, p])) for p in range(ND)]
rnk = sorted(range(ND), key=lambda p: med[p])
ax.barh([ND - 1 - q for q, p in enumerate(rnk)], [med[p] for p in rnk], color="#4c72b0", height=0.62)
ax.set_yticks([ND - 1 - q for q in range(ND)], [names[p] for p in rnk])
ax.set_xlabel("median $|\\Delta$param$|$ at closest 1% of pairs")

for ax, Lb in zip(axes.ravel(), labels):
    ax.text(0.015, 0.97, f"({Lb})", transform=ax.transAxes, fontsize=11, fontweight="bold",
            va="top", ha="left", bbox=dict(fc="white", ec="none", alpha=0.8))
fig.tight_layout(pad=1.2)
fig.savefig(os.path.join(OUT, "collision_analysis.png"), dpi=300)
plt.close(fig)
print("\n[saved] collision_analysis/ nearest_neighbor_pairs.csv, top_collision_pairs.csv,")
print("        parameter_ambiguity_summary.csv, collision_summary.txt, collision_analysis.png")
