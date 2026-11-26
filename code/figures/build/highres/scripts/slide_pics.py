# -*- coding: utf-8 -*-
"""List every picture-bearing element of a slide with its rect in inches."""
import re, os, sys
import xml.etree.ElementTree as ET

P = '{http://schemas.openxmlformats.org/presentationml/2006/main}'
A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
ASVG = '{http://schemas.microsoft.com/office/drawing/2016/SVG/main}'
EMU = 914400.0


def rels(base, i):
    rm = {}
    for m in re.finditer(r'<Relationship([^>]*)/>',
                         open(os.path.join(base, 'ppt/slides/_rels/slide%d.xml.rels' % i), encoding='utf-8').read()):
        a = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
        rm[a['Id']] = a['Target']
    return rm


def walk(el, base, rm, out, depth=0):
    for ch in el:
        tag = ch.tag.split('}')[1]
        if tag == 'grpSp':
            xf = ch.find(P + 'grpSpPr').find(A + 'xfrm')
            off = xf.find(A + 'off'); ext = xf.find(A + 'ext')
            cho = xf.find(A + 'chOff'); che = xf.find(A + 'chExt')
            walk(ch, base, rm, out, depth + 1)
        elif tag in ('pic', 'sp'):
            blip = None
            for b in ch.iter(A + 'blip'):
                blip = b.get(R + 'embed')
            svg = None
            for b in ch.iter(ASVG + 'svgBlip'):
                svg = b.get(R + 'embed')
            if not blip:
                continue
            spr = ch.find(P + 'spPr')
            xf = spr.find(A + 'xfrm') if spr is not None else None
            if xf is None:
                continue
            off = xf.find(A + 'off'); ext = xf.find(A + 'ext')
            out.append(dict(png=os.path.basename(rm.get(blip, '')),
                            svg=os.path.basename(rm.get(svg, '')) if svg else '',
                            x=int(off.get('x')) / EMU, y=int(off.get('y')) / EMU,
                            w=int(ext.get('cx')) / EMU, h=int(ext.get('cy')) / EMU))


if __name__ == '__main__':
    base = sys.argv[1]; i = int(sys.argv[2])
    rm = rels(base, i)
    root = ET.parse(os.path.join(base, 'ppt/slides/slide%d.xml' % i)).getroot()
    out = []
    walk(root.find(P + 'cSld').find(P + 'spTree'), base, rm, out)
    for o in out:
        print('%-14s %-14s  %5.2f x %5.2f in @ (%.2f, %.2f)' % (o['png'], o['svg'] or '-', o['w'], o['h'], o['x'], o['y']))
