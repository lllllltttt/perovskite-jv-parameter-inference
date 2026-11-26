# -*- coding: utf-8 -*-
"""Zip the delivery folder (UTF-8 names, stored foldering, no junk)."""
import hashlib
import os
import zipfile

ROOT = r"E:\project\work1\20261119_si_s4_meanlines"
PKG = os.path.join(ROOT, "package", "si_s4_meanlines")
ZIP = os.path.join(ROOT, "si_s4_meanlines.zip")

with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for f in sorted(os.listdir(PKG)):
        p = os.path.join(PKG, f)
        z.write(p, "si_s4_meanlines/" + f)

with open(ZIP, "rb") as fh:
    data = fh.read()
print("files:", len(zipfile.ZipFile(ZIP).namelist()))
print("size: %.2f MB" % (len(data) / 1048576.0))
print("md5:", hashlib.md5(data).hexdigest().upper())
