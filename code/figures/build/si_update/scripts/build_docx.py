# -*- coding: utf-8 -*-
"""Replace the five figures inside the latest SI docx, leaving everything else
(text, captions, other figures, tables, citations, comments) untouched."""
import os, re, io, shutil, zipfile

BASE = r'E:/project/work1/20261125_integration/highres_20261125/deliverables/Supplementary_Information_20261125.docx'
OUTD = r'E:/project/work1/20261126_SI_update_work/out'
DST = os.path.join(OUTD, 'Supplementary_Information_20261126_updated.docx')
FIG = r'E:/project/work1/20261126_SI_update_work/figures'

REPL = {
    'word/media/final_si1_svg_svg.svg': os.path.join(OUTD, 'FigureS1.svg'),
    'word/media/final_si1_png.png': os.path.join(FIG, 'FigureS1.png'),
    'word/media/final_si2_svg_svg.svg': os.path.join(OUTD, 'FigureS2.svg'),
    'word/media/final_si2_png.png': os.path.join(FIG, 'FigureS2.png'),
    'word/media/final_si4_svg_svg.svg': os.path.join(OUTD, 'FigureS4.svg'),
    'word/media/final_si4_png.png': os.path.join(FIG, 'FigureS4.png'),
    'word/media/final_si8_svg_svg.svg': os.path.join(OUTD, 'FigureS8.svg'),
    'word/media/final_si8_png.png': os.path.join(FIG, 'FigureS8.png'),
    'word/media/final_si10_svg_svg.svg': os.path.join(OUTD, 'FigureS10.svg'),
    'word/media/final_si10_png.png': os.path.join(FIG, 'FigureS10.png'),
}

zin = zipfile.ZipFile(BASE)
doc = zin.read('word/document.xml').decode('utf-8')

# --- S1 only: its canvas is 1280x613 (user widened it so the rotated
#     "Spearman" label is no longer clipped).  Adjust the stored height so the
#     aspect ratio stays true; width is unchanged.
old_ext = '<wp:extent cx="5732126" cy="2790840"/>'
new_ext = '<wp:extent cx="5732126" cy="2745128"/>'
assert doc.count(old_ext) == 1
doc = doc.replace(old_ext, new_ext)
old_aext = '<a:ext cx="5739248" cy="2794308"/>'
new_aext = '<a:ext cx="5739248" cy="2748543"/>'
assert doc.count(old_aext) == 1
doc = doc.replace(old_aext, new_aext)
print('S1 extent 6.2687 x', 2745128 / 914400, 'in')

zout = zipfile.ZipFile(DST, 'w', zipfile.ZIP_DEFLATED)
for item in zin.infolist():
    data = zin.read(item.filename)
    if item.filename == 'word/document.xml':
        data = doc.encode('utf-8')
    elif item.filename in REPL:
        data = io.open(REPL[item.filename], 'rb').read()
        print('replaced', item.filename, len(data))
    zout.writestr(item, data, compress_type=item.compress_type)
zout.close()
zin.close()
print('written', DST, os.path.getsize(DST))
