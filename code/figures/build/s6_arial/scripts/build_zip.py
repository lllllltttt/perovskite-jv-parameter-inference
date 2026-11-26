# -*- coding: utf-8 -*-
import hashlib
import os
import zipfile

ROOT = r"E:\project\work1\20261119_si_s5_arial"
PKG = os.path.join(ROOT, "package", "s5_arial_font")
ZIP = os.path.join(ROOT, "s5_arial_font.zip")

with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for f in sorted(os.listdir(PKG)):
        z.write(os.path.join(PKG, f), "s5_arial_font/" + f)
data = open(ZIP, "rb").read()
print("files:", len(zipfile.ZipFile(ZIP).namelist()))
print("size: %.2f MB" % (len(data) / 1048576.0))
print("md5:", hashlib.md5(data).hexdigest().upper())
