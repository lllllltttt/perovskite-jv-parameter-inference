# -*- coding: utf-8 -*-
"""Reproduce the frozen Figure 3 / Table S6 nearest-neighbour analysis.

Read-only on every input.  The nearest-neighbour rules below are copied
verbatim from the archived verification script
`20261006/figure_revision_phase1_v2_final/scripts/lib_v2.py`:

  * distance: Euclidean on the frozen normalized 131-point current matrix;
  * self-distance set to +inf;
  * directed nearest neighbour for every test curve;
  * directed links mapped to ordered (min, max) keys and deduplicated;
  * tier size k = max(1, round(n_pairs * frac));
  * random baseline: np.random.default_rng(42), 200,000 ordered index pairs,
    self-pairs dropped, median absolute difference per coordinate.

No model, no scaler is refitted and no COMSOL solve is started.
"""
import hashlib
import json
import os

import numpy as np
import pandas as pd

BASE = r"E:\project\work1"
OUT = os.path.join(BASE, "20261019_NN_stability", "out", "reproduction")
os.makedirs(OUT, exist_ok=True)

DATA_NPZ = os.path.join(BASE, "data", "dataset_normalized.npz")
FROZEN_NPZ = os.path.join(BASE, "final_figures", "scripts", "_frozen_preds.npz")
SCALER_PKL = os.path.join(BASE, "data", "param_scaler.pkl")
J_SCALER_PKL = os.path.join(BASE, "data", "J_scaler.pkl")
ARCH = os.path.join(BASE, "20261006",
                    "manuscript_figures_SI_integrated_v2_layout_final",
                    "data_used")

COORD_IDS = ["a_mu", "r_mu", "a_tau", "r_tau", "a_D", "r_D"]
COORDS = [("a_mu", 0, 1), ("r_mu", 0, 1), ("a_tau", 2, 3),
          ("r_tau", 2, 3), ("a_D", 4, 5), ("r_D", 4, 5)]
TIERS = [("closest 10%", 0.10), ("closest 5%", 0.05), ("closest 1%", 0.01),
         ("closest 0.5%", 0.005), ("closest 0.1%", 0.001)]
RANDOM_SEED = 42
N_RANDOM = 200000
N_TEST = 15307
N_VOLTAGE = 131


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def coordinates(L):
    return np.column_stack([
        0.5 * (L[:, 0] + L[:, 1]), L[:, 0] - L[:, 1],
        0.5 * (L[:, 2] + L[:, 3]), L[:, 2] - L[:, 3],
        0.5 * (L[:, 4] + L[:, 5]), L[:, 4] - L[:, 5]])


def nearest_neighbours(Jn):
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
    lo = np.minimum(np.arange(N), nn)
    hi = np.maximum(np.arange(N), nn)
    key = lo.astype(np.int64) * N + hi.astype(np.int64)
    _, first = np.unique(key, return_index=True)
    first = np.sort(first)
    return lo[first], hi[first], first


def random_pairs(N, seed=RANDOM_SEED, n=N_RANDOM):
    rng = np.random.default_rng(seed)
    ra = rng.integers(0, N, n)
    rb = rng.integers(0, N, n)
    keep = ra != rb
    return ra[keep], rb[keep]


def tier_k(n_pairs, frac):
    return max(1, int(round(n_pairs * frac)))


def main():
    import pickle
    d = np.load(DATA_NPZ, allow_pickle=True)
    f = np.load(FROZEN_NPZ, allow_pickle=True)
    with open(SCALER_PKL, "rb") as fh:
        sc = pickle.load(fh)["scaler"]
    with open(J_SCALER_PKL, "rb") as fh:
        js = pickle.load(fh)

    raw = f["params_test_raw"].astype(np.float64)
    L = np.log10(raw)
    L_ref = f["params_test"].astype(np.float64) * sc.data_range_ + sc.data_min_
    Jn = f["J_test"].astype(np.float64)                # archived input
    Jn64 = d["J_test"].astype(np.float64)              # same data, float64
    Jraw = f["J_test_raw"].astype(np.float64)
    V = f["V_GRID"].astype(np.float64)
    C = coordinates(L)

    checks = {
        "n_test": int(L.shape[0]),
        "n_voltage": int(V.size),
        "voltage_last": float(V[-1]),
        "n_test_expected": N_TEST,
        "n_voltage_expected": N_VOLTAGE,
        "shapes_ok": bool(L.shape == (N_TEST, 9) and Jn.shape == (N_TEST, N_VOLTAGE)),
        "param_raw_vs_scaler_inverse_max_abs": float(np.max(np.abs(L - L_ref))),
        "param_alignment_ok": bool(np.max(np.abs(L - L_ref)) < 1e-9),
        "frozen_J_vs_dataset_J_max_abs": float(np.max(np.abs(Jn - Jn64))),
        "frozen_J_float32_ok": bool(np.max(np.abs(Jn - Jn64)) < 1e-7),
        "J_inverse_vs_raw_max_abs": float(np.max(np.abs(
            Jn * js.data_range_[None, :] + js.data_min_[None, :] - Jraw))),
        "J_inverse_max_rel_to_span": float(np.max(np.abs(
            Jn * js.data_range_[None, :] + js.data_min_[None, :] - Jraw)
            / js.data_range_[None, :])),
        "input_sha256": {
            "dataset_normalized.npz": sha256(DATA_NPZ),
            "_frozen_preds.npz": sha256(FROZEN_NPZ),
            "param_scaler.pkl": sha256(SCALER_PKL),
            "J_scaler.pkl": sha256(J_SCALER_PKL),
        },
        "archived_reference_dir": ARCH,
    }
    # Row correspondence: the same archived parameter row and current row are
    # joined by position in the frozen files (no Sample_ID exists).
    jsc = f["jsc"].astype(np.float64)
    checks["jsc_matches_raw_at_zero_voltage_max_abs"] = float(
        np.max(np.abs(jsc - np.abs(Jraw[:, int(np.argmin(np.abs(V)))]))))

    # ------------------------------------------------------------- NN graph --
    nn, dJ_dir = nearest_neighbours(Jn)
    ni, nj, first = dedup_undirected(nn, len(L))
    deg = np.bincount(np.concatenate([ni, nj]), minlength=len(L))

    d = {}
    for cid, p, q in COORDS:
        col = COORD_IDS.index(cid)
        d[cid] = C[:, col]
    absd = {cid: np.abs(d[cid][ni] - d[cid][nj]) for cid in COORD_IDS}
    dJ = np.sqrt(np.sum((Jn[ni] - Jn[nj]) ** 2, axis=1) / Jn.shape[1])

    # -------------------------------------------------------- random baseline --
    ra, rb = random_pairs(len(L))
    rand_med = {}
    for cid in COORD_IDS:
        col = COORD_IDS.index(cid)
        rand_med[cid] = float(np.median(np.abs(C[ra, col] - C[rb, col])))

    # ------------------------------------------------------------- summaries --
    order = np.argsort(dJ, kind="stable")
    rows = []

    def describe(tag, sel):
        row = dict(set=tag, n_pairs=int(sel.size),
                   distinct_samples=int(np.unique(np.concatenate([ni[sel], nj[sel]])).size),
                   samples_in_multiple_pairs=int(
                       np.sum(np.bincount(np.concatenate([ni[sel], nj[sel]]),
                                          minlength=len(L)) > 1)),
                   max_pairs_per_sample=int(np.max(
                       np.bincount(np.concatenate([ni[sel], nj[sel]]),
                                   minlength=len(L)))),
                   median_dJ=float(np.median(dJ[sel])))
        for cid in COORD_IDS:
            v = absd[cid][sel]
            row["median_absd_" + cid] = float(np.median(v))
            row["q25_absd_" + cid] = float(np.percentile(v, 25))
            row["q75_absd_" + cid] = float(np.percentile(v, 75))
            row["median_norm_" + cid] = float(np.median(v) / rand_med[cid])
        return row

    rows.append(describe("all corrected pairs", order))
    for name, frac in TIERS:
        rows.append(describe(name, order[:tier_k(len(order), frac)]))
    S = pd.DataFrame(rows)
    S.to_csv(os.path.join(OUT, "s6_reproduced.csv"), index=False)

    P = pd.DataFrame({"i": ni, "j": nj, "dJ": dJ})
    for cid in COORD_IDS:
        P["absd_" + cid] = absd[cid]
    P.to_csv(os.path.join(OUT, "pairs_reproduced.csv"), index=False)

    # ------------------------------------------------------- archived compare --
    ref = pd.read_csv(os.path.join(ARCH, "fig3_pair_summary_v2.csv"))
    ref = ref.set_index("set")
    chk = []
    for _, r in S.iterrows():
        tag = r["set"]
        rr = ref.loc[tag]
        chk.append(dict(set=tag, n_pairs=int(r["n_pairs"]),
                        n_pairs_archived=int(rr["n_pairs"]),
                        distinct_samples=int(r["distinct_samples"]),
                        distinct_samples_archived=int(rr["distinct_samples"]),
                        samples_in_multiple_pairs=int(r["samples_in_multiple_pairs"]),
                        samples_in_multiple_pairs_archived=int(
                            rr["samples_in_multiple_pairs"]),
                        max_pairs_per_sample=int(r["max_pairs_per_sample"]),
                        max_pairs_per_sample_archived=int(
                            rr["max_pairs_per_sample"])))
        for cid in COORD_IDS:
            chk[-1]["d_median_absd_" + cid] = float(
                r["median_absd_" + cid] - rr["median_absd_" + cid])
            chk[-1]["d_median_norm_" + cid] = float(
                r["median_norm_" + cid] - rr["median_norm_" + cid])
    chkdf = pd.DataFrame(chk)
    chkdf.to_csv(os.path.join(OUT, "s6_reproduction_check.csv"), index=False)

    rb_ref = pd.read_csv(os.path.join(ARCH, "fig3_random_baseline_v2.csv"))
    rb_ref = rb_ref.set_index("coordinate")
    rbrows = []
    for cid in COORD_IDS:
        rbrows.append(dict(coordinate=cid, median_absd_random=rand_med[cid],
                           median_absd_random_archived=float(
                               rb_ref.loc[cid, "median_absd_random"]),
                           difference=rand_med[cid] - float(
                               rb_ref.loc[cid, "median_absd_random"]),
                           n_random_pairs=int(ra.size),
                           n_random_pairs_archived=int(
                               rb_ref.loc[cid, "n_random_pairs"])))
    rbdf = pd.DataFrame(rbrows)
    rbdf.to_csv(os.path.join(OUT, "random_baseline_check.csv"), index=False)

    # pair-set identity against the archived per-pair table
    ap = pd.read_csv(os.path.join(ARCH, "fig3_pairs_v2.csv"))
    ours = set(zip(ni.tolist(), nj.tolist()))
    theirs = set(zip(ap["i"].astype(int).tolist(), ap["j"].astype(int).tolist()))
    pair_check = {
        "n_pairs_reproduced": len(ours),
        "n_pairs_archived": len(theirs),
        "pair_sets_identical": bool(ours == theirs),
        "archived_only": len(theirs - ours),
        "reproduced_only": len(ours - theirs),
        "directed_links": int(len(nn)),
        "mutual_nearest_pairs": int(np.sum(nn[nn] == np.arange(len(L)))),
        "curves_touched": int(np.unique(np.concatenate([ni, nj])).size),
        "curves_in_multiple_pairs": int(np.sum(deg > 1)),
        "max_pairs_per_curve": int(deg.max()),
    }

    all_tol = 5e-12
    diff_cols = [c for c in chkdf.columns if c.startswith("d_median_")]
    max_abs_median_diff = float(np.max(np.abs(chkdf[diff_cols].values)))
    max_rand_diff = float(np.max(np.abs(rbdf["difference"])))
    summary = {
        "pair_set": pair_check,
        "median_statistics_max_abs_difference": max_abs_median_diff,
        "median_statistics_match": bool(max_abs_median_diff < all_tol),
        "random_baseline_max_abs_difference": max_rand_diff,
        "random_baseline_match": bool(max_rand_diff < all_tol),
        "tier_counts_match": bool((chkdf["n_pairs"] == chkdf["n_pairs_archived"]).all()),
        "reproduction_ok": bool(
            pair_check["pair_sets_identical"]
            and max_abs_median_diff < all_tol
            and max_rand_diff < all_tol
            and (chkdf["n_pairs"] == chkdf["n_pairs_archived"]).all()
            and checks["shapes_ok"] and checks["param_alignment_ok"]),
    }
    with open(os.path.join(OUT, "input_verification.json"), "w", encoding="utf-8") as fh:
        json.dump(checks, fh, indent=2, ensure_ascii=False)
    with open(os.path.join(OUT, "reproduction_check.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print("\nreproduced S6 summary:")
    print(S[["set", "n_pairs", "median_norm_a_mu", "median_norm_r_mu",
             "median_norm_a_tau", "median_norm_r_tau",
             "median_norm_a_D", "median_norm_r_D"]].to_string(index=False))
    print("\nrandom baseline medians:")
    print(rbdf.to_string(index=False))
    print("\ninput checks:")
    print(json.dumps(checks, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
