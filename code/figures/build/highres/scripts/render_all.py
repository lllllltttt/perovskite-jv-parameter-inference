# -*- coding: utf-8 -*-
"""Render every figure to a 600-dpi PNG at its final Word insert width."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render import to_png

B = r'E:/project/work1/20261125_integration/highres_20261125'
FIGS = os.path.join(B, 'figs')
DXM = os.path.join(B, 'work/Manuscript_20261125_final_figures_text_corrected/word/media')
DXS = os.path.join(B, 'work/Supplementary_Information_20261125_final_figures_text_corrected/word/media')

SRC = {}
for i in range(1, 6):
    SRC['Figure%d' % i] = os.path.join(FIGS, 'Figure%d.svg' % i) if i >= 2 else os.path.join(DXM, 'final_main1_svg_svg.svg')
for i in range(1, 12):
    p = os.path.join(FIGS, 'FigureS%d.svg' % i)
    if not os.path.exists(p):
        p = os.path.join(B, '..', 'finalfig', 'SI', 'SI%d.svg' % i)
    SRC['FigureS%d' % i] = p

WIDTH = {'main': 6.8, 'si': 6.27}
info = {}
for name, p in SRC.items():
    w_in = WIDTH['main'] if name.startswith('Figure') and name[6].isdigit() else WIDTH['si']
    px = int(round(w_in * 600))
    out = os.path.join(FIGS, name + '.png')
    w, h = to_png(p, out, px, w_in)
    info[name] = dict(src=os.path.basename(p), png=os.path.basename(out), w=w, h=h,
                      in_w=w_in, in_h=round(h / 600, 3), dpi=600)
    print('%-10s %-28s %5dx%-5d  %.2f x %.2f in' % (name, info[name]['src'], w, h, w_in, h / 600))
json.dump(info, open(os.path.join(B, 'figs', 'figure_sizes.json'), 'w'), indent=1)
