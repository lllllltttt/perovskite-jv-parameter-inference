# -*- coding: utf-8 -*-
"""
lib_v2.py — shared frozen loaders and definitions for the v2 revision.
======================================================================
Read-only. Every array here comes from a frozen source; nothing is retrained,
re-predicted or re-solved.

Unit basis (verified against manuscript Table 1 and Methods, not assumed)
------------------------------------------------------------------------
The stored `params_test_raw` / `params_train` columns are in the units the
sampling ranges of Table 1 are quoted in (manuscript Methods, "Simulation
setup": "Mobilities and densities of states were supplied in SI units. The
radiative coefficient rrad (rad_c in the original code and simulator) was
sampled in cm3 s-1 and converted to m3 s-1 by multiplying by 1e-6."):

    mu_n_pvk, mu_p_pvk    m^2 V^-1 s^-1      Table 1 g: 1e-6 .. 1e-3
    tau_n_pvk, tau_p_pvk  s                  Table 1 g: 1e-9 .. 1e-2
    Nc_eff_pvk, Nv_eff_pvk m^-3              Table 1 g: 1e22 .. 1e26
    tau_ETL               s                  1e-12 .. 1e-8
    tau_HTL               s                  1e-14 .. 1e-10
    rad_c                 cm^3 s^-1          1e-12 .. 1e-9

The difference matters only for the absolute value of the shared-scale
coordinate a, because a = log10(g) with g the geometric mean of the pair;
differences of log10 values (and r itself) are invariant to the unit basis.
verify_units() asserts the observed ranges fall inside Table 1's bounds.

Current density is in mA cm^-2: the frozen figure package states this
explicitly (final_figures/scripts/plot_Fig2_arch_recon.py: "physical units
(mA/cm2)") and plots `J_test_raw` on a (-6, 33) mA cm^-2 axis in
plot_Fig5_final.py. Its extreme reverse-bias tail is a known property of the
retained set, not a unit error.
"""
import os
import pickle

import numpy as np
import pandas as pd

BASE = r"E:\project\work1"
DATA_NPZ = os.path.join(BASE, "data", "dataset_normalized.npz")
FROZEN_NPZ = os.path.join(BASE, "final_figures", "scripts", "_frozen_preds.npz")
SCALER_PKL = os.path.join(BASE, "data", "param_scaler.pkl")
V1_DATADIR = os.path.join(BASE, "20261006", "figure_revision_phase1",
                          "source_data")

N_TEST = 15307
N_TRAIN = 71432

PARAM_NAMES = ["mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk",
               "Nc_eff_pvk", "Nv_eff_pvk", "tau_ETL", "tau_HTL", "rad_c"]
PARAM_UNITS = ["m$^2$ V$^{-1}$ s$^{-1}$", "m$^2$ V$^{-1}$ s$^{-1}$",
               "s", "s", "m$^{-3}$", "m$^{-3}$", "s", "s", "cm$^3$ s$^{-1}$"]
PARAM_UNITS_PLAIN = ["m^2 V^-1 s^-1", "m^2 V^-1 s^-1", "s", "s",
                     "m^-3", "m^-3", "s", "s", "cm^3 s^-1"]
PARAM_LABELS = [r"$\mu_n$", r"$\mu_p$", r"$\tau_n$", r"$\tau_p$",
                r"$N_c$", r"$N_v$", r"$\tau_\mathrm{ETL}$",
                r"$\tau_\mathrm{HTL}$", r"$r_\mathrm{rad}$"]

# Table 1 sampling bounds, used only to *verify* the unit basis.
TABLE1 = {
    "mu_n_pvk": (1e-6, 1e-3), "mu_p_pvk": (1e-6, 1e-3),
    "tau_n_pvk": (1e-9, 1e-2), "tau_p_pvk": (1e-9, 1e-2),
    "Nc_eff_pvk": (1e22, 1e26), "Nv_eff_pvk": (1e22, 1e26),
    "tau_ETL": (1e-12, 1e-8), "tau_HTL": (1e-14, 1e-10),
    "rad_c": (1e-12, 1e-9),
}
# Table 1 constructs each correlated pair from a shared scale g and a ratio q:
# theta_n = g*sqrt(q), theta_p = g/sqrt(q), q in [0.2, 5].
Q_BOUNDS = (0.2, 5.0)

# the six paired coordinates: (coordinate id, family, column n, column p)
COORDS = [("a_mu", "mobility", 0, 1), ("r_mu", "mobility", 0, 1),
          ("a_tau", "lifetime", 2, 3), ("r_tau", "lifetime", 2, 3),
          ("a_D", "DOS", 4, 5), ("r_D", "DOS", 4, 5)]
COORD_IDS = [c[0] for c in COORDS]
FAMILIES = ["mobility", "lifetime", "DOS"]

RANDOM_SEED = 42
N_RANDOM = 200000
BOOTSTRAP_SEED = 43
N_BOOT = 2000

# Figure 3 representative cases: kept unchanged this round, by instruction.
CASES = [("(a)", 2890, 5067, "mobility log-ratio"),
         ("(b)", 500, 4560, "lifetime log-ratio")]

# The rule those two picks come from, stated once here so the figure, the SI
# table and the Methods paragraph cannot describe it differently:
#
#   restrict to the closest 1% of the corrected undirected pairs (the tier_k
#   rule below, applied to ascending d_J); take the pair with the largest
#   absolute mobility log-ratio difference |Delta r_mu|; then, from the same
#   tier with that pair removed, take the pair with the largest absolute bulk-
#   lifetime log-ratio difference |Delta r_tau|.
#
# Ties are broken by position in the tier ordering, i.e. by smaller d_J first
# and then by the pair set's own row order (np.argsort(kind="stable") over
# fig3_pairs_v2.csv, which follows the deduplicated edge order). The tier
# restriction is load-bearing: the largest |Delta r_mu| over ALL 11,245 pairs
# is a different pair.
FIGURE_CASE_RULE = ("closest 1% of corrected undirected pairs by ascending "
                    "d_J; case (a) = largest |Delta r_mu| in that tier; "
                    "case (b) = largest |Delta r_tau| in the same tier with "
                    "case (a)'s pair removed")


def select_figure_cases(pairs):
    """Re-derive the two Figure 3 picks from the corrected pair table.

    `pairs` is data_used/fig3_pairs_v2.csv, read in. Nothing here is new
    analysis: it is the rule the frozen picks were made by, written down and
    checked against them, so a later reader can reproduce the choice instead of
    taking the two indices on trust.
    """
    n = len(pairs)
    k = tier_k(n, 0.01)
    order = np.argsort(pairs["dJ_rmse"].values, kind="stable")[:k]
    ia = int(order[np.argmax(pairs["absd_r_mu"].values[order])])
    rest = order[order != ia]
    ib = int(rest[np.argmax(pairs["absd_r_tau"].values[rest])])
    picks = [(int(pairs["i"].iloc[ia]), int(pairs["j"].iloc[ia])),
             (int(pairs["i"].iloc[ib]), int(pairs["j"].iloc[ib]))]
    assert picks == [(i, j) for _t, i, j, _w in CASES], (
        "the stated selection rule no longer reproduces the frozen Figure 3 "
        "cases: rule gives %s, figure draws %s"
        % (picks, [(i, j) for _t, i, j, _w in CASES]))
    # the same statistic without the tier restriction, so the SI can show that
    # the restriction is doing work and that the two picks are not simply the
    # global extremes (measured, not asserted from memory)
    g = int(np.argmax(pairs["absd_r_mu"].values))
    return picks, dict(n_pairs=n, tier_pairs=k,
                       absd_r_mu=float(pairs["absd_r_mu"].values[ia]),
                       absd_r_tau=float(pairs["absd_r_tau"].values[ib]),
                       global_absd_r_mu=float(pairs["absd_r_mu"].values[g]),
                       global_pair=(int(pairs["i"].iloc[g]),
                                    int(pairs["j"].iloc[g])))


def load_frozen():
    """Physical log10 test parameters, physical current, voltage grid."""
    d = np.load(DATA_NPZ)
    f = np.load(FROZEN_NPZ)
    with open(SCALER_PKL, "rb") as fh:
        sc = pickle.load(fh)["scaler"]

    raw = f["params_test_raw"].astype(np.float64)
    L = np.log10(raw)
    # cross-check the raw array against the inverse of the frozen scaler
    L_ref = f["params_test"].astype(np.float64) * sc.data_range_ + sc.data_min_
    assert np.max(np.abs(L - L_ref)) < 1e-9, "raw/scaler mismatch"

    out = dict(
        L=L, raw=raw,
        J=f["J_test_raw"].astype(np.float64),      # mA cm^-2
        V=f["V_GRID"].astype(np.float64),
        Jn=f["J_test"].astype(np.float64),         # normalized current
        params_test=f["params_test"].astype(np.float64),
        L_train=d["params_train"].astype(np.float64) * sc.data_range_
                + sc.data_min_,
        scaler=sc, param_names=[str(x) for x in f["param_names"]],
    )
    assert out["V"].size == 131 and abs(out["V"][-1] - 1.3) < 1e-12
    return out


def verify_units(raw):
    """Assert the observed raw ranges lie inside Table 1's stated bounds."""
    lo_q, hi_q = np.sqrt(Q_BOUNDS[0]), np.sqrt(Q_BOUNDS[1])
    rows = []
    for k, name in enumerate(PARAM_NAMES):
        col = raw[:, k]
        lo, hi = TABLE1[name]
        # correlated pairs widen the individual bound by sqrt(q); tau_ETL,
        # tau_HTL and rad_c are sampled directly over their stated range.
        wid = name in ("tau_ETL", "tau_HTL", "rad_c")
        lo_eff = lo if wid else lo / hi_q
        hi_eff = hi if wid else hi * hi_q
        ok = bool(col.min() >= lo_eff * 0.999 and col.max() <= hi_eff * 1.001)
        rows.append(dict(parameter=name, unit=PARAM_UNITS_PLAIN[k],
                         observed_min=float(col.min()),
                         observed_max=float(col.max()),
                         table1_lo=lo, table1_hi=hi,
                         effective_lo=lo_eff, effective_hi=hi_eff,
                         inside_bounds=ok))
    df = pd.DataFrame(rows)
    assert df["inside_bounds"].all(), df[~df["inside_bounds"]]
    return df


def coordinates(L):
    """(N,6) paired coordinates in physical log10 space, column order COORD_IDS."""
    return np.column_stack([
        0.5 * (L[:, 0] + L[:, 1]), L[:, 0] - L[:, 1],
        0.5 * (L[:, 2] + L[:, 3]), L[:, 2] - L[:, 3],
        0.5 * (L[:, 4] + L[:, 5]), L[:, 4] - L[:, 5]])


def nearest_neighbours(Jn):
    """Existing primary metric: Euclidean in normalized J space, self excluded."""
    N, JD = Jn.shape
    q2 = np.einsum("ij,ij->i", Jn, Jn)
    nn = np.empty(N, np.int64)
    d2min = np.empty(N)
    CH = 1024
    for s in range(0, N, CH):
        e = min(s + CH, N)
        q = Jn[s:e]
        d2 = q2[s:e, None] + q2[None, :] - 2.0 * (q @ Jn.T)
        d2[np.arange(e - s), np.arange(s, e)] = np.inf
        k = np.argmin(d2, axis=1)
        nn[s:e] = k
        d2min[s:e] = d2[np.arange(e - s), k]
    return nn, np.sqrt(d2min / JD)


def dedup_undirected(nn, N):
    """Directed links -> ordered (min,max) -> unique set.

    Returns (i, j, first) where `first` is the index of the directed link that
    represents each surviving undirected edge.
    """
    lo = np.minimum(np.arange(N), nn)
    hi = np.maximum(np.arange(N), nn)
    key = lo.astype(np.int64) * N + hi.astype(np.int64)
    _, first = np.unique(key, return_index=True)
    first = np.sort(first)          # stable, reproducible ordering
    return lo[first], hi[first], first


def random_pairs(N, seed=RANDOM_SEED, n=N_RANDOM):
    """Random-pair baseline. Same seed, size and rule as the archived analysis."""
    rng = np.random.default_rng(seed)
    ra = rng.integers(0, N, n)
    rb = rng.integers(0, N, n)
    keep = ra != rb
    return ra[keep], rb[keep]


def tier_k(n_pairs, frac):
    """Tier size rule used throughout (documented in the data dictionary)."""
    return max(1, int(round(n_pairs * frac)))


TIERS = [("closest 10%", 0.10), ("closest 5%", 0.05), ("closest 1%", 0.01),
         ("closest 0.5%", 0.005), ("closest 0.1%", 0.001)]


def read_v1_pairs():
    """The corrected pair set produced by phase 1, for an independent re-check."""
    return pd.read_csv(os.path.join(V1_DATADIR, "fig3_pairs_new.csv"))
