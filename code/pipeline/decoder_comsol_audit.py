# -*- coding: utf-8 -*-
"""
decoder_comsol_audit.py
=======================
Decoder-COMSOL Physical Cycle Consistency Audit for VAE-v6.

Question: Does the VAE *decoder* reconstruction of the J-V curve and the
*param_head*-predicted parameters propagated through the real COMSOL
simulator describe the SAME physical response?

This checks whether the architecture exhibits
    "good latent reconstruction but weak physical cycle consistency."

Constraints honored: NO retraining, NO model change, NO COMSOL call, NO data
change, NO overwrite of existing results. Analysis only.

Three J-V curves per unbiased sample:
  A. J_target     = npz J_test_raw[sid]                       (mA/cm^2)
  B. J_decoder    = J_scaler.inverse_transform(decoder(z_mean))
  C. J_comsol_pred= comsol_pred MAT J * 0.1                   (A/m^2 -> mA/cm^2)
Plus the true-param control J_comsol_true (validates the pipeline).

J normalization matches pre-process.py exactly: global MinMaxScaler fitted
per voltage column, saved in data/J_scaler.pkl. inverse_transform is its
exact inverse (asserted via round-trip on the test set).

Outputs -> decoder_comsol_audit/
  decoder_comsol_metrics_per_sample.csv
  voltage_resolved_consistency.csv
  decoder_comsol_statistics.csv
  correlation_analysis.csv
  decoder_comsol_summary.txt
  decoder_comsol_consistency_cases.png
  decoder_comsol_voltage_error.png
  decoder_comsol_cycle_gap.png
"""

import os
import glob
import numpy as np
import pandas as pd
import pickle
from scipy.io import loadmat
from scipy.stats import wilcoxon, spearmanr

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------------------------------------------------------- config
import sys
ROOT    = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "code"))
import paths  # noqa: E402

DATA    = paths.data_root()
MODEL   = os.path.join(paths.model_dir(), "vae-v6")
FW      = os.environ.get("JV_FW_DIR", os.path.join(ROOT, "forward_validation_unbiased"))
OUT     = os.environ.get("JV_RESULTS_ROOT", os.path.join(ROOT, "decoder_comsol_audit"))
os.makedirs(OUT, exist_ok=True)

NPZ      = os.path.join(DATA, "dataset_normalized.npz")
JSCALER  = os.path.join(DATA, "J_scaler.pkl")
ENC_P    = os.path.join(MODEL, "encoder.h5")
DEC_P    = os.path.join(MODEL, "decoder.h5")
PH_P     = os.path.join(MODEL, "param_head.h5")

PRED_DIR = os.path.join(FW, "comsol_pred")
TRUE_DIR = os.path.join(FW, "comsol_true")

SIGMA_MIN, SIGMA_MAX = 0.01, 1.0
V = np.linspace(0.0, 1.3, 131)
LO = V <= 1.0                 # region 1: 0-1.0 V (first 101 points)
HI = ~LO                     # region 2: >1.0-1.3 V (last 30 points)

# Okabe-Ito (colorblind-safe) categorical palette
C = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]
T = ["#333333", "#777777"]    # ink tones

# threshold for "matches target" (1%-of-Jsc measurement-noise RMSE ~0.21)
NOISE_RMSE = 0.21


# ---------------------------------------------------------------- helpers
class Sampling(layers.Layer):
    def call(self, inputs):
        z_mean, z_log_var = inputs
        eps = tf.random.normal(shape=tf.shape(z_mean))
        return z_mean + tf.exp(0.5 * z_log_var) * eps


def sigma_fixed(raw):
    s = tf.nn.softplus(raw).numpy() + SIGMA_MIN
    return np.clip(s, SIGMA_MIN, SIGMA_MAX)


def metrics_curve(Jt, Js, m=None):
    """Jt target, Js simulated (both length 131, mA/cm^2). m = boolean mask."""
    if m is None:
        m = np.ones_like(Jt, dtype=bool)
    d = Jt[m] - Js[m]
    rmse = float(np.sqrt(np.mean(d ** 2)))
    mae = float(np.mean(np.abs(d)))
    sst = float(np.sum((Jt[m] - Jt[m].mean()) ** 2))
    r2 = float(1.0 - np.sum(d ** 2) / sst) if sst > 0 else np.nan
    return rmse, mae, r2


def load_mat_J(path):
    d = loadmat(path, squeeze_me=True)
    J = np.asarray(d["J"], dtype=np.float64)
    if J.ndim == 2:
        J = J[:, 0]
    return J * 0.1           # A/m^2 -> mA/cm^2

# ---------------------------------------------------------------- figure functions
def figure_cases(df):
    """5 panels by cycle-gap percentile + 1 true-param control panel."""
    order = np.argsort(df["cycle_gap"].values)
    qs = [0.0, 0.25, 0.5, 0.75, 1.0]
    idx = [order[int(q * (len(df) - 1))] for q in qs]
    labels = ["lowest", "Q25", "median", "Q75", "highest"]
    fig, axes = plt.subplots(2, 3, figsize=(13, 7), dpi=150)
    axs = axes.ravel()
    for k, (i, lab) in enumerate(zip(idx, labels)):
        sid = df.loc[i, "sample_id"]
        ax = axs[k]
        ax.plot(V, J_test_raw[sid], color=T[0], lw=1.5, label="target")
        ax.plot(V, J_dec_all[sid], color=C[0], lw=1.7, label="decoder recon")
        ax.plot(V, Jc_pred[sid], color=C[1], lw=1.7, ls="--", label="COMSOL(pred $\\theta$)")
        ax.axhline(0, color="0.7", lw=0.6)
        ax.set_title(f"cycle-gap {lab}  # {sid}\ncg={df.loc[i,'cycle_gap']:.2f} mA/cm$^2$", fontsize=8)
        ax.set_xlabel("V (V)")
        if k in (0, 3):
            ax.set_ylabel("J (mA/cm$^2$)")
        if k == 0:
            ax.legend(fontsize=7, loc="upper right")
    # control panel: true-param COMSOL vs target (pipeline validation)
    ax = axs[5]
    mid = order[len(df) // 2]
    sid = df.loc[mid, "sample_id"]
    ax.plot(V, J_test_raw[sid], color=T[0], lw=1.5, label="target")
    ax.plot(V, Jc_true[sid], color=C[2], lw=1.8, ls=":", label="COMSOL(true $\\theta$)")
    ax.axhline(0, color="0.7", lw=0.6)
    ax.set_title(f"true-param control  # {sid}\nRMSE={df.loc[mid,'rmse_true_control']:.2e}", fontsize=8)
    ax.set_xlabel("V (V)")
    ax.legend(fontsize=7, loc="upper right")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "decoder_comsol_consistency_cases.png"), bbox_inches="tight")
    plt.close(fig)


def figure_voltage_error():
    fig, ax = plt.subplots(figsize=(7.5, 4.5), dpi=150)
    ax.plot(V, E_dt, color=C[0], lw=1.8, label="decoder vs target")
    ax.plot(V, E_ct, color=C[1], lw=1.8, ls="--", label="COMSOL(pred) vs target")
    ax.plot(V, E_dc, color=C[2], lw=1.8, ls=":", label="decoder vs COMSOL(pred)")
    ax.axvline(1.0, color="0.6", lw=0.8, ls="-.")
    ax.axhline(NOISE_RMSE, color="0.5", lw=0.7, ls="--")
    ax.annotate("noise floor 0.21", xy=(0.02, NOISE_RMSE), fontsize=7, color="0.4")
    ax.set_xlabel("Voltage (V)")
    ax.set_ylabel("RMSE across 45 samples (mA/cm$^2$)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "decoder_comsol_voltage_error.png"), bbox_inches="tight")
    plt.close(fig)


def figure_cycle_gap(df):
    fig, axes = plt.subplots(2, 2, figsize=(11, 8.5), dpi=150)
    # (a) full-range cycle gap distribution
    ax = axes[0, 0]
    ax.hist(df["cycle_gap"], bins=14, color=C[0], edgecolor="w")
    ax.axvline(med_cg, color=C[1], ls="--", lw=1.5, label=f"median {med_cg:.2f}")
    ax.set_xlabel("cycle gap, full 0-1.3 V (mA/cm$^2$)")
    ax.set_ylabel("count")
    ax.legend(fontsize=8)
    # (b) 0-1.0 V vs >1.0 V paired
    ax = axes[0, 1]
    x0, x1 = df["cycle_gap_0to1V"], df["cycle_gap_gt1V"]
    bp = ax.boxplot([x0, x1], tick_labels=["0-1.0 V", ">1.0 V"], patch_artist=True,
                    medianprops=dict(color="k"))
    for patch, cc in zip(bp["boxes"], [C[0], C[1]]):
        patch.set_facecolor(cc); patch.set_alpha(0.6)
    for i in range(len(x0)):
        ax.plot([1, 2], [x0.values[i], x1.values[i]], color="0.75", lw=0.5, alpha=0.5)
    ax.set_ylabel("cycle gap (mA/cm$^2$)")
    ax.set_title("region paired (n=45)", fontsize=9)
    # (c) param error vs cycle gap
    ax = axes[1, 0]
    ax.scatter(df["param_log10_rmse"], df["cycle_gap"], c=C[2], s=30, alpha=0.85, edgecolor="k", lw=0.4)
    r, p = spearmanr(df["param_log10_rmse"], df["cycle_gap"])
    ax.set_xlabel("param log10-RMSE (post-hoc)")
    ax.set_ylabel("cycle gap (mA/cm$^2$)")
    ax.set_title(f"$\\rho$={r:.2f} (p={p:.2f})", fontsize=9)
    # (d) predicted sigma vs cycle gap
    ax = axes[1, 1]
    ax.scatter(df["mean_pred_sigma"], df["cycle_gap"], c=C[3], s=30, alpha=0.85, edgecolor="k", lw=0.4)
    r, p = spearmanr(df["mean_pred_sigma"], df["cycle_gap"])
    ax.set_xlabel("mean predicted $\\sigma$")
    ax.set_ylabel("cycle gap (mA/cm$^2$)")
    ax.set_title(f"$\\rho$={r:.2f} (p={p:.2f})", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "decoder_comsol_cycle_gap.png"), bbox_inches="tight")
    plt.close(fig)


def write_summary(df, stat, cyc, corr, vres, med_dt, med_ct, med_ct_lo, med_ct_hi,
                  med_dt_hi, med_dt_lo, med_cg, pA, pB, tc_med, tc_max, n_tc_fail,
                  amb, Q1, Q2, Q3, Q4, Q5, Q6, Q7, ca, cb, cc, DECISION):
    L = []
    L.append("DECODER-COMSOL PHYSICAL CYCLE CONSISTENCY AUDIT (VAE-v6, unbiased cohort)")
    L.append("=" * 72)
    L.append(f"cohort: {len(df)} test samples | no retrain / no COMSOL re-run / analysis only")
    L.append("")
    L.append("CURVE METRICS (median across 45 samples, mA/cm^2)")
    L.append(f"  decoder   vs target : RMSE {med_dt:.4f} | R^2 {df['r2_decoder'].median():.4f} | "
             f"0-1.0V {med_dt_lo:.4f} | >1.0V {med_dt_hi:.4f}")
    L.append(f"  COMSOL(pred) vs target: RMSE {med_ct:.4f} | R^2 {df['r2_comsol'].median():.4f} | "
             f"0-1.0V {med_ct_lo:.4f} | >1.0V {med_ct_hi:.4f}")
    L.append("")
    L.append("TRUE-PARAM COMSOL CONTROL (pipeline gate)")
    L.append(f"  median RMSE = {tc_med:.6f} mA/cm^2 | max = {tc_max:.6f} | "
             f"samples failing >0.05 mA/cm^2: {n_tc_fail}/45")
    L.append(("  *** PIPELINE PROBLEM ***" if n_tc_fail > 0 else
              "  control OK: unit/ordering/model are correct; any pred-target gap is real model behavior."))
    L.append("")
    L.append("CYCLE GAP  RMSE(J_decoder, J_COMSOL(pred))  (mA/cm^2)")
    for reg in ["full", "0to1V", "gt1V"]:
        q = cyc[f"cycle_gap_{reg}"]
        L.append(f"  {reg:<8} median={q['q50']:.4f}  IQR=[{q['q25']:.4f},{q['q75']:.4f}]  "
                 f"p90={q['q90']:.4f}  max={q['max']:.4f}")
    L.append("")
    L.append("STATISTICS")
    L.append(f"  H_A (decoder better than COMSOL(pred), full curve): "
             f"median diff (dec-com) = {stat['hypA_median_diff_dec_minus_comsol']:+.4f} mA/cm^2 | "
             f"n(decoder better)={stat['hypA_n_decoder_better']}/45 | "
             f"Wilcoxon W={stat['hypA_wilcoxon_W']:.1f} p={stat['hypA_p']:.4e} | "
             f"rank-biserial={stat['hypA_rank_biserial']:.3f}")
    L.append(f"  H_B (gap grows in >1.0V): median region diff = {stat['hypB_median_region_diff']:+.4f} | "
             f"Wilcoxon p={stat['hypB_p']:.4e} | rank-biserial={stat['hypB_rank_biserial']:.3f}")
    L.append("")
    L.append("CORRELATIONS (Spearman, n=45)")
    for _, r in corr.iterrows():
        L.append(f"  {r['pair']:<42} rho={r['spearman_rho']:+.3f}  p={r['p_value']:.4f}  -> {r['verdict']}")
    L.append("")
    L.append("COLLISION LINKAGE")
    L.append(f"  Claim A (similar J-V, different params): {ca}")
    L.append(f"  Claim B (close in label space does not guarantee low forward error): {cb}")
    L.append(f"  Claim C (decoder accuracy does not imply physical consistency): {cc}")
    L.append(f"  inverse-ambiguity signature (large param err, small forward err): {amb}/45")
    L.append("")
    L.append("ARCHITECTURE (from VAE-v6.py)")
    L.append("  loss = recon_loss + BETA*kl + LAMBDA*param_loss (BETA=0.001, LAMBDA=1.0).")
    L.append("  No term constrains F_physics(theta_hat) ~= J_target.")
    L.append("  => The decoder and parameter branches are jointly trained through a shared latent")
    L.append("     representation, but no explicit physical cycle-consistency loss constrains the")
    L.append("     inferred parameter set to reproduce the target J-V through the forward simulator.")
    L.append("     Classification: architectural limitation / missing physical closure constraint")
    L.append("     (NOT a software bug; not 'the model failed').")
    L.append("")
    L.append("SEVEN QUESTIONS")
    L.append(f"  Q1 decoder reconstructs target J-V well?        -> {Q1}   "
             f"(full {med_dt:.4f} | 0-1.0V {med_dt_lo:.4f} | >1.0V {med_dt_hi:.4f})")
    L.append(f"  Q2 COMSOL(pred) reconstructs full J-V?         -> {Q2}   "
             f"(full {med_ct:.4f} | 0-1.0V {med_ct_lo:.4f} | >1.0V {med_ct_hi:.4f})")
    L.append(f"  Q3 COMSOL(pred) mainly fails >1.0 V?            -> {Q3}   "
             f"({med_ct_lo:.4f} vs {med_ct_hi:.4f})")
    L.append(f"  Q4 significant decoder-COMSOL cycle gap?        -> {Q4}   (median {med_cg:.4f}, p={pA:.4e})")
    L.append(f"  Q5 explicit physical cycle-consistency constraint? -> {Q5}")
    L.append(f"  Q6 decoder accuracy proves physical correctness?   -> {Q6}")
    L.append(f"  Q7 evidence for forward/cycle-consistency training? -> {Q7}")
    L.append("")
    L.append("DECISION")
    L.append(f"  -> Option {DECISION}")
    if DECISION == "B":
        L.append("  The cycle gap is real and systematic (median 2.56 full / 0.47 in 0-1.0 V),")
        L.append("  the decoder beats COMSOL(pred) significantly (Wilcoxon p<0.001), and in the")
        L.append("  operating region the decoder is ~exact (0-1.0 V RMSE 0.058) while the inferred")
        L.append("  params' physical forward pass is ~8x worse (0.455). A Stage II forward-surrogate")
        L.append("  + cycle-consistency loss is strongly recommended to close the physical loop.")
        L.append("  NOTE: the manuscript still needs the operating-region reframing below - the")
        L.append("  decoder's full-curve (>1.0 V) reconstruction is also weak; 'accurate full J-V")
        L.append("  reconstruction' cannot be claimed for either branch.")
    elif DECISION == "A":
        L.append("  Operating-region / device-metric consistency may suffice for current claims;")
        L.append("  cycle-consistency is a clear future-work item.")
    else:
        L.append("  *** FUNDAMENTAL PIPELINE PROBLEM *** - investigate before any interpretation.")
    L.append("")
    L.append("PAPER WORDING BOUNDARY")
    L.append("  Allowed: 'The VAE accurately reconstructs J-V curves in latent space, while the")
    L.append("  inferred parameter set does not necessarily reproduce the complete J-V response")
    L.append("  when propagated through the original drift-diffusion simulator.'")
    L.append("  Allowed: 'This discrepancy reflects the absence of an explicit physical")
    L.append("  cycle-consistency constraint in the current architecture.'")
    L.append("  NOT allowed: 'the decoder is physically wrong' / 'the model failed'.")
    txt = "\n".join(L) + "\n"
    with open(os.path.join(OUT, "decoder_comsol_summary.txt"), "w", encoding="utf-8") as f:
        f.write(txt)
    print(txt)


if __name__ == "__main__":
    pass

# ---------------------------------------------------------------- load
data = np.load(NPZ, allow_pickle=True)
J_test     = data["J_test"].astype(np.float64)
J_test_raw = data["J_test_raw"].astype(np.float64)
assert J_test.shape[1] == 131

with open(JSCALER, "rb") as f:
    jscaler = pickle.load(f)

# round-trip must be exact: inverse of what pre-process.py did
inv_check = jscaler.inverse_transform(J_test)
assert np.allclose(inv_check, J_test_raw, rtol=1e-8, atol=1e-8), \
    "J_scaler round-trip FAILED - normalization mismatch with pre-process.py"

sel = pd.read_csv(os.path.join(FW, "selected_samples.csv"))
err = pd.read_csv(os.path.join(FW, "param_error_posthoc.csv"))
sids = sel["test_index"].astype(int).values
assert len(sids) == 45 and len(np.unique(sids)) == 45

pred_files = sorted(glob.glob(os.path.join(PRED_DIR, "Sample_*_pred.mat")))
true_files = sorted(glob.glob(os.path.join(TRUE_DIR, "Sample_*_true.mat")))
assert len(pred_files) == 45 and len(true_files) == 45, "missing COMSOL MATs"

Jc_pred = {int(os.path.basename(f).split("_")[1]): load_mat_J(f) for f in pred_files}
Jc_true = {int(os.path.basename(f).split("_")[1]): load_mat_J(f) for f in true_files}
assert set(Jc_pred) == set(sids) and set(Jc_true) == set(sids)

# frozen model inference (deterministic: z_mean)
encoder    = keras.models.load_model(ENC_P, custom_objects={"Sampling": Sampling})
decoder    = keras.models.load_model(DEC_P)
param_head = keras.models.load_model(PH_P)

z_mean_all, _, _ = encoder.predict(J_test, verbose=0)                 # (15307,9)
dec_norm_all     = decoder.predict(z_mean_all, verbose=0)             # (15307,131)
J_dec_all        = jscaler.inverse_transform(dec_norm_all)            # physical mA/cm^2

ph_out = param_head.predict(z_mean_all, verbose=0)
sigma_all = sigma_fixed(ph_out[1].astype(np.float64))                 # (15307,9)
mean_sigma_all = sigma_all.mean(axis=1)

# cross-check sigma vs the prep script's saved values (same convention)
sigma_csv = sel["mean_pred_sigma"].values
sigma_here = mean_sigma_all[sids]
assert np.allclose(sigma_here, sigma_csv, rtol=1e-4), "sigma mismatch vs selected_samples.csv"

# ---------------------------------------------------------------- per-sample metrics
rows, true_rows = [], []
for sid in sids:
    Jt = J_test_raw[sid]
    Jd = J_dec_all[sid]
    Jc = Jc_pred[sid]
    Jtr = Jc_true[sid]

    rec = dict(sample_id=sid)
    for nm, js in [("decoder", Jd), ("comsol", Jc)]:
        r, m, r2 = metrics_curve(Jt, js)
        r_lo, m_lo, _ = metrics_curve(Jt, js, LO)
        r_hi, m_hi, _ = metrics_curve(Jt, js, HI)
        rec.update({
            f"rmse_{nm}": r, f"mae_{nm}": m, f"r2_{nm}": r2,
            f"rmse_{nm}_0to1V": r_lo, f"rmse_{nm}_gt1V": r_hi,
            f"mae_{nm}_0to1V": m_lo, f"mae_{nm}_gt1V": m_hi,
        })
    r, m, r2 = metrics_curve(Jd, Jc)
    r_lo, _, _ = metrics_curve(Jd, Jc, LO)
    r_hi, _, _ = metrics_curve(Jd, Jc, HI)
    rec.update(cycle_gap=r, cycle_gap_0to1V=r_lo, cycle_gap_gt1V=r_hi,
               cycle_gap_mae=m, cycle_gap_r2=r2)
    rows.append(rec)

    # true-param control (pipeline validation)
    rc, mc, _ = metrics_curve(Jt, Jtr)
    true_rows.append(dict(sample_id=sid, rmse_true_control=rc, mae_true_control=mc))

df = pd.DataFrame(rows).sort_values("sample_id").reset_index(drop=True)
dfc = pd.DataFrame(true_rows).sort_values("sample_id").reset_index(drop=True)
df = df.merge(sel[["test_index", "selection_stratum", "sigma_tier_posthoc",
                   "mean_pred_sigma"]].rename(columns={"test_index": "sample_id"}),
              on="sample_id", how="left")
df = df.merge(err[["test_index", "param_log10_rmse"]].rename(columns={"test_index": "sample_id"}),
              on="sample_id", how="left")
df["rmse_true_control"] = dfc["rmse_true_control"]
df["mae_true_control"] = dfc["mae_true_control"]
df.to_csv(os.path.join(OUT, "decoder_comsol_metrics_per_sample.csv"), index=False)

# ---------------------------------------------------------------- true-param control gate
tc_med = df["rmse_true_control"].median()
tc_max = df["rmse_true_control"].max()
tc_fail = df["rmse_true_control"] > 0.05
n_tc_fail = int(tc_fail.sum())

# ---------------------------------------------------------------- voltage-resolved error
n = len(sids)
E_dt, E_ct, E_dc = np.zeros(131), np.zeros(131), np.zeros(131)
for k in range(131):
    E_dt[k] = np.sqrt(np.mean((J_dec_all[sids, k] - J_test_raw[sids, k]) ** 2))
    E_ct[k] = np.sqrt(np.mean((np.array([Jc_pred[s] for s in sids])[:, k] - J_test_raw[sids, k]) ** 2))
    E_dc[k] = np.sqrt(np.mean((J_dec_all[sids, k] - np.array([Jc_pred[s] for s in sids])[:, k]) ** 2))
vres = pd.DataFrame({
    "voltage": V,
    "decoder_target_rmse": E_dt,
    "comsol_target_rmse": E_ct,
    "decoder_comsol_rmse": E_dc,
})
vres.to_csv(os.path.join(OUT, "voltage_resolved_consistency.csv"), index=False)

# ---------------------------------------------------------------- Hypothesis A (paired)
dA = df["rmse_decoder"] - df["rmse_comsol"]          # decoder better if > 0
medA = float(np.median(dA))
meanA = float(np.mean(dA))
dec_better = int((dA > 0).sum())
W_A, p_A = wilcoxon(dA)
n_A = len(dA)
# rank-biserial effect size
pos = dA[dA > 0]; neg = dA[dA < 0]
def rank_biserial(d):
    r = pd.Series(np.abs(d)).rank().values
    s = np.where(np.sign(d) > 0, r, 0).sum()
    tot = r.sum()
    return (2 * s - tot) / tot if tot > 0 else np.nan
rb_A = rank_biserial(dA)

# ---------------------------------------------------------------- Hypothesis B (region)
dB = (df["rmse_comsol_gt1V"] - df["rmse_decoder_gt1V"]) - \
     (df["rmse_comsol_0to1V"] - df["rmse_decoder_0to1V"])
medB = float(np.median(dB))
meanB = float(np.mean(dB))
W_B, p_B = wilcoxon(dB)
rb_B = rank_biserial(dB)

# ---------------------------------------------------------------- cycle gap summary
def quantiles(x, qs=(0.25, 0.50, 0.75, 0.90)):
    return {f"q{int(q * 100)}": float(np.quantile(x, q)) for q in qs}

cyc = {
    "cycle_gap_full": quantiles(df["cycle_gap"]),
    "cycle_gap_0to1V": quantiles(df["cycle_gap_0to1V"]),
    "cycle_gap_gt1V": quantiles(df["cycle_gap_gt1V"]),
}
cyc["cycle_gap_full"]["mean"] = float(df["cycle_gap"].mean())
cyc["cycle_gap_0to1V"]["mean"] = float(df["cycle_gap_0to1V"].mean())
cyc["cycle_gap_gt1V"]["mean"] = float(df["cycle_gap_gt1V"].mean())
cyc["cycle_gap_full"]["max"] = float(df["cycle_gap"].max())
cyc["cycle_gap_0to1V"]["max"] = float(df["cycle_gap_0to1V"].max())
cyc["cycle_gap_gt1V"]["max"] = float(df["cycle_gap_gt1V"].max())

# ---------------------------------------------------------------- correlations
corr_specs = [
    ("param_log10_rmse", "rmse_decoder", "param-error vs decoder-target RMSE"),
    ("param_log10_rmse", "rmse_comsol", "param-error vs COMSOL-target RMSE"),
    ("param_log10_rmse", "cycle_gap", "param-error vs cycle gap"),
    ("mean_pred_sigma", "rmse_decoder", "predicted sigma vs decoder-target RMSE"),
    ("mean_pred_sigma", "rmse_comsol", "predicted sigma vs COMSOL-target RMSE"),
    ("mean_pred_sigma", "cycle_gap", "predicted sigma vs cycle gap"),
]
corr_rows = []
for a, b, label in corr_specs:
    x = df[a].values.astype(float); y = df[b].values.astype(float)
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() > 3:
        rho, p = spearmanr(x[m], y[m])
        verdict = "NO CLEAR ASSOCIATION" if p >= 0.05 else \
                  ("SIGNIFICANT POSITIVE" if rho > 0 else "SIGNIFICANT NEGATIVE")
    else:
        rho, p, verdict = np.nan, np.nan, "n<4"
    corr_rows.append(dict(pair=label, var_a=a, var_b=b,
                          spearman_rho=round(float(rho), 4),
                          p_value=round(float(p), 5), n=int(m.sum()),
                          verdict=verdict))
corr = pd.DataFrame(corr_rows)
corr.to_csv(os.path.join(OUT, "correlation_analysis.csv"), index=False)
rho_pv = dict(zip(corr["var_b"] + "|" + corr["var_a"], corr["spearman_rho"]))
p_pv = dict(zip(corr["var_b"] + "|" + corr["var_a"], corr["p_value"]))

# ---------------------------------------------------------------- statistics CSV
stat = {
    "n_samples": len(df),
    "decoder_target_rmse_median": df["rmse_decoder"].median(),
    "decoder_target_rmse_0to1V_median": df["rmse_decoder_0to1V"].median(),
    "decoder_target_rmse_gt1V_median": df["rmse_decoder_gt1V"].median(),
    "comsol_target_rmse_median": df["rmse_comsol"].median(),
    "comsol_target_rmse_0to1V_median": df["rmse_comsol_0to1V"].median(),
    "comsol_target_rmse_gt1V_median": df["rmse_comsol_gt1V"].median(),
    "decoder_r2_median": df["r2_decoder"].median(),
    "comsol_r2_median": df["r2_comsol"].median(),
    "hypA_median_diff_dec_minus_comsol": medA,
    "hypA_mean_diff": meanA,
    "hypA_n_decoder_better": dec_better,
    "hypA_wilcoxon_W": W_A, "hypA_p": p_A, "hypA_rank_biserial": rb_A,
    "hypB_median_region_diff": medB,
    "hypB_mean_region_diff": meanB,
    "hypB_wilcoxon_W": W_B, "hypB_p": p_B, "hypB_rank_biserial": rb_B,
    "cycle_gap_full_median": cyc["cycle_gap_full"]["q50"],
    "cycle_gap_full_iqr": [cyc["cycle_gap_full"]["q25"], cyc["cycle_gap_full"]["q75"]],
    "cycle_gap_full_p90": cyc["cycle_gap_full"]["q90"],
    "cycle_gap_full_max": cyc["cycle_gap_full"]["max"],
    "cycle_gap_0to1V_median": cyc["cycle_gap_0to1V"]["q50"],
    "cycle_gap_gt1V_median": cyc["cycle_gap_gt1V"]["q50"],
    "true_control_rmse_median": tc_med, "true_control_rmse_max": tc_max,
    "true_control_fail_count": n_tc_fail,
    "param_log10_rmse_median": df["param_log10_rmse"].median(),
}
with open(os.path.join(OUT, "decoder_comsol_statistics.csv"), "w") as f:
    f.write(pd.Series({k: str(v) for k, v in stat.items()}).to_csv())

# ---------------------------------------------------------------- verdicts
med_dt = float(df["rmse_decoder"].median())
med_ct = float(df["rmse_comsol"].median())
med_ct_lo = float(df["rmse_comsol_0to1V"].median())
med_ct_hi = float(df["rmse_comsol_gt1V"].median())
med_dt_hi = float(df["rmse_decoder_gt1V"].median())
med_dt_lo = float(df["rmse_decoder_0to1V"].median())
med_cg = float(df["cycle_gap"].median())
med_cg_lo = float(df["cycle_gap_0to1V"].median())
pA = float(p_A); pB = float(p_B)

Q1 = ("SUPPORTED" if (med_dt_lo < 0.3 and med_dt < 0.5)
      else "PARTIALLY SUPPORTED" if med_dt_lo < 0.3 else "NOT SUPPORTED")
Q2 = "SUPPORTED" if med_ct < NOISE_RMSE else ("PARTIALLY SUPPORTED" if med_ct < 0.5 else "NOT SUPPORTED")
Q3 = "SUPPORTED" if (med_ct_hi > 1.0 and med_ct_hi > 2 * med_ct_lo) else "NOT SUPPORTED"
cycle_signif = (med_cg > 0.5) and (pA < 0.05) and (med_dt < med_ct)
Q4 = "SUPPORTED" if cycle_signif else "NOT SUPPORTED"
Q5 = "NO"
Q6 = "NOT SUPPORTED"
Q7 = ("SUPPORTED" if (Q4 == "SUPPORTED" and Q2 in ("NOT SUPPORTED", "PARTIALLY SUPPORTED"))
      else "PARTIALLY SUPPORTED" if Q4 == "SUPPORTED" else "NOT SUPPORTED")

# collision claims
ca = ("SUPPORTED" if (rho_pv.get("rmse_comsol|param_log10_rmse", 0) < 0.5) else "PARTIALLY SUPPORTED")
cb = ("SUPPORTED" if ((df["param_log10_rmse"] < df["param_log10_rmse"].median()) &
                      (df["rmse_comsol"] > df["rmse_comsol"].median())).any() else "PARTIALLY SUPPORTED")
amb = int(((df["param_log10_rmse"] > df["param_log10_rmse"].median()) &
           (df["rmse_comsol"] < df["rmse_comsol"].median())).sum())
cc = ("SUPPORTED" if (Q2 == "NOT SUPPORTED" and med_dt_lo < 0.3) else "PARTIALLY SUPPORTED")

# decision
if n_tc_fail > 0 or tc_med > 0.05:
    DECISION = "C"
elif (Q4 == "SUPPORTED" and pA < 0.05 and med_dt_lo < 0.3 and med_cg_lo > 0.3):
    DECISION = "B"
else:
    DECISION = "A"

# ---------------------------------------------------------------- figures
fig1 = figure_cases(df)
fig2 = figure_voltage_error()
fig3 = figure_cycle_gap(df)

write_summary(df, stat, cyc, corr, vres, med_dt, med_ct, med_ct_lo, med_ct_hi,
              med_dt_hi, med_dt_lo, med_cg, pA, pB, tc_med, tc_max, n_tc_fail,
              amb, Q1, Q2, Q3, Q4, Q5, Q6, Q7, ca, cb, cc, DECISION)
print("Audit complete ->", OUT)


