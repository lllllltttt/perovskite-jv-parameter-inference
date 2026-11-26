# -*- coding: utf-8 -*-
"""
Align the legend colour patches of Fig3c / Fig3d to the optical centre of the
legend text (cap-height centre of the rendered glyphs), keep swatch size,
row pitch and swatch-text gap unchanged.
"""
import re, sys

CAP = 0.716          # Arial cap height, em
EM = 7.0             # font-size used in these legends
HALF = 0.5 * CAP * EM


def legend_blocks(svg):
    out = []
    for m in re.finditer(r'<g id="legend_\d+">', svg):
        i = m.start()
        depth = 0
        for t in re.finditer(r'<g\b[^>]*>|</g>', svg[i:]):
            depth += -1 if t.group(0).startswith('</g') else 1
            if depth == 0:
                out.append((i, i + t.end()))
                break
    return out


def fix(path, dst):
    s = open(path, encoding='utf-8').read()
    blk = None
    for a, b in legend_blocks(s):
        blk = s[a:b]
        break
    if blk is None:
        raise SystemExit('no legend in ' + path)

    # patches and their text baselines, in document order
    patches = list(re.finditer(r'<g id="patch_\d+">\s*<path d="([^"]*)"', blk))
    texts = list(re.finditer(r'<g transform="translate\(([\d.\-]+) ([\d.\-]+)\)">\s*<text>\s*<tspan x="[\d.\-]+" y="([\d.\-]+)"', blk))
    if len(patches) != len(texts):
        raise SystemExit('legend structure mismatch in ' + path)

    new = blk
    shifts = []
    for p, t in zip(patches, texts):
        d = p.group(1)
        nums = [float(x) for x in re.findall(r'-?\d+\.?\d*', d)]
        xs, ys = nums[0::2], nums[1::2]
        y0, y1 = min(ys), max(ys)
        top, bot = y0, y1
        h = bot - top

        # glyph baseline of this row and its optical centre
        # text ink top/bottom measured from the render:
        base = float(t.group(2)) + float(t.group(3))       # translate_y + tspan_y
        ink_top, ink_bot = base - CAP * EM, base            # caps/ascenders down to baseline
        # optical centre = cap-height centre of the glyph body (descenders ignored:
        # they are sparse and would drag the swatch down, which is the defect we fix)
        c_text = 0.5 * (ink_top + ink_bot)
        c_patch = 0.5 * (top + bot)
        dy = c_text - c_patch
        shifts.append(dy)

        new_top, new_bot = top + dy, bot + dy
        # rewrite the path: first two points are the bottom edge, next two the top edge
        pts = re.findall(r'([ML])\s*(-?\d+\.?\d*)\s+(-?\d+\.?\d*)', d)
        vals = [float(p[1]) for p in pts], [float(p[2]) for p in pts]
        ys_new = []
        for y in vals[1]:
            ys_new.append(new_bot if abs(y - bot) < 1e-6 else new_top)
        out = d
        idx = 0
        for m2 in re.finditer(r'([ML])\s*(-?\d+\.?\d*)\s+(-?\d+\.?\d*)', d):
            out = out.replace(m2.group(0), '%s %s %s' % (m2.group(1), m2.group(2), ('%.6f' % ys_new[idx]).rstrip('0').rstrip('.')), 1)
            idx += 1
        new = new.replace(d, out, 1)

    s = s.replace(blk, new, 1)
    open(dst, 'w', encoding='utf-8').write(s)
    print('%-10s shifts(pt): %s' % (path.split('/')[-1], ', '.join('%+.3f' % x for x in shifts)))


if __name__ == '__main__':
    fix(r'E:/project/work1/20261111_fig345_standalone_revision/figures/Fig3c.svg',
        r'E:/project/work1/20261125_integration/highres_20261125/work/Fig3c_fixed.svg')
    fix(r'E:/project/work1/20261111_fig345_standalone_revision/figures/Fig3d.svg',
        r'E:/project/work1/20261125_integration/highres_20261125/work/Fig3d_fixed.svg')
