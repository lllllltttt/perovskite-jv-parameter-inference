# -*- coding: utf-8 -*-
"""Package the delivery and verify archive integrity (CRC + SHA256)."""
import hashlib
import os
import zipfile

ROOT = r"E:\project\work1\20261019_NN_stability"
OUT = r"E:\project\work1\20261019_NN_stability_deliverables.zip"
SKIP_DIRS = {"__pycache__"}
SKIP_EXT = {".pyc", ".zip"}


def main():
    files = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for fn in sorted(filenames):
            if os.path.splitext(fn)[1].lower() in SKIP_EXT:
                continue
            p = os.path.join(dirpath, fn)
            arc = os.path.join("20261019_NN_stability",
                               os.path.relpath(p, ROOT)).replace("\\", "/")
            files.append((p, arc))

    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED,
                         compresslevel=6) as z:
        for p, arc in files:
            z.write(p, arc)

    with zipfile.ZipFile(OUT, "r") as z:
        bad = z.testzip()
        infos = z.infolist()
        total = sum(i.file_size for i in infos)

    h = hashlib.sha256()
    with open(OUT, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    print("zip:", OUT)
    print("entries:", len(infos), "uncompressed bytes:", total)
    print("compressed bytes:", os.path.getsize(OUT))
    print("testzip:", "OK" if bad is None else "BAD: %s" % bad)
    print("sha256:", h.hexdigest())
    return 0 if bad is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
