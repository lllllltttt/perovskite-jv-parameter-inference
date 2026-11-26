# -*- coding: utf-8 -*-
"""Re-open the delivered archives and verify them against MANIFEST.json.

For every entry in the manifest the member is read from the archive, its size
and sha256 are recomputed and compared.  Member lists are compared both ways so
an unrecorded file fails the check as well.  Exit code is non-zero on any
mismatch.
"""
import hashlib
import json
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DELIV = os.path.join(ROOT, "deliverables")


def main():
    man_path = os.path.join(DELIV, "MANIFEST.json")
    with open(man_path, encoding="utf-8") as f:
        man = json.load(f)
    failures = []
    for arc, info in man["archives"].items():
        if not os.path.exists(arc):
            failures.append("missing archive %s" % arc)
            continue
        with zipfile.ZipFile(arc) as zf:
            names = set(zf.namelist())
            recorded = {e["path"] for e in info["files"]}
            for e in info["files"]:
                if e["path"] not in names:
                    failures.append("not in archive: %s :: %s" % (arc, e["path"]))
                    continue
                data = zf.read(e["path"])
                h = hashlib.sha256(data).hexdigest()
                if h != e["sha256"]:
                    failures.append("sha mismatch: %s :: %s" % (arc, e["path"]))
                if len(data) != e["bytes"]:
                    failures.append("size mismatch: %s :: %s" % (arc, e["path"]))
            extra = names - recorded
            if extra:
                failures.append("%s has %d unrecorded members, e.g. %s"
                                % (arc, len(extra), sorted(extra)[:3]))
            if len(info["files"]) != info["n_files"]:
                failures.append("n_files mismatch for %s" % arc)
        print("checked %s : %d files, %.1f MB"
              % (os.path.basename(arc), info["n_files"],
                 os.path.getsize(arc) / 1e6))
    # a few required members
    with zipfile.ZipFile(man["archives"].keys().__iter__().__next__()) as zf:
        names = set(zf.namelist())
    for req in ("PATCH_NOTES.md", "RESULTS.md", "PARAGRAPHS_EN.md", "data_QA.md",
                "README.md", "out/metrics/inference_provenance.csv",
                "out/metrics/before_after_metrics.csv",
                "out/metrics/eval_manifest.json", "out/metrics_v1/metrics_long.csv",
                "out/qa/qa_report.md", "out/qa/inference_validation.json",
                "out/qa/fault_injection_log.json", "out/qa/verification.json",
                "figures/fig03_common_test_paired.png",
                "scripts/04_evaluate.py", "scripts/11_validate_inference.py",
                "scripts/12_before_after.py"):
        if req not in names:
            failures.append("required member missing: %s" % req)
    print("\n%d failures" % len(failures))
    for f in failures:
        print("FAIL", f)
    out = os.path.join(ROOT, "out", "qa", "archive_verification.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write("failures: %d\n" % len(failures))
        for x in failures:
            f.write("FAIL " + x + "\n")
        f.write("ok\n" if not failures else "")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
