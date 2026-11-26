# -*- coding: utf-8 -*-
"""Verify a checkout (or download) against the released checksum manifests.

    python code/verify_manifest.py                 # repository files only
    python code/verify_manifest.py --assets DIR    # also the downloaded archives

Exit code 0 only when every listed file matches.

The repository manifest (``docs/FILE_MANIFEST_SHA256.txt``) was computed from
the committed blobs, and ``.gitattributes`` sets ``eol=lf`` for every text file,
so a fresh clone reproduces the listed hashes byte for byte on any platform.
If a file differs only by CRLF it is reported as ``eol`` -- that means the
checkout ignored .gitattributes, not that the content changed.

The asset manifest (``docs/ASSET_MANIFEST_SHA256.txt``) covers the release
archives.  They are not in the repository; point ``--assets`` at the directory
you downloaded them into.
"""
import argparse
import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_MANIFEST = os.path.join(ROOT, "docs", "FILE_MANIFEST_SHA256.txt")
ASSET_MANIFEST = os.path.join(ROOT, "docs", "ASSET_MANIFEST_SHA256.txt")


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def parse(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.rstrip("\n").split("  ")
            if len(parts) != 3 or len(parts[0]) != 64:
                continue
            out.append((parts[0], int(parts[1]), parts[2]))
    return out


def check(base, entries, label):
    ok = missing = failed = eol = 0
    problems = []
    for want, size, rel in entries:
        p = os.path.join(base, rel)
        if not os.path.exists(p):
            missing += 1
            problems.append(("missing", rel))
            continue
        b = open(p, "rb").read()
        if sha256_bytes(b) == want:
            ok += 1
        elif sha256_bytes(b.replace(b"\r\n", b"\n")) == want:
            eol += 1
            problems.append(("eol", rel))
        else:
            failed += 1
            problems.append(("failed", rel))
        if len(b) != size:
            problems.append(("size", rel))
    print(f"{label}: {len(entries)} entries | ok {ok} | eol {eol} | "
          f"failed {failed} | missing {missing}")
    for kind, rel in problems[:40]:
        print(f"  {kind:8s} {rel}")
    if len(problems) > 40:
        print(f"  ... {len(problems) - 40} more")
    return failed, missing, eol


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--assets", default=None,
                    help="directory containing the downloaded *.tar.gz assets")
    a = ap.parse_args()

    failed = missing = eol = 0
    if os.path.exists(REPO_MANIFEST):
        f, m, e = check(ROOT, parse(REPO_MANIFEST), "repository")
        failed += f; missing += m; eol += e
    else:
        print("missing", REPO_MANIFEST)
        return 2

    if a.assets:
        if not os.path.exists(ASSET_MANIFEST):
            print("missing", ASSET_MANIFEST)
            return 2
        entries = [(h, s, os.path.basename(p)) for h, s, p in parse(ASSET_MANIFEST)]
        f, m, e = check(a.assets, entries, "assets")
        failed += f; missing += m; eol += e

    print("\nRESULT:", "PASS" if (failed == 0 and missing == 0) else "FAIL")
    if eol:
        print(f"note: {eol} file(s) differ only by CRLF -- the checkout ignored "
              ".gitattributes; content is unchanged")
    return 0 if (failed == 0 and missing == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
