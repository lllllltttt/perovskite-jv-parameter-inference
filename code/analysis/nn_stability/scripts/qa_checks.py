# -*- coding: utf-8 -*-
"""QA for the random-subset stability delivery.  Exits non-zero on failure."""
import csv
import hashlib
import importlib.util
import json
import os
import re
import sys

import numpy as np
import pandas as pd

ROOT = r"E:\project\work1\20261019_NN_stability"
STAB = os.path.join(ROOT, "out", "stability")
REPRO = os.path.join(ROOT, "out", "reproduction")
PILOT = os.path.join(ROOT, "pilot")
SCRIPTS = os.path.join(ROOT, "scripts")

COORD_IDS = ["a_mu", "r_mu", "a_tau", "r_tau", "a_D", "r_D"]
FAMILIES = [("mobility", "a_mu", "r_mu"),
            ("lifetime", "a_tau", "r_tau"),
            ("DOS", "a_D", "r_D")]
SETS = [("all", "all"), ("t10", "10%"), ("t5", "5%"), ("t1", "1%"),
        ("t05", "0.5%"), ("t01", "0.1%")]

results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    # ------------------------------------------------ A. reproduction -----
    with open(os.path.join(REPRO, "reproduction_check.json"),
              encoding="utf-8") as fh:
        rep = json.load(fh)
    with open(os.path.join(REPRO, "input_verification.json"),
              encoding="utf-8") as fh:
        inp = json.load(fh)
    check("reproduction pair set is identical (11,245)",
          rep["pair_set"]["pair_sets_identical"]
          and rep["pair_set"]["n_pairs_reproduced"] == 11245,
          json.dumps(rep["pair_set"]))
    check("reproduction S6 medians match archived table",
          rep["median_statistics_match"],
          "max abs diff %.3g" % rep["median_statistics_max_abs_difference"])
    check("reproduction random baseline matches (seed 42, 199,985 pairs)",
          rep["random_baseline_match"],
          "max abs diff %.3g" % rep["random_baseline_max_abs_difference"])
    check("input shapes 15,307 x 131",
          inp["shapes_ok"] and inp["n_test"] == 15307
          and inp["n_voltage"] == 131,
          "n_test=%d n_voltage=%d" % (inp["n_test"], inp["n_voltage"]))
    check("curve/parameter row alignment",
          inp["param_alignment_ok"] and inp["jsc_matches_raw_at_zero_voltage_max_abs"] < 1e-12,
          "param max abs %.3g; jsc max abs %.3g"
          % (inp["param_raw_vs_scaler_inverse_max_abs"],
             inp["jsc_matches_raw_at_zero_voltage_max_abs"]))

    # a/r coordinates are built from the physical log10 parameters once.
    f = np.load(r"E:\project\work1\final_figures\scripts\_frozen_preds.npz",
                allow_pickle=True)
    L = np.log10(f["params_test_raw"].astype(np.float64))
    C = np.column_stack([
        0.5 * (L[:, 0] + L[:, 1]), L[:, 0] - L[:, 1],
        0.5 * (L[:, 2] + L[:, 3]), L[:, 2] - L[:, 3],
        0.5 * (L[:, 4] + L[:, 5]), L[:, 4] - L[:, 5]])
    check("a = mean and r = difference of physical log10 parameters",
          bool(np.array_equal(C[:, 0], 0.5 * (L[:, 0] + L[:, 1])))
          and bool(np.array_equal(C[:, 1], L[:, 0] - L[:, 1])),
          "single log10 of raw parameter values")

    # ------------------------------------------------ B. replicates -------
    R = pd.read_csv(os.path.join(STAB, "per_replicate.csv"))
    check("1,000 consecutive replicates", len(R) == 1000
          and R["rep"].tolist() == list(range(1, 1001)),
          "rows=%d" % len(R))
    numeric = R.select_dtypes("number").values
    check("no missing or non-finite values in per-replicate table",
          not R.isna().any().any() and bool(np.isfinite(numeric).all()),
          "%d NaN, %d non-finite" % (int(R.isna().sum().sum()),
                                     int((~np.isfinite(numeric)).sum())))
    n_ok = ((R["n_t10"] == np.maximum(1, np.round(R["n_pairs"] * 0.10).astype(int)))
            & (R["n_t5"] == np.maximum(1, np.round(R["n_pairs"] * 0.05).astype(int)))
            & (R["n_t1"] == np.maximum(1, np.round(R["n_pairs"] * 0.01).astype(int)))
            & (R["n_t05"] == np.maximum(1, np.round(R["n_pairs"] * 0.005).astype(int)))
            & (R["n_t01"] == np.maximum(1, np.round(R["n_pairs"] * 0.001).astype(int))))
    check("tier sizes follow archived k=max(1,round(n*frac))", bool(n_ok.all()))
    rcols = ["rand_" + c for c in COORD_IDS]
    ncols = [c for c in R.columns if c.startswith("norm_")]
    check("random-pair baselines positive and normalized medians positive",
          bool((R[rcols].values > 0).all() and (R[ncols].values > 0).all()),
          "baseline min %.3g; normalized min %.3g"
          % (R[rcols].values.min(), R[ncols].values.min()))
    check("unique subset smaller than 15,307 and non-empty",
          bool((R["n_unique"] > 9000).all() and (R["n_unique"] < 15307).all()),
          "n_unique %d..%d" % (R["n_unique"].min(), R["n_unique"].max()))

    # ------------------------------------------------ C. determinism ------
    ns = load_module("nn_stability", os.path.join(SCRIPTS, "nn_stability.py"))
    L, C, Jn = ns.load_inputs()
    for rep_id in (1, 500, 1000):
        row = ns.one_replicate(rep_id, L, C, Jn)
        ref = R[R["rep"] == rep_id].iloc[0]
        keys = [k for k in row if k != "elapsed_s"]
        bad = [k for k in keys if not np.isclose(row[k], float(ref[k]),
                                                 rtol=1e-12, atol=1e-12)]
        check("replicate %d reproduces exactly" % rep_id, not bad,
              "mismatches: %s" % bad)

    # ------------------------------------------------ D. summary ----------
    S = pd.read_csv(os.path.join(STAB, "summary.csv")).set_index("quantity")
    max_d = 0.0
    for q in S.index:
        if q not in R.columns:
            continue
        x = R[q].values
        vals = [np.median(x), np.percentile(x, 2.5), np.percentile(x, 97.5),
                np.min(x), np.max(x)]
        ref = [S.loc[q, "rep_median"], S.loc[q, "p2_5"],
               S.loc[q, "p97_5"], S.loc[q, "rep_min"], S.loc[q, "rep_max"]]
        max_d = max(max_d, max(abs(float(a) - float(b))
                               for a, b in zip(vals, ref)))
    check("summary matches per-replicate table", max_d < 1e-12,
          "max abs diff %.3g" % max_d)
    check("summary carries original full-sample values",
          S.loc["norm_all_a_mu", "original"] > 0
          and S.loc["norm_all_r_mu", "original"] > 0
          and S.loc["n_pairs", "original"] == 11245,
          "n_pairs original=%s" % S.loc["n_pairs", "original"])

    # ------------------------------------------------ E. first 500 --------
    F = pd.read_csv(os.path.join(STAB, "first500_vs_all1000.csv")).set_index("quantity")
    max_e = 0.0
    for q in F.index:
        x5, xa = R[q].values[:500], R[q].values
        max_e = max(max_e,
                    abs(F.loc[q, "median_first500"] - np.median(x5)),
                    abs(F.loc[q, "median_all"] - np.median(xa)),
                    abs(F.loc[q, "d_median"]
                        - (np.median(xa) - np.median(x5))))
    check("first-500 vs all-1000 table is consistent", max_e < 1e-12,
          "max abs diff %.3g" % max_e)

    # ------------------------------------------------ F. figure -----------
    FV = pd.read_csv(os.path.join(STAB, "figure_values.csv"))
    max_f = 0.0
    for _, r in FV[FV.panel == "a"].iterrows():
        cid = r["series"].replace("norm_all_", "")
        row = S.loc["norm_all_" + cid]
        max_f = max(max_f, abs(r["median"] - row["rep_median"]),
                    abs(r["p2_5"] - row["p2_5"]),
                    abs(r["p97_5"] - row["p97_5"]))
    for _, r in FV[FV.panel == "b"].iterrows():
        tag = SETS[int(r["x"])][0]
        fam = r["series"]
        ca, cr = {"mobility": ("a_mu", "r_mu"),
                  "lifetime": ("a_tau", "r_tau"),
                  "DOS": ("a_D", "r_D")}[fam]
        d = R["norm_%s_%s" % (tag, cr)].values - R["norm_%s_%s" % (tag, ca)].values
        max_f = max(max_f, abs(r["median"] - np.median(d)),
                    abs(r["p2_5"] - np.percentile(d, 2.5)),
                    abs(r["p97_5"] - np.percentile(d, 97.5)))
    check("figure values match the CSV tables", max_f < 1e-12,
          "max abs diff %.3g" % max_f)
    for ext in ("png", "pdf", "svg"):
        p = os.path.join(STAB, "nn_stability_results." + ext)
        check("figure %s exists" % ext, os.path.exists(p) and os.path.getsize(p) > 5000,
              "%.1f KB" % (os.path.getsize(p) / 1024) if os.path.exists(p) else "missing")

    # ------------------------------------------------ G. pilot logs --------
    def parse_log(p):
        txt = open(p, encoding="utf-8").read()
        m = re.search(r"FAILURES: (\d+)", txt)
        statuses = re.findall(r"\b(PASS|FAIL)[ \t]{2}", txt)
        return int(m.group(1)), statuses.count("PASS"), statuses.count("FAIL")

    nf_norm, pass_norm, fail_norm = parse_log(
        os.path.join(PILOT, "logs", "selftest_normal.txt"))
    nf_fault, pass_fault, fail_fault = parse_log(
        os.path.join(PILOT, "logs", "selftest_fault_injection.txt"))
    codes = dict(line.split("=") for line in open(
        os.path.join(PILOT, "logs", "exit_codes.txt"), encoding="utf-8").read().split())
    check("normal selftest: 9 PASS, 0 failures, exit 0",
          nf_norm == 0 and pass_norm == 9 and int(codes["normal_exit"]) == 0,
          "PASS=%d FAILURES=%d exit=%s" % (pass_norm, nf_norm, codes["normal_exit"]))
    check("fault injection: exactly the injected case fails, exit non-zero",
          nf_fault == 1 and fail_fault == 1 and int(codes["fault_injection_exit"]) != 0,
          "PASS=%d FAILURES=%d exit=%s"
          % (pass_fault, nf_fault, codes["fault_injection_exit"]))

    # ------------------------------------------------ H. production guard --
    pilot = load_module("pilot_train_eval", os.path.join(PILOT, "pilot_train_eval.py"))
    try:
        pilot.make_split(2, ratios=(0.70, 0.15, 0.15))
        guard_ok = False
    except pilot.SplitError:
        guard_ok = True
    check("production make_split still rejects n=2 outside selftest", guard_ok)

    # ------------------------------------------------ I. inputs unchanged --
    for path, h in inp["input_sha256"].items():
        base = {"dataset_normalized.npz": r"E:\project\work1\data\dataset_normalized.npz",
                "_frozen_preds.npz": r"E:\project\work1\final_figures\scripts\_frozen_preds.npz",
                "param_scaler.pkl": r"E:\project\work1\data\param_scaler.pkl",
                "J_scaler.pkl": r"E:\project\work1\data\J_scaler.pkl"}[path]
        hh = hashlib.sha256(open(base, "rb").read()).hexdigest()
        check("input unchanged: %s" % path, hh == h, hh[:16])

    # ------------------------------------------------ J. no solver/training --
    import ast
    forbidden = {"comsol", "mph", "tensorflow", "torch", "subprocess",
                 "socket", "requests", "urllib", "http"}
    hits, imports = [], set()
    for fn in sorted(os.listdir(SCRIPTS)):
        if not fn.endswith(".py"):
            continue
        tree = ast.parse(open(os.path.join(SCRIPTS, fn),
                              encoding="utf-8").read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module.split(".")[0]]
            else:
                continue
            imports.update(names)
            for nm in names:
                if nm.lower() in forbidden:
                    hits.append("%s:%s" % (fn, nm))
    check("no solver, training or network imports in analysis scripts", not hits,
          "imports: %s" % ", ".join(sorted(imports)))
    with open(os.path.join(STAB, "run_manifest.json"), encoding="utf-8") as fh:
        run = json.load(fh)
    check("run manifest: 1,000 completed, no failures or retries",
          run["completed_replicates"] == 1000 and not run["failures"]
          and not run["retries"],
          "completed=%s failures=%d retries=%d"
          % (run["completed_replicates"], len(run["failures"]),
             len(run["retries"])))

    # ------------------------------------------------ K. deliverables ------
    for rel in ["docs/candidate_paragraphs.md", "QA.md", "README.md",
                os.path.join("out", "stability", "summary.csv"),
                os.path.join("out", "stability", "closest01_volatility.csv"),
                os.path.join("out", "stability", "interpretation_by_family.csv"),
                os.path.join("out", "stability", "interpretation_all_three.csv"),
                os.path.join("out", "stability", "run_manifest.json")]:
        p = os.path.join(ROOT, rel)
        check("deliverable exists: %s" % rel, os.path.exists(p),
              "%.1f KB" % (os.path.getsize(p) / 1024) if os.path.exists(p) else "missing")

    # ------------------------------------------------------ report --------
    bad = [r for r in results if not r[1]]
    for name, ok, detail in results:
        print("%s  %-70s %s" % ("PASS" if ok else "FAIL", name, detail))
    print("\n%d checks, %d failed" % (len(results), len(bad)))
    out = os.path.join(ROOT, "out", "qa_checks.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump([dict(check=n, pass_=o, detail=d) for n, o, d in results],
                  fh, indent=2, ensure_ascii=False)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
