# -*- coding: utf-8 -*-
"""
v2lib.py -- shared library for supplementary_validation_v2 (round-2 corrections).

All numbers derive from FROZEN inputs under E:\\project\\work1 (read-only).  Nothing
here imports TensorFlow (model inference lives in infer_frozen.py so that
analysis scripts stay light).

Coordinate / unit conventions (verified in round-1 audit A-D and reused here):
  * 9 params order: mu_n, mu_p, tau_n, tau_p, Nc_eff, Nv_eff, tau_ETL, tau_HTL, rad_c
  * pairs (mu, tau, DOS) obey  log10 theta_n = a + r/2,  log10 theta_p = a - r/2,
    a = 0.5*(xn+xp) = log10 s,  r = xn - xp = log10 q.
  * Frozen generative prior (declared):  s log-uniform per pair
        mu  : s in [1e-6, 1e-3] m2/V/s   (log10 a in [-6, -3])
        tau : s in [1e-9, 1e-2] s        (log10 a in [-9, -2])
        DOS : s in [1e22, 1e26] 1/m3     (log10 a in [22, 26])
    q linear in [0.2, 5]  ->  r in [-log10(5), +log10(5)] = [-0.698970, 0.698970]
    independent: tau_ETL log-uniform [1e-12,1e-8] s, tau_HTL [1e-14,1e-10] s,
                 rad_c [1e-12,1e-9] cm3/s (x1e-6 -> m3/s inside COMSOL).
  * The 'Table-1 box' used to clamp E1 single-coordinate scans is the looser
    physical marginal box derived from the generative box:
        mu [4.5e-7, 2.2e-3], tau [4.5e-10, 2.2e-2], DOS [4.5e21, 2.2e26].
    A point can be inside the Table-1 box yet OUTSIDE the generative (s,q)
    box -> this is the source of round-1's out-of-prior perturbation count.
  * J unit in the frozen DB / scalers: mA/cm2 on V = 0:0.01:1.3 (131 pts).
    COMSOL returns A/m2;  x 0.1 -> mA/cm2.
"""
import os, pickle
import numpy as np

BASE = r"E:\project\work1"
V2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
NPZ = os.path.join(DATA, "dataset_normalized.npz")

PARAM_NAMES = ["mu_n", "mu_p", "tau_n", "tau_p", "Nc", "Nv", "tau_ETL", "tau_HTL", "rad_c"]
PAIR_NAMES = ["mobility", "lifetime", "DOS"]
# 0-based log10-param column pairs
PAIRS = {"mobility": (0, 1), "lifetime": (2, 3), "DOS": (4, 5)}
COORD_NAMES = ["a_mu", "r_mu", "a_tau", "r_tau", "a_D", "r_D"]
COORD_PAIR = ["mobility", "mobility", "lifetime", "lifetime", "DOS", "DOS"]
V = np.linspace(0.0, 1.3, 131)
AM2 = 0.1                      # A/m2 -> mA/cm2

# declared generative prior (log10 of s and of q) per pair, by pair index
PRIOR = {
    # a = log10 s bounds, and half-width of r allowed = log10(q_max)
    0: dict(a_lo=-6.0, a_hi=-3.0, r_max=float(np.log10(5.0))),   # mobility
    1: dict(a_lo=-9.0, a_hi=-2.0, r_max=float(np.log10(5.0))),   # lifetime
    2: dict(a_lo=22.0, a_hi=26.0, r_max=float(np.log10(5.0))),   # DOS
}
# Table-1 declared physical marginal boxes (lo, hi), used as the E1 clamp box
T1_BOX = {
    0: (4.5e-7, 2.2e-3),
    1: (4.5e-10, 2.2e-2),
    2: (4.5e21, 2.2e26),
}
T1_BOXLOG = {j: (np.log10(T1_BOX[j][0]), np.log10(T1_BOX[j][1])) for j in (0, 1, 2)}

_sc = {}
def param_scaler():
    """Frozen param MinMaxScaler fitted on log10(params_train)."""
    if "p" not in _sc:
        with open(os.path.join(DATA, "param_scaler.pkl"), "rb") as f:
            _sc["p"] = pickle.load(f)["scaler"]
    return _sc["p"]

def j_scaler():
    if "j" not in _sc:
        with open(os.path.join(DATA, "J_scaler.pkl"), "rb") as f:
            _sc["j"] = pickle.load(f)
    return _sc["j"]

def norm_to_log10(norm):
    """normalized log10 (0..1 by train min/max) -> log10 physical."""
    sc = param_scaler()
    return np.asarray(norm, np.float64) * sc.data_range_ + sc.data_min_

def log10_to_norm(L):
    sc = param_scaler()
    return (np.asarray(L, np.float64) - sc.data_min_) / sc.data_range_

def Jnorm_to_Jphys(Jn):
    sc = j_scaler()
    return np.asarray(Jn, np.float64) * sc.data_range_ + sc.data_min_

def Jphys_to_Jnorm(Jp):
    sc = j_scaler()
    return (np.asarray(Jp, np.float64) - sc.data_min_) / sc.data_range_

def load_npz():
    return np.load(NPZ, allow_pickle=True)

# ----------------------------------------------------------------------
# coordinates
# ----------------------------------------------------------------------
def coords_from_log10(L):
    """(N,9) log10 phys -> (N,6) [a_mu,r_mu,a_tau,r_tau,a_D,r_D]."""
    L = np.asarray(L, np.float64)
    return np.column_stack([
        0.5*(L[:,0]+L[:,1]), L[:,0]-L[:,1],
        0.5*(L[:,2]+L[:,3]), L[:,2]-L[:,3],
        0.5*(L[:,4]+L[:,5]), L[:,4]-L[:,5]])

def log10_from_coords(C):
    """(N,6) coords -> (N,9) log10 physical (paired cols 0..5; 6..8 untouched)."""
    C = np.asarray(C, np.float64)
    a_mu, r_mu, a_tau, r_tau, a_D, r_D = C[:,0], C[:,1], C[:,2], C[:,3], C[:,4], C[:,5]
    return np.column_stack([
        a_mu+0.5*r_mu, a_mu-0.5*r_mu,
        a_tau+0.5*r_tau, a_tau-0.5*r_tau,
        a_D+0.5*r_D,   a_D-0.5*r_D])

def prior_status_of_coords(C):
    """Per-row (and per-pair + overall) membership in the DECLARED generative
    (s,q) prior.  C is (N,6). Returns dict with bool masks.
    inside_table1: all 3 pairs' physical marginal theta_n,theta_p inside Table-1 box.
    inside_sq    : each pair has a=log10 s in [a_lo,a_hi] AND |r|<=r_max.
    """
    C = np.asarray(C, np.float64)
    N = C.shape[0]
    inside_sq = np.ones(N, bool)
    in_t1 = np.ones(N, bool)
    per = {}
    for pi in range(3):
        a = C[:, 2*pi]; r = C[:, 2*pi+1]
        pr = PRIOR[pi]
        ok = (a >= pr["a_lo"]-1e-9) & (a <= pr["a_hi"]+1e-9) & (np.abs(r) <= pr["r_max"]+1e-9)
        inside_sq &= ok
        Lpair = log10_from_coords(C)[:, (2*pi, 2*pi+1)]
        lo, hi = T1_BOXLOG[pi]
        t1ok = (Lpair[:, 0] >= lo-1e-9) & (Lpair[:, 0] <= hi+1e-9) & \
               (Lpair[:, 1] >= lo-1e-9) & (Lpair[:, 1] <= hi+1e-9)
        in_t1 &= t1ok
        per[PAIR_NAMES[pi]] = ok
    return dict(inside_sq=inside_sq, inside_table1=in_t1,
                per_pair={k: v for k, v in per.items()})

# ----------------------------------------------------------------------
# device metrics -- SINGLE EXPLICIT extractor (A2-v2)
# ----------------------------------------------------------------------
def device_metrics(J, voc_mode="interp", Vgrid=V, max_voltage_scan=1.3):
    """Unified device-metric extractor on a raw 131-pt curve (mA/cm2).

    voc_mode:
      'interp' : first downward zero crossing, linearly interpolated (J<0).
      'grid'   : grid-node convention of the frozen store (first V with J<=0).
    Returns dict with keys Jsc, Voc, Vmp, Pmax, FF, PCE, n_cross, plus flags:
      Jsc  = |J(V=0)|  (mA/cm2)
      Vmp/Pmax = discrete max of V*J over the forward quadrant (scan-range Pmax)
      PCE  = Jsc*Voc*FF only when a finite Voc and FF>0 exist (else NaN), using
             the interp (true zero-crossing) Voc when available.
    NaN is used for any metric that is not well defined (no crossing, non-finite,
    or Pmax at a window boundary -> flag 'pmax_at_edge').
    """
    J = np.asarray(J, np.float64).ravel()
    out = dict(Jsc=abs(J[0]), Voc=np.nan, Vmp=np.nan, Pmax=np.nan, FF=np.nan,
               PCE=np.nan, n_down_cross=0, pmax_at_edge=False, finite=True)
    if len(J) != len(Vgrid):
        out["finite"] = False
        out["mismatch_len"] = (len(J), len(Vgrid))
        return out
    if not np.all(np.isfinite(J)):
        out["finite"] = False
        return out
    s = np.diff(np.sign(J))
    down = np.where(s < 0)[0]                 # indices of downward zero crossings
    out["n_down_cross"] = int(len(down))
    if len(down):
        kk = down[0]
        if voc_mode == "interp":
            voc = Vgrid[kk] - J[kk]*(Vgrid[kk+1]-Vgrid[kk])/(J[kk+1]-J[kk])
        else:
            voc = Vgrid[kk+1]                 # first grid node with J<=0 (grid convention)
        out["Voc"] = float(voc)
    # generation quadrant: V <= Voc and J >= 0
    if np.isfinite(out["Voc"]) and out["Voc"] > 0:
        gen = (Vgrid <= out["Voc"]) & (J >= 0)
    else:
        gen = J >= 0
    p = np.where(gen, J*Vgrid, np.nan)
    if np.isfinite(np.nanmax(p)):
        i = int(np.nanargmax(p))
        out["Pmax"] = float(p[i]); out["Vmp"] = float(Vgrid[i])
        # flag a max-power point that sits on the very last gen point (boundary)
        edges = np.where(gen)[0]
        if len(edges) and i in (edges[0], edges[-1]):
            out["pmax_at_edge"] = True
    if np.isfinite(out["Voc"]) and out["Voc"] > 0 and np.isfinite(out["Jsc"]) \
       and out["Jsc"] > 0 and np.isfinite(out["Pmax"]):
        out["FF"] = float(out["Pmax"]/(out["Jsc"]*out["Voc"]))
    if np.isfinite(out["FF"]) and out["FF"] > 0 and np.isfinite(out["Voc"]) \
       and np.isfinite(out["Jsc"]):
        out["PCE"] = float(out["Jsc"]*out["Voc"]*out["FF"])   # mW/cm2 ~ %
    return out

# ----------------------------------------------------------------------
# windows (fixed rules + target-reference windows)
# ----------------------------------------------------------------------
def window_masks(voc_t, vmp_t, mpp_half=0.05, Vgrid=V):
    """Return dict of boolean masks over the 131-pt grid.
    full:[0,1.3]; le1:V<=1; gt1:V>1; gen0:V<=voc_t; gtvoc:V>voc_t;
    mpp:|V-vmp_t|<=0.05. Windows that cannot be defined (NaN target metric)
    are all-False."""
    w = dict(full=np.ones(len(Vgrid), bool),
             le1=Vgrid <= 1.0,
             gt1=Vgrid > 1.0,
             gen0=np.zeros(len(Vgrid), bool),
             gtvoc=np.zeros(len(Vgrid), bool),
             mpp=np.zeros(len(Vgrid), bool))
    if np.isfinite(voc_t):
        w["gen0"] = Vgrid <= voc_t
        w["gtvoc"] = Vgrid > voc_t
    if np.isfinite(vmp_t):
        w["mpp"] = np.abs(Vgrid - vmp_t) <= mpp_half
    return w

def rmse_windows(Jt, Js, masks):
    """Windowed RMSE + MAE between target curve Jt and sim curve Js (mA/cm2)."""
    out = {}
    for nm, m in masks.items():
        if m.sum() == 0:
            out[f"rmse_{nm}"] = np.nan; out[f"mae_{nm}"] = np.nan; continue
        d = Jt[m] - Js[m]
        out[f"rmse_{nm}"] = float(np.sqrt(np.mean(d*d)))
        out[f"mae_{nm}"] = float(np.mean(np.abs(d)))
    return out

# ----------------------------------------------------------------------
# interval score (Gneiting & Raftery 2007 Eq. 43)
# ----------------------------------------------------------------------
def interval_score(l, u, x, alpha):
    """Proper interval score for a central (l,u) at nominal coverage alpha.
       IS = (u-l) + 2/(1-alpha)*(l-x)*I(x<l) + 2/(1-alpha)*(x-u)*I(x>u).
    All in whatever additive units l,u,x share."""
    w = (u-l).astype(float)
    s = w + (2.0/(1.0-alpha))*np.maximum(l-x, 0.0) + (2.0/(1.0-alpha))*np.maximum(x-u, 0.0)
    return s

# ----------------------------------------------------------------------
# sample mapping (test index -> DB csv row -> Sample_ID)
# ----------------------------------------------------------------------
def test_index_to_sample_id():
    """Return (csv_row_index array (15307,), sample_id array (15307,), sid_from_...).
    Built from the float-exact match established in round 2 (15307/15307 unique,
    J exact to 1e-10).  Saved under v2/_work/provenance/_testidx_to_csvrow.npy."""
    cr = np.load(os.path.join(V2, "_work", "provenance", "_testidx_to_csvrow.npy"))
    return cr

_SID = None
def sample_ids():
    global _SID
    if _SID is None:
        import pandas as pd
        df = pd.read_csv(os.path.join(DATA, "JV_database_9D_interface_lifetimes-2.csv"),
                         usecols=["Sample_ID"])
        _SID = df["Sample_ID"].values.astype(np.int64)
    return _SID

def sid_of_test_index(idx):
    cr = test_index_to_sample_id()
    return sample_ids()[cr[idx]]
