# -*- coding: utf-8 -*-
"""S5: 336 histogram-bar fragments -> inline the nine original panel SVGs."""
import re, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compose import parse_tf, mul, apply, fmt, load_asset, prefix_ids, expand_block
from fix_si_panels import axes_rect_of_panel

SRC = r'E:/project/work1/20261125_integration/highres_20261125/work/Supplementary_Information_20261125_final_figures_text_corrected/word/media/final_si5_svg_svg.svg'
OUT = r'E:/project/work1/20261125_integration/highres_20261125/figs/FigureS5.svg'
MEDIA = 'si_ppt/ppt/media/'
# panels by slide position (x,y) in inches -> (row, col) order after sorting
PANELS = {(2.26, 0.63): 'image91', (5.11, 0.63): 'image89', (7.98, 0.63): 'image87',
          (2.26, 2.70): 'image85', (5.11, 2.70): 'image83', (7.98, 2.70): 'image81',
          (2.26, 4.88): 'image79', (5.11, 4.88): 'image77', (7.98, 4.88): 'image75'}

src = open(SRC, encoding='utf-8').read()

# --- global axes rects of the export ---------------------------------------
rects = []
for m in re.finditer(r'<path d="([^"]*)"[^>]*fill="#FFFFFF"[^>]*>', src):
    n = [float(x) for x in re.findall(r'-?\d+\.?\d*', m.group(1))]
    if len(n) < 8:
        continue
    b = (min(n[0::2]), min(n[1::2]),
         max(n[0::2]) - min(n[0::2]), max(n[1::2]) - min(n[1::2]))
    if not (200 < b[2] < 260 and 150 < b[3] < 190):
        continue
    t = re.search(r'transform="([^"]+)"', m.group(0))
    M = parse_tf(t.group(1)) if t else (1, 0, 0, 1, 0, 0)
    p0 = apply(M, b[0], b[1])
    p1 = apply(M, b[0] + b[2], b[1] + b[3])
    rects.append((p0[0], p0[1], p1[0] - p0[0], p1[1] - p0[1]))
rects = sorted(rects, key=lambda r: (round(r[1] / 40), r[0]))
print('axes rects', len(rects), [tuple(round(v, 1) for v in r) for r in rects[:3]])

panel_by_cell = {}
for k, key in enumerate(sorted(PANELS, key=lambda k: (k[1], k[0]))):
    panel_by_cell[k] = PANELS[key]

# --- fragments --------------------------------------------------------------
frags = []
for m in re.finditer(r'<image [^>]*width="([\d.]+)" height="([\d.]+)"[^>]*id="(img\d+)"></image>', src):
    imgid = m.group(3)
    iw, ih = float(m.group(1)), float(m.group(2))
    use = re.search(r'<use [^>]*xlink:href="#%s"[^>]*></use>' % imgid, src)
    b0, b1 = expand_block(src, use.start(), use.end())
    block = src[b0:b1]
    M = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    for attrs in re.findall(r'<g\b([^>]*)>', block):
        t = re.search(r'transform="([^"]+)"', attrs)
        if t:
            M = mul(M, parse_tf(t.group(1)))
    ut = re.search(r'<use [^>]*transform="([^"]+)"', block)
    M = mul(M, parse_tf(ut.group(1)) if ut else (1, 0, 0, 1, 0, 0))
    p0 = apply(M, 0, 0)
    frags.append((imgid, b0, b1, p0[0] + iw * M[0] / 2, p0[1] + ih * M[3] / 2))
print('fragments', len(frags))

edits = {}
for k, rect in enumerate(rects):
    name = panel_by_cell[k]
    members = [f for f in frags
               if rect[0] - 10 < f[3] < rect[0] + rect[2] + 10 and rect[1] - 10 < f[4] < rect[1] + rect[3] + 10]
    members.sort(key=lambda f: f[1])
    if not members:
        print('  WARN no fragments for', name); continue
    W, H, body = load_asset(MEDIA + name + '.svg')
    body = prefix_ids(body, 's5p%d_' % k)
    pa = axes_rect_of_panel(MEDIA + name + '.svg')
    sx = rect[2] / pa[2]
    sy = rect[3] / pa[3]
    ox = rect[0] - pa[0] * sx
    oy = rect[1] - pa[1] * sy
    edits[members[0][0]] = ('<g transform="matrix(%s 0 0 %s %s %s)" stroke-linejoin="round" '
                            'stroke-linecap="butt">%s</g>' % (fmt(sx), fmt(sy), fmt(ox), fmt(oy), body))
    print('  %-8s <- %s  %d frags  rect=(%.0f,%.0f,%.0f,%.0f)' % (k, name, len(members), *rect))

for imgid, b0, b1, _, _ in sorted(frags, key=lambda f: -f[1]):
    src = src[:b0] + edits.get(imgid, '') + src[b1:]

src = re.sub(r'<image [^>]*id="img\d+"></image>', '', src)
m = re.search(r'<svg\b([^>]*)>', src)
attrs = m.group(1)
w0 = float(re.search(r'width="([\d.]+)', attrs).group(1))
h0 = float(re.search(r'height="([\d.]+)', attrs).group(1))
h_in = 6.27 * h0 / w0
new_attrs = re.sub(r'width="[\d.]+(px)?"', 'width="6.270in"', attrs, count=1)
new_attrs = re.sub(r'height="[\d.]+(px)?"', 'height="%.3fin"' % h_in, new_attrs, count=1)
if 'viewBox' not in new_attrs:
    new_attrs += ' viewBox="0 0 %g %g"' % (w0, h0)
src = src[:m.start()] + '<svg' + new_attrs + '>' + src[m.end():]
open(OUT, 'w', encoding='utf-8').write(src)
print('written', OUT, len(src) // 1024, 'KB')
