# -*- coding: utf-8 -*-
"""Swap the re-laid-out Figure S3 into the latest SI docx (all else untouched)."""
import os, zipfile, io

BASE = r'E:/project/work1/20261126_SI_update_work/out/Supplementary_Information_20261126_updated.docx'
DST = r'E:/project/work1/20261126_SI_update_work/out/Supplementary_Information_20261126_S3_updated.docx'
S3D = r'E:/project/work1/20261126_SI_update_work/s3'

REPL = {
    'word/media/final_si3_svg_svg.svg': os.path.join(S3D, 'FigureS3.svg'),
    'word/media/final_si3_png.png': os.path.join(S3D, 'FigureS3.png'),
}

zin = zipfile.ZipFile(BASE)
zout = zipfile.ZipFile(DST, 'w', zipfile.ZIP_DEFLATED)
for item in zin.infolist():
    data = zin.read(item.filename)
    if item.filename in REPL:
        data = open(REPL[item.filename], 'rb').read()
        print('replaced', item.filename, len(data))
    zout.writestr(item, data, compress_type=item.compress_type)
zout.close(); zin.close()
print('written', DST, os.path.getsize(DST))
