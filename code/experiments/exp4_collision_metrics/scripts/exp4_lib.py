# -*- coding: utf-8 -*-
"""
EXP4 shared library — collision-metric robustness.

Analysis-only: reads the frozen normalized dataset and the frozen collision
analysis outputs. No model is loaded, nothing trains, no COMSOL, and nothing
outside this experiment directory is written.

Distance definitions (all on the same N=15307 test set; d_Theta is FIXED):
  M1  normalized full-curve (0-1.3 V) RMSE, 131 pts     (original metric)
  M2  physical-current full-curve RMSE, 131 pts (mA/cm^2)
  M3  physical full-curve RMSE / 0.5*(|Jsc_i|+|Jsc_k|), 131 pts
  M4  physical 0-1.0 V RMSE, 101 pts
  M5  physical 0-1.0 V RMSE / 0.5*(|Jsc_i|+|Jsc_k|), 101 pts
  M6  optional: J/|Jsc| shape RMSE, 131 pts (supplementary only)
"""
import os
import numpy as np

BASE = r"E:\project\work1"
DATA_NPZ = os.path.join(BASE, "data", "dataset_normalized.npz")
COLL_DIR = os.path.join(BASE, "collision_analysis")
EXP4 = os.path.join(BASE, "reviewer_experiments", "exp4_collision_metric_robustness")

PARAM_NAMES = ["mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk",
               "Nc_eff_pvk", "Nv_eff_pvk", "tau_ETL", "tau_HTL", "rad_c"]
# manuscript / spec column names (rad_c == r_rad)
PARAM_OUT = ["mu_n", "mu_p", "tau_n", "tau_p", "Nc", "Nv",
             "tau_ETL", "tau_HTL", "r_rad"]

# frozen reference for Phase 0
REF_DEDUP = 7666
REF_SPEARMAN, REF_PEARSON = 0.1576, 0.0785
REF_MED_NN, REF_MED_RAND = 0.1999, 0.3490
REF_TIER_MED = {0.01: 0.1443, 0.005: 0.1337, 0.001: 0.1021}
REF_PARM_AMB = {"mu_n": 0.1177, "mu_p": 0.0727, "tau_n": 0.1006, "tau_p": 0.0866,
                "Nc": 0.0520, "Nv": 0.0596, "tau_ETL": 0.1536, "tau_HTL": 0.1011,
                "r_rad": 0.0885}

# frozen representative pairs (from collision_analysis/summary): tau_ETL- and r_rad-dominant
REP_TAUETL = (1010, 2641)
REP_RRAD = (8271, 10258)

_NPZ = None
def npz():
    global _NPZ
    if _NPZ is None:
        _NPZ = np.load(DATA_NPZ)
    return _NPZ

def J_test():
    return npz()["J_test"].astype(np.float64)          # (15307,131) normalized

def P_test():
    return npz()["params_test"].astype(np.float64)     # (15307,9) normalized log

def J_raw():
    return npz()["J_test_raw"].astype(np.float64)      # (15307,131) physical mA/cm^2

V_FULL = np.linspace(0.0, 1.3, 131)
LOW_MASK = V_FULL <= 1.0 + 1e-12                        # 101 points, 0.00-1.00 V

# ---------------------------------------------------------------- distances
def d_theta_matrix(P, nn_idx):
    """FIXED parameter distance: RMSE over 9 normalized-log parameters.
    Same implementation for every J metric (identical-by-construction)."""
    return np.sqrt(np.mean((P - P[nn_idx]) ** 2, axis=1))

def exact_nn_rmse(X, npts, chunk=1024):
    """Exact chunked nearest neighbor by RMSE over npts columns.
    Returns (nn_idx, d_rmse) for every query; self excluded."""
    N = X.shape[0]
    q2 = np.einsum("ij,ij->i", X, X)
    nn_idx = np.empty(N, dtype=np.int64)
    nn_d2 = np.empty(N)
    for s in range(0, N, chunk):
        e = min(s + chunk, N)
        q = X[s:e]
        d2 = q2[s:e, None] + q2[None, :] - 2.0 * (q @ X.T)
        d2[np.arange(e - s), np.arange(s, e)] = np.inf     # exclude self
        idx = np.argmin(d2, axis=1)
        nn_idx[s:e] = idx
        nn_d2[s:e] = d2[np.arange(e - s), idx]
    np.maximum(nn_d2, 0.0, out=nn_d2)                     # clamp tiny negatives
    return nn_idx, np.sqrt(nn_d2 / npts)

def exact_nn_pair_scaled(X_phys, npts, jsc, chunk=1024):
    """Exact chunked NN for pair-dependent Jsc-relative metrics.
    d(i,k) = RMSE_phys(i,k) / (0.5*(|jsc_i|+|jsc_k|)).  Self excluded."""
    N = X_phys.shape[0]
    q2 = np.einsum("ij,ij->i", X_phys, X_phys)
    js = np.abs(jsc)
    nn_idx = np.empty(N, dtype=np.int64)
    nn_d = np.empty(N)
    for s in range(0, N, chunk):
        e = min(s + chunk, N)
        q = X_phys[s:e]
        d2 = q2[s:e, None] + q2[None, :] - 2.0 * (q @ X_phys.T)
        d2[np.arange(e - s), np.arange(s, e)] = np.inf
        np.maximum(d2, 0.0, out=d2)
        dphys = np.sqrt(d2 / npts)                        # (chunk, N) physical RMSE
        scale = 0.5 * (js[s:e, None] + js[None, :])       # pair-mean |Jsc|
        dr = dphys / scale
        idx = np.argmin(dr, axis=1)
        nn_idx[s:e] = idx
        nn_d[s:e] = dr[np.arange(e - s), idx]
    return nn_idx, nn_d

def nn_for_metric(metric):
    """Directed exact NN for one metric -> (nn_idx, dJ)."""
    if metric == "M1":
        return exact_nn_rmse(J_test(), 131)
    if metric == "M2":
        return exact_nn_rmse(J_raw(), 131)
    if metric == "M3":
        return exact_nn_pair_scaled(J_raw(), 131, J_raw()[:, 0])
    if metric == "M4":
        return exact_nn_rmse(J_raw()[:, LOW_MASK], LOW_MASK.sum())
    if metric == "M5":
        X = J_raw()[:, LOW_MASK]
        return exact_nn_pair_scaled(X, LOW_MASK.sum(), J_raw()[:, 0])
    if metric == "M6":
        shp = J_raw() / np.abs(J_raw()[:, 0:1])
        return exact_nn_rmse(shp, 131)
    raise ValueError(metric)

def dedup(nn_idx):
    """Unordered unique pairs: keep i < NN(i) (identical to original rule)."""
    keep = np.arange(len(nn_idx)) < nn_idx
    I = np.arange(len(nn_idx))[keep]
    J = nn_idx[keep]
    return I, J

def coupling(dJ, dTh):
    from scipy.stats import spearmanr, pearsonr
    return spearmanr(dJ, dTh)[0], pearsonr(dJ, dTh)[0]

def tier_stats(dJ, dTh, fracs=(0.10, 0.05, 0.01, 0.005, 0.001)):
    order = np.argsort(dJ, kind="stable")
    M = len(dJ)
    out = {}
    for f in fracs:
        k = max(1, int(round(M * f)))
        sel = order[:k]
        out[f] = dict(n=k, med_dJ=float(np.median(dJ[sel])),
                      max_dJ=float(dJ[sel].max()),
                      med_dTh=float(np.median(dTh[sel])),
                      q25_dTh=float(np.percentile(dTh[sel], 25)),
                      q75_dTh=float(np.percentile(dTh[sel], 75)))
    return out

def random_pairs_seed42(P, n=200000, seed=42):
    """Reproduce the frozen random-pair baseline exactly (original draw)."""
    rng = np.random.default_rng(seed)
    ra, rb = rng.integers(0, P.shape[0], n), rng.integers(0, P.shape[0], n)
    ok = ra != rb
    return ra[ok], rb[ok], np.sqrt(np.mean((P[ra[ok]] - P[rb[ok]]) ** 2, axis=1))

def random_pairs_fixed(P, n=100000, seed=20260827):
    """Spec-preferred fixed random-pair set: unique, no self-pairs."""
    rng = np.random.default_rng(seed)
    N = P.shape[0]
    seen = set()
    ra, rb = [], []
    while len(ra) < n:
        a = rng.integers(0, N, n)
        b = rng.integers(0, N, n)
        for x, y in zip(a, b):
            if x == y:
                continue
            key = (min(x, y), max(x, y))
            if key in seen:
                continue
            seen.add(key)
            ra.append(x); rb.append(y)
            if len(ra) >= n:
                break
    ra, rb = np.array(ra[:n]), np.array(rb[:n])
    return ra, rb, np.sqrt(np.mean((P[ra] - P[rb]) ** 2, axis=1))
