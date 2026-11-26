# -*- coding: utf-8 -*-
"""Rebuild Figure 2 (and re-run 3/4/5) from the SVG copies that live in the docx."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compose import compose

B = r'E:/project/work1'
DX = os.path.join(B, '20261125_integration/highres_20261125/work/Manuscript_20261125_final_figures_text_corrected/word/media')
A = os.path.join(B, '20261109_fig2_final_D_assets')
OUT = os.path.join(B, '20261125_integration/highres_20261125/figs')

JOBS = {
    'Figure2': ('final_main2_svg_svg.svg', [
        ('img2', os.path.join(A, 'panels/a3_Density_of_states.svg')),
        ('img5', os.path.join(A, 'panels/a1_Mobility.svg')),
        ('img8', os.path.join(A, 'panels/a2_Bulk_lifetime.svg')),
        ('img11', os.path.join(A, 'panels/b1_Mobility.svg')),
        ('img14', os.path.join(A, 'panels/b2_Bulk_lifetime.svg')),
        ('img17', os.path.join(A, 'panels/b3_Density_of_states.svg')),
        ('img20', os.path.join(A, 'colorbars/Colorbar_log_ratio_orange.svg')),
        ('img23', os.path.join(A, 'colorbars/Colorbar_shared_scale_blue.svg')),
    ]),
    'Figure3': ('final_main3_svg_svg.svg', [
        ('img1', os.path.join(B, '20261111_fig345_standalone_revision/figures/Fig3d.svg')),
        ('img6', os.path.join(B, '20261112_fig3ab_shared_yaxis/figures/Fig3b.svg')),
        ('img9', os.path.join(B, '20261111_fig345_standalone_revision/figures/Fig3c.svg')),
    ]),
    'Figure4': ('final_main4_svg_svg.svg', [
        ('img1', os.path.join(B, '20261112_fig4d_clean_half_right/figures/Fig4d_clean_half.svg')),
        ('img3', os.path.join(B, '20261110_fig4_standalone/figures/Fig4b.svg')),
        ('img5', os.path.join(B, '20261110_fig4_standalone/figures/Fig4a.svg')),
        ('img8', os.path.join(B, '20261110_fig4de_standalone/figures/Fig4e_Jsc.svg')),
        ('img11', os.path.join(B, '20261110_fig4de_standalone/figures/Fig4e_PCE.svg')),
        ('img14', os.path.join(B, '20261110_fig4de_standalone/figures/Fig4e_FF_pp.svg')),
        ('img17', os.path.join(B, '20261110_fig4de_standalone/figures/Fig4e_Voc.svg')),
    ]),
    'Figure5': ('final_main5_svg_svg.svg', [
        ('img1', os.path.join(B, '20261111_fig345_standalone_revision/figures/Fig5e.svg')),
        ('img4', os.path.join(B, '20261110_fig5_standalone/figures/Fig5b.svg')),
        ('img7', os.path.join(B, '20261110_fig5_standalone/figures/Fig5c.svg')),
        ('img10', os.path.join(B, '20261110_fig5_standalone/figures/Fig5d.svg')),
        ('img13', os.path.join(B, '20261111_fig345_standalone_revision/figures/Fig5a.svg')),
    ]),
}

for name, (f, blocks) in JOBS.items():
    jobs = [dict(id=i, kind='svg', path=p) for i, p in blocks]
    rep = compose(os.path.join(DX, f), os.path.join(OUT, name + '.svg'), jobs, 6.8)
    print('==', name, len(rep), 'blocks')
