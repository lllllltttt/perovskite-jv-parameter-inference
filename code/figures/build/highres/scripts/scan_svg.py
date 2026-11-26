# -*- coding: utf-8 -*-
"""For every exported figure SVG: page size, and for each <image> block its
intrinsic pixel size, on-page display size (page px), and effective dpi at the
final Word insert width."""
import re, os, sys, io, base64
import xml.etree.ElementTree as ET
from PIL import Image

NS = '{http://www.w3.org/2000/svg}'
XL = '{http://www.w3.org/1999/xlink}'

FIGDIR = r'E:/project/work1/20261125_integration/finalfig'
JOBS = [('正文/图片%d.svg' % i, 'Fig%d' % i, 6.8) for i in range(1, 6)] + \
       [('SI/SI%d.svg' % i, 'S%d' % i, 6.27) for i in range(1, 12)]


def mat(s):
    out = (1, 0, 0, 1, 0, 0)
    for part in re.findall(r'[a-zA-Z]+\([^)]*\)', s or ''):
        name = part[:part.index('(')]
        v = [float(x) for x in part[part.index('(') + 1:-1].replace(',', ' ').split()] or [0, 0]
        if name == 'matrix':
            M = tuple(v)
        elif name == 'translate':
            M = (1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0)
        elif name == 'scale':
            M = (v[0], 0, 0, v[1] if len(v) > 1 else v[0], 0, 0)
        elif name == 'rotate':
            import math
            a = math.radians(v[0]); c, s = math.cos(a), math.sin(a)
            M = (c, s, -s, c, 0, 0)
        else:
            M = (1, 0, 0, 1, 0, 0)
        out = mul(out, M)
    return out


def mul(A, B):
    a, b, c, d, e, f = A
    a2, b2, c2, d2, e2, f2 = B
    return (a * a2 + c * b2, b * a2 + d * b2, a * c2 + c * d2, b * c2 + d * d2,
            a * e2 + c * f2 + e, b * e2 + d * f2 + f)


def main():
    print('%-6s %-16s %-10s %-8s %-10s %-9s %-8s %s' %
          ('fig', 'file', 'page(px)', 'ins(in)', 'scale', 'img#', 'intrinsic', 'display px -> dpi'))
    for rel, name, ins in JOBS:
        p = os.path.join(FIGDIR, rel)
        if not os.path.exists(p):
            print('%-6s MISSING %s' % (name, rel)); continue
        try:
            root = ET.parse(p).getroot()
        except Exception as e:
            print('%-6s PARSE FAIL %s' % (name, e)); continue
        w = float(root.get('width', '0').replace('px', '').replace('pt', ''))
        h = float(root.get('height', '0').replace('px', '').replace('pt', ''))
        scale = ins / (w / 96.0)
        rows = []

        def walk(el, M):
            M = mul(M, mat(el.get('transform')))
            if el.tag == NS + 'image':
                iw = float(el.get('width') or 0); ih = float(el.get('height') or 0)
                dw = iw * (M[0] ** 2 + M[1] ** 2) ** .5
                dh = ih * (M[2] ** 2 + M[3] ** 2) ** .5
                href = el.get(XL + 'href') or ''
                m = re.match(r'data:image/(\w+);base64,(.*)$', href, re.S)
                pix = None
                if m:
                    try:
                        pix = Image.open(io.BytesIO(base64.b64decode(re.sub(r'\s', '', m.group(2))))).size
                    except Exception:
                        pass
                rows.append((pix, m.group(1) if m else '?', dw * scale, dh * scale,
                             (pix[0] / (dw * scale / 96)) if pix else 0))
            for c in el:
                walk(c, M)

        walk(root, (1, 0, 0, 1, 0, 0))
        if not rows:
            print('%-6s %-16s %-10s %-8.2f %-10.4f %s' % (name, os.path.basename(rel), '%dx%d' % (w, h), ins, scale, 'NO IMAGES (pure vector)'))
        for i, (pix, fmt, dw, dh, dpi) in enumerate(rows, 1):
            print('%-6s %-16s %-10s %-8.2f %-10.4f %-8d %-9s %6.1fx%-6.1f -> %5.0f dpi  %s' %
                  (name, os.path.basename(rel), '%dx%d' % (w, h), ins, scale, i,
                   '%dx%d' % pix if pix else '?', dw, dh, dpi, fmt))


if __name__ == '__main__':
    main()
