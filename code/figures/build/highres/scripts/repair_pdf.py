# -*- coding: utf-8 -*-
"""
Word exports PDFs with every raster capped at ~200 dpi.  Put the 600-dpi raster
back: each image XObject is replaced by the corresponding crop of the 600-dpi
figure PNG that was rendered from the same SVG.
"""
import os, sys, io, re
import numpy as np
import pymupdf
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svg_rects import image_rects


def page_images(page):
    out = []
    for img in page.get_images(full=True):
        xref = img[0]
        rects = page.get_image_rects(xref)
        for r in rects:
            out.append((xref, r))
    return out


def fit(svg_rects, pdf_rects):
    """pair by drawing order when counts agree, else by aspect; then LSQ fit"""
    pairs = []
    if len(svg_rects) == len(pdf_rects):
        pairs = list(zip(svg_rects, [r for _, r in pdf_rects]))
    else:
        used = set()
        for (xr, r) in pdf_rects:
            pa = r.width / r.height
            best = None
            for i, sr in enumerate(svg_rects):
                if i in used:
                    continue
                sa = sr[4] / sr[5]
                d = abs(sa - pa) / pa
                if best is None or d < best[0]:
                    best = (d, i)
            if best and best[0] < 0.03:
                used.add(best[1])
                pairs.append((svg_rects[best[1]], r))
    if len(pairs) < 2:
        return None, pairs
    Ax = np.array([[sr[2], 1] for sr, _ in pairs])
    Ay = np.array([[sr[3], 1] for sr, _ in pairs])
    bx = np.array([r.x0 for _, r in pairs])
    by = np.array([r.y0 for _, r in pairs])
    sx, x0 = np.linalg.lstsq(Ax, bx, rcond=None)[0]
    sy, y0 = np.linalg.lstsq(Ay, by, rcond=None)[0]
    res = max(np.abs(Ax @ np.array([sx, x0]) - bx).max(), np.abs(Ay @ np.array([sy, y0]) - by).max())
    return (sx, sy, x0, y0, res), pairs


def repair(pdf_path, out_path, jobs, dpi=600):
    doc = pymupdf.open(pdf_path)
    log = []
    for page_no, svg_path, png_path in jobs:
        page = doc[page_no - 1]
        png = Image.open(png_path).convert('RGB')
        k = dpi / 72.0
        svg_r = image_rects(svg_path)
        pdf_r = page_images(page)
        f, pairs = fit(svg_r, pdf_r)
        if f is None:
            log.append((page_no, 'NO FIT', len(pdf_r)))
            continue
        sx, sy, X0, Y0, res = f
        # sanity: scale must match the png resolution
        exp = 0.7733
        if not (0.6 < sx < 0.9):
            log.append((page_no, 'SCALE MISMATCH %.4f vs %.4f' % (sx, exp), len(pdf_r)))
            continue
        n = 0
        for xr, r in pdf_r:
            x0 = (r.x0 - X0) * k
            y0 = (r.y0 - Y0) * k
            x1 = (r.x1 - X0) * k
            y1 = (r.y1 - Y0) * k
            x0, y0 = max(0, int(round(x0))), max(0, int(round(y0)))
            x1, y1 = min(png.width, int(round(x1))), min(png.height, int(round(y1)))
            if x1 - x0 < 2 or y1 - y0 < 2:
                continue
            crop = png.crop((x0, y0, x1, y1))
            tmp = os.path.join(os.path.dirname(os.path.abspath(png_path)), '_crop_tmp.png')
            crop.save(tmp)
            try:
                page.replace_image(xr, filename=tmp)
                n += 1
            except Exception as e:
                pass
        log.append((page_no, 'res=%.2fpt scale=%.4f X0=%.2f Y0=%.2f' % (res, sx, X0, Y0), '%d/%d images' % (n, len(pdf_r))))
    doc.save(out_path, garbage=3, deflate=True)
    return log


JOBS_MS = [(5, r'E:/project/work1/20261125_integration/highres_20261125/figs/Figure2.svg',
            r'E:/project/work1/20261125_integration/highres_20261125/figs/Figure2.png'),
           (7, r'E:/project/work1/20261125_integration/highres_20261125/figs/Figure3.svg',
            r'E:/project/work1/20261125_integration/highres_20261125/figs/Figure3.png'),
           (9, r'E:/project/work1/20261125_integration/highres_20261125/figs/Figure4.svg',
            r'E:/project/work1/20261125_integration/highres_20261125/figs/Figure4.png'),
           (11, r'E:/project/work1/20261125_integration/highres_20261125/figs/Figure5.svg',
             r'E:/project/work1/20261125_integration/highres_20261125/figs/Figure5.png')]

JOBS_SI = [(49, r'E:/project/work1/20261125_integration/highres_20261125/figs/FigureS1.png'),
           (51, r'E:/project/work1/20261125_integration/highres_20261125/figs/FigureS4.png'),
           (52, r'E:/project/work1/20261125_integration/highres_20261125/figs/FigureS5.png'),
           (53, r'E:/project/work1/20261125_integration/highres_20261125/figs/FigureS6.png'),
           (54, r'E:/project/work1/20261125_integration/highres_20261125/figs/FigureS7.png'),
           (55, r'E:/project/work1/20261125_integration/highres_20261125/figs/FigureS8.png')]

if __name__ == '__main__':
    D = r'E:/project/work1/20261125_integration/highres_20261125'
    for r in repair(os.path.join(D, 'deliverables/Manuscript_20261125_highres.pdf'),
                    os.path.join(D, 'deliverables/_ms_rep.pdf'), JOBS_MS):
        print('MS', r)
