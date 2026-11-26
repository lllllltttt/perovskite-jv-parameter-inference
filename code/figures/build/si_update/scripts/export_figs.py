# -*- coding: utf-8 -*-
"""Export each final SVG to PDF (Chromium) and 600-dpi PNG at the SI insert width."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_svg import to_pdf, to_png
import pymupdf
from PIL import Image

OUT = r'E:/project/work1/20261126_SI_update_work/out'
FIG = r'E:/project/work1/20261126_SI_update_work/figures'
os.makedirs(FIG, exist_ok=True)

W_IN = 6.268729221347332   # wp:extent of every SI figure in the base docx
W_PX = 3762                # 600 dpi

sizes = {}
for n in ('S1', 'S2', 'S4', 'S8', 'S10'):
    src = os.path.join(OUT, 'Figure%s.svg' % n)
    pdf = os.path.join(FIG, 'Figure%s.pdf' % n)
    cpdf, w, h = to_pdf(src, pdf, W_IN)
    os.replace(cpdf, pdf)
    d = pymupdf.open(pdf)
    pg = d[0]
    imgs = pg.get_images(full=True)
    print(n, 'pdf %.4f x %.4f in, images %d, page %.2f x %.2f pt' %
          (w, h, len(imgs), pg.rect.width, pg.rect.height))
    d.close()
    png = os.path.join(FIG, 'Figure%s.png' % n)
    pw, ph = to_png(src, png, W_PX, W_IN)
    im = Image.open(png)
    im.save(png, dpi=(600, 600))
    sizes[n] = {'svg': os.path.getsize(src), 'pdf': os.path.getsize(pdf),
                'png': [pw, ph], 'in': [round(w, 5), round(h, 5)]}
    print('   png', pw, ph)

json.dump(sizes, open(os.path.join(FIG, 'sizes.json'), 'w'), indent=1)
print(json.dumps(sizes, indent=1))
