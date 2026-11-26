# -*- coding: utf-8 -*-
"""Replace S3 with the 1.3:1 version and shrink its Word extent height
(width unchanged), leaving every other part of the SI untouched."""
import os, zipfile

BASE = r'E:/project/work1/20261126_SI_update_work/out/Supplementary_Information_20261126_S3_updated.docx'
DST = r'E:/project/work1/20261126_SI_update_work/out/Supplementary_Information_20261126_S3_ratio_updated.docx'
S3D = r'E:/project/work1/20261126_SI_update_work/s3'

OLD_CY = '6483665'
NEW_CY = '5350761'          # 421.3197 pt * 12700

REPL = {
    'word/media/final_si3_svg_svg.svg': os.path.join(S3D, 'FigureS3.svg'),
    'word/media/final_si3_png.png': os.path.join(S3D, 'FigureS3.png'),
}

zin = zipfile.ZipFile(BASE)
doc = zin.read('word/document.xml').decode('utf-8')
old_wp = '<wp:extent cx="5732126" cy="%s"/>' % OLD_CY
new_wp = '<wp:extent cx="5732126" cy="%s"/>' % NEW_CY
old_a = '<a:ext cx="5732126" cy="%s"/>' % OLD_CY
new_a = '<a:ext cx="5732126" cy="%s"/>' % NEW_CY
assert doc.count(old_wp) == 1, doc.count(old_wp)
assert doc.count(old_a) == 1, doc.count(old_a)
doc = doc.replace(old_wp, new_wp).replace(old_a, new_a)
print('S3 extent height: %.4f -> %.4f in' % (int(OLD_CY) / 914400, int(NEW_CY) / 914400))

zout = zipfile.ZipFile(DST, 'w', zipfile.ZIP_DEFLATED)
for item in zin.infolist():
    data = zin.read(item.filename)
    if item.filename == 'word/document.xml':
        data = doc.encode('utf-8')
    elif item.filename in REPL:
        data = open(REPL[item.filename], 'rb').read()
        print('replaced', item.filename, len(data))
    zout.writestr(item, data, compress_type=item.compress_type)
zout.close(); zin.close()
print('written', DST, os.path.getsize(DST))
