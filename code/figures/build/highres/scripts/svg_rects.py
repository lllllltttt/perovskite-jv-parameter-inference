# -*- coding: utf-8 -*-
"""On-page rect (in the SVG user units) of every <image> in a composed figure SVG."""
import re, sys, os
import xml.etree.ElementTree as ET

NS = '{http://www.w3.org/2000/svg}'
XL = '{http://www.w3.org/1999/xlink}'


def mat(s):
    out = (1, 0, 0, 1, 0, 0)
    for part in re.findall(r'[a-zA-Z]+\([^)]*\)', s or ''):
        name = part[:part.index('(')]
        v = [float(x) for x in part[part.index('(') + 1:-1].replace(',', ' ').split()]
        if name == 'matrix':
            M = tuple(v)
        elif name == 'translate':
            M = (1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0)
        elif name == 'scale':
            M = (v[0], 0, 0, v[1] if len(v) > 1 else v[0], 0, 0)
        else:
            M = (1, 0, 0, 1, 0, 0)
        a, b, c, d, e, f = out
        a2, b2, c2, d2, e2, f2 = M
        out = (a * a2 + c * b2, b * a2 + d * b2, a * c2 + c * d2, b * c2 + d * d2,
               a * e2 + c * f2 + e, b * e2 + d * f2 + f)
    return out


def image_rects(svg_path):
    root = ET.parse(svg_path).getroot()
    res = []

    def walk(el, M):
        if el.get('transform'):
            a,b,c,d,e,f=M; a2,b2,c2,d2,e2,f2=mat(el.get('transform'))
            M=(a*a2+c*b2, b*a2+d*b2, a*c2+c*d2, b*c2+d*d2, a*e2+c*f2+e, b*e2+d*f2+f)
        if el.tag == NS + 'image':
            w = float(el.get('width')); h = float(el.get('height'))
            x = float(el.get('x') or 0); y = float(el.get('y') or 0)
            a, b, c, d, e, f = M
            pts = [(a*px + c*py + e, b*px + d*py + f) for px, py in
                   ((x, y), (x+w, y), (x, y+h), (x+w, y+h))]
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            res.append((w, h, min(xs), min(ys), max(xs)-min(xs), max(ys)-min(ys)))
        for ch in el:
            walk(ch, M)

    walk(root, (1, 0, 0, 1, 0, 0))
    return res


if __name__ == '__main__':
    for r in image_rects(sys.argv[1]):
        print('%.1fx%.1f at (%.2f,%.2f) size %.2fx%.2f' % r)
