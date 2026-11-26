# -*- coding: utf-8 -*-
"""Build the lightweight review ZIP, the separate model ZIP and a manifest.

The lightweight package carries scripts, configuration, splits, QA outputs,
metrics tables, per-sample predictions, figures and the written reports.  The
trained weights are shipped separately so the review archive stays small; the
manifest lists every file of both archives with size and sha256, and records
which large caches were deliberately left out of both.
"""
import hashlib
import json
import os
import zipfile
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DELIV = os.path.join(ROOT, "deliverables")
os.makedirs(DELIV, exist_ok=True)

RUNS = ["original_20261021", "original_20261022", "original_20261023",
        "original_20261024", "original_20261025",
        "expanded_20261021", "expanded_20261022", "expanded_20261023",
        "expanded_20261024", "expanded_20261025"]

LIGHT = [
    "README.md", "data_QA.md", "RESULTS.md", "EXPERIMENT_DESIGN.md",
    "PARAGRAPHS_EN.md", "PATCH_NOTES.md",
    "config/experiment_config.json",
    "data/split_manifest_original.csv", "data/split_manifest_expanded.csv",
    "data/split_summary.json",
    "data/param_scaler_original.pkl", "data/param_scaler_expanded.pkl",
    "data/current_scaler_original.pkl", "data/current_scaler_expanded.pkl",
    "out/qa", "out/metrics", "out/metrics_v1", "out/predictions",
    "figures", "figures_v1",
    "logs/formal_run_status.json", "logs/driver.log", "logs/runs.jsonl",
    "scripts",
] + ["logs/" + r for r in RUNS] + ["logs/stdout_%s.txt" % r for r in RUNS]
MODELS = ["models/" + r for r in RUNS]
SKIP_EXT = {".pyc"}
EXCLUDE_NAMES = {"arm_original.npz", "arm_expanded.npz"}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def expand(rel):
    p = os.path.join(ROOT, rel)
    if os.path.isfile(p):
        yield p
    elif os.path.isdir(p):
        for d, _, fs in os.walk(p):
            if "__pycache__" in d:
                continue
            for f in sorted(fs):
                if os.path.splitext(f)[1] in SKIP_EXT:
                    continue
                if f in EXCLUDE_NAMES:
                    continue
                yield os.path.join(d, f)


def add_tree(zf, rels):
    entries = []
    for rel in rels:
        for p in expand(rel):
            arc = os.path.relpath(p, ROOT).replace("\\", "/")
            zf.write(p, arc)
            entries.append({"path": arc, "bytes": os.path.getsize(p),
                            "sha256": sha256(p)})
    return entries


def main():
    stamp = datetime.now().strftime("%Y%m%d")
    light_zip = os.path.join(DELIV, "review_package_%s_v2.zip" % stamp)
    model_zip = os.path.join(DELIV, "models_%s_v2.zip" % stamp)

    with zipfile.ZipFile(light_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        light = add_tree(zf, LIGHT)

    with zipfile.ZipFile(model_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        models = add_tree(zf, MODELS)

    excluded = []
    for rel in ("data/arm_original.npz", "data/arm_expanded.npz"):
        p = os.path.join(ROOT, rel)
        if os.path.exists(p):
            excluded.append({"path": rel, "bytes": os.path.getsize(p),
                             "sha256": sha256(p),
                             "reason": "regenerable from 01/02 + the two source CSVs"})

    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "root": ROOT,
        "archives": {
            light_zip: {"files": light, "n_files": len(light),
                        "bytes": os.path.getsize(light_zip)},
            model_zip: {"files": models, "n_files": len(models),
                        "bytes": os.path.getsize(model_zip)},
        },
        "excluded_from_all_archives": excluded + [
            {"path": "out/predictions_v1/", "bytes": 0,
             "reason": ("superseded v1 predictions (71 MB) -- the ten diagonal files are "
                        "numerically identical to v2 and the ten cross-arm files are the buggy "
                        "ones; the full v1 tree, including them, is in the upstream archive "
                        "below")},
        ],
        "upstream_v1_delivery": {
            "root": "E:/project/work1/20261021_expanded_ratio_comparison",
            "review_package": {
                "path": "E:/project/work1/20261021_expanded_ratio_comparison/deliverables/review_package_20261021.zip",
                "sha256": "4bb1e3f270b8696439bee81d5dfbc4f83b78e4acc98dba4f7faf6fee9cb5de57",
                "note": "33,278,991 bytes, 118 files"},
            "model_package": {
                "path": "E:/project/work1/20261021_expanded_ratio_comparison/deliverables/models_20261021.zip",
                "sha256": "6617018bca8471e46c30966123317c2e24cb873ce827eccdfbb1558761aee3f8",
                "note": ("the ten model directories in this v2 delivery are byte-identical to "
                         "this archive; per-file sha256 of every model actually used is in "
                         "out/metrics/inference_provenance.csv and out/metrics/eval_manifest.json")},
        },
        "shipped_only_in_model_archive": [
            {"path": m["path"], "bytes": m["bytes"]} for m in models
        ],
        "source_inputs": [
            {"path": r"E:\project\work1\data\JV_database_9D_interface_lifetimes-2.csv",
             "sha256": sha256(r"E:\project\work1\data\JV_database_9D_interface_lifetimes-2.csv")},
            {"path": r"E:\project\work1\20261021\JV_database_9D_interface_lifetimes-newratio.csv",
             "sha256": sha256(r"E:\project\work1\20261021\JV_database_9D_interface_lifetimes-newratio.csv")},
        ],
        "note": ("Trained weights are in the model archive, not the review "
                 "archive. Arm caches (arm_*.npz) are regenerable and are "
                 "shipped in neither. The smoke-test (logs/_smoke, "
                 "models/_smoke) and the 3-epoch timing probe "
                 "(logs/original_20261021_timing) are execution artefacts "
                 "described in EXPERIMENT_DESIGN.md section 8 and are "
                 "shipped in neither archive."),
    }
    with open(os.path.join(DELIV, "MANIFEST.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print("light zip :", light_zip, "%.1f MB" % (os.path.getsize(light_zip) / 1e6),
          len(light), "files")
    print("model zip :", model_zip, "%.1f MB" % (os.path.getsize(model_zip) / 1e6),
          len(models), "files")


if __name__ == "__main__":
    main()
