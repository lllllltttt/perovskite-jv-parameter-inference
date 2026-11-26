# -*- coding: utf-8 -*-
"""S8 (d) de-rasterisation on the user's 2026-11-26 14:01 SI8.svg base.

Only:
  * the 239x189 JPEG in (d)  -> the original vector panel (S7d)
  * a vector (d) legend copied from (a) (second rule re-coloured orange)
Everything else - including the new x-axis label "Normalized coordinate
difference" and the other five panels - is left byte-for-byte untouched.
"""
import re, io, os

BASE = r'E:/project/work1/20261126-SI8/SI8.svg'
S7B = r'E:/project/work1/20261116_figs7_split/out/svg/S7b.svg'
OUT = r'E:/project/work1/20261126_SI_update_work/s8fix'
os.makedirs(OUT, exist_ok=True)

new = io.open(BASE, encoding='utf-8').read()
s7b = io.open(S7B, encoding='utf-8').read()

assert new.count('<image') == 1
assert 'Normalized coordinate difference' in new

# ---------------------------------------------------------------- panel group
# Old S7b = r_mu mobility (the correct source for S8(d)); its axes span
# (200.432719,15.31)-(328.052719,113.822631).
inner = s7b[s7b.index('>', s7b.index('<svg')) + 1:s7b.rindex('</svg>')]
sx = (463.73 - 258.21) / (328.052719 - 200.432719)
sy = (538.50 - 381.28) / (113.822631 - 15.31)
tx = 258.21 - 200.432719 * sx
ty = 381.28 - 15.31 * sy
panel = ('<g transform="translate(%.4f %.4f) scale(%.6f %.6f)">'
         '<clipPath id="s8d_vb"><rect x="181.2927" y="10.09" width="149.72" height="118.28"/></clipPath>'
         '<g clip-path="url(#s8d_vb)">%s</g></g>' % (tx, ty, sx, sy, inner))
print('panel %.1f x %.1f units -> scale %.5f/%.5f at (%.2f,%.2f)'
      % (463.73 - 258.21, 538.5 - 381.28, sx, sy, tx, ty))

# ---------------------------------------------------------------- remove raster
m = re.search(r'<image\b[^>]*id="img1"[^>]*>.*?</image>', new, re.S); assert m
new = new.replace(m.group(0), '')

# ---------------------------------------------------------------- swap group
i = new.find('<g clip-path="url(#clip0)" transform="matrix(0.000104987')
assert i > 0
depth = 0; j = None
for mm in re.finditer(r'<g\b|</g>', new[i:]):
    depth += 1 if mm.group(0) == '<g' else -1
    if depth == 0:
        j = i + mm.end(); break
old_group = new[i:j]
new = new.replace(old_group, panel)
print('replaced image group', len(old_group), '->', len(panel))

# ---------------------------------------------------------------- (d) legend from (a)
def rule(y, color, width):
    return ('<path d="M125.34 %.3f 134.119 %.3f" stroke="%s" stroke-width="%s" '
            'stroke-linecap="square" stroke-linejoin="round" fill="none" '
            'transform="matrix(1 0 0 1.00101 205.439 126.877)"/>' % (y, y, color, width))

r_gray = rule(150.687, '#9A9A9A', '2.07519')
r_col = rule(166.492, '#D55E00', '2.55407')
assert rule(150.687, '#9A9A9A', '2.07519') in new
assert rule(166.492, '#0072B2', '2.55407') in new

texts = []
for tr in ('matrix(1 0 0 -1.00101 344.029 281.63)',
           'matrix(1 0 0 -1.00101 344.029 297.452)'):
    mm = re.search(r'<path\b[^>]*transform="' + re.escape(tr) + r'"[^>]*>', new)
    assert mm
    texts.append(mm.group(0))

legend = ('<g id="s8d_legend" transform="translate(-2.6 230)">' + r_gray + r_col +
          texts[0] + texts[1] + '</g>')
assert new.rstrip().endswith('</g></svg>')
k = new.rindex('</g></svg>')
new = new[:k] + legend + new[k:]

assert '<image' not in new
assert 'Normalized coordinate difference' in new
io.open(os.path.join(OUT, 'FigureS8.svg'), 'w', encoding='utf-8', newline='\n').write(new)
print('written', len(new), 'images', new.count('<image'))
