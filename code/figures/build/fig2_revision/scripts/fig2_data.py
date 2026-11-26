# -*- coding: utf-8 -*-
"""fig2_data.py -- rebuild the Figure 2 plotting table from the frozen sources.

Nothing is retrained, re-predicted or refitted here. The frozen arrays are the
same ones the accepted Figure 2 was drawn from; this module only re-derives the
two coordinates and the two metrics so that the numbers on the new figure can be
asserted against the archived values before anything is drawn.

Coordinates (identical to the manuscript caption and to the earlier script):

    a = (log10 p_n + log10 p_p) / 2        p_n, p_p = paired bulk parameters
    r = log10(p_n / p_p)                   (denominator is p_p, the hole value)

Mobility pair  (mu_n, mu_p)   m^2 V^-1 s^-1
Lifetime pair  (tau_n, tau_p) s
DOS pair       (Nc, Nv)       m^-3

Writes data_used/fig2_coordinates.csv and data_used/fig2_metrics.csv.
"""
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import pearsonr

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
DATADIR = os.path.join(OUT, "data_used")
BASE = r"E:\project\work1"

DATA_NPZ = os.path.join(BASE, "data", "dataset_normalized.npz")
FROZEN_NPZ = os.path.join(BASE, "final_figures", "scripts", "_frozen_preds.npz")
SCALER_PKL = os.path.join(BASE, "data", "param_scaler.pkl")

# (label, column of p_n, column of p_p, column title, unit)
FAMILIES = [
    ("mobility", 0, 1, "Mobility", r"m$^{2}$ V$^{-1}$ s$^{-1}$"),
    ("lifetime", 2, 3, "Bulk lifetime", "s"),
    ("DOS", 4, 5, "Density of states", r"m$^{-3}$"),
]
TAG = {"mobility": "mu", "lifetime": "tau", "DOS": "D"}

# archived values that the new figure has to reproduce; the build script
# asserts every one of these before saving a single byte.
ARCHIVE = {
    ("a", "mobility"): (0.925047, 0.680984),
    ("r", "mobility"): (0.428887, 0.083636),
    ("a", "lifetime"): (0.881870, 0.612916),
    ("r", "lifetime"): (0.351667, 0.027472),
    ("a", "DOS"): (0.924758, 0.662630),
    ("r", "DOS"): (0.266298, 0.008322),
}


def load_coordinates():
    f = np.load(FROZEN_NPZ)
    d = np.load(DATA_NPZ)
    import pickle
    with open(SCALER_PKL, "rb") as fh:
        sc = pickle.load(fh)["scaler"]

    L_true = np.log10(f["params_test_raw"].astype(np.float64))
    L_pred = np.log10(f["params_pred_phys"].astype(np.float64))
    L_train = d["params_train"].astype(np.float64) * sc.data_range_ + sc.data_min_

    # the physical log10 values must equal the stored normalized values mapped
    # back through the frozen scaler -- otherwise "physical" would be a guess.
    assert np.max(np.abs(L_true - (f["params_test"] * sc.data_range_
                                   + sc.data_min_))) < 1e-12
    assert np.max(np.abs(L_pred - (f["param_mu"] * sc.data_range_
                                   + sc.data_min_))) < 1e-12

    coords = {}
    for lab, p, q, _title, _unit in FAMILIES:
        coords[("a", lab)] = (0.5 * (L_true[:, p] + L_true[:, q]),
                              0.5 * (L_pred[:, p] + L_pred[:, q]),
                              0.5 * (L_train[:, p] + L_train[:, q]))
        coords[("r", lab)] = (L_true[:, p] - L_true[:, q],
                              L_pred[:, p] - L_pred[:, q],
                              L_train[:, p] - L_train[:, q])

    per = pd.DataFrame({"test_index": np.arange(L_true.shape[0])})
    for lab, _p, _q, _t, _u in FAMILIES:
        for fam in ("a", "r"):
            t, pr, _tr = coords[(fam, lab)]
            per["%s_%s_true" % (fam, TAG[lab])] = t
            per["%s_%s_pred" % (fam, TAG[lab])] = pr
    return coords, per


def metrics(coords):
    rows, rho, red = [], {}, {}
    for lab, _p, _q, _t, unit in FAMILIES:
        for fam in ("a", "r"):
            t, pr, tr = coords[(fam, lab)]
            base = float(np.median(tr))
            r = float(pearsonr(t, pr)[0])
            red_v = 1.0 - float(np.mean(np.abs(t - pr))) / float(
                np.mean(np.abs(t - base)))
            rho[(fam, lab)] = r
            red[(fam, lab)] = red_v
            rows.append(dict(
                family=lab, coordinate=fam, symbol="%s_%s" % (fam, TAG[lab]),
                unit=(unit if fam == "a" else "dimensionless"),
                n_test=int(len(t)), pearson_r=r,
                mae_model=float(np.mean(np.abs(t - pr))),
                mae_training_median=float(np.mean(np.abs(t - base))),
                train_median=base, mae_reduction=red_v))
    return pd.DataFrame(rows), rho, red


def main():
    os.makedirs(DATADIR, exist_ok=True)
    coords, per = load_coordinates()
    tab, rho, red = metrics(coords)

    bad = []
    for key, (rho_ref, red_ref) in ARCHIVE.items():
        if abs(rho[key] - rho_ref) > 5e-7:
            bad.append(("rho", key, rho[key], rho_ref))
        if abs(red[key] - red_ref) > 5e-7:
            bad.append(("mae_reduction", key, red[key], red_ref))
    if bad:
        raise SystemExit("ARCHIVE MISMATCH: %r" % (bad,))

    per.to_csv(os.path.join(DATADIR, "fig2_coordinates.csv"), index=False)
    tab.to_csv(os.path.join(DATADIR, "fig2_metrics.csv"), index=False)

    print("n test curves:", len(per))
    print("%-9s %-2s %10s %10s %10s" % ("family", "co", "rho", "MAEred", "MAEbase"))
    for _, r in tab.iterrows():
        print("%-9s %-2s %10.6f %10.6f %10.4f"
              % (r.family, r.coordinate, r.pearson_r, r.mae_reduction,
                 r.mae_training_median))
    print("all 12 archived values reproduced")


if __name__ == "__main__":
    main()
