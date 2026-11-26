# -*- coding: utf-8 -*-
"""
Panel S8(d) = the r_mu ECDF panel (S7b) without a legend.
Lift the whole legend group of panel (a) (S7a, the a_mu panel of the same composite)
and drop it into (d) at the same position relative to the axes, recolouring only the
"nearest-neighbour pairs" sample line from the blue of (a) to the orange of the r panels.
"""
import re

A = r'E:/project/work1/20261116_figs7_split/out/svg/S7a.svg'      # panel (a), has the legend
B = r'E:/project/work1/20261116_figs7_split/out/svg/S7b.svg'      # panel (d) without a legend
DST = r'E:/project/work1/20261125_integration/highres_20261125/work/S8d_vector.svg'

# axes origin of the two panels (patch_2 background of (a), patch_8 of (b))
AX_A, AX_B = 34.527, 200.432719
DX = AX_B - AX_A            # = difference of the two viewBox origins


def legend_block(svg):
    i = svg.index('<g id="legend_1">')
    depth = 0
    for t in re.finditer(r'<g\b[^>]*>|</g>', svg[i:]):
        depth += -1 if t.group(0).startswith('</g') else 1
        if depth == 0:
            return svg[i:i + t.end()]
    raise SystemExit('legend not closed')


sa = open(A, encoding='utf-8').read()
sb = open(B, encoding='utf-8').read()

blk = legend_block(sa)

# (a)'s "nearest-neighbour pairs" sample line -> the orange used by the r coordinates
assert blk.count('#0072b2') == 1, blk.count('#0072b2')
blk = blk.replace('#0072b2', '#d55e00')
for i in ('legend_1', 'patch_7', 'line2d_14', 'line2d_15', 'text_14', 'text_15'):
    blk = blk.replace('id="%s"' % i, 'id="d_%s"' % i)

payload = '<g transform="translate(%s 0)">%s</g>' % (('%f' % DX).rstrip('0').rstrip('.'), blk)
out = sb.replace('</svg>', payload + '</svg>')
open(DST, 'w', encoding='utf-8').write(out)
print('dx =', DX, '| wrote', DST, len(out) // 1024, 'KB')
