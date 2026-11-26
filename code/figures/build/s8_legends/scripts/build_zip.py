# -*- coding: utf-8 -*-
import hashlib
import os
import zipfile

ROOT = r"E:\project\work1\20261119_si_s7_legends"
PKG = os.path.join(ROOT, "package", "si_s7_legends")
ZIP = os.path.join(ROOT, "si_s7_legends.zip")

with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for f in sorted(os.listdir(PKG)):
        z.write(os.path.join(PKG, f), "si_s7_legends/" + f)
data = open(ZIP, "rb").read()
print("files:", len(zipfile.ZipFile(ZIP).namelist()))
print("size: %.2f MB" % (len(data) / 1048576.0))
print("md5:", hashlib.md5(data).hexdigest().upper())
