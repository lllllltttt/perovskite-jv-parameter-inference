# -*- coding: utf-8 -*-
"""Zip the Fig. 4(d) half-extension deliverable directory and print its sha256."""
import hashlib
import os
import zipfile

ROOT = r"E:\project\work1\20261112_fig4d_clean_half_right"
OUT = r"E:\project\work1\20261112_fig4d_clean_half_right_deliverables.zip"

items = []
for dp, _dn, fn in os.walk(ROOT):
    for f in fn:
        p = os.path.join(dp, f)
        rel = os.path.relpath(p, ROOT).replace(os.sep, "/")
        items.append((rel, p))
items.sort()

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    for rel, p in items:
        z.write(p, rel)

h = hashlib.sha256(open(OUT, "rb").read()).hexdigest()
with open(OUT + ".sha256", "w", encoding="ascii") as f:
    f.write("%s  %s\n" % (h, os.path.basename(OUT)))
print(len(items), "files")
print("sha256", h)
print("size", os.path.getsize(OUT))
