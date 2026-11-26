# -*- coding: utf-8 -*-
"""Copy the two text_corrected docx and swap in the high-resolution figure media."""
import os, zipfile, shutil

B = r'E:/project/work1/20261125_integration'
DEL = os.path.join(B, 'deliverables')
HR = os.path.join(B, 'highres_20261125')
FIGS = os.path.join(HR, 'figs')
OUT = os.path.join(HR, 'deliverables')
os.makedirs(OUT, exist_ok=True)

JOBS = [
    ('Manuscript_20261125_final_figures_text_corrected.docx', 'Manuscript_20261125_highres.docx', {
        'word/media/final_main2_svg_svg.svg': 'Figure2.svg',
        'word/media/final_main3_svg_svg.svg': 'Figure3.svg',
        'word/media/final_main4_svg_svg.svg': 'Figure4.svg',
        'word/media/final_main5_svg_svg.svg': 'Figure5.svg',
        **{'word/media/final_main%d_png.png' % i: 'Figure%d.png' % i for i in range(1, 6)},
    }),
    ('Supplementary_Information_20261125_final_figures_text_corrected.docx',
     'Supplementary_Information_20261125_highres.docx', {
         'word/media/final_si4_svg_svg.svg': 'FigureS4.svg',
         'word/media/final_si5_svg_svg.svg': 'FigureS5.svg',
         'word/media/final_si7_svg_svg.svg': 'FigureS7.svg',
         **{'word/media/final_si%d_png.png' % i: 'FigureS%d.png' % i for i in range(1, 12)},
     }),
]

for src, dst, repl in JOBS:
    srcp = os.path.join(DEL, src)
    dstp = os.path.join(OUT, dst)
    zin = zipfile.ZipFile(srcp, 'r')
    zout = zipfile.ZipFile(dstp, 'w', zipfile.ZIP_DEFLATED, compresslevel=6)
    done = set()
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename in repl:
            p = os.path.join(FIGS, repl[item.filename])
            data = open(p, 'rb').read()
            done.add(item.filename)
        zout.writestr(item, data)
    zin.close(); zout.close()
    missing = set(repl) - done
    print('%-58s %8.1f MB  replaced %d  missing %s' %
          (dst, os.path.getsize(dstp) / 1e6, len(done), sorted(missing) if missing else '-'))
