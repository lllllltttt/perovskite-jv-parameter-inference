# -*- coding: utf-8 -*-
"""
Word's PDF export caps every raster at ~200 dpi.  Restore the native rasters:
each image XObject is replaced by the PNG that the composed figure SVG carries
(same content, full resolution, alpha preserved).
"""
import os, sys, re, base64, io
import numpy as np
import pymupdf
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svg_rects import image_rects

W = r'E:/project/work1/20261125_integration/highres_20261125/work'


def page_images(page):
    out = []
    seen = set()
    for img in page.get_images(full=True):
        xref = img[0]
        if xref in seen:
            continue
        seen.add(xref)
        rects = page.get_image_rects(xref)
        if rects:
            out.append((xref, rects[0], img[2], img[3]))
    return out


def svg_rasters(svg_path):
    s = open(svg_path, encoding='utf-8').read()
    out = []
    for m in re.finditer(r'<image[^>]*?xlink:href="data:image/(\w+);base64,([A-Za-z0-9+/=\s]+?)"[^>]*>', s, re.S):
        out.append((m.group(1), base64.b64decode(re.sub(r'\s', '', m.group(2)))))
    return out


def repair(pdf_in, pdf_out, jobs):
    doc = pymupdf.open(pdf_in)
    log = []
    for page_no, svg_path in jobs:
        page = doc[page_no - 1]
        pdf_imgs = page_images(page)
        rasters = svg_rasters(svg_path)
        if not pdf_imgs:
            log.append((page_no, 'no images', 0))
            continue
        if not rasters:
            log.append((page_no, 'no rasters in svg', len(pdf_imgs)))
            continue
        if len(rasters) != len(pdf_imgs):
            log.append((page_no, 'count mismatch %d vs %d' % (len(rasters), len(pdf_imgs)), 0))
            continue
        n = 0
        for (xref, rect, iw, ih), (fmt, data) in zip(pdf_imgs, rasters):
            tmp = os.path.join(W, '_tmp_%d.png' % xref)
            open(tmp, 'wb').write(data)
            try:
                page.replace_image(xref, filename=tmp)
                n += 1
            except Exception as e:
                log.append((page_no, 'ERR %s' % e, 0))
            os.remove(tmp)
        log.append((page_no, 'replaced %d' % n, len(pdf_imgs)))
    doc.save(pdf_out, garbage=3, deflate=True)
    return log


D = r'E:/project/work1/20261125_integration/highres_20261125'
if __name__ == '__main__':
    ms = [(5, D + '/figs/Figure2.svg')]
    for r in repair(D + '/deliverables/Manuscript_20261125_highres.pdf', D + '/deliverables/_ms_rep.pdf', ms):
        print('MS', r)
    si = [(49, D + '/../finalfig/SI/SI1.svg'), (54, D + '/figs/FigureS7.svg'), (55, D + '/../finalfig/SI/SI8.svg')]
    for r in repair(D + '/deliverables/Supplementary_Information_20261125_highres.pdf',
                    D + '/deliverables/_si_rep.pdf', si):
        print('SI', r)
    # S6: single whole-figure PNG (no SVG in the docx)
    doc = pymupdf.open(D + '/deliverables/_si_rep.pdf')
    page = doc[52]
    for img in page.get_images(full=True):
        rects = page.get_image_rects(img[0])
        if rects:
            page.replace_image(img[0], filename=D + '/figs/FigureS6.png')
            print('SI S6 replaced', img[2], img[3], '->', Image.open(D + '/figs/FigureS6.png').size)
    doc.save(D + '/deliverables/_si_rep2.pdf', garbage=3, deflate=True)
