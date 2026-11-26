# -*- coding: utf-8 -*-
"""Render SVG -> PDF (Chromium print) -> PNG at a requested pixel width."""
import os, re, subprocess, sys
import pymupdf

EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
WORK = os.path.dirname(os.path.abspath(__file__))


def svg_dims(svg_text):
    m = re.search(r'<svg\b[^>]*>', svg_text)
    attrs = m.group(0)
    wm = re.search(r'\bwidth="([\d.]+)(in|px|pt)?"', attrs)
    hm = re.search(r'\bheight="([\d.]+)(in|px|pt)?"', attrs)
    conv = {'in': 1.0, 'px': 1 / 96.0, 'pt': 1 / 72.0, '': 1 / 96.0, None: 1 / 96.0}
    return float(wm.group(1)) * conv[wm.group(2)], float(hm.group(1)) * conv[hm.group(2)], attrs


def to_pdf(svg_path, pdf_path, width_in=None):
    s = open(svg_path, encoding='utf-8').read()
    w_in, h_in, attrs = svg_dims(s)
    if width_in:
        h_in = h_in * width_in / w_in
        w_in = width_in
    if 'viewBox' not in attrs:
        vb = re.search(r'<svg\b[^>]*width="([\d.]+)[a-z]*"[^>]*height="([\d.]+)', attrs)
        s = s.replace(attrs, attrs[:-1] + ' viewBox="0 0 %s %s" >' % (vb.group(1), vb.group(2)), 1)
    s = s[s.index('<svg'):]
    s = re.sub(r'<svg\b[^>]*>', lambda m: re.sub(r'(width|height)="[\d.]+[a-z]*"', '', m.group(0)), s, count=1)
    html = ('<!doctype html><html><head><meta charset="utf-8"><style>'
            '@page{size:%.5fin %.5fin;margin:0}html,body{margin:0;padding:0;background:#fff}'
            'svg{display:block;width:%.5fin;height:%.5fin}</style></head><body>' % (w_in, h_in, w_in, h_in)) \
           + s + '</body></html>'
    tmp = os.path.join(WORK, '_tmp_print.html')
    open(tmp, 'w', encoding='utf-8').write(html)
    subprocess.run([EDGE, '--headless=new', '--disable-gpu', '--no-pdf-header-footer',
                    '--run-all-compositor-stages-before-draw',
                    '--print-to-pdf=' + pdf_path, 'file:///' + tmp.replace('\\', '/')],
                   capture_output=True)
    d = pymupdf.open(pdf_path)
    pg = d[0]
    r = pg.rect
    pg.set_mediabox(pymupdf.Rect(0, r.height - h_in * 72, w_in * 72, r.height))
    out = pdf_path.replace('.pdf', '_c.pdf')
    d.save(out, garbage=3, deflate=True)
    d.close()
    return out, w_in, h_in


def to_png(svg_path, png_path, width_px, width_in=None):
    pdf, w_in, h_in = to_pdf(svg_path, os.path.join(WORK, '_tmp_render.pdf'), width_in)
    d = pymupdf.open(pdf)
    z = width_px / d[0].rect.width
    p = d[0].get_pixmap(matrix=pymupdf.Matrix(z, z))
    p.save(png_path)
    d.close()
    return p.width, p.height


if __name__ == '__main__':
    src, dst, px = sys.argv[1], sys.argv[2], int(sys.argv[3])
    wi = float(sys.argv[4]) if len(sys.argv) > 4 else None
    print(to_png(src, dst, px, wi))
