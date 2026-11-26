# -*- coding: utf-8 -*-
"""Build the five updated SI figures from the user's 2026-11-26 sources.

S1/S2/S10  : copied verbatim (user's own edits preserved)
S4         : two PowerPoint fallback rasters (96x4, 96x16) replaced by vector
S8         : low-res (d) panel JPEG replaced by the original vector panel S7d;
             (a)/(d) legend sample lines unified (length/width/gap/alignment/
             row spacing); blue legend line recoloured for (d).
"""
import os, re, io

SRC = r'E:/project/work1/20261126_SI局部更新'
OUT = r'E:/project/work1/20261126_SI_update_work/out'
S7D = r'E:/project/work1/20261116_figs7_split/out/svg/S7d.svg'

os.makedirs(OUT, exist_ok=True)


def read(p):
    return io.open(p, encoding='utf-8').read()


def write(p, s):
    io.open(p, 'w', encoding='utf-8', newline='\n').write(s)


# ---------------------------------------------------------------- S1/S2/S10
for n in ('S1', 'S2', 'S10'):
    s = read(os.path.join(SRC, 'SI%s.svg' % n[1:]))
    write(os.path.join(OUT, 'Figure%s.svg' % n), s)
    print(n, 'copied', len(s))


# ---------------------------------------------------------------- S4
s = read(os.path.join(SRC, 'SI4.svg'))

# drop the two embedded PNG fallbacks
for m in list(re.finditer(r'<image\b[^>]*id="img[46]"[^>]*>.*?</image>', s, re.S)):
    s = s.replace(m.group(0), '')
    print('S4 removed image', m.group(0)[:60])

u4 = '<use width="100%" height="100%" xlink:href="#img4" transform="translate(726 297)"></use>'
u6 = '<use width="100%" height="100%" xlink:href="#img6" transform="translate(912 280)"></use>'
assert u4 in s and u6 in s
# img4: 2-px dark rule (median line slice), img6: orange box (fill+border), both
# reproduced as flat vector shapes in the same local coordinate system.
v4 = ('<g transform="translate(726 297)">'
      '<rect x="0" y="1" width="96" height="2" fill="#595959"/></g>')
v6 = ('<g transform="translate(912 280)">'
      '<rect x="0" y="0" width="96" height="16" fill="#595959"/>'
      '<rect x="2" y="2" width="92" height="12" fill="#E39659"/></g>')
s = s.replace(u4, v4).replace(u6, v6)
assert '<image' not in s, 'S4 still has rasters'
write(os.path.join(OUT, 'FigureS4.svg'), s)
print('S4 built', len(s))


# ---------------------------------------------------------------- S8
s = read(os.path.join(SRC, 'SI8.svg'))

# 1. drop the low-res (d) raster (239x189 JPEG in a 274x217 frame)
m = re.search(r'<image\b[^>]*id="img1"[^>]*>.*?</image>', s, re.S)
assert m
s = s.replace(m.group(0), '')
print('S8 removed raster', m.group(0)[:60])

# 2. replace its placement group with the original vector panel (S7d)
i = s.find('<g clip-path="url(#clip0)" transform="matrix(0.000104987')
assert i > 0
depth = 0
j = None
for mm in re.finditer(r'<g\b|</g>', s[i:]):
    depth += 1 if mm.group(0) == '<g' else -1
    if depth == 0:
        j = i + mm.end()
        break
assert j
old_group = s[i:j]

s7d = read(S7D)
inner = s7d[s7d.index('>', s7d.index('<svg')) + 1:s7d.rindex('</svg>')]
# S7d viewBox: 15.3867 162.7846 149.72 118.28
# map S7d's axes (34.526719,168.004577)-(162.146719,266.517208) onto the
# axes actually present in the user's 239x189 (d) raster: (30,8)-(234,165)
# inside a 238.6 x 189.0 unit placement at (230,371).
sx = (463.62 - 259.95) / (162.146719 - 34.526719)
sy = (536.00 - 379.00) / (266.517208 - 168.004577)
tx = 259.95 - 34.526719 * sx
ty = 379.00 - 168.004577 * sy
new_group = (
    '<g transform="translate(%.4f %.4f) scale(%.6f %.6f)">'
    '<clipPath id="s8d_vb"><rect x="15.3867" y="162.7846" width="149.72" height="118.28"/></clipPath>'
    '<g clip-path="url(#s8d_vb)">%s</g></g>' % (tx, ty, sx, sy, inner)
)
s = s.replace(old_group, new_group)
print('S8 (d) vector panel inserted, scale %.4f/%.4f' % (sx, sy))

# 3. unify the (a) legend sample-line width to the grey rule (2.06628)
old_blue = ('<path d="M124.802 165.778 133.544 165.778" stroke="#0072B2" '
            'stroke-width="2.54312" stroke-linecap="square" stroke-linejoin="round" '
            'fill="none" transform="matrix(1.00851 0 0 1 206.337 125.962)"/>')
assert old_blue in s
s = s.replace(old_blue, old_blue.replace('2.54312', '2.06628'))

# 4. copy the (a) legend geometry (two rules + two text outlines) into (d),
#    translated by (0, 230) i.e. from row-1 baseline 173.90 to 403.90.
rule_g = ('<path d="M124.802 150.04 133.544 150.04" stroke="#9A9A9A" stroke-width="2.06628" '
          'stroke-linecap="square" stroke-linejoin="round" fill="none" '
          'transform="matrix(1.00851 0 0 1 206.337 125.962)"/>')
rule_c = ('<path d="M124.802 165.778 133.544 165.778" stroke="#D55E00" stroke-width="2.06628" '
          'stroke-linecap="square" stroke-linejoin="round" fill="none" '
          'transform="matrix(1.00851 0 0 1 206.337 125.962)"/>')
texts = []
for tr in ('matrix(1.00851 0 0 -1 345.506 279.897)',
           'matrix(1.00851 0 0 -1 345.506 295.635)'):
    mm = re.search(r'<path\b[^>]*transform="' + re.escape(tr) + r'"[^>]*>', s)
    assert mm
    texts.append(mm.group(0))
legend_d = ('<g id="s8d_legend" transform="translate(-3 230)">' + rule_g + rule_c +
            texts[0] + texts[1] + '</g>')
# append inside the outermost translate(-185 -106) group, i.e. just before the
# final </g></svg>
assert s.rstrip().endswith('</g></svg>')
k = s.rindex('</g></svg>')
s = s[:k] + legend_d + s[k:]
write(os.path.join(OUT, 'FigureS8.svg'), s)
print('S8 built', len(s), 'rasters left:', s.count('<image'))
