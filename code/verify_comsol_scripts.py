# -*- coding: utf-8 -*-
"""Static checks on the archived and published COMSOL drivers (no COMSOL/MATLAB).

    python code/verify_comsol_scripts.py \
        --design-main <PSC_LHS_..._200000_3.csv> \
        --design-independent <PSC_LHS_..._300000_5.csv>

Checks
  * the published drivers in `code/comsol/main_200k/` and the independent ones in
    `code/comsol/independent_300k/`: function name equals file name, and every
    table column they read exists in the corresponding design file;
  * the published main drivers against the recovered originals in
    `code/comsol/archive/original_200k/`: same port and row range, and identical
    code outside the header, the path block, the function line and the column
    alias;
  * the path constants of the published main drivers name the released design
    table, the model file and `result-main-200k/`.

Defects in the recovered originals are reported (`original:` lines) and do not
fail the run.  This is a static check: nothing is executed.
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
COMSOL = os.path.join(HERE, "comsol")
MAIN = os.path.join(COMSOL, "main_200k")
INDEP = os.path.join(COMSOL, "independent_300k")
ARCHIVE = os.path.join(COMSOL, "archive", "original_200k")

FUNC_RE = re.compile(r"^function\s+(\w+)\s*\(", re.M)
PORT_RE = re.compile(r"mphstart\((\d+)\)")
START_RE = re.compile(r"start_idx\s*=\s*(\d+)")
N_RE = re.compile(r"^N\s*=\s*(\d+)", re.M)
COL_RE = re.compile(r"tbl\.([A-Za-z_]\w*)")

ALIAS_LINES = {
    "if ~ismember('tau_ETL_in', tbl.Properties.VariableNames)",
    "tbl.tau_ETL_in = tbl.tau_interface_ETL_in;",
    "tbl.tau_HTL_in = tbl.tau_interface_HTL_in;",
    "end",
}
HEADER_RE = re.compile(r"^% (Driver for|Input design:|Output: Sample_)")
CONT_RE = re.compile(r"^(input_path|mph_path|result_dir)\s*=\s*\.\.\.$")
PATH_LINES = {
    "here      = fileparts(mfilename('fullpath'));",
    "repo_root = fileparts(fileparts(fileparts(here)));        "
    "% code/comsol/main_200k -> repository root",
    "input_path = fullfile(repo_root, 'data', '_assets', ...",
    "                      'PSC_LHS_9D_interface_lifetimes_200000_3.csv');",
    "mph_path   = fullfile(repo_root, 'code', 'comsol', '1D_PSC_wen.mph');",
    "result_dir = fullfile(repo_root, 'result-main-200k');",
}
ALIASED = {"tau_ETL_in", "tau_HTL_in"}


def read(p):
    with open(p, encoding="utf-8", newline="") as f:
        return f.read().replace("\r\n", "\n")


def describe(path):
    t = read(path)
    f = FUNC_RE.search(t)
    m = lambda r: r.search(t).group(1) if r.search(t) else None
    cols = {c for c in COL_RE.findall(t) if c != "Properties"} - ALIASED
    return {"text": t, "func": f.group(1) if f else None, "port": m(PORT_RE),
            "start": m(START_RE), "end": m(N_RE), "cols": sorted(cols)}


def body_lines(text):
    """Significant lines: drop the regions that are meant to differ."""
    out = []
    for ln in text.split("\n"):
        s = ln.strip()
        if not s or s in ALIAS_LINES:
            continue
        if s.startswith("function ") or HEADER_RE.match(s) or CONT_RE.match(s):
            continue
        if any(k in s for k in ("fullfile(", "fileparts(", "PSC_LHS_9D",
                                "1D_PSC_wen.mph", "result-main-200k",
                                "/home/student2/")):
            continue
        out.append(s)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--design-main")
    ap.add_argument("--design-independent")
    a = ap.parse_args()
    hdr_main = (open(a.design_main, encoding="utf-8").readline().strip().split(",")
                if a.design_main else None)
    hdr_ind = (open(a.design_independent, encoding="utf-8").readline().strip().split(",")
               if a.design_independent else None)

    fails, notes = [], []

    print("== main_200k (published)")
    for name in sorted(n for n in os.listdir(MAIN) if n.endswith(".m")):
        d = describe(os.path.join(MAIN, name))
        stem = name[:-2]
        print(f"  {name:16s} func={d['func']:14s} port={d['port']} rows {d['start']}..{d['end']}")
        if d["func"] != stem:
            fails.append(f"main_200k/{name}: function name {d['func']}")
        if "result-main-200k" not in d["text"]:
            fails.append(f"main_200k/{name}: output directory is not result-main-200k")
        if "PSC_LHS_9D_interface_lifetimes_200000_3.csv" not in d["text"]:
            fails.append(f"main_200k/{name}: input design is not …_200000_3.csv")
        if hdr_main:
            miss = [c for c in d["cols"] if c not in hdr_main]
            if miss:
                fails.append(f"main_200k/{name}: columns {miss} absent from the design file")
        arch = os.path.join(ARCHIVE, name)
        if os.path.exists(arch):
            o = describe(arch)
            if (o["port"], o["start"], o["end"]) != (d["port"], d["start"], d["end"]):
                fails.append(f"main_200k/{name}: port or row range differs from the original")
            if body_lines(o["text"]) != body_lines(d["text"]):
                fails.append(f"main_200k/{name}: code differs outside the documented regions")

    print("\n== archive/original_200k")
    for name in sorted(n for n in os.listdir(ARCHIVE) if n.endswith(".m")):
        d = describe(os.path.join(ARCHIVE, name))
        stem = name[:-2]
        print(f"  {name:16s} func={d['func']:14s} port={d['port']} rows {d['start']}..{d['end']}")
        if d["func"] != stem:
            notes.append(f"original {name}: function name {d['func']} != {stem} (archived unchanged)")
        if hdr_main:
            miss = [c for c in d["cols"] if c not in hdr_main]
            if miss:
                notes.append(f"original {name}: reads {miss}, the recovered input file supplied them")

    print("\n== independent_300k")
    for name in sorted(n for n in os.listdir(INDEP) if n.endswith(".m")):
        d = describe(os.path.join(INDEP, name))
        stem = name[:-2]
        print(f"  {name:16s} func={d['func']:14s} port={d['port']} rows {d['start']}..{d['end']}")
        if d["func"] != stem:
            fails.append(f"independent_300k/{name}: function name {d['func']}")
        if hdr_ind:
            miss = [c for c in d["cols"] if c not in hdr_ind]
            if miss:
                fails.append(f"independent_300k/{name}: columns {miss} absent from the design file")

    for n in notes:
        print("\noriginal:", n)
    if fails:
        print("\nFAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("\nPASS: published drivers are self-consistent, match the design files, "
          "and match the archived originals outside the documented regions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
