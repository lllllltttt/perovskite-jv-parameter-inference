# -*- coding: utf-8 -*-
"""Render an SVG to PNG/PDF through Chromium (Edge) so that opacity, dashes and
vector text behave exactly as in a browser / Word."""
import os, re, subprocess, sys, tempfile
import pymupdf

EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
WORK = os.path.dirname(os.path.abspath(__file__))


def svg_dims(svg_text):
    m = re.search(r'<svg\b[^>]*>', svg_text)
    attrs = m.group(0)
    w = float(re.search(r'width="([\d.]+)(?:in|px|pt)?"', attrs).group(1))
    unit_w = re.search(r'width="[\d.]+(in|px|pt)?"', attrs).group(1) or 'px'
    h = float(re.search(r'height="([\d.]+)(?:in|px|pt)?"', attrs).group(1))
    unit_h = re.search(r'height="[\d.]+(in|px|pt)?"', attrs).group(1) or 'px'
    conv = {'in': 1.0, 'px': 1 / 96.0, 'pt': 1 / 72.0}
    return w * conv[unit_w], h * conv[unit_h], attrs


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
    d.save(pdf_path.replace('.pdf', '_c.pdf'), garbage=3, deflate=True)
    return pdf_path.replace('.pdf', '_c.pdf'), w_in, h_in


def to_png(svg_path, png_path, width_px, width_in=None):
    pdf, w_in, h_in = to_pdf(svg_path, os.path.join(WORK, '_tmp_render.pdf'), width_in)
    d = pymupdf.open(pdf)
    z = width_px / d[0].rect.width
    p = d[0].get_pixmap(matrix=pymupdf.Matrix(z, z))
    p.save(png_path)
    return p.width, p.height


if __name__ == '__main__':
    print(to_png(sys.argv[1], sys.argv[2], int(sys.argv[3]), float(sys.argv[4]) if len(sys.argv) > 4 else None))
