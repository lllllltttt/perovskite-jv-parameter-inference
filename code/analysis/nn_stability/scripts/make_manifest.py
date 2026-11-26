# -*- coding: utf-8 -*-
"""Build MANIFEST.json: inputs, code, seeds, threads, timing, outputs."""
import hashlib
import json
import os
import time

import matplotlib
import numpy as np
import pandas as pd

ROOT = r"E:\project\work1\20261019_NN_stability"
STAB = os.path.join(ROOT, "out", "stability")
REPRO = os.path.join(ROOT, "out", "reproduction")
OUT = os.path.join(ROOT, "MANIFEST.json")

SKIP_DIRS = {"__pycache__"}
SKIP_FILES = {"MANIFEST.json"}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    with open(os.path.join(STAB, "run_manifest.json"), encoding="utf-8") as fh:
        run = json.load(fh)
    with open(os.path.join(REPRO, "input_verification.json"), encoding="utf-8") as fh:
        inp = json.load(fh)
    with open(os.path.join(REPRO, "reproduction_check.json"), encoding="utf-8") as fh:
        repchk = json.load(fh)

    R = pd.read_csv(os.path.join(STAB, "per_replicate.csv"))
    elapsed = R["elapsed_s"].values

    # inputs read (never written)
    input_paths = {
        "dataset_normalized.npz": r"E:\project\work1\data\dataset_normalized.npz",
        "frozen_predictions": r"E:\project\work1\final_figures\scripts\_frozen_preds.npz",
        "param_scaler.pkl": r"E:\project\work1\data\param_scaler.pkl",
        "J_scaler.pkl": r"E:\project\work1\data\J_scaler.pkl",
        "archived_fig3_pair_summary_v2.csv": os.path.join(
            r"E:\project\work1\20261006\manuscript_figures_SI_integrated_v2_layout_final\data_used",
            "fig3_pair_summary_v2.csv"),
        "archived_fig3_pairs_v2.csv": os.path.join(
            r"E:\project\work1\20261006\manuscript_figures_SI_integrated_v2_layout_final\data_used",
            "fig3_pairs_v2.csv"),
        "archived_fig3_random_baseline_v2.csv": os.path.join(
            r"E:\project\work1\20261006\manuscript_figures_SI_integrated_v2_layout_final\data_used",
            "fig3_random_baseline_v2.csv"),
        "archived_lib_v2.py": os.path.join(
            r"E:\project\work1\20261006\figure_revision_phase1_v2_final\scripts",
            "lib_v2.py"),
        "archived_fig3_pair_analysis_v2.py": os.path.join(
            r"E:\project\work1\20261006\figure_revision_phase1_v2_final\scripts",
            "fig3_pair_analysis_v2.py"),
    }

    # code
    code_paths = {
        "reproduce_original.py": os.path.join(ROOT, "scripts", "reproduce_original.py"),
        "nn_stability.py": os.path.join(ROOT, "scripts", "nn_stability.py"),
        "summarize.py": os.path.join(ROOT, "scripts", "summarize.py"),
        "make_figure.py": os.path.join(ROOT, "scripts", "make_figure.py"),
        "qa_checks.py": os.path.join(ROOT, "scripts", "qa_checks.py"),
        "make_manifest.py": os.path.join(ROOT, "scripts", "make_manifest.py"),
        "pilot_train_eval.py (patched copy)": os.path.join(
            ROOT, "pilot", "pilot_train_eval.py"),
    }

    outputs = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for fn in sorted(filenames):
            if fn in SKIP_FILES or fn.endswith(".zip"):
                continue
            p = os.path.join(dirpath, fn)
            outputs.append(dict(path=os.path.relpath(p, ROOT).replace("\\", "/"),
                                bytes=os.path.getsize(p), sha256=sha256(p)))

    manifest = {
        "analysis": "random-subset stability analysis with duplicate collapse",
        "delivery_root": ROOT,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "seed": {"base": run["seed_base"],
                 "rng_rule": run["rng_rule"],
                 "random_pair_seed": run["random_pair_seed"],
                 "random_pairs_requested": run["random_pairs_requested"]},
        "metric": run["metric"],
        "target_replicates": run["target"],
        "completed_replicates": run["completed_replicates"],
        "failures": run["failures"],
        "retries": run["retries"],
        "timing": {
            "wall_s_this_run": run["elapsed_s_this_run"],
            "started_utc": run["started_utc"],
            "finished_utc": run["finished_utc"],
            "sum_elapsed_s_all_replicates": float(elapsed.sum()),
            "median_s_per_replicate": float(np.median(elapsed)),
            "min_s_per_replicate": float(np.min(elapsed)),
            "max_s_per_replicate": float(np.max(elapsed)),
            "note": ("wall_s_this_run covers only the resumed run from replicate "
                     "11 to 1,000; the 10-replicate trial was timed separately "
                     "at 9.0 s wall. Thread settings were left at library "
                     "defaults; the measured time is not a single-core or "
                     "linear-scaling claim."),
        },
        "threads": run["thread_info"],
        "libraries": {"numpy": np.__version__, "pandas": pd.__version__,
                      "matplotlib": matplotlib.__version__},
        "inputs_read_only": {k: {"path": v, "sha256": sha256(v)}
                             for k, v in input_paths.items()},
        "reproduction": {
            "ok": repchk["reproduction_ok"],
            "n_pairs": repchk["pair_set"]["n_pairs_reproduced"],
            "pair_sets_identical": repchk["pair_set"]["pair_sets_identical"],
            "max_abs_median_difference": repchk["median_statistics_max_abs_difference"],
            "max_abs_random_baseline_difference":
                repchk["random_baseline_max_abs_difference"],
        },
        "code": {k: {"path": v, "sha256": sha256(v)} for k, v in code_paths.items()},
        "outputs": outputs,
        "output_count": len(outputs),
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)
    print("wrote", OUT)
    print("outputs:", len(outputs), "completed:", run["completed_replicates"],
          "failures:", len(run["failures"]), "retries:", len(run["retries"]))


if __name__ == "__main__":
    main()
