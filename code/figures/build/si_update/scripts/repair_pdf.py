# -*- coding: utf-8 -*-
"""Restore the rasters that Word's PDF exporter capped at 200 dpi (S6, S7 only;
S1/S4/S5/S8 are unchanged in kind from the previous high-res build)."""
import os, re, io, zipfile, base64
import pymupdf
from PIL import Image

PDF_IN = r'E:/project/work1/20261126_SI_update_work/out/Supplementary_Information_20261126_updated.pdf'
PDF_OUT = r'E:/project/work1/20261126_SI_update_work/out/_si_rep.pdf'
DOCX = r'E:/project/work1/20261126_SI_update_work/out/Supplementary_Information_20261126_updated.docx'
TMP = r'E:/project/work1/20261126_SI_update_work/work_tmp'
os.makedirs(TMP, exist_ok=True)

z = zipfile.ZipFile(DOCX)
s6 = os.path.join(TMP, 's6.png')
open(s6, 'wb').write(z.read('word/media/final_si6_png.png'))

s7 = z.read('word/media/final_si7_svg_svg.svg').decode('utf-8')
s7r = []
for m in re.finditer(r'xlink:href="data:image/(\w+);base64,([^"]+)"', s7):
    p = os.path.join(TMP, 's7_%d.%s' % (len(s7r), m.group(1)))
    open(p, 'wb').write(base64.b64decode(m.group(2)))
    s7r.append(p)
print('S7 rasters', [(os.path.basename(p), Image.open(p).size) for p in s7r])

doc = pymupdf.open(PDF_IN)

# --- S6 (page 53)
page = doc[52]
imgs = [i for i in page.get_images(full=True) if page.get_image_rects(i[0])]
print('S6 images', [(i[2], i[3]) for i in imgs])
for im in imgs:
    page.replace_image(im[0], filename=s6)

# --- S7 (page 54)
page = doc[53]
imgs = [i for i in page.get_images(full=True) if page.get_image_rects(i[0])]
print('S7 images', [(i[2], i[3]) for i in imgs])
assert len(imgs) == len(s7r), (len(imgs), len(s7r))
for im, path in zip(imgs, s7r):
    page.replace_image(im[0], filename=path)

doc.save(PDF_OUT, garbage=3, deflate=True)
print('saved', PDF_OUT)
