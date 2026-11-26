# -*- coding: utf-8 -*-
"""
For figures whose panels were partly rasterised by the PowerPoint SVG exporter
(scatter layer / histogram bars), re-insert the original panel SVG aligned on the
axes rectangle, so the panel is drawn from its own vector source and the leftover
raster fragments are covered by the panel's own white background.
"""
import re, os, sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compose import parse_tf, mul, apply, fmt, load_asset, prefix_ids, expand_block

NS = '{http://www.w3.org/2000/svg}'


def path_bbox(d):
    nums = [float(x) for x in re.findall(r'-?\d+\.?\d*(?:[eE][-+]?\d+)?', d)]
    xs, ys = nums[0::2], nums[1::2]
    return min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)


def axes_rect_of_panel(svg_path):
    """bbox of the axes background patch (mpl id=patch_2) of a panel SVG"""
    s = open(svg_path, encoding='utf-8').read()
    m = re.search(r'<g id="patch_2">\s*<path d="([^"]*)"', s)
    if m:
        return path_bbox(m.group(1))
    best = None
    for m in re.finditer(r'<path d="([^"]*)"[^>]*fill="#FFFFFF"', s):
        b = path_bbox(m.group(1))
        if 20 < b[2] < 600 and 20 < b[3] < 600:
            if best is None or b[2] * b[3] < best[2] * best[3]:
                best = b
    return best


def main(src_svg, out_svg, jobs, final_w_in):
    src = open(src_svg, encoding='utf-8').read()
    extra = []
    for n, (imgid, panel_svg) in enumerate(jobs, 1):
        W, H, body = load_asset(panel_svg)
        body = prefix_ids(body, 'q%d_' % n)
        pa = axes_rect_of_panel(panel_svg)
        # export axes rect: nearest preceding white filled rectangle path
        ms = re.search(r'<image [^>]*id="%s"></image>' % imgid, src)
        use = re.search(r'<use [^>]*xlink:href="#%s"[^>]*></use>' % imgid, src)
        b0, b1 = expand_block(src, use.start(), use.end())
        head = src[:b0]
        cands = [(m.start(), path_bbox(m.group(1))) for m in
                 re.finditer(r'<path d="([^"]*)" fill="#FFFFFF"/>', head)]
        ea = None
        for pos, bb in reversed(cands):
            if 30 < bb[2] < 600 and 30 < bb[3] < 600:
                ea = bb
                break
        if ea is None or pa is None:
            raise SystemExit('axes rect not found for ' + imgid)
        sx = ea[2] / pa[2]
        sy = ea[3] / pa[3]
        ox = ea[0] - pa[0] * sx
        oy = ea[1] - pa[1] * sy
        new = ('<g transform="matrix(%s 0 0 %s %s %s)" stroke-linejoin="round" '
               'stroke-linecap="butt">%s</g>' % (fmt(sx), fmt(sy), fmt(ox), fmt(oy), body))
        src = head + new + src[b1:]
        print('  %s <- %s  scale %.4f/%.4f  axes->(%.1f,%.1f)' %
              (imgid, os.path.basename(panel_svg), sx, sy, ea[0], ea[1]))
    for imgid, _ in jobs:
        src = re.sub(r'<image [^>]*id="%s"></image>' % imgid, '', src)
    m = re.search(r'<svg\b([^>]*)>', src)
    attrs = m.group(1)
    w0 = float(re.search(r'width="([\d.]+)', attrs).group(1))
    h0 = float(re.search(r'height="([\d.]+)', attrs).group(1))
    h_in = final_w_in * h0 / w0
    new_attrs = re.sub(r'width="[\d.]+(px)?"', 'width="%.3fin"' % final_w_in, attrs, count=1)
    new_attrs = re.sub(r'height="[\d.]+(px)?"', 'height="%.3fin"' % h_in, new_attrs, count=1)
    if 'viewBox' not in new_attrs:
        new_attrs += ' viewBox="0 0 %g %g"' % (w0, h0)
    src = src[:m.start()] + '<svg' + new_attrs + '>' + src[m.end():]
    open(out_svg, 'w', encoding='utf-8').write(src)
    print('written', out_svg)


if __name__ == '__main__':
    pass
