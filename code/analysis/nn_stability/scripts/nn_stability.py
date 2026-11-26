# -*- coding: utf-8 -*-
"""Random-subset stability analysis with duplicate collapse (M1 only).

Each replicate
--------------
1. draw 15,307 test indices with replacement;
2. collapse to the unique original curves (actual n_unique is recorded and is
   NOT treated as fixed at 15,307);
3. rebuild the directed nearest-neighbour graph on that subset, excluding
   self-distance, using the frozen normalized 131-point current vectors;
4. map directed links to ordered (min, max) keys and deduplicate;
5. draw the random-pair baseline from the same subset with the archived rule
   (default_rng(42), 200,000 ordered index pairs, self-pairs dropped);
6. record the median absolute difference of each of the six paired
   coordinates for all pairs and the closest 10/5/1/0.5/0.1% tiers, raw and
   normalized by the subset's own random-pair median.

Interpretation: this is a *random-subset stability analysis with duplicate
collapse*.  Percentiles across replicates are descriptive resampling
percentile ranges, not confidence intervals, not a bootstrap CI, and not
independent experimental replicates.

Read-only on frozen data.  No network, no COMSOL solve, no scaler refit.

Resume: rows are appended to out/stability/per_replicate.csv with fsync after
each replicate.  Re-running with a larger --target skips completed replicates.
"""
import argparse
import csv
import hashlib
import json
import os
import platform
import sys
import time
import traceback

import numpy as np

BASE = r"E:\project\work1"
OUT = os.path.join(BASE, "20261019_NN_stability", "out", "stability")
os.makedirs(OUT, exist_ok=True)

DATA_NPZ = os.path.join(BASE, "data", "dataset_normalized.npz")
FROZEN_NPZ = os.path.join(BASE, "final_figures", "scripts", "_frozen_preds.npz")
SCALER_PKL = os.path.join(BASE, "data", "param_scaler.pkl")

COORD_IDS = ["a_mu", "r_mu", "a_tau", "r_tau", "a_D", "r_D"]
TIERS = [("t10", 0.10), ("t5", 0.05), ("t1", 0.01),
         ("t05", 0.005), ("t01", 0.001)]
PAIR_SETS = ["all"] + [t[0] for t in TIERS]
SEED = 20261019          # deterministic base seed for the 1,000 replicates
RANDOM_SEED = 42         # archived random-pair rule
N_RANDOM = 200000
N_TEST = 15307
N_VOLTAGE = 131
DEFAULT_TARGET = 1000
CSV_PATH = os.path.join(OUT, "per_replicate.csv")
LOG_PATH = os.path.join(OUT, "run_log.txt")


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
    """Archived M1 rule: Euclidean in normalized J space, self excluded."""
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


def load_inputs():
    import pickle
    f = np.load(FROZEN_NPZ, allow_pickle=True)
    d = np.load(DATA_NPZ, allow_pickle=True)
    with open(SCALER_PKL, "rb") as fh:
        sc = pickle.load(fh)["scaler"]
    raw = f["params_test_raw"].astype(np.float64)
    L = np.log10(raw)
    assert np.max(np.abs(
        L - (f["params_test"].astype(np.float64) * sc.data_range_
             + sc.data_min_))) < 1e-9
    Jn = f["J_test"].astype(np.float64)
    assert Jn.shape == (N_TEST, N_VOLTAGE)
    assert L.shape == (N_TEST, 9)
    return L, coordinates(L), Jn


def thread_info():
    info = {
        "python": sys.version,
        "numpy": np.__version__,
        "platform": platform.platform(),
        "os_cpu_count": os.cpu_count(),
        "env_thread_vars": {k: os.environ.get(k) for k in
                            ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                             "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS",
                             "VECLIB_MAXIMUM_THREADS")},
        "numpy_config": None,
    }
    try:
        cfg = np.__config__.show(mode="dicts")
        blas = cfg.get("Build Dependencies", {}).get("blas", {})
        info["numpy_config"] = {"blas": blas,
                                "lapack": cfg.get("Build Dependencies", {}).get("lapack", {})}
    except Exception:
        pass
    try:
        from threadpoolctl import threadpool_info as tpi
        info["threadpoolctl"] = tpi()
    except Exception:
        info["threadpoolctl"] = None
    return info


def one_replicate(rep, L, C, Jn):
    N = L.shape[0]
    rng = np.random.default_rng([SEED, rep])
    draw = rng.integers(0, N, N)
    uniq = np.unique(draw)                 # duplicate collapse
    n_unique = int(uniq.size)

    Js = Jn[uniq]
    Cs = C[uniq]
    nn, _ = nearest_neighbours(Js)
    ni, nj, _ = dedup_undirected(nn, n_unique)
    n_pairs = int(ni.size)

    dJ = np.sqrt(np.sum((Js[ni] - Js[nj]) ** 2, axis=1) / Js.shape[1])
    absd = {cid: np.abs(Cs[ni, k] - Cs[nj, k])
            for k, cid in enumerate(COORD_IDS)}

    ra, rb = random_pairs(n_unique)
    rand_med = {cid: float(np.median(np.abs(Cs[ra, k] - Cs[rb, k])))
                for k, cid in enumerate(COORD_IDS)}

    order = np.argsort(dJ, kind="stable")
    sets = {"all": order}
    tier_counts = {}
    for tag, frac in TIERS:
        k = tier_k(n_pairs, frac)
        sets[tag] = order[:k]
        tier_counts[tag] = int(k)

    deg = np.bincount(np.concatenate([ni, nj]), minlength=n_unique)
    deg01 = np.bincount(
        np.concatenate([ni[sets["t01"]], nj[sets["t01"]]]), minlength=n_unique)

    row = {
        "rep": rep,
        "n_unique": n_unique,
        "n_pairs": n_pairs,
        "n_directed": int(nn.size),
        "n_mutual": int(np.sum(nn[nn] == np.arange(n_unique))),
        "distinct_all": int(np.unique(np.concatenate([ni, nj])).size),
        "multi_all": int(np.sum(deg > 1)),
        "max_all": int(deg.max()),
        "distinct_t01": int(np.unique(np.concatenate(
            [ni[sets["t01"]], nj[sets["t01"]]])).size),
        "multi_t01": int(np.sum(deg01 > 1)),
        "max_t01": int(deg01.max()),
    }
    for tag in ["t10", "t5", "t1", "t05", "t01"]:
        row["n_" + tag] = tier_counts[tag]
    for cid in COORD_IDS:
        row["rand_" + cid] = rand_med[cid]
    for tag in PAIR_SETS:
        sel = sets[tag]
        row["median_dJ_" + tag] = float(np.median(dJ[sel]))
        for k, cid in enumerate(COORD_IDS):
            v = absd[cid][sel]
            row["absd_%s_%s" % (tag, cid)] = float(np.median(v))
            row["norm_%s_%s" % (tag, cid)] = float(np.median(v) / rand_med[cid])
    return row


def load_done():
    """Return completed replicate numbers, truncating a partial last line."""
    if not os.path.exists(CSV_PATH):
        return set()
    with open(CSV_PATH, "r", encoding="utf-8", newline="") as fh:
        text = fh.read()
    if not text.endswith("\n"):
        cut = text.rfind("\n")
        if cut < 0:
            os.remove(CSV_PATH)
            return set()
        print("truncating partial last line of", CSV_PATH)
        with open(CSV_PATH, "w", encoding="utf-8", newline="") as fh:
            fh.write(text[:cut + 1])
    import pandas as pd
    df = pd.read_csv(CSV_PATH)
    return set(int(x) for x in df["rep"].tolist())


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, default=DEFAULT_TARGET,
                    help="total completed replicates to reach (default 1000)")
    ap.add_argument("--max-reps-this-run", type=int, default=None)
    a = ap.parse_args(argv)

    t_start = time.time()
    L, C, Jn = load_inputs()
    done = load_done()
    todo = [r for r in range(1, a.target + 1) if r not in done]
    if a.max_reps_this_run is not None:
        todo = todo[:a.max_reps_this_run]
    print("completed before run: %d; running %d replicates (%s..%s)"
          % (len(done), len(todo), todo[0] if todo else "-", todo[-1] if todo else "-"))

    manifest = {
        "analysis": "random-subset stability analysis with duplicate collapse",
        "metric": "M1 (per-column normalized-J RMSE, full 131-point curve)",
        "seed_base": SEED,
        "rng_rule": "np.random.default_rng([SEED, rep]) per replicate",
        "random_pair_seed": RANDOM_SEED,
        "random_pairs_requested": N_RANDOM,
        "n_test": N_TEST,
        "n_voltage": N_VOLTAGE,
        "target": a.target,
        "thread_info": thread_info(),
        "inputs": {p: {"path": p, "sha256": sha256(p)}
                   for p in (DATA_NPZ, FROZEN_NPZ, SCALER_PKL)},
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    write_header = not os.path.exists(CSV_PATH) or os.path.getsize(CSV_PATH) == 0
    fields = None
    if not write_header:
        with open(CSV_PATH, "r", encoding="utf-8", newline="") as fh:
            fields = next(csv.reader(fh))
    failures = []
    retries = []

    with open(CSV_PATH, "a", encoding="utf-8", newline="") as fh, \
            open(LOG_PATH, "a", encoding="utf-8") as log:
        writer = csv.DictWriter(fh, fieldnames=fields) if fields else None
        for rep in todo:
            t0 = time.time()
            attempt = 0
            while True:
                attempt += 1
                try:
                    row = one_replicate(rep, L, C, Jn)
                    break
                except Exception:
                    tb = traceback.format_exc()
                    if attempt == 1:
                        retries.append({"rep": rep, "error": tb})
                        log.write("RETRY rep=%d\n%s\n" % (rep, tb))
                        log.flush()
                        continue
                    failures.append({"rep": rep, "error": tb})
                    log.write("FAIL rep=%d\n%s\n" % (rep, tb))
                    log.flush()
                    row = None
                    break
            if row is None:
                continue
            dt = time.time() - t0
            row["elapsed_s"] = float(dt)
            if writer is None:
                fields = list(row.keys())
                writer = csv.DictWriter(fh, fieldnames=fields)
                writer.writeheader()
            writer.writerow(row)
            fh.flush()
            os.fsync(fh.fileno())
            log.write("rep=%4d n_unique=%5d n_pairs=%5d t01=%3d %.2fs\n"
                      % (rep, row["n_unique"], row["n_pairs"], row["n_t01"], dt))
            log.flush()
            if rep % 25 == 0 or rep == todo[-1]:
                print("rep %d/%d  n_unique=%d n_pairs=%d  %.2fs"
                      % (rep, a.target, row["n_unique"], row["n_pairs"], dt))

    completed = len(load_done())
    manifest.update({
        "completed_replicates": completed,
        "failures": failures,
        "retries": retries,
        "elapsed_s_this_run": time.time() - t_start,
        "finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "per_replicate_csv": CSV_PATH,
    })
    mpath = os.path.join(OUT, "run_manifest.json")
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False, default=float)
    print("completed:", completed, "failures:", len(failures),
          "retries:", len(retries), "elapsed %.1f s" % manifest["elapsed_s_this_run"])
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
