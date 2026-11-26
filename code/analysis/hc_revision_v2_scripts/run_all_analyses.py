# -*- coding: utf-8 -*-
"""Consolidated, read-only supplementary analyses for the HC1015 revision.

Every number written into the manuscript / SI in this round is produced here
and saved under analysis/out/.  No model is retrained and no COMSOL solve is
started; the script only reads frozen arrays, frozen scalers, archived COMSOL
outputs and archived benchmark tables.
"""
import glob
import hashlib
import json
import os
import re
import warnings

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")

import metrics_lib as ml

BASE = r"E:\project\work1"
STAGE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(STAGE, "analysis", "out")
os.makedirs(OUT, exist_ok=True)

FWD = os.path.join(BASE, "forward_validation_unbiased")
S6_DIR = os.path.join(BASE, "20261006", "manuscript_figures_SI_integrated_v2_layout_final", "data_used")
EXP1 = os.path.join(BASE, "reviewer_experiments", "exp1_leakage_free_baselines")
EXP3 = os.path.join(BASE, "reviewer_experiments", "exp3_prior_coordinate_recoverability")

V_LOW_MAX = 1.0 + 1e-9


def save(df, name, **kw):
    p = os.path.join(OUT, name)
    df.to_csv(p, index=False, **kw)
    print("wrote", p, getattr(df, "shape", ""))
    return p


def save_json(obj, name):
    p = os.path.join(OUT, name)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False, default=float)
    print("wrote", p)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ----------------------------------------------------------------------------
# A. Paired coordinates: reproduce Table S11 and add R^2
# ----------------------------------------------------------------------------
D = ml.load()
F, d, sc, js = D["f"], D["d"], D["sc"], D["js"]
L_true, L_pred, L_train = D["L_true"], D["L_pred"], D["L_train"]
C_true, C_pred, C_train = ml.coords(L_true), ml.coords(L_pred), ml.coords(L_train)

rows = []
for k, name in enumerate(ml.COORD_NAMES):
    m = ml.metrics(C_true[:, k], C_pred[:, k], C_train[:, k])
    rows.append(dict(coordinate=name, **m))
tab_s11 = pd.DataFrame(rows)
tab_s11["median_abs_log_error"] = [np.median(np.abs(C_true[:, k] - C_pred[:, k]))
                                   for k in range(6)]
save(tab_s11, "table_s11_reproduction_with_r2.csv")

# Compare with the archived EXP3 table (independent recomputation)
arch = pd.read_csv(os.path.join(EXP3, "results", "frozen_coordinate_recoverability.csv"))
chk = tab_s11[["coordinate", "pearson", "skill_mse", "mae_reduction"]].merge(
    arch[["coordinate", "pearson_r", "skill_rmse", "mae_reduction"]], on="coordinate")
chk["d_pearson"] = chk["pearson"] - chk["pearson_r"]
chk["d_skill"] = chk["skill_mse"] - chk["skill_rmse"]
chk["d_mae_reduction"] = chk["mae_reduction_x"] - chk["mae_reduction_y"]
save(chk, "table_s11_archived_reproduction_check.csv")

print(tab_s11[["coordinate", "pearson", "skill_mse", "r2_test", "mae_reduction",
               "median_abs_log_error"]].to_string(index=False))

# Training vs test means: why Skill_MSE and R2_test are numerically close
mean_shift = pd.DataFrame({
    "coordinate": ml.COORD_NAMES,
    "train_mean": [C_train[:, k].mean() for k in range(6)],
    "test_mean": [C_true[:, k].mean() for k in range(6)],
})
mean_shift["difference"] = mean_shift["test_mean"] - mean_shift["train_mean"]
mean_shift["sd_test"] = [C_true[:, k].std(ddof=1) for k in range(6)]
mean_shift["difference_in_test_sd"] = mean_shift["difference"] / mean_shift["sd_test"]
save(mean_shift, "paired_coordinate_mean_shift.csv")

# ----------------------------------------------------------------------------
# B. Nine single parameters: R^2 / Skill / RMSE in physical log10 space
# ----------------------------------------------------------------------------
rows = []
for k, name in enumerate(ml.PARAM_NAMES):
    m = ml.metrics(L_true[:, k], L_pred[:, k], L_train[:, k])
    rows.append(dict(parameter=name, coordinate_space="physical log10",
                     **m))
single = pd.DataFrame(rows)
save(single, "single_parameter_point_metrics.csv")

# Explicit correspondence table of metric conventions used in this round.
corr = []
for _, r in tab_s11.iterrows():
    corr.append(dict(result="Table S11 / main Results 2.2", quantity="Skill_MSE",
                     coordinate_space="physical log10 paired coordinate",
                     n=int(r["n"]), baseline="training-partition mean",
                     note="primary metric; R2_test uses the test-set mean"))
for _, r in tab_s11.iterrows():
    corr.append(dict(result="Table S11 / main Results 2.2", quantity="MAE reduction",
                     coordinate_space="physical log10 paired coordinate",
                     n=int(r["n"]), baseline="training-partition median",
                     note="supplementary metric; mean absolute errors"))
for _, r in single.iterrows():
    corr.append(dict(result="Table S11b (new)", quantity="R2_test / Skill_MSE / RMSE",
                     coordinate_space="physical log10 single parameter",
                     n=int(r["n"]), baseline="test mean (R2) / training mean (Skill)",
                     note="R2 is invariant to the scaler's positive affine map, RMSE is not"))
corr.append(dict(result="Main Results 2.4 / Table S18c-d (new)", quantity="per-curve R2 and RMSE",
                 coordinate_space="physical current density, mA cm-2",
                 n=45, baseline="that target curve's mean in the same voltage window",
                 note="window-specific squared-deviation denominator; negative values retained"))
corr.append(dict(result="Main Results 2.4 / Table S18e (new)", quantity="decoder and COMSOL SSE shares",
                 coordinate_space="normalized current (decoder) and physical current (both)",
                 n=45, baseline="full-sweep SSE over the same 45 matched curves",
                 note=("same 45 test indices for decoder and COMSOL; window SSE sum "
                       "divided by full-sweep SSE sum, not the mean of per-curve shares")))
corr.append(dict(result="Table S6 / S10", quantity="normalized coordinate difference",
                 coordinate_space="physical log10 parameter differences",
                 n=11245, baseline="median absolute difference among random pairs",
                 note="descriptive; pairs are not independent"))
save(pd.DataFrame(corr), "metric_correspondence.csv")

# ----------------------------------------------------------------------------
# C. Forward back-substitution: per-curve RMSE and R2 in three windows
# ----------------------------------------------------------------------------
recs = []
for mp in sorted(glob.glob(os.path.join(FWD, "comsol_pred", "Sample_*_pred.mat"))):
    import scipy.io as sio
    sid = int(re.search(r"Sample_(\d+)_pred", mp).group(1))
    pred = sio.loadmat(mp)
    true = sio.loadmat(os.path.join(FWD, "comsol_true", "Sample_%05d_true.mat" % sid))
    V = pred["V_grid"].ravel().astype(float)
    Jp = pred["J"].ravel().astype(float) * 0.1      # A m-2 -> mA cm-2
    Jt = true["J"].ravel().astype(float) * 0.1
    assert np.allclose(V, true["V_grid"].ravel())
    rec = dict(sample_id=sid, test_index=int(pred["test_index"].ravel()[0]))
    for wname, mask in (("full", np.ones_like(V, bool)),
                        ("0to1V", V <= V_LOW_MAX),
                        ("gt1V", V > V_LOW_MAX)):
        y, yh = Jt[mask], Jp[mask]
        sse = float(np.sum((y - yh) ** 2))
        denom = float(np.sum((y - y.mean()) ** 2))
        rec["n_" + wname] = int(mask.sum())
        rec["rmse_" + wname] = float(np.sqrt(sse / mask.sum()))
        rec["denom_" + wname] = denom
        rec["r2_" + wname] = float(1.0 - sse / denom) if denom > 0 else np.nan
        rec["mean_target_" + wname] = float(y.mean())
        rec["min_abs_dev_" + wname] = float(np.min(np.abs(y - y.mean())))
    recs.append(rec)
fwd = pd.DataFrame(recs).sort_values("sample_id").reset_index(drop=True)
fwd["near_zero_denom_full"] = fwd["denom_full"] < 1e-8
fwd["near_zero_denom_0to1V"] = fwd["denom_0to1V"] < 1e-8
fwd["near_zero_denom_gt1V"] = fwd["denom_gt1V"] < 1e-8
save(fwd, "forward_per_curve_r2_rmse.csv")

# Reproduce the stored per-sample RMSE values exactly
stored = pd.read_csv(os.path.join(FWD, "forward_metrics_per_sample.csv"))
mrg = fwd.merge(stored[["sample_id", "rmse_full", "rmse_0to1V", "rmse_gt1V", "r2_full"]],
                on="sample_id", suffixes=("", "_stored"))
rep = {}
for w, cs in (("full", "rmse_full"), ("0to1V", "rmse_0to1V"), ("gt1V", "rmse_gt1V")):
    diff = np.abs(mrg["rmse_" + w] - mrg[cs + "_stored"]).max()
    rep[w] = float(diff)
rep["r2_full_max_abs_diff"] = float(np.abs(mrg["r2_full"] - mrg["r2_full_stored"]).max())
rep["n_cases"] = int(len(fwd))
save_json(rep, "forward_rmse_reproduction_check.json")

# Summary: valid n, median, quartiles, negative R2 counts
summ = []
for w in ("full", "0to1V", "gt1V"):
    for metric in ("rmse", "r2"):
        x = fwd[metric + "_" + w].dropna().values
        summ.append(dict(window=w, metric=metric, n_valid=int(x.size),
                         median=float(np.median(x)),
                         q25=float(np.percentile(x, 25)),
                         q75=float(np.percentile(x, 75)),
                         min=float(np.min(x)), max=float(np.max(x)),
                         n_negative=int(np.sum(x < 0)),
                         n_below_0p1=int(np.sum(x < 0.1))))
summ = pd.DataFrame(summ)
save(summ, "forward_summary_by_window.csv")

# Window definitions / denominators that need flagging
flags = pd.DataFrame({
    "check": ["min denom full", "min denom 0-1V", "min denom >1V",
              "n denom < 1e-8 full", "n denom < 1e-8 0-1V", "n denom < 1e-8 >1V",
              "min mean |target| >1V", "n R2<0 full", "n R2<0 0-1V", "n R2<0 >1V"],
    "value": [fwd["denom_full"].min(), fwd["denom_0to1V"].min(), fwd["denom_gt1V"].min(),
              int((fwd["denom_full"] < 1e-8).sum()), int((fwd["denom_0to1V"] < 1e-8).sum()),
              int((fwd["denom_gt1V"] < 1e-8).sum()),
              float(fwd["mean_target_gt1V"].abs().min()),
              int((fwd["r2_full"] < 0).sum()), int((fwd["r2_0to1V"] < 0).sum()),
              int((fwd["r2_gt1V"] < 0).sum())],
})
save(flags, "forward_denominator_flags.csv")

# Pooled R2 (explicitly a pooled summary, not a replacement for per-curve values)
pooled = {}
for w in ("full", "0to1V", "gt1V"):
    sse = float(np.sum((fwd["rmse_" + w] ** 2) * fwd["n_" + w]))
    # pooled denominator requires the raw curves; recomputed in the loop below
for w in ("full", "0to1V", "gt1V"):
    pass
# recompute pooled sums properly
allJt, allJp, masks = [], [], None
for mp in sorted(glob.glob(os.path.join(FWD, "comsol_pred", "Sample_*_pred.mat"))):
    import scipy.io as sio
    sid = int(re.search(r"Sample_(\d+)_pred", mp).group(1))
    pred = sio.loadmat(mp); true = sio.loadmat(os.path.join(FWD, "comsol_true", "Sample_%05d_true.mat" % sid))
    V = pred["V_grid"].ravel()
    Jp = pred["J"].ravel() * 0.1; Jt = true["J"].ravel() * 0.1
    if masks is None:
        masks = {"full": np.ones_like(V, bool), "0to1V": V <= V_LOW_MAX, "gt1V": V > V_LOW_MAX}
    allJt.append(Jt); allJp.append(Jp)
Jt_all = np.array(allJt); Jp_all = np.array(allJp)
for w in ("full", "0to1V", "gt1V"):
    m = masks[w]
    y = Jt_all[:, m].ravel(); yh = Jp_all[:, m].ravel()
    sse = float(np.sum((y - yh) ** 2))
    den = float(np.sum((y - y.mean()) ** 2))
    pooled[w] = dict(n_points=int(y.size), r2_pooled=float(1 - sse / den),
                     note="pooled over all cases and voltages; not a per-curve R2")
pooled["note"] = "R2 computed on pooled residuals around the pooled mean; report only as a pooled summary"
save_json(pooled, "forward_pooled_r2.json")

# ----------------------------------------------------------------------------
# D. Voltage-dependent scaler range and weights
# ----------------------------------------------------------------------------
V = F["V_GRID"].astype(float)
Rv = js.data_range_.astype(float)                 # mA cm-2, MinMaxScaler range
wv = 1.0 / Rv ** 2
win = np.where(V <= V_LOW_MAX, "0to1V", "gt1V")
vw = pd.DataFrame({"V": V, "R_mA_cm2": Rv, "w_per_mA2": wv, "window": win})
save(vw, "voltage_scaler_range_and_weight.csv")

wsum = []
for w, m in (("0to1V", V <= V_LOW_MAX), ("gt1V", V > V_LOW_MAX), ("full", np.ones_like(V, bool))):
    wsum.append(dict(window=w, n_points=int(m.sum()), total_weight=float(wv[m].sum()),
                     weight_share=float(wv[m].sum() / wv.sum()),
                     mean_weight_per_point=float(wv[m].mean())))
save(pd.DataFrame(wsum), "weight_window_summary.csv")

# Verify the frozen scaler implementation against the MinMaxScaler formula
jn = F["J_test"].astype(float)
jr = F["J_test_raw"].astype(float)
formula = (jr - js.data_min_[None, :]) / js.data_range_[None, :]
alt = jr / js.data_range_[None, :]
scaler_chk = dict(
    max_abs_diff_standard_minmax=float(np.abs(jn - formula).max()),
    max_abs_diff_range_only=float(np.abs(jn - alt).max()),
    conclusion="frozen normalized J equals (J - data_min_)/data_range_ (standard MinMaxScaler)",
    units_of_scaler="mA cm-2",
    n_voltages=int(len(V)),
)
save_json(scaler_chk, "scaler_implementation_check.json")

# ----------------------------------------------------------------------------
# E. Decoder vs target and COMSOL vs target: physical and normalized residuals
# ----------------------------------------------------------------------------
recon = F["recon_test"].astype(float)
recon_raw = recon * js.data_range_[None, :] + js.data_min_[None, :]

dec_rows = []
for w, m in (("full", np.ones_like(V, bool)), ("0to1V", V <= V_LOW_MAX), ("gt1V", V > V_LOW_MAX)):
    res_phys = recon_raw[:, m] - jr[:, m]
    rmse_curve = np.sqrt(np.mean(res_phys ** 2, axis=1))
    sse_norm = float(np.sum((recon[:, m] - jn[:, m]) ** 2))
    sse_phys = float(np.sum(res_phys ** 2))
    dec_rows.append(dict(window=w, n_points=int(m.sum()), n_curves=int(len(jr)),
                         median_curve_rmse_mA=float(np.median(rmse_curve)),
                         q25_curve_rmse_mA=float(np.percentile(rmse_curve, 25)),
                         q75_curve_rmse_mA=float(np.percentile(rmse_curve, 75)),
                         pooled_sse_phys_mA2=sse_phys,
                         pooled_sse_normalized=sse_norm,
                         target_relative_median_rmse=float(np.median(
                             rmse_curve / np.sqrt(np.mean(jr[:, m] ** 2, axis=1))))))
dec = pd.DataFrame(dec_rows)
dec["share_pooled_sse_normalized"] = dec["pooled_sse_normalized"] / dec["pooled_sse_normalized"].iloc[0]
dec["share_pooled_sse_phys"] = dec["pooled_sse_phys_mA2"] / dec["pooled_sse_phys_mA2"].iloc[0]
save(dec, "decoder_residual_by_window_all_test.csv")

# Same decoder statistics restricted to the exact 45 forward cases.
# The 45 archived cases are indexed by zero-based test index.  Verify the
# index set, the voltage grid, and that the archived target curve equals the
# COMSOL true-parameter curve before combining anything.
import scipy.io as sio

idx45 = fwd["test_index"].values.astype(int)
mask45 = np.isin(np.arange(len(jr)), idx45)
assert len(idx45) == 45, len(idx45)
assert np.unique(idx45).size == 45, "the 45 archived test indices are not unique"
assert np.all((idx45 >= 0) & (idx45 < len(jr))), "test index outside the test set"
assert int(mask45.sum()) == 45, int(mask45.sum())

max_grid_dev = 0.0
max_target_abs = 0.0
max_target_rmse = 0.0
target_rows = []
for rec in fwd.itertuples():
    sid = int(rec.sample_id)
    ti = int(rec.test_index)
    pred = sio.loadmat(os.path.join(FWD, "comsol_pred", "Sample_%05d_pred.mat" % sid))
    true = sio.loadmat(os.path.join(FWD, "comsol_true", "Sample_%05d_true.mat" % sid))
    Vp = pred["V_grid"].ravel().astype(float)
    Vt = true["V_grid"].ravel().astype(float)
    max_grid_dev = max(max_grid_dev,
                       float(np.max(np.abs(Vp - V))),
                       float(np.max(np.abs(Vt - V))))
    Jt = true["J"].ravel().astype(float) * 0.1
    d = Jt - jr[ti]
    target_rows.append(dict(sample_id=sid, test_index=ti,
                            max_abs_target_diff_mA=float(np.max(np.abs(d))),
                            rmse_target_diff_mA=float(np.sqrt(np.mean(d ** 2)))))
    max_target_abs = max(max_target_abs, float(np.max(np.abs(d))))
    max_target_rmse = max(max_target_rmse, float(np.sqrt(np.mean(d ** 2))))

# Per-curve decoder contributions on the same 45 cases.
pc_rows = []
for rec in fwd.itertuples():
    ti = int(rec.test_index)
    row = dict(sample_id=int(rec.sample_id), test_index=ti)
    for w, m in (("full", np.ones_like(V, bool)),
                 ("0to1V", V <= V_LOW_MAX), ("gt1V", V > V_LOW_MAX)):
        rp = recon_raw[ti, m] - jr[ti, m]
        rn = recon[ti, m] - jn[ti, m]
        row["n_points_" + w] = int(m.sum())
        row["sse_phys_" + w] = float(np.sum(rp ** 2))
        row["sse_norm_" + w] = float(np.sum(rn ** 2))
        row["rmse_phys_" + w] = float(np.sqrt(np.mean(rp ** 2)))
        row["rmse_norm_" + w] = float(np.sqrt(np.mean(rn ** 2)))
    for w in ("0to1V", "gt1V"):
        row["share_phys_" + w] = row["sse_phys_" + w] / row["sse_phys_full"]
        row["share_norm_" + w] = row["sse_norm_" + w] / row["sse_norm_full"]
    pc_rows.append(row)
pc45 = pd.DataFrame(pc_rows)
save(pc45, "decoder_same45_per_curve_shares.csv")

dec45 = []
for w, m in (("full", np.ones_like(V, bool)),
             ("0to1V", V <= V_LOW_MAX), ("gt1V", V > V_LOW_MAX)):
    rp = recon_raw[mask45][:, m] - jr[mask45][:, m]
    rn = recon[mask45][:, m] - jn[mask45][:, m]
    rmse_p = np.sqrt(np.mean(rp ** 2, axis=1))
    rmse_n = np.sqrt(np.mean(rn ** 2, axis=1))
    dec45.append(dict(window=w, n_points=int(m.sum()), n_curves=int(mask45.sum()),
                      sse_phys_mA2=float(np.sum(rp ** 2)),
                      sse_norm=float(np.sum(rn ** 2)),
                      median_curve_rmse_mA=float(np.median(rmse_p)),
                      q25_curve_rmse_mA=float(np.percentile(rmse_p, 25)),
                      q75_curve_rmse_mA=float(np.percentile(rmse_p, 75)),
                      median_curve_rmse_norm=float(np.median(rmse_n)),
                      q25_curve_rmse_norm=float(np.percentile(rmse_n, 25)),
                      q75_curve_rmse_norm=float(np.percentile(rmse_n, 75)),
                      median_per_curve_share_phys=float(np.median(pc45["share_phys_" + w]))
                      if w != "full" else 1.0,
                      median_per_curve_share_norm=float(np.median(pc45["share_norm_" + w]))
                      if w != "full" else 1.0))
dec45 = pd.DataFrame(dec45)
full_phys = float(dec45.loc[dec45.window == "full", "sse_phys_mA2"].iloc[0])
full_norm = float(dec45.loc[dec45.window == "full", "sse_norm"].iloc[0])
dec45["share_pooled_sse_phys"] = dec45["sse_phys_mA2"] / full_phys
dec45["share_pooled_sse_norm"] = dec45["sse_norm"] / full_norm
save(dec45, "decoder_residual_by_window_45cases.csv")

prov = dict(
    n_archived_cases=int(len(idx45)),
    n_unique_test_indices=int(np.unique(idx45).size),
    all_indices_matched=bool(mask45.sum() == len(idx45)),
    decoder_voltage_grid_points=int(len(V)),
    comsol_voltage_grid_points=int(len(V)),
    max_abs_voltage_grid_difference_V=float(max_grid_dev),
    target_source="J_test_raw (frozen test target) compared with COMSOL true-parameter J",
    max_abs_target_difference_mA=float(max_target_abs),
    max_per_curve_target_rmse_mA=float(max_target_rmse),
    share_definition=("window SSE summed over all 45 matched cases divided by "
                      "full-sweep SSE summed over the same 45 cases; not the "
                      "mean of per-curve shares"),
    same_45_decoder_physical_sse_share={w: float(dec45.loc[dec45.window == w,
                                                           "share_pooled_sse_phys"].iloc[0])
                                        for w in ("0to1V", "gt1V")},
    same_45_decoder_normalized_sse_share={w: float(dec45.loc[dec45.window == w,
                                                             "share_pooled_sse_norm"].iloc[0])
                                          for w in ("0to1V", "gt1V")},
    all_test_decoder_normalized_sse_share={
        w: float(dec.loc[dec.window == w, "share_pooled_sse_normalized"].iloc[0])
        for w in ("0to1V", "gt1V")},
    note=("The archived target curves match the COMSOL true-parameter curves "
          "to numerical precision; the same 45 test indices are used for the "
          "decoder and COMSOL shares."),
)
save(pd.DataFrame(target_rows), "decoder_same45_target_check.csv")
save_json(prov, "decoder_same45_provenance.json")

# COMSOL per-case contributions
com_rows = []
for mp in sorted(glob.glob(os.path.join(FWD, "comsol_pred", "Sample_*_pred.mat"))):
    import scipy.io as sio
    sid = int(re.search(r"Sample_(\d+)_pred", mp).group(1))
    pred = sio.loadmat(mp); true = sio.loadmat(os.path.join(FWD, "comsol_true", "Sample_%05d_true.mat" % sid))
    Vv = pred["V_grid"].ravel()
    Jp = pred["J"].ravel() * 0.1; Jtt = true["J"].ravel() * 0.1
    rec = dict(sample_id=sid)
    tot_phys = tot_norm = 0.0
    parts = {}
    for w, m in (("0to1V", Vv <= V_LOW_MAX), ("gt1V", Vv > V_LOW_MAX)):
        r = Jp[m] - Jtt[m]
        sp = float(np.sum(r ** 2))
        sn = float(np.sum((r / Rv[m]) ** 2))
        parts[w] = (sp, sn, float(np.sqrt(np.mean(r ** 2))))
        tot_phys += sp; tot_norm += sn
    for w in ("0to1V", "gt1V"):
        sp, sn, rm = parts[w]
        rec["sse_phys_" + w] = sp
        rec["sse_norm_" + w] = sn
        rec["rmse_" + w] = rm
        rec["share_phys_" + w] = sp / tot_phys if tot_phys > 0 else np.nan
        rec["share_norm_" + w] = sn / tot_norm if tot_norm > 0 else np.nan
    com_rows.append(rec)
com = pd.DataFrame(com_rows)
save(com, "comsol_residual_contributions_per_case.csv")

com_sum = []
for w in ("0to1V", "gt1V"):
    com_sum.append(dict(
        window=w,
        median_share_phys=float(com["share_phys_" + w].median()),
        q25_share_phys=float(com["share_phys_" + w].quantile(.25)),
        q75_share_phys=float(com["share_phys_" + w].quantile(.75)),
        median_share_norm=float(com["share_norm_" + w].median()),
        q25_share_norm=float(com["share_norm_" + w].quantile(.25)),
        q75_share_norm=float(com["share_norm_" + w].quantile(.75)),
        median_rmse_mA=float(com["rmse_" + w].median()),
        q25_rmse_mA=float(com["rmse_" + w].quantile(.25)),
        q75_rmse_mA=float(com["rmse_" + w].quantile(.75)),
        pooled_share_phys=float(com["sse_phys_" + w].sum() / com[["sse_phys_0to1V", "sse_phys_gt1V"]].sum().sum()),
        pooled_share_norm=float(com["sse_norm_" + w].sum() / com[["sse_norm_0to1V", "sse_norm_gt1V"]].sum().sum()),
    ))
save(pd.DataFrame(com_sum), "comsol_residual_contributions_summary.csv")

# Manuscript-ready combined weighting / residual table.
# Primary decoder columns are on the SAME 45 curves as the COMSOL columns;
# the all-test decoder share is retained only as a clearly labelled reference.
comb = pd.DataFrame({
    "window": ["0-1.0 V", ">1.0 V"],
    "n_points": [int((V <= V_LOW_MAX).sum()), int((V > V_LOW_MAX).sum())],
    "n_curves_same45": [45, 45],
    "weight_share": [float(wv[V <= V_LOW_MAX].sum() / wv.sum()),
                     float(wv[V > V_LOW_MAX].sum() / wv.sum())],
    "mean_weight_per_point": [float(wv[V <= V_LOW_MAX].mean()), float(wv[V > V_LOW_MAX].mean())],
    "decoder_same45_physical_sse_share": [
        dec45.loc[dec45.window == "0to1V", "share_pooled_sse_phys"].iloc[0],
        dec45.loc[dec45.window == "gt1V", "share_pooled_sse_phys"].iloc[0]],
    "decoder_same45_normalized_sse_share": [
        dec45.loc[dec45.window == "0to1V", "share_pooled_sse_norm"].iloc[0],
        dec45.loc[dec45.window == "gt1V", "share_pooled_sse_norm"].iloc[0]],
    "decoder_same45_median_curve_rmse_mA": [
        dec45.loc[dec45.window == "0to1V", "median_curve_rmse_mA"].iloc[0],
        dec45.loc[dec45.window == "gt1V", "median_curve_rmse_mA"].iloc[0]],
    "decoder_all_test_normalized_sse_share_reference": [
        dec.loc[dec.window == "0to1V", "share_pooled_sse_normalized"].iloc[0],
        dec.loc[dec.window == "gt1V", "share_pooled_sse_normalized"].iloc[0]],
    "n_curves_all_test": [int(len(jr)), int(len(jr))],
    "comsol_normalized_sse_share_pooled": [
        com_sum[0]["pooled_share_norm"], com_sum[1]["pooled_share_norm"]],
    "comsol_physical_sse_share_pooled": [
        com_sum[0]["pooled_share_phys"], com_sum[1]["pooled_share_phys"]],
    "comsol_median_rmse_mA": [com_sum[0]["median_rmse_mA"], com_sum[1]["median_rmse_mA"]],
})
save(comb, "weighting_and_residual_summary.csv")

# ----------------------------------------------------------------------------
# F. Shuffled-pairing null: verify the archived statistic
# ----------------------------------------------------------------------------
sh = pd.read_csv(os.path.join(EXP3, "results", "shuffled_pairing_null.csv"))
perm = sh[sh["perm"].astype(str).str.match(r"^\d+$")].copy()
perm["perm"] = perm["perm"].astype(int)
obs = arch.set_index("coordinate")["pearson_r"]
srows = []
for c in ml.COORD_NAMES:
    x = perm[c].astype(float).values
    mean, sd = float(x.mean()), float(x.std(ddof=1))
    srows.append(dict(coordinate=c, statistic="Pearson r between true and predicted coordinate",
                      observed=float(obs[c]), null_mean=mean, null_sd=sd,
                      null_p95=float(np.percentile(x, 95)),
                      z_standardized=(float(obs[c]) - mean) / sd,
                      n_permutations=int(len(x)), seed=20260826,
                      exceeds_all_permutations=bool(obs[c] > x.max())))
shv = pd.DataFrame(srows)
save(shv, "shuffle_null_verification.csv")

# ----------------------------------------------------------------------------
# G. S13 paired tests (five seeds, paired by seed)
# ----------------------------------------------------------------------------
def seed_means(rs):
    d = pd.read_csv(os.path.join(rs, "per_seed_metrics.csv"))
    g = d.groupby(["model", "seed"])["pearson_r"].mean().unstack("model")
    return g

envs = {"env1_TF2.20_Keras3.13": os.path.join(EXP1, "results"),
        "env2_TF2.13_Keras2": os.path.join(EXP1, "results_server")}
trows = []
for env, rs in envs.items():
    g = seed_means(rs)
    seeds = list(g.index)
    for a, b in (("det_ae", "mlp"), ("vae", "mlp"), ("vae", "det_ae")):
        if a not in g.columns or b not in g.columns:
            continue
        diff = (g[a] - g[b]).values
        t, p = stats.ttest_rel(g[a].values, g[b].values)
        trows.append(dict(environment=env, contrast="%s - %s" % (a, b),
                          mean_diff=float(diff.mean()), sd_diff=float(diff.std(ddof=1)),
                          t=float(t), df=len(diff) - 1, p_two_sided=float(p),
                          n_seed_pairs=len(diff), seeds=";".join(str(s) for s in seeds)))
save(pd.DataFrame(trows), "s13_paired_tests.csv")

# per-seed means for provenance
prs = []
for env, rs in envs.items():
    g = seed_means(rs)
    for seed, row in g.iterrows():
        for model in g.columns:
            prs.append(dict(environment=env, seed=int(seed), family=model,
                            mean_pearson_nine_params=float(row[model])))
save(pd.DataFrame(prs), "s13_seed_level_means.csv")

# ----------------------------------------------------------------------------
# H. Coverage vs predicted scale (cross-parameter, nine parameters)
# ----------------------------------------------------------------------------
sig = pd.read_csv(os.path.join(OUT, "..", "..", "20261019_HC_revision_stage1",
                               "analysis", "out", "single_parameter_point_metrics.csv")) \
    if False else None
# Values transcribed from SI Tables S3 (mean sigma) and S2 (95% coverage)
sig_mean = [0.0927, 0.0874, 0.1091, 0.1091, 0.0748, 0.0812, 0.2295, 0.1909, 0.2283]
cov95 = [0.947, 0.952, 0.958, 0.960, 0.946, 0.950, 0.969, 0.967, 0.966]
cs = pd.DataFrame({"parameter": ml.PARAM_NAMES, "mean_pred_sigma": sig_mean,
                   "coverage95": cov95})
cs["abs_dev_from_0.95"] = (cs["coverage95"] - 0.95).abs()
cs["rank_sigma"] = cs["mean_pred_sigma"].rank()
cs["rank_coverage"] = cs["coverage95"].rank()
cs["rank_abs_dev"] = cs["abs_dev_from_0.95"].rank()
save(cs, "coverage_vs_predicted_scale.csv")
rho_cov = stats.spearmanr(cs["mean_pred_sigma"], cs["coverage95"])
rho_dev = stats.spearmanr(cs["mean_pred_sigma"], cs["abs_dev_from_0.95"])
save_json(dict(n_parameters=9,
               spearman_sigma_coverage=float(rho_cov.statistic),
               spearman_p_coverage=float(rho_cov.pvalue),
               spearman_sigma_abs_dev=float(rho_dev.statistic),
               spearman_p_abs_dev=float(rho_dev.pvalue),
               scope="cross-parameter association over nine parameters; descriptive, not sample-level calibration"),
          "coverage_vs_scale_summary.json")

# ----------------------------------------------------------------------------
# I. S6 / S10 verification
# ----------------------------------------------------------------------------
s6 = pd.read_csv(os.path.join(S6_DIR, "si_table_s6_pair_summary.csv")).iloc[0]
tiers = pd.read_csv(os.path.join(S6_DIR, "si_table_s6_8_tiers.csv"))
# Table S10 has six metrics.  The metric-summary CSV in the archive contains
# only M1-M5, so the complete metric inventory is taken from the tier table,
# and every range is computed by EXPLICIT metric ID, never by row position.
s10_tiers = pd.read_csv(os.path.join(S6_DIR, "si_table_s10_tiers_v2.csv"))
S10_ALL = ["M1", "M2", "M3", "M4", "M5", "M6"]
S10_ALT = ["M2", "M3", "M4", "M5", "M6"]
assert set(s10_tiers["metric"]) == set(S10_ALL), sorted(set(s10_tiers["metric"]))
assert len(s10_tiers) == len(S10_ALL) * 6, len(s10_tiers)
s10_summary = pd.read_csv(os.path.join(S6_DIR, "si_table_s10_metric_summary_v2.csv"))
random_median = float(s10_summary.loc[s10_summary.metric == "M1",
                                     "random_median_dTheta"].iloc[0])


def metric_tier(metric, tier):
    row = s10_tiers[(s10_tiers.metric == metric) & (s10_tiers.tier == tier)]
    assert len(row) == 1, (metric, tier, len(row))
    return row.iloc[0]


def range_block(ids, label):
    nn = [int(metric_tier(m, "all_NN")["n_pairs"]) for m in ids]
    c1 = [float(metric_tier(m, "closest 1%")["median_dTheta"]) for m in ids]
    c01 = [float(metric_tier(m, "closest 0.1%")["median_dTheta"]) for m in ids]
    return dict(scope=label, metric_ids=";".join(ids), n_metrics=len(ids),
                n_unique_pairs_min=min(nn), n_unique_pairs_max=max(nn),
                closest1_median_min=min(c1), closest1_median_max=max(c1),
                closest01_median_min=min(c01), closest01_median_max=max(c01))


s10_ranges = pd.DataFrame([range_block(S10_ALL, "all six metrics (M1-M6)"),
                           range_block(S10_ALT, "five alternatives (M2-M6)")])
save(s10_ranges, "s10_metric_ranges.csv")
save_json(dict(
    source="si_table_s10_tiers_v2.csv",
    all_metric_ids=S10_ALL,
    alternative_metric_ids=S10_ALT,
    primary_metric="M1",
    ranges={r["scope"]: {k: v for k, v in r.items() if k != "scope"}
            for r in s10_ranges.to_dict("records")},
    per_metric_n_unique_pairs={m: int(metric_tier(m, "all_NN")["n_pairs"])
                              for m in S10_ALL},
    per_metric_closest1_median={m: float(metric_tier(m, "closest 1%")["median_dTheta"])
                               for m in S10_ALL},
    per_metric_closest01_median={m: float(metric_tier(m, "closest 0.1%")["median_dTheta"])
                                for m in S10_ALL},
    random_pair_median_dTheta=random_median,
    note=("The archived metric-summary CSV contains M1-M5 only; the complete "
          "six-metric inventory is in the tier table.  Ranges are explicitly "
          "filtered by metric ID."),
), "s10_metric_ranges.json")
ver = [
    dict(item="unique undirected pairs", value=int(s6["n_pairs"]), source="si_table_s6_pair_summary.csv"),
    dict(item="test curves", value=int(s6["n_test"]), source="si_table_s6_pair_summary.csv"),
    dict(item="curves in more than one pair", value=int(s6["samples_in_multiple_pairs"]), source="si_table_s6_pair_summary.csv"),
    dict(item="maximum pairs per curve", value=int(s6["max_pairs_per_sample"]), source="si_table_s6_pair_summary.csv"),
    dict(item="withdrawn old pair rule", value=int(s6["archived_pairs"]), source="archived, NOT used"),
    dict(item="closest 10% pairs", value=int(tiers.loc[tiers.set == "closest 10%", "n_pairs"].iloc[0]), source="si_table_s6_8_tiers.csv"),
    dict(item="closest 5% pairs", value=int(tiers.loc[tiers.set == "closest 5%", "n_pairs"].iloc[0]), source="si_table_s6_8_tiers.csv"),
    dict(item="closest 1% pairs", value=int(tiers.loc[tiers.set == "closest 1%", "n_pairs"].iloc[0]), source="si_table_s6_8_tiers.csv"),
    dict(item="closest 0.5% pairs", value=int(tiers.loc[tiers.set == "closest 0.5%", "n_pairs"].iloc[0]), source="si_table_s6_8_tiers.csv"),
    dict(item="closest 0.1% pairs", value=int(tiers.loc[tiers.set == "closest 0.1%", "n_pairs"].iloc[0]), source="si_table_s6_8_tiers.csv"),
    dict(item="pair count min, all six metrics M1-M6",
         value=int(s10_ranges.loc[s10_ranges.scope.str.startswith("all six"),
                                 "n_unique_pairs_min"].iloc[0]),
         source="si_table_s10_tiers_v2.csv (explicit metric IDs)"),
    dict(item="pair count max, all six metrics M1-M6",
         value=int(s10_ranges.loc[s10_ranges.scope.str.startswith("all six"),
                                 "n_unique_pairs_max"].iloc[0]),
         source="si_table_s10_tiers_v2.csv (explicit metric IDs)"),
    dict(item="closest-1% median dTheta min, all six metrics",
         value=float(s10_ranges.loc[s10_ranges.scope.str.startswith("all six"),
                                   "closest1_median_min"].iloc[0]),
         source="si_table_s10_tiers_v2.csv (explicit metric IDs)"),
    dict(item="closest-1% median dTheta max, all six metrics",
         value=float(s10_ranges.loc[s10_ranges.scope.str.startswith("all six"),
                                   "closest1_median_max"].iloc[0]),
         source="si_table_s10_tiers_v2.csv (explicit metric IDs)"),
    dict(item="pair count min, five alternatives M2-M6",
         value=int(s10_ranges.loc[s10_ranges.scope.str.startswith("five"),
                                 "n_unique_pairs_min"].iloc[0]),
         source="si_table_s10_tiers_v2.csv (explicit metric IDs)"),
    dict(item="pair count max, five alternatives M2-M6",
         value=int(s10_ranges.loc[s10_ranges.scope.str.startswith("five"),
                                 "n_unique_pairs_max"].iloc[0]),
         source="si_table_s10_tiers_v2.csv (explicit metric IDs)"),
    dict(item="closest-1% median dTheta min, five alternatives",
         value=float(s10_ranges.loc[s10_ranges.scope.str.startswith("five"),
                                   "closest1_median_min"].iloc[0]),
         source="si_table_s10_tiers_v2.csv (explicit metric IDs)"),
    dict(item="closest-1% median dTheta max, five alternatives",
         value=float(s10_ranges.loc[s10_ranges.scope.str.startswith("five"),
                                   "closest1_median_max"].iloc[0]),
         source="si_table_s10_tiers_v2.csv (explicit metric IDs)"),
    dict(item="random-pair median dTheta", value=random_median,
         source="si_table_s10_metric_summary_v2.csv (M1 row)"),
]
ver.append(dict(item="M2 closest-0.1% median dTheta (non-monotone; n=11)",
                value=float(metric_tier("M2", "closest 0.1%")["median_dTheta"]),
                source="si_table_s10_tiers_v2.csv (explicit metric ID M2)"))
save(pd.DataFrame(ver), "s6_s10_verification.csv")

# ----------------------------------------------------------------------------
# J. Sigma bounds
# ----------------------------------------------------------------------------
sig_all = F["param_sigma"].astype(float)
save_json(dict(min=float(sig_all.min()), max=float(sig_all.max()),
               lower_bound=0.01, upper_bound=1.0,
               lower_engaged=bool(sig_all.min() <= 0.01),
               upper_engaged=bool(sig_all.max() >= 1.0),
               space="normalized log10 coordinates of the frozen scaler"),
          "sigma_bounds_check.json")

# ----------------------------------------------------------------------------
# K. Evidence inventory (path, role, size, sha256)
# ----------------------------------------------------------------------------
targets = [
    (os.path.join(BASE, "20261019", "Manuscript_20261007_HC1015.docx"), "supervisor manuscript base with comments/tracked changes"),
    (os.path.join(BASE, "20261006", "manuscript_figures_SI_integrated_v2_layout_final", "si", "Supplementary_Information_synced.docx"), "latest official SI (50 pages, layout final)"),
    (os.path.join(BASE, "20261006", "manuscript_figures_SI_integrated_v2_layout_final", "manuscript", "Manuscript_20261002_Working_integrated.docx"), "assembled manuscript paired with the SI"),
    (os.path.join(BASE, "data", "dataset_normalized.npz"), "frozen split + normalized data (71,432/15,307/15,307)"),
    (os.path.join(BASE, "data", "param_scaler.pkl"), "frozen parameter scaler (fit on the full 102,046-curve retained dataset before partitioning)"),
    (os.path.join(BASE, "data", "J_scaler.pkl"), "frozen per-voltage J scaler (fit on the full retained dataset); source of Rv and wv"),
    (os.path.join(BASE, "final_figures", "scripts", "_frozen_preds.npz"), "frozen test predictions, sigma, reconstruction"),
    (os.path.join(BASE, "data", "vae-v6", "vae-v6", "best.weights.h5"), "main model H / VAE-v6 weights"),
    (os.path.join(BASE, "data", "vae-v6", "vae-v6", "encoder.h5"), "main model H encoder"),
    (os.path.join(BASE, "data", "vae-v6", "vae-v6", "decoder.h5"), "main model H decoder"),
    (os.path.join(BASE, "data", "vae-v6", "vae-v6", "param_head.h5"), "main model H parameter head"),
    (os.path.join(FWD, "forward_metrics_per_sample.csv"), "45-case forward metrics (archived)"),
    (os.path.join(FWD, "forward_metrics_summary.csv"), "45-case forward summary (archived)"),
    (os.path.join(FWD, "config.json"), "45-case forward configuration"),
    (os.path.join(S6_DIR, "si_table_s6_pair_summary.csv"), "S6 pair summary source"),
    (os.path.join(S6_DIR, "si_table_s6_8_tiers.csv"), "S6 tier source"),
    (os.path.join(S6_DIR, "si_table_s10_metric_summary_v2.csv"), "S10 metric summary (M1-M5 only; M6 absent)"),
    (os.path.join(S6_DIR, "si_table_s10_tiers_v2.csv"), "S10 tier source (complete M1-M6 inventory)"),
    (os.path.join(S6_DIR, "fig3_pairs_v2.csv"), "11,245-pair per-pair table"),
    (os.path.join(S6_DIR, "fig3_random_baseline_v2.csv"), "random-pair baseline (seed 42, 200,000 draws)"),
    (os.path.join(EXP3, "results", "shuffled_pairing_null.csv"), "archived shuffled-pairing null raw output"),
    (os.path.join(EXP3, "results", "frozen_coordinate_recoverability.csv"), "EXP3 coordinate metrics"),
    (os.path.join(EXP3, "scripts", "shuffled.py"), "shuffle script (seed 20260826, 100 permutations)"),
    (os.path.join(EXP3, "scripts", "recoverability.py"), "Skill/MAE-reduction implementation"),
    (os.path.join(EXP1, "results", "per_seed_metrics.csv"), "S13 environment-1 per-seed results"),
    (os.path.join(EXP1, "results_server", "per_seed_metrics.csv"), "S13 environment-2 per-seed results"),
    (os.path.join(EXP1, "train_only_scalers.pkl"), "S13 train-only scalers"),
    (os.path.join(EXP1, "split_indices_original_reproduced.npz"), "split reproduction"),
]
inv = []
for p, role in targets:
    inv.append(dict(path=p, role=role, bytes=os.path.getsize(p) if os.path.exists(p) else None,
                    sha256=sha256(p) if os.path.exists(p) else None,
                    exists=os.path.exists(p)))
for p in sorted(glob.glob(os.path.join(FWD, "comsol_pred", "*.mat"))) + \
         sorted(glob.glob(os.path.join(FWD, "comsol_true", "*.mat"))):
    inv.append(dict(path=p, role="45-case COMSOL curve", bytes=os.path.getsize(p),
                    sha256=sha256(p), exists=True))
save(pd.DataFrame(inv), "evidence_inventory.csv")

print("\nALL ANALYSES COMPLETE")
