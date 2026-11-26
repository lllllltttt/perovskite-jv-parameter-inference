# -*- coding: utf-8 -*-
"""Identify which asset each exported JPEG block came from."""
import re, base64, io, os, sys
import numpy as np
from PIL import Image

BASE = r'E:/project/work1'
FIG = os.path.join(BASE, '20261125_integration/finalfig')


def blocks(svg):
    s = open(svg, encoding='utf-8').read()
    out = []
    for m in re.finditer(r'<image[^>]*?width="([\d.]+)" height="([\d.]+)"[^>]*?base64,([A-Za-z0-9+/=]+)"', s):
        out.append(Image.open(io.BytesIO(base64.b64decode(m.group(3)))).convert('RGB'))
    return out


def score(a, b):
    b = b.convert('RGB').resize(a.size, Image.LANCZOS)
    return float(abs(np.asarray(a.convert('RGB'), float) - np.asarray(b, float)).mean())


JOBS = {
    'zhengwen3': (os.path.join(FIG, '正文'), '图片3.svg',
                  ['20261111_fig345_standalone_revision/figures/Fig3d.png',
                   '20261112_fig3ab_shared_yaxis/figures/Fig3b.png',
                   '20261111_fig345_standalone_revision/figures/Fig3c.png',
                   '20261112_fig3ab_shared_yaxis/figures/Fig3a.png',
                   '20261111_fig345_standalone_revision/figures/Fig3a.png']),
    'zhengwen4': (os.path.join(FIG, '正文'), '图片4.svg',
                  ['20261112_fig4d_clean_half_right/figures/Fig4d_clean_half.png',
                   '20261110_fig4_standalone/figures/Fig4a.png',
                   '20261110_fig4_standalone/figures/Fig4b.png',
                   '20261110_fig4_standalone/figures/Fig4c.png',
                   '20261110_fig4de_standalone/figures/Fig4e_Jsc.png',
                   '20261110_fig4de_standalone/figures/Fig4e_Voc.png',
                   '20261110_fig4de_standalone/figures/Fig4e_FF_pp.png',
                   '20261110_fig4de_standalone/figures/Fig4e_PCE.png']),
    'zhengwen5': (os.path.join(FIG, '正文'), '图片5.svg',
                  ['20261111_fig345_standalone_revision/figures/Fig5a.png',
                   '20261111_fig345_standalone_revision/figures/Fig5e.png',
                   '20261110_fig5_standalone/figures/Fig5b.png',
                   '20261110_fig5_standalone/figures/Fig5c.png',
                   '20261110_fig5_standalone/figures/Fig5d.png']),
}

for k, (d, f, cands) in JOBS.items():
    bs = blocks(os.path.join(d, f))
    print('==', k, 'blocks', len(bs), [b.size for b in bs])
    for i, b in enumerate(bs, 1):
        sc = sorted((score(b, Image.open(os.path.join(BASE, c))), os.path.basename(c)) for c in cands)
        print('   block%d -> %-24s %5.1f   (2nd %s %.1f)' % (i, sc[0][1], sc[0][0], sc[1][1], sc[1][0]))
