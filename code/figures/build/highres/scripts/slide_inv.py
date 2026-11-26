# -*- coding: utf-8 -*-
"""Per-slide inventory of a pptx: pictures (with media + size), svg media, charts, text."""
import re, os, sys
import xml.etree.ElementTree as ET

P = '{http://schemas.openxmlformats.org/presentationml/2006/main}'
A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
ASVG = '{http://schemas.microsoft.com/office/drawing/2016/SVG/main}'
EMU = 914400.0


def rels(path):
    d = {}
    for m in re.finditer(r'<Relationship([^>]*)/>', open(path, encoding='utf-8').read()):
        a = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
        d[a['Id']] = (a['Target'], a['Type'].split('/')[-1])
    return d


def fmt(x):
    return '%.2f' % x


def main(base):
    from PIL import Image
    for i in range(1, 40):
        sp = os.path.join(base, 'ppt/slides/slide%d.xml' % i)
        if not os.path.exists(sp):
            break
        rp = os.path.join(base, 'ppt/slides/_rels/slide%d.xml.rels' % i)
        rm = rels(rp)
        root = ET.parse(sp).getroot()
        print('=' * 100)
        print('SLIDE', i)
        # walk top-level shapes
        tree = root.find(P + 'cSld').find(P + 'spTree')

        def walk(el, depth=0):
            ind = '  ' * (depth + 1)
            for ch in el:
                tag = ch.tag.split('}')[1]
                if tag == 'pic':
                    nv = ch.find(P + 'nvPicPr')
                    name = nv.find(P + 'cNvPr').get('name') if nv is not None else '?'
                    blip = ch.find(P + 'blipFill')
                    emb = svg = None
                    if blip is not None:
                        b = blip.find(A + 'blip')
                        if b is not None:
                            emb = b.get(R + 'embed')
                        for sb in ch.iter(ASVG + 'svgBlip'):
                            svg = sb.get(R + 'embed')
                    xfrm = ch.find(P + 'spPr').find(A + 'xfrm')
                    off = xfrm.find(A + 'off') if xfrm is not None else None
                    ext = xfrm.find(A + 'ext') if xfrm is not None else None
                    desc = ''
                    if ext is not None:
                        desc = '%s x %s in @ (%s,%s)' % (fmt(int(ext.get('cx')) / EMU), fmt(int(ext.get('cy')) / EMU),
                                                         fmt(int(off.get('x')) / EMU), fmt(int(off.get('y')) / EMU))
                    info = ''
                    for rid, tag2 in [('png', emb), ('svg', svg)]:
                        if tag2 and tag2 in rm:
                            tgt, kind = rm[tag2]
                            path = os.path.join(base, 'ppt', tgt.replace('../', ''))
                            if path.endswith('.png'):
                                im = Image.open(path)
                                info += ' %s=%s(%dx%d %dKB)' % (rid, os.path.basename(tgt), im.size[0], im.size[1],
                                                                os.path.getsize(path) // 1024)
                            elif path.endswith('.svg'):
                                info += ' %s=%s(%dKB)' % (rid, os.path.basename(tgt), os.path.getsize(path) // 1024)
                    print('%sPIC %-22s %-28s%s' % (ind, name[:22], desc, info))
                elif tag == 'grpSp':
                    print('%sGRP' % ind)
                    walk(ch, depth + 1)
                elif tag == 'graphicFrame':
                    print('%sCHART/FRAME' % ind)
                elif tag == 'sp':
                    txt = ''.join(t.text or '' for t in ch.iter(A + 't')).strip()
                    if txt:
                        print('%sTXT %r' % (ind, txt[:60]))

        walk(tree)


if __name__ == '__main__':
    main(sys.argv[1])
