# -*- coding: utf-8 -*-
"""Match a raster picture against candidate SVG assets by rendering + comparing."""
import sys, os, io
import numpy as np
import pymupdf
from PIL import Image


def render_svg(path, w, h):
    d = pymupdf.open(path)
    r = d[0].rect
    z = min(w / r.width, h / r.height)
    p = d[0].get_pixmap(matrix=pymupdf.Matrix(z, z), alpha=False)
    im = Image.frombytes('RGB', (p.width, p.height), p.samples)
    canvas = Image.new('RGB', (w, h), 'white')
    canvas.paste(im, (0, 0))
    return canvas


def score(a, b):
    A = np.asarray(a.convert('L'), dtype=float)
    B = np.asarray(b.convert('L'), dtype=float)
    return float(np.abs(A - B).mean())


def best(target_png, cands, w=420):
    t = Image.open(target_png).convert('RGB')
    ar = t.height / t.width
    tw, th = w, max(1, int(round(w * ar)))
    t = t.resize((tw, th), Image.LANCZOS)
    out = []
    for c in cands:
        try:
            r = render_svg(c, tw, th)
            out.append((score(t, r), c))
        except Exception as e:
            out.append((999, c + '  ERR ' + str(e)[:40]))
    out.sort()
    return out


if __name__ == '__main__':
    tgt = sys.argv[1]
    for s, c in best(tgt, sys.argv[2:])[:6]:
        print('%7.2f  %s' % (s, c))
