# -*- coding: utf-8 -*-
"""Split and partial data preparation for the expanded-ratio pilot.

DRY-RUN BY DEFAULT.  This script never trains a network, never starts a COMSOL
solve, and never writes to the frozen project data.

What it does
------------
* Defines a **new explicit split rule** for the pilot (the published split
  lineage is not fully recoverable, so no reuse of it is claimed):
    - either explicit train/validation/test ratios, or explicit counts;
    - deterministic rounding by the largest-remainder method;
    - a recorded seed and a recorded permutation.
* Stops with an error if the requested split is invalid, if any set would be
  empty, or if the data cannot support three non-empty sets.
* Asserts that the three index sets are disjoint and that their union covers
  every row of the experiment data.
* Fits a parameter MinMaxScaler on log10(parameters), **training partition
  only**, and, when 131 voltage columns are present, a per-voltage current
  MinMaxScaler also **training partition only**.
* Writes the split indices, the scalers, and a manifest containing the seed,
  actual set sizes, input SHA256 and the rule used.

What it does **not** do
-----------------------
Training and evaluation are **not wired**.  ``--stage train`` and
``--stage evaluate`` terminate with an explicit "not wired" message.  This is
therefore a **partial data-preparation utility**, not an end-to-end pipeline.
The preparation is also partial in the scaler sense when the input has no
voltage columns: only the parameter scaler can then be fitted, and the manifest
says so.

Usage
-----
    python pilot_train_eval.py --csv retained.csv --arm expanded \
        --split-ratios 0.70 0.15 0.15                 # dry run
    python pilot_train_eval.py --csv retained.csv --arm expanded \
        --split-counts 10500 2250 2250 --execute --stage prepare
    python pilot_train_eval.py --selftest             # synthetic-data checks
    python pilot_train_eval.py --selftest --fault-injection
                                                      # negative control

Synthetic validation
--------------------
``--selftest`` runs in memory on synthetic data only (n = 15,000, n = 20,000,
a tiny unsplittable sample, an invalid ratio, mismatched counts, missing
parameter columns, 130 and 131 current columns) and writes its log.  It never
reads or writes real data.

Every ``ok=False`` case is recorded as FAIL and counted, including a case that
was *expected* to raise but did not.  ``--fault-injection`` is a negative
control: for the duration of the tiny-unsplittable case only, the test-local
binding of ``make_split`` is replaced by a wrapper that wrongly accepts n = 2.
The production function is not modified.  This must make the selftest report
one FAIL and make the CLI exit non-zero; otherwise the harness itself is
broken.
"""
import argparse
import hashlib
import json
import os
import pickle
import sys
import tempfile

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

STAGE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUTDIR = os.path.join(STAGE, "pilot_out")
DEFAULT_VALIDATION = os.path.join(STAGE, "analysis",
                                  "pilot_split_validation.txt")

PARAMS = ["mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk",
          "Nc_eff_pvk", "Nv_eff_pvk", "tau_interface_ETL_in",
          "tau_interface_HTL_in", "rad_c_in"]
N_VOLTAGE = 131
J_PREFIX = "J_"

SPLIT_RULE = ("new explicit pilot rule: seeded permutation, largest-remainder "
              "allocation of ratios (or explicit counts), non-empty/disjoint/"
              "full-coverage assertions")


class SplitError(ValueError):
    """Raised when the requested split cannot be formed."""


# ---------------------------------------------------------------------------
# Split arithmetic
# ---------------------------------------------------------------------------
def _validate_ratios(ratios):
    r = np.asarray(ratios, dtype=float)
    if r.size != 3:
        raise SplitError("exactly three ratios are required, got %d" % r.size)
    if np.any(~np.isfinite(r)):
        raise SplitError("ratios must be finite")
    if np.any(r <= 0):
        raise SplitError("every ratio must be > 0, got %s" % r.tolist())
    if abs(float(r.sum()) - 1.0) > 1e-9:
        raise SplitError("ratios must sum to 1.0, got %.12f" % float(r.sum()))
    return r


def allocate_counts(n, ratios):
    """Largest-remainder allocation; deterministic and sum-exact.

    Raises SplitError on n < 3 or if any set would be empty.
    """
    if not isinstance(n, (int, np.integer)) or n < 3:
        raise SplitError("n=%r cannot be split into three non-empty sets" % n)
    r = _validate_ratios(ratios)
    raw = r * float(n)
    counts = np.floor(raw).astype(int)
    remainder = int(n - counts.sum())
    # Largest fractional remainder first; ties broken by set order (stable).
    order = np.argsort(-(raw - counts), kind="stable")
    for k in range(remainder):
        counts[order[k % 3]] += 1
    if np.any(counts < 1):
        raise SplitError("allocation would leave an empty set: n=%d, "
                         "ratios=%s -> %s" % (n, r.tolist(), counts.tolist()))
    if int(counts.sum()) != int(n):
        raise SplitError("internal allocation error: %s sums to %d, not %d"
                         % (counts.tolist(), int(counts.sum()), int(n)))
    return counts.tolist()


def validate_counts(n, counts):
    c = np.asarray(counts, dtype=int)
    if c.size != 3:
        raise SplitError("exactly three counts are required, got %d" % c.size)
    if np.any(c < 1):
        raise SplitError("every count must be >= 1, got %s" % c.tolist())
    if int(c.sum()) != int(n):
        raise SplitError("counts must cover all %d rows exactly; got %s "
                         "(sum %d)" % (n, c.tolist(), int(c.sum())))
    return c.tolist()


def make_split(n, *, ratios=None, counts=None, seed=20261019):
    """Return (dict of index arrays, rule dict) with hard assertions."""
    if (ratios is None) == (counts is None):
        raise SplitError("give exactly one of ratios or counts")
    if ratios is not None:
        sizes = allocate_counts(n, ratios)
        rule = {"method": "ratios_largest_remainder",
                "ratios": [float(x) for x in ratios],
                "seed": int(seed)}
    else:
        sizes = validate_counts(n, counts)
        rule = {"method": "explicit_counts",
                "counts": [int(x) for x in sizes],
                "seed": int(seed)}

    perm = np.random.default_rng(int(seed)).permutation(int(n))
    a, b = sizes[0], sizes[0] + sizes[1]
    split = {"train": perm[:a], "val": perm[a:b], "test": perm[b:]}

    for name in ("train", "val", "test"):
        if split[name].size == 0:
            raise SplitError("set %s is empty" % name)
    sets = [set(split[k].tolist()) for k in ("train", "val", "test")]
    if (sets[0] & sets[1]) or (sets[0] & sets[2]) or (sets[1] & sets[2]):
        raise SplitError("index sets overlap")
    union = sets[0] | sets[1] | sets[2]
    if len(union) != int(n):
        raise SplitError("union covers %d of %d rows" % (len(union), int(n)))
    for name in ("train", "val", "test"):
        if int(split[name].min()) < 0 or int(split[name].max()) >= int(n):
            raise SplitError("index out of range in %s" % name)
    rule["sizes"] = [int(x) for x in sizes]
    rule["n"] = int(n)
    return split, rule


# ---------------------------------------------------------------------------
# Data preparation
# ---------------------------------------------------------------------------
def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def current_columns(df):
    return [c for c in df.columns if str(c).startswith(J_PREFIX)]


def prepare(df, *, arm, ratios=None, counts=None, seed=20261019,
            outdir=DEFAULT_OUTDIR, j_units="mA/cm2", j_prefix=J_PREFIX,
            require_matched=None, source_csv=None):
    """Split, validate, fit train-only scalers, write artifacts.

    Returns the manifest dict.  Raises SplitError or ValueError on any invalid
    input.  No model is trained and no solver is called.
    """
    if j_units != "mA/cm2":
        raise ValueError("current units must be mA/cm2 for this pilot; got %r"
                         % j_units)
    missing = [c for c in PARAMS if c not in df.columns]
    if missing:
        raise ValueError("missing parameter columns: %s" % missing)
    n = int(len(df))
    split, rule = make_split(n, ratios=ratios, counts=counts, seed=seed)

    params = df[PARAMS].to_numpy(dtype=float)
    if not np.all(np.isfinite(params)):
        raise ValueError("non-finite parameter values")
    if np.any(params <= 0):
        raise ValueError("parameter values must be > 0 for log10 scaling")

    jcols = [c for c in df.columns if str(c).startswith(j_prefix)]
    if len(jcols) not in (0, N_VOLTAGE):
        raise ValueError("expected 0 or %d columns starting with %r, found %d"
                         % (N_VOLTAGE, j_prefix, len(jcols)))
    if jcols:
        J = df[jcols].to_numpy(dtype=float)
        if not np.all(np.isfinite(J)):
            raise ValueError("non-finite current values")
        if J.shape[1] != N_VOLTAGE:
            raise ValueError("current block has %d columns, expected %d"
                             % (J.shape[1], N_VOLTAGE))

    os.makedirs(outdir, exist_ok=True)

    np.savez(os.path.join(outdir, "split_%s.npz" % arm),
             train=split["train"], val=split["val"], test=split["test"])

    lx = np.log10(params)
    psc = MinMaxScaler().fit(lx[split["train"]])
    with open(os.path.join(outdir, "param_scaler_%s.pkl" % arm), "wb") as f:
        pickle.dump({"scaler": psc,
                     "log10": True,
                     "columns": PARAMS,
                     "fit_partition": "train",
                     "n_fit": int(split["train"].size)}, f)

    scalers = {"parameter": "fitted on train partition only (log10, MinMax)",
               "current": None}
    if jcols:
        J = df[jcols].to_numpy(dtype=float)
        jsc = MinMaxScaler().fit(J[split["train"]])
        with open(os.path.join(outdir, "current_scaler_%s.pkl" % arm),
                  "wb") as f:
            pickle.dump({"scaler": jsc,
                         "columns": jcols,
                         "units": j_units,
                         "n_voltage": len(jcols),
                         "fit_partition": "train",
                         "n_fit": int(split["train"].size)}, f)
        scalers["current"] = ("fitted on train partition only "
                              "(per-voltage MinMax, %d columns, %s)"
                              % (len(jcols), j_units))

    scope = ("parameter scaler only (partial: no voltage columns)"
             if not jcols else
             "parameter + current scalers (partial: training/evaluation "
             "not wired)")

    manifest = {
        "arm": arm,
        "source_csv": source_csv,
        "source_sha256": _sha256(source_csv) if source_csv else None,
        "n_rows": n,
        "parameter_columns": PARAMS,
        "voltage_columns_found": len(jcols),
        "voltage_units": j_units if jcols else None,
        "split_rule": SPLIT_RULE,
        "split": rule,
        "split_sizes": {k: int(split[k].size) for k in
                        ("train", "val", "test")},
        "split_indices_file": "split_%s.npz" % arm,
        "scalers": scalers,
        "preparation_scope": scope,
        "end_to_end": False,
        "training_wired": False,
        "evaluation_wired": False,
        "starts_training": False,
        "starts_solver": False,
    }

    if require_matched:
        with open(require_matched, "r", encoding="utf-8") as f:
            other = json.load(f)
        if other.get("n_rows") != n:
            raise SplitError("matched-arm check failed: n_rows %r vs %r"
                             % (n, other.get("n_rows")))
        if other.get("split_sizes") != manifest["split_sizes"]:
            raise SplitError("matched-arm check failed: sizes %r vs %r"
                             % (manifest["split_sizes"],
                                other.get("split_sizes")))
        manifest["matched_against"] = require_matched

    with open(os.path.join(outdir, "train_plan_%s.json" % arm), "w",
              encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return manifest


# ---------------------------------------------------------------------------
# Synthetic validation
# ---------------------------------------------------------------------------
def _synthetic(n, n_current=0, drop_last_param=False):
    rng = np.random.default_rng(7)
    data = {}
    for i, c in enumerate(PARAMS):
        if drop_last_param and c == PARAMS[-1]:
            continue
        data[c] = 10 ** rng.uniform(-4, 4, n)
    for k in range(n_current):
        data["%s%06.3f" % (J_PREFIX, k * 0.01)] = rng.normal(size=n)
    return pd.DataFrame(data)


def run_selftest(path=DEFAULT_VALIDATION, fault_injection=False):
    lines = ["pilot split / preparation validation (synthetic data only)",
             "generated by scripts/pilot_train_eval.py --selftest",
             "no real, frozen or solver data was read or written"]
    if fault_injection:
        lines.append("FAULT INJECTION: the tiny-unsplittable case must FAIL")
    lines.append("")
    failures = 0

    def record(name, n, expected_sizes, ok, detail):
        nonlocal failures
        # Every negative outcome is a failure.  A correctly raised expected
        # exception is passed in as ok=True by the caller and is a PASS.
        status = "PASS" if ok else "FAIL"
        if not ok:
            failures += 1
        lines.append("%-42s n=%-6s sizes=%-24s %s  %s"
                     % (name, n, expected_sizes, status, detail))

    tmp = tempfile.mkdtemp(prefix="pilot_split_selftest_")
    for n, ratios, expect in ((15000, (0.70, 0.15, 0.15), [10500, 2250, 2250]),
                              (20000, (0.70, 0.15, 0.15), [14000, 3000, 3000])):
        df = _synthetic(n)
        m = prepare(df, arm="selftest", ratios=ratios, outdir=tmp)
        ok = m["split_sizes"] == {"train": expect[0], "val": expect[1],
                                  "test": expect[2]}
        record("valid split, expected ratio", n, m["split_sizes"], ok,
               "rule=%s" % m["split"]["method"])

    # tiny unsplittable (optionally with the isolated negative control)
    if fault_injection:
        _real_make_split = make_split

        def _accept_illegal_split(n, **kwargs):
            """Test-local wrapper: wrongly accept n < 3; production untouched."""
            if n < 3:
                return {k: np.array([], dtype=np.int64)
                        for k in ("train", "val", "test")}
            return _real_make_split(n, **kwargs)

        globals()["make_split"] = _accept_illegal_split
    try:
        try:
            make_split(2, ratios=(0.70, 0.15, 0.15))
            record("tiny unsplittable", 2, None, False, "no error raised")
        except SplitError as e:
            record("tiny unsplittable", 2, None, True, "SplitError: %s" % e)
    finally:
        if fault_injection:
            globals()["make_split"] = _real_make_split

    # invalid ratio (does not sum to 1)
    try:
        make_split(15000, ratios=(0.70, 0.15, 0.10))
        record("invalid ratio (sum != 1)", 15000, None, False, "no error")
    except SplitError as e:
        record("invalid ratio (sum != 1)", 15000, None, True,
               "SplitError: %s" % e)

    # invalid ratio (non-positive)
    try:
        make_split(15000, ratios=(0.80, 0.20, 0.0))
        record("invalid ratio (non-positive)", 15000, None, False, "no error")
    except SplitError as e:
        record("invalid ratio (non-positive)", 15000, None, True,
               "SplitError: %s" % e)

    # counts that do not cover all rows
    try:
        make_split(15000, counts=(10500, 2250, 2200))
        record("counts do not cover all rows", 15000, None, False, "no error")
    except SplitError as e:
        record("counts do not cover all rows", 15000, None, True,
               "SplitError: %s" % e)

    # missing parameter column
    try:
        df = _synthetic(15000, drop_last_param=True)
        prepare(df, arm="selftest", ratios=(0.70, 0.15, 0.15), outdir=tmp)
        record("missing parameter column", 15000, None, False, "no error")
    except ValueError as e:
        record("missing parameter column", 15000, None, True,
               "ValueError: %s" % str(e)[:90])

    # wrong current-column count
    try:
        df = _synthetic(15000, n_current=130)
        prepare(df, arm="selftest", ratios=(0.70, 0.15, 0.15), outdir=tmp)
        record("130 current columns", 15000, None, False, "no error")
    except ValueError as e:
        record("130 current columns", 15000, None, True,
               "ValueError: %s" % str(e)[:90])

    # correct current-column count
    try:
        df = _synthetic(15000, n_current=131)
        m = prepare(df, arm="selftest", ratios=(0.70, 0.15, 0.15), outdir=tmp)
        ok = (m["voltage_columns_found"] == 131
              and m["split_sizes"] == {"train": 10500, "val": 2250,
                                       "test": 2250})
        record("131 current columns", 15000, m["split_sizes"], ok,
               "current scaler fitted on train only")
    except Exception as e:  # noqa: BLE001 - validation must record failures
        record("131 current columns", 15000, None, False,
               "%s: %s" % (type(e).__name__, e))

    lines.append("")
    lines.append("FAILURES: %d" % failures)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return failures


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", help="retained curves CSV for this arm "
                                 "(not required with --selftest)")
    ap.add_argument("--arm", choices=["original", "expanded"])
    ap.add_argument("--split-ratios", type=float, nargs=3)
    ap.add_argument("--split-counts", type=int, nargs=3)
    ap.add_argument("--seed", type=int, default=20261019)
    ap.add_argument("--outdir", default=DEFAULT_OUTDIR)
    ap.add_argument("--j-units", default="mA/cm2",
                    help="current units; only mA/cm2 is accepted")
    ap.add_argument("--require-matched",
                    help="path to another arm's train_plan JSON; sizes must "
                         "match")
    ap.add_argument("--execute", action="store_true",
                    help="perform the split and fit scalers (still no "
                         "training)")
    ap.add_argument("--stage", choices=["prepare", "train", "evaluate"],
                    default="prepare")
    ap.add_argument("--selftest", action="store_true",
                    help="run synthetic-data validation and exit")
    ap.add_argument("--fault-injection", action="store_true",
                    help="negative control for --selftest: make the "
                         "tiny-unsplittable case wrongly pass; the selftest "
                         "must then report a failure and exit non-zero")
    ap.add_argument("--validation-out", default=DEFAULT_VALIDATION)
    return ap.parse_args(argv)


def main(argv=None):
    a = parse_args(argv)

    if a.selftest:
        return run_selftest(a.validation_out, a.fault_injection)
    if a.fault_injection:
        sys.exit("--fault-injection is only valid with --selftest")

    if not a.csv or not a.arm:
        sys.exit("--csv and --arm are required unless --selftest is used")
    if (a.split_ratios is None) == (a.split_counts is None):
        sys.exit("give exactly one of --split-ratios or --split-counts")
    if not os.path.exists(a.csv):
        sys.exit("CSV not found: %s" % a.csv)

    print("=== expanded-ratio pilot: split / partial preparation ===")
    print("arm                    :", a.arm)
    print("retained CSV           :", a.csv)
    print("split rule             :", SPLIT_RULE)
    print("split input            :",
          ("ratios %s" % a.split_ratios) if a.split_ratios is not None
          else ("counts %s" % a.split_counts))
    print("seed                   :", a.seed)
    print("parameter scaler       : MinMax on log10(params), TRAIN only")
    print("current scaler         : per-voltage MinMax, TRAIN only "
          "(if 131 voltage columns exist)")
    print("training / evaluation  : NOT WIRED")
    print("solver started         : NO")
    print("training started       : NO")

    if a.stage in ("train", "evaluate"):
        sys.exit("Stage %r is not wired in this round; this script is a "
                 "partial data-preparation utility only. Start training or "
                 "evaluation only in a later, approved round." % a.stage)

    if not a.execute:
        # Dry-run: report the plan only.  If the CSV is readable, report the
        # sizes the rule would produce without writing anything.
        print("\nDRY RUN: no split, no scaler, no training, no solver.")
        try:
            df = pd.read_csv(a.csv)
            split, rule = make_split(
                len(df), ratios=a.split_ratios, counts=a.split_counts,
                seed=a.seed)
            print("would produce sizes    :",
                  {k: int(split[k].size) for k in ("train", "val", "test")})
            print("voltage columns found  :",
                  len([c for c in df.columns
                       if str(c).startswith(J_PREFIX)]))
        except Exception as e:  # noqa: BLE001 - dry run reports, never writes
            print("dry-run check failed   : %s: %s"
                  % (type(e).__name__, e))
        return 0

    df = pd.read_csv(a.csv)
    try:
        manifest = prepare(
            df, arm=a.arm, ratios=a.split_ratios, counts=a.split_counts,
            seed=a.seed, outdir=a.outdir, j_units=a.j_units,
            require_matched=a.require_matched, source_csv=a.csv)
    except (SplitError, ValueError) as e:
        sys.exit("preparation failed: %s: %s" % (type(e).__name__, e))

    print("\nprepared in", a.outdir)
    print("actual split sizes     :", manifest["split_sizes"])
    print("preparation scope      :", manifest["preparation_scope"])
    print("end-to-end             : NO (training/evaluation not wired)")
    print("No network was trained and no solver was started.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
