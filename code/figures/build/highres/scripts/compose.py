# -*- coding: utf-8 -*-
"""
Rebuild a PowerPoint-exported figure SVG by replacing its degraded raster blocks.

  * source = ('svg', path)  -> the original matplotlib SVG is inlined at exactly
    the same page rectangle (vector text/axes, native raster layers untouched)
  * source = ('png', path)  -> only the data URI is swapped for the lossless PNG,
    every transform/attribute of the original <image> is kept

The vector content of the export (PowerPoint text, native charts, bar panels that
were exported as vectors) is copied byte for byte.
"""
import re, os, sys, base64, io
import xml.etree.ElementTree as ET

NS = '{http://www.w3.org/2000/svg}'
XL = '{http://www.w3.org/1999/xlink}'

# ---------------------------------------------------------------- matrices
def parse_one(s):
    s = s.strip()
    m = re.fullmatch(r'matrix\(([^)]*)\)', s)
    if m:
        return tuple(float(x) for x in m.group(1).replace(',', ' ').split())
    m = re.fullmatch(r'scale\(([^)]*)\)', s)
    if m:
        v = [float(x) for x in m.group(1).replace(',', ' ').split()]
        return (v[0], 0.0, 0.0, v[1] if len(v) > 1 else v[0], 0.0, 0.0)
    m = re.fullmatch(r'translate\(([^)]*)\)', s)
    if m:
        v = [float(x) for x in m.group(1).replace(',', ' ').split()]
        return (1.0, 0.0, 0.0, 1.0, v[0], v[1] if len(v) > 1 else 0.0)
    if s.startswith('rotate('):
        import math
        v = [float(x) for x in re.search(r'\(([^)]*)\)', s).group(1).replace(',', ' ').split()]
        a = math.radians(v[0]); c, sn = math.cos(a), math.sin(a)
        return (c, sn, -sn, c, 0.0, 0.0)
    raise ValueError('bad transform ' + s)


def parse_tf(s):
    if not s:
        return (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    M = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    for part in re.findall(r'[a-zA-Z]+\([^)]*\)', s):
        M = mul(M, parse_one(part))
    return M


def mul(A, B):
    a, b, c, d, e, f = A
    a2, b2, c2, d2, e2, f2 = B
    return (a * a2 + c * b2, b * a2 + d * b2, a * c2 + c * d2, b * c2 + d * d2,
            a * e2 + c * f2 + e, b * e2 + d * f2 + f)


def apply(M, x, y):
    a, b, c, d, e, f = M
    return (a * x + c * y + e, b * x + d * y + f)


def fmt(x):
    s = '%.6f' % x
    s = s.rstrip('0').rstrip('.')
    return s if s not in ('', '-0') else '0'


# ---------------------------------------------------------------- helpers
def clip_rect(src, cid):
    m = re.search(r'<clipPath id="%s"><rect x="([-\d.eE+]+)" y="([-\d.eE+]+)" '
                  r'width="([-\d.eE+]+)" height="([-\d.eE+]+)"/>' % cid, src)
    if not m:
        m = re.search(r'<clipPath id="%s">\s*<rect x="([-\d.eE+]+)" y="([-\d.eE+]+)" '
                      r'width="([-\d.eE+]+)" height="([-\d.eE+]+)"' % cid, src)
    return [float(g) for g in m.groups()]


def expand_block(src, start, end):
    """grow outwards while the enclosing <g> contains nothing but this subtree"""
    while True:
        m = re.compile(r'\s*</g>').match(src, end)
        if not m:
            break
        depth = 0
        gstart = gend = None
        for t in reversed(list(re.finditer(r'<g(\s[^>]*)?>|</g>', src[:m.end()]))):
            if t.group(0) == '</g>':
                depth += 1
            else:
                depth -= 1
                if depth == 0:
                    gstart, gend = t.start(), t.end()
                    break
        if gstart is None:
            break
        if src[gend:start].strip():      # the group holds other siblings too
            break
        start, end = gstart, m.end()
    return start, end


def load_asset(path):
    s = open(path, encoding='utf-8').read()
    vb = re.search(r'viewBox="([-\d.]+) ([-\d.]+) ([\d.]+) ([\d.]+)"', s)
    if vb:
        vbx, vby = float(vb.group(1)), float(vb.group(2))
        W, H = float(vb.group(3)), float(vb.group(4))
    else:
        m = re.search(r'<svg[^>]*width="([\d.]+)pt"[^>]*height="([\d.]+)pt"', s)
        W, H = float(m.group(1)), float(m.group(2))
        vbx = vby = 0.0
    body = s[s.index('>', s.index('<svg')) + 1: s.rindex('</svg>')]
    body = re.sub(r'<metadata>.*?</metadata>', '', body, flags=re.S)
    body = re.sub(r'<defs>\s*<style[^>]*>.*?</style>\s*</defs>', '', body, flags=re.S)
    return W, H, body.strip(), vbx, vby


def prefix_ids(body, pfx):
    ids = sorted(set(re.findall(r'\bid="([^"]+)"', body)), key=len, reverse=True)
    for i in ids:
        body = body.replace('id="%s"' % i, 'id="%s%s"' % (pfx, i))
        body = body.replace('href="#%s"' % i, 'href="#%s%s"' % (pfx, i))
        body = body.replace('url(#%s)' % i, 'url(#%s%s)' % (pfx, i))
    return body


# ---------------------------------------------------------------- main
def compose(src_svg, out_svg, jobs, final_w_in, title=None):
    """jobs: list of dicts {use: '#imgN' or index, kind: 'svg'|'png', path: ...}"""
    src = open(src_svg, encoding='utf-8').read()
    report = []
    extra_defs = []
    for n, job in enumerate(jobs, 1):
        imgid = job['id']
        ms = re.search(r'<image [^>]*id="%s"></image>' % imgid, src)
        if not ms:
            raise SystemExit('image %s not found' % imgid)
        tag = ms.group(0)
        iw = float(re.search(r'width="([\d.]+)"', tag).group(1))
        ih = float(re.search(r'height="([\d.]+)"', tag).group(1))
        use = re.search(r'<use [^>]*xlink:href="#%s"[^>]*></use>' % imgid, src)
        if not use:
            raise SystemExit('use for %s not found' % imgid)
        b0, b1 = expand_block(src, use.start(), use.end())
        block = src[b0:b1]

        # transforms inside the block, outer -> inner
        gs = re.findall(r'<g\b([^>]*)>', block)
        M = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
        clip_first = None
        for attrs in gs:
            t = re.search(r'transform="([^"]+)"', attrs)
            c = re.search(r'clip-path="url\(#([^)]+)\)"', attrs)
            Mt = parse_tf(t.group(1)) if t else (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
            if c and clip_first is None:
                clip_first = (M, Mt, c.group(1))
            M = mul(M, Mt)
        ut = re.search(r'<use [^>]*transform="([^"]+)"', block)
        M = mul(M, parse_tf(ut.group(1)) if ut else (1, 0, 0, 1, 0, 0))
        p00 = apply(M, 0, 0)
        p10 = apply(M, iw, 0)
        p01 = apply(M, 0, ih)

        if job['kind'] == 'png':
            data = base64.b64encode(open(job['path'], 'rb').read()).decode()
            newtag = re.sub(r'xlink:href="data:image/[a-z]+;base64,[^"]*"',
                            'xlink:href="data:image/png;base64,%s"' % data, tag)
            newblock = block.replace(tag, newtag)
            note = 'PNG %s' % os.path.basename(job['path'])
        else:
            W, H, body, vbx, vby = load_asset(job['path'])
            body = prefix_ids(body, 'p%d_' % n)
            ax = (p10[0] - p00[0]) / W
            ay = (p01[1] - p00[1]) / H
            tx = p00[0] - ax * vbx          # the asset may have a non-zero viewBox origin
            ty = p00[1] - ay * vby
            fid = 'frame%d' % n
            rx0, ry0 = apply(clip_first[0], *(0, 0)) if False else (0, 0)
            Mcl = clip_first[0]
            Mrc = clip_first[1]
            r = clip_rect(src, clip_first[2])
            f00 = apply(mul(Mcl, Mrc), r[0], r[1])
            f10 = apply(mul(Mcl, Mrc), r[0] + r[2], r[1] + r[3])
            newblock = ('<g clip-path="url(#%s)"><g transform="matrix(%s 0 0 %s %s %s)" '
                        'stroke-linejoin="round" stroke-linecap="butt">%s</g></g>'
                        % (fid, fmt(ax), fmt(ay), fmt(tx), fmt(ty), body))
            extra_defs.append('<clipPath id="%s" clipPathUnits="userSpaceOnUse"><rect x="%s" y="%s" '
                              'width="%s" height="%s"/></clipPath>'
                              % (fid, fmt(f00[0]), fmt(f00[1]), fmt(f10[0] - f00[0]), fmt(f10[1] - f00[1])))
            note = 'SVG %s (%gx%g pt)' % (os.path.basename(job['path']), W, H)
        src = src[:b0] + newblock + src[b1:]
        report.append((imgid, job['kind'], os.path.basename(job['path']),
                       (round(p00[0], 2), round(p00[1], 2)), (round(p10[0] - p00[0], 2), round(p01[1] - p00[1], 2))))

    if extra_defs:
        src = src.replace('<defs>', '<defs>' + ''.join(extra_defs), 1)

    # drop the now-unused <image> definitions that were only referenced by replaced blocks
    for job in jobs:
        if job['kind'] == 'svg':
            src = re.sub(r'<image [^>]*id="%s"></image>' % job['id'], '', src)

    # rewrite the root tag with an explicit physical size + viewBox
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
    return report


if __name__ == '__main__':
    pass
