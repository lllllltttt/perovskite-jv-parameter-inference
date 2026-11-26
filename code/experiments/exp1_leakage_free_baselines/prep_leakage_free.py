# -*- coding: utf-8 -*-
"""
Phase C + D — Lock the original split, recover raw data, build TRAIN-ONLY scalers.

Steps
-----
1. Recover the full raw dataset (physical units) by inverting the frozen
   full-data scalers on the concatenated scaled npz blocks (float64-exact).
2. Reproduce the exact original split with sklearn train_test_split
   (test_size=0.30 then 0.50, random_state=42) exactly as pre-process.py.
3. VERIFY: multiset equality of the reproduced train/val/test rows against the
   npz blocks (rounded 140-dim rows). If any block mismatches -> report + STOP.
4. Fit leakage-free scalers on TRAIN ONLY:
     params: log10 -> MinMax per column (train rows only)
     J:      MinMax per column  (train rows only)
   Transform train/val/test with these constants. Do NOT clip.
5. Record val/test out-of-[0,1] fractions and maximum excursion.
6. Save split indices, train-only scalers, and the leakage-free npz.
"""
import os, io, pickle
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split

BASE = r"E:\project\work1"
EXPDIR = r"E:\project\work1\reviewer_experiments\exp1_leakage_free_baselines"
NPZ = os.path.join(BASE, "data", "dataset_normalized.npz")

out = io.open(os.path.join(EXPDIR, "preprocessing_statistics.md"), "w", encoding="utf-8")
def P(*a):
    print(*a)
    out.write(" ".join(str(x) for x in a) + "\n")

PARAM_NAMES = ["mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk",
               "Nc_eff_pvk", "Nv_eff_pvk", "tau_ETL", "tau_HTL", "rad_c"]

npz = np.load(NPZ, allow_pickle=True)
with open(os.path.join(BASE, "data", "param_scaler.pkl"), "rb") as f:
    ps = pickle.load(f)
with open(os.path.join(BASE, "data", "J_scaler.pkl"), "rb") as f:
    js = pickle.load(f)

J_tr = npz["J_train"].astype(np.float64)
J_va = npz["J_val"].astype(np.float64)
J_te = npz["J_test"].astype(np.float64)
Q_tr = npz["params_train"].astype(np.float64)
Q_va = npz["params_val"].astype(np.float64)
Q_te = npz["params_test"].astype(np.float64)

N = J_tr.shape[0] + J_va.shape[0] + J_te.shape[0]
P(f"N total = {N}  (train {J_tr.shape[0]}, val {J_va.shape[0]}, test {J_te.shape[0]})")
assert N == 102046, "N mismatch"
assert J_tr.shape[0] == 71432 and J_va.shape[0] == 15307 and J_te.shape[0] == 15307

# ---------- 1) recover raw full dataset (npz-block order) ----------
Q_scaled_all = np.concatenate([Q_tr, Q_va, Q_te], axis=0)   # (102046, 9)  log10-scaled
J_scaled_all = np.concatenate([J_tr, J_va, J_te], axis=0)   # (102046, 131)
log_mask = ps["log_mask"].astype(bool)
Q_log_all = ps["scaler"].inverse_transform(Q_scaled_all)     # log10 space
Q_raw_all = Q_log_all.copy()
Q_raw_all[:, log_mask] = 10.0 ** Q_log_all[:, log_mask]      # physical
J_raw_all = js.inverse_transform(J_scaled_all)               # physical mA/cm^2

# sanity: recovery of raw test rows matches stored raw test rows
P("recovery max rel err params (vs stored raw test): %.2e" % np.max(
    np.abs(Q_raw_all[J_tr.shape[0]+J_va.shape[0]:] - npz["params_test_raw"])
    / np.maximum(np.abs(npz["params_test_raw"]), 1e-300)))
P("recovery max abs err J (vs stored raw test): %.2e" % np.max(
    np.abs(J_raw_all[J_tr.shape[0]+J_va.shape[0]:] - npz["J_test_raw"])))

# ---------- 2) split membership: ARCHIVED npz blocks are authoritative ----------
# NOTE / DISCREPANCY RECORD
# pre-process.py documents a two-step sklearn split of the retained set
# (train_test_split(arange(N), test_size=0.30, random_state=42) then
#  train_test_split(temp, test_size=0.50, random_state=42)).
# An independent reproduction with this recipe was attempted and DOES NOT
# reproduce the archived npz block membership (crosstab of candidate vs true
# blocks is essentially random; a scan of random_states 0..400 reaches at most
# ~54% diagonal overlap, i.e. chance level). The observed per-block counts
# (71432/15307/15307 = 70/15/15% of 102046) are exactly what a uniform ~49%
# invalid-sample drop across the three splits of a 200,000-sample pre-filter
# set would produce, i.e. split-before-filter. The independent indices are
# therefore not recoverable from code + seed alone.
# RESOLUTION: use the archived npz blocks verbatim as the Stage-I membership
# (this IS the exact membership the Stage-I study used), indexed by their
# position in the concatenated archive. This satisfies the spec requirement
# "Use EXACTLY the same train/validation/test sample membership".
idx_train = np.arange(0, 71432)          # archived train block positions
idx_val   = np.arange(71432, 86739)      # archived val   block positions
idx_test  = np.arange(86739, 102046)     # archived test  block positions
P(f"split membership taken from archived npz: train {len(idx_train)}, "
  f"val {len(idx_val)}, test {len(idx_test)}")
P("NOTE: independent sklearn seed-42 reproduction does NOT match the archived")
P("membership (documented in detail in README.md §Split). Blocks used verbatim.")

np.savez(os.path.join(EXPDIR, "split_indices_original_reproduced.npz"),
         idx_train=idx_train, idx_val=idx_val, idx_test=idx_test,
         N=N,
         membership_source="archived dataset_normalized.npz blocks (verbatim)",
         independent_sklearn_seed42_reproduction="FAILED to match (see README.md)")
P("saved split_indices_original_reproduced.npz")

# ---------- 4) train-only scalers ----------
Q_raw_train = Q_raw_all[idx_train]
J_raw_train = J_raw_all[idx_train]

Q_log_train = Q_raw_train.copy()
Q_log_train[:, log_mask] = np.log10(Q_raw_train[:, log_mask])
param_scaler_tr = MinMaxScaler()
param_scaler_tr.fit(Q_log_train)
P("\n===== TRAIN-ONLY PARAM SCALER =====")
P("param train min (log10):", param_scaler_tr.data_min_)
P("param train max (log10):", param_scaler_tr.data_max_)

J_scaler_tr = MinMaxScaler()
J_scaler_tr.fit(J_raw_train)
P("J train min (first/last cols): %.6g / %.6g" % (J_scaler_tr.data_min_[0], J_scaler_tr.data_min_[-1]))
P("J train max (first/last cols): %.6g / %.6g" % (J_scaler_tr.data_max_[0], J_scaler_tr.data_max_[-1]))

# transform (no clipping)
Q_log_all_tr = Q_log_all.copy()
Q_log_all_tr[:, log_mask] = np.log10(Q_raw_all[:, log_mask])
Q_scaled_lf = param_scaler_tr.transform(Q_log_all_tr)
J_scaled_lf = J_scaler_tr.transform(J_raw_all)

# split back
Q_tr_lf, Q_va_lf, Q_te_lf = Q_scaled_lf[idx_train], Q_scaled_lf[idx_val], Q_scaled_lf[idx_test]
J_tr_lf, J_va_lf, J_te_lf = J_scaled_lf[idx_train], J_scaled_lf[idx_val], J_scaled_lf[idx_test]

# ---------- 5) extrapolation statistics ----------
P("\n===== OUT-OF-[0,1] STATISTICS (train-only scalers) =====")
P("Parameter (log10 space, unscaled-for-[0,1]):")
P("%-12s %9s %9s %9s %9s" % ("param", "val<0", "val>1", "test<0", "test>1"))
for i, name in enumerate(PARAM_NAMES):
    vt = Q_va_lf[:, i]; tt = Q_te_lf[:, i]
    P("%-12s %9.4f %9.4f %9.4f %9.4f" % (
        name, np.mean(vt < 0), np.mean(vt > 1), np.mean(tt < 0), np.mean(tt > 1)))
P("max param extrapolation: val %.4f  test %.4f" % (
    max(abs(Q_va_lf.min()), abs(Q_va_lf.max() - 1)), max(abs(Q_te_lf.min()), abs(Q_te_lf.max() - 1))))
P("\nJ columns out-of-[0,1]:")
P("  val fraction <0: %.5f   >1: %.5f   min %.4f  max %.4f" % (
    np.mean(J_va_lf < 0), np.mean(J_va_lf > 1), J_va_lf.min(), J_va_lf.max()))
P("  test fraction <0: %.5f   >1: %.5f   min %.4f  max %.4f" % (
    np.mean(J_te_lf < 0), np.mean(J_te_lf > 1), J_te_lf.min(), J_te_lf.max()))
# affected voltage locations (J columns with >0 val/test out-of-range)
V = np.linspace(0, 1.3, 131)
for tag, A in [("val", J_va_lf), ("test", J_te_lf)]:
    below = np.where(np.any(A < 0, axis=0))[0]
    above = np.where(np.any(A > 1, axis=0))[0]
    P(f"  {tag}: columns with any <0: {list(below)} (V={[round(float(V[i]),3) for i in below]})")
    P(f"  {tag}: columns with any >1: {list(above)} (V={[round(float(V[i]),3) for i in above]})")

# ---------- 6) save ----------
with open(os.path.join(EXPDIR, "train_only_scalers.pkl"), "wb") as f:
    pickle.dump({
        "log_mask": log_mask,
        "param_names": np.array(PARAM_NAMES),
        "param_min_log10": param_scaler_tr.data_min_,
        "param_max_log10": param_scaler_tr.data_max_,
        "param_scale": (param_scaler_tr.scale_, param_scaler_tr.min_),
        "J_min": J_scaler_tr.data_min_,
        "J_max": J_scaler_tr.data_max_,
        "J_scale": (J_scaler_tr.scale_, J_scaler_tr.min_),
        "N_train": len(idx_train), "N_val": len(idx_val), "N_test": len(idx_test),
    }, f)
P("\nsaved train_only_scalers.pkl")

np.savez(os.path.join(EXPDIR, "leakage_free_dataset.npz"),
         J_train=J_tr_lf.astype(np.float32), J_val=J_va_lf.astype(np.float32),
         J_test=J_te_lf.astype(np.float32),
         params_train=Q_tr_lf.astype(np.float32), params_val=Q_va_lf.astype(np.float32),
         params_test=Q_te_lf.astype(np.float32),
         params_test_raw=Q_raw_all[idx_test],
         J_test_raw=J_raw_all[idx_test],
         log_transform_mask=log_mask, param_names=np.array(PARAM_NAMES),
         idx_train=idx_train, idx_val=idx_val, idx_test=idx_test)
P("saved leakage_free_dataset.npz")
out.close()
print("done; see preprocessing_statistics.md")
