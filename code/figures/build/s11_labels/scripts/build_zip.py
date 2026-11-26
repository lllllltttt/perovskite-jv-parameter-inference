# -*- coding: utf-8 -*-
import hashlib
import os
import zipfile

ROOT = r"E:\project\work1\20261119_si_s10_labels"
PKG = os.path.join(ROOT, "package", "s10_value_labels")
ZIP = os.path.join(ROOT, "s10_value_labels.zip")

with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for f in sorted(os.listdir(PKG)):
        z.write(os.path.join(PKG, f), "s10_value_labels/" + f)
data = open(ZIP, "rb").read()
print("files:", len(zipfile.ZipFile(ZIP).namelist()))
print("size: %.2f MB" % (len(data) / 1048576.0))
print("md5:", hashlib.md5(data).hexdigest().upper())
