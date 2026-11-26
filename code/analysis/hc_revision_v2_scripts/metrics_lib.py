# -*- coding: utf-8 -*-
"""Shared loaders and metric definitions for the HC1015 revision (read-only on frozen data)."""
import os
import pickle

import numpy as np
import pandas as pd

BASE = r"E:\project\work1"
DATA_NPZ = os.path.join(BASE, "data", "dataset_normalized.npz")
FROZEN_NPZ = os.path.join(BASE, "final_figures", "scripts", "_frozen_preds.npz")
SCALER_PKL = os.path.join(BASE, "data", "param_scaler.pkl")
J_SCALER_PKL = os.path.join(BASE, "data", "J_scaler.pkl")

PARAM_NAMES = ["mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk",
               "Nc_eff_pvk", "Nv_eff_pvk", "tau_ETL", "tau_HTL", "rad_c"]
FAMILIES = [("mobility", 0, 1), ("lifetime", 2, 3), ("DOS", 4, 5)]
COORD_NAMES = ["a_mu", "r_mu", "a_tau", "r_tau", "a_D", "r_D"]


def load():
    f = np.load(FROZEN_NPZ, allow_pickle=True)
    d = np.load(DATA_NPZ, allow_pickle=True)
    with open(SCALER_PKL, "rb") as fh:
        sc = pickle.load(fh)["scaler"]
    with open(J_SCALER_PKL, "rb") as fh:
        js = pickle.load(fh)
    L_true = np.log10(f["params_test_raw"].astype(np.float64))
    L_pred = np.log10(f["params_pred_phys"].astype(np.float64))
    L_train = d["params_train"].astype(np.float64) * sc.data_range_ + sc.data_min_
    assert np.max(np.abs(L_true - (f["params_test"] * sc.data_range_ + sc.data_min_))) < 1e-12
    return dict(f=f, d=d, sc=sc, js=js, L_true=L_true, L_pred=L_pred, L_train=L_train)


def coords(L):
    """(N,6) a/r coordinates in physical log10; column order COORD_NAMES."""
    return np.column_stack([
        0.5 * (L[:, 0] + L[:, 1]), L[:, 0] - L[:, 1],
        0.5 * (L[:, 2] + L[:, 3]), L[:, 2] - L[:, 3],
        0.5 * (L[:, 4] + L[:, 5]), L[:, 4] - L[:, 5]])


def metrics(y_true, y_pred, y_train):
    """All point metrics for one coordinate. Returns a dict.

    Definitions (all in the same physical log10 coordinate):
      RMSE                   sqrt(mean((y-yhat)^2))
      MAE                    mean(|y-yhat|)
      Pearson                corr(y, yhat)
      Skill_MSE              1 - SSE_model / SSE_train_mean
                             baseline = MEAN of the training partition
      R2_test                1 - SSE_model / SSE_test_mean
                             baseline = MEAN of the evaluation (test) set
      MAE_reduction          1 - MAE_model / MAE_train_median
                             baseline = MEDIAN of the training partition

    Negative values are retained. If a denominator is zero the metric is
    returned as NaN with a flag in `undefined`.
    """
    y_true = np.asarray(y_true, float)
    y_pred = np.asarray(y_pred, float)
    y_train = np.asarray(y_train, float)
    n = y_true.size
    resid = y_true - y_pred
    sse = float(np.sum(resid ** 2))
    mse = sse / n
    base_tr_mean = float(np.mean(y_train))
    base_te_mean = float(np.mean(y_true))
    base_tr_med = float(np.median(y_train))
    sse_tr = float(np.sum((y_true - base_tr_mean) ** 2))
    sse_te = float(np.sum((y_true - base_te_mean) ** 2))
    mae_model = float(np.mean(np.abs(resid)))
    mae_tr_med = float(np.mean(np.abs(y_true - base_tr_med)))
    undefined = []
    skill = 1.0 - sse / sse_tr if sse_tr > 0 else np.nan
    r2 = 1.0 - sse / sse_te if sse_te > 0 else np.nan
    mae_red = 1.0 - mae_model / mae_tr_med if mae_tr_med > 0 else np.nan
    if sse_tr <= 0:
        undefined.append("Skill_MSE: zero training-mean denominator")
    if sse_te <= 0:
        undefined.append("R2_test: zero test-mean denominator")
    if mae_tr_med <= 0:
        undefined.append("MAE_reduction: zero training-median denominator")
    rho = float(np.corrcoef(y_true, y_pred)[0, 1]) if np.std(y_true) > 0 and np.std(y_pred) > 0 else np.nan
    return dict(n=int(n), rmse=float(np.sqrt(mse)), mae=mae_model,
                pearson=rho,
                skill_mse=float(skill), r2_test=float(r2),
                mae_reduction=float(mae_red),
                train_mean=base_tr_mean, train_median=base_tr_med,
                test_mean=base_te_mean,
                sse_model=sse, sse_train_mean=sse_tr, sse_test_mean=sse_te,
                mae_train_median_baseline=mae_tr_med,
                undefined="; ".join(undefined))


def iqr(x):
    x = np.asarray(x, float)
    q1, q2, q3 = np.percentile(x, [25, 50, 75])
    return float(q1), float(q2), float(q3)
