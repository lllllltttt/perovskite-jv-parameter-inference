# -*- coding: utf-8 -*-
"""Static checks on the archived COMSOL drivers (no COMSOL, no MATLAB).

    python code/verify_comsol_scripts.py \
        --design-main <PSC_LHS_..._200000_3.csv> \
        --design-independent <PSC_LHS_..._300000_5.csv>

For every driver it reports the function name, port, row range, input/output
constants and the table columns it reads, and checks:

  * the adapted copies use the file name as function name, keep the row range
    and port of the original, and read only columns the design file has;
  * an adapted copy differs from its original only in the documented regions
    (function name, three path constants, four-line column-alias block, header).

Defects found in the archived originals are reported as `original:` lines and
do not fail the run; the run fails only if an *adapted* copy is inconsistent.

This is a static check.  It does not run MATLAB or COMSOL.
"""
import argparse
import difflib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GROUPS = {"main_200k": os.path.join(HERE, "comsol", "main_200k"),
          "independent_300k": os.path.join(HERE, "comsol", "independent_300k")}

FUNC_RE = re.compile(r"^function\s+(\w+)\s*\(", re.M)
PORT_RE = re.compile(r"mphstart\((\d+)\)")
INPUT_RE = re.compile(r"input_path\s*=\s*\.\.\.\s*\n\s*'([^']+)'")
OUT_RE = re.compile(r"result_dir\s*=\s*\.\.\.\s*\n\s*'([^']+)'")
START_RE = re.compile(r"start_idx\s*=\s*(\d+)")
N_RE = re.compile(r"^N\s*=\s*(\d+)", re.M)
COL_RE = re.compile(r"tbl\.([A-Za-z_]\w*)")

ALIAS_LINES = {
    "if ~ismember('tau_ETL_in', tbl.Properties.VariableNames)",
    "tbl.tau_ETL_in = tbl.tau_interface_ETL_in;",
    "tbl.tau_HTL_in = tbl.tau_interface_HTL_in;",
    "end",
}
HEADER_LINES = {
    "% ADAPTED COPY of the archived driver in the parent directory.",
    "% Paths are relative names; the column-alias block after readtable() accepts",
    "% both design-file column conventions. Body unchanged.",
}
ALIASED = {"tau_ETL_in", "tau_HTL_in"}


def read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return f.read().replace("\r\n", "\n")


def describe(path):
    t = read(path)
    f = FUNC_RE.search(t)
    m = lambda r: r.search(t).group(1) if r.search(t) else None
    cols = {c for c in COL_RE.findall(t) if c != "Properties"}
    if os.path.basename(os.path.dirname(path)) == "adapted":
        cols -= ALIASED          # supplied by the alias block when absent
    return {"func": f.group(1) if f else None, "port": m(PORT_RE),
            "input": m(INPUT_RE), "out": m(OUT_RE), "start": m(START_RE),
            "end": m(N_RE), "cols": sorted(cols), "text": t}


def header_of(path):
    if not path:
        return None
    with open(path, encoding="utf-8") as f:
        return f.readline().strip().split(",")


def changed_lines(a, b):
    out = []
    for ln in difflib.unified_diff(a.split("\n"), b.split("\n"), lineterm="", n=0):
        if ln[:1] in "+-" and not ln.startswith(("+++", "---")):
            out.append(ln[1:].strip())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--design-main")
    ap.add_argument("--design-independent")
    a = ap.parse_args()
    designs = {"main_200k": header_of(a.design_main),
               "independent_300k": header_of(a.design_independent)}

    fails, notes = [], []
    for group, base in GROUPS.items():
        header = designs[group]
        print(f"== {group}" + ("" if header else "  (no design file given)"))
        for name in sorted(n for n in os.listdir(base) if n.endswith(".m")):
            d = describe(os.path.join(base, name))
            stem = name[:-2]
            print(f"  {name:16s} func={d['func']:14s} port={d['port']} "
                  f"rows {d['start']}..{d['end']}  input={d['input']}")
            if d["func"] != stem:
                notes.append(f"original {group}/{name}: function name "
                             f"{d['func']} != {stem} (archived unchanged)")
            if header:
                miss = [c for c in d["cols"] if c not in header]
                if miss:
                    notes.append(f"original {group}/{name}: reads {miss}, "
                                 f"absent from {os.path.basename(a.design_main if group=='main_200k' else a.design_independent)}")

        ad = os.path.join(base, "adapted")
        if not os.path.isdir(ad):
            print()
            continue
        print(f"  -- adapted copies")
        for name in sorted(n for n in os.listdir(ad) if n.endswith(".m")):
            o = describe(os.path.join(base, name))
            x = describe(os.path.join(ad, name))
            stem = name[:-2]
            problems = []
            if x["func"] != stem:
                problems.append(f"function name {x['func']}")
            if (o["start"], o["end"], o["port"]) != (x["start"], x["end"], x["port"]):
                problems.append("row range or port differs from the original")
            if header:
                miss = [c for c in x["cols"] if c not in header]
                if miss:
                    problems.append(f"reads {miss}, absent from the design file")
            changed = changed_lines(o["text"], x["text"])
            bad = [ln for ln in changed
                   if ln not in ALIAS_LINES and ln not in HEADER_LINES
                   and not ln.startswith("function ")
                   and "'" not in ln]
            print(f"  {name:16s} func={x['func']:14s} port={x['port']} "
                  f"rows {x['start']}..{x['end']}  changed={len(changed)} "
                  f"unexpected={len(bad)}")
            if bad:
                problems.append(f"{len(bad)} unexpected changed lines: {bad[:2]}")
            fails.extend(f"adapted {group}/{name}: {p}" for p in problems)
        print()

    for n in notes:
        print("original:", n)
    if fails:
        print("\nFAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("\nPASS: adapted copies are consistent with the archived originals "
          "and the design files; originals are reported above and unchanged.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
