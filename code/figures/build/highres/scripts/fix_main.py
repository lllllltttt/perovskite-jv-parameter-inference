# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from compose import compose

B = r'E:/project/work1'
FIG = os.path.join(B, '20261125_integration/finalfig/正文')
OUT = os.path.join(B, '20261125_integration/highres_20261125/figs')

JOBS = {
    'Figure3': ('图片3.svg', [
        ('img1', '20261111_fig345_standalone_revision/figures/Fig3d.svg'),
        ('img6', '20261112_fig3ab_shared_yaxis/figures/Fig3b.svg'),
        ('img9', '20261111_fig345_standalone_revision/figures/Fig3c.svg'),
    ]),
    'Figure4': ('图片4.svg', [
        ('img1', '20261112_fig4d_clean_half_right/figures/Fig4d_clean_half.svg'),
        ('img3', '20261110_fig4_standalone/figures/Fig4b.svg'),
        ('img5', '20261110_fig4_standalone/figures/Fig4a.svg'),
        ('img8', '20261110_fig4de_standalone/figures/Fig4e_Jsc.svg'),
        ('img11', '20261110_fig4de_standalone/figures/Fig4e_PCE.svg'),
        ('img14', '20261110_fig4de_standalone/figures/Fig4e_FF_pp.svg'),
        ('img17', '20261110_fig4de_standalone/figures/Fig4e_Voc.svg'),
    ]),
    'Figure5': ('图片5.svg', [
        ('img1', '20261111_fig345_standalone_revision/figures/Fig5e.svg'),
        ('img4', '20261110_fig5_standalone/figures/Fig5b.svg'),
        ('img7', '20261110_fig5_standalone/figures/Fig5c.svg'),
        ('img10', '20261110_fig5_standalone/figures/Fig5d.svg'),
        ('img13', '20261111_fig345_standalone_revision/figures/Fig5a.svg'),
    ]),
}

os.makedirs(OUT, exist_ok=True)
for name, (src, blocks) in JOBS.items():
    jobs = [dict(id=i, kind='svg', path=os.path.join(B, p)) for i, p in blocks]
    for j in jobs:
        if not os.path.exists(j['path']):
            raise SystemExit('missing ' + j['path'])
    rep = compose(os.path.join(FIG, src), os.path.join(OUT, name + '.svg'), jobs, 6.8)
    print('==', name, '->', os.path.join(OUT, name + '.svg'))
    for r in rep:
        print('   ', r)
