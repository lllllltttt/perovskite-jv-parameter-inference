"""Detailed structural report of the slide-1 SVG."""
import sys, collections, re
from lxml import etree

P = sys.argv[1]
root = etree.parse(P).getroot()
CS = "{http://www.w3.org/2000/svg}"


def walk(e, d=0, maxd=2):
    if not isinstance(e.tag, str):
        return
    tag = e.tag.split("}")[-1]
    ident = e.get("id", "")
    print("  " * d + "<%s>%s%s" % (tag, " " + ident if ident else "",
                                   " n=%d" % len(e) if len(e) else ""))
    if d < maxd:
        for ch in e:
            walk(ch, d + 1, maxd)


print("=== per-axes child census ===")
for g in root.iter(CS + "g"):
    gid = g.get("id", "")
    if re.match(r"axes_\d+$", gid):
        c = collections.Counter(ch.tag.split("}")[-1] for ch in g)
        print("  %-9s n=%-4d %s" % (gid, len(g), dict(c)))

print("\n=== every <text> node ===")
def txt(e):
    # concatenate all text/tspan contents under e
    return "".join(e.itertext())

n = 0
for g in root.iter(CS + "g"):
    gid = g.get("id", "")
    if not re.match(r"(axes_\d+|text_\d+)$", gid):
        continue
    for t in g.iter(CS + "text"):
        n += 1
        par = t.getparent()
        pid = par.get("id", "?")
        tr = t.get("transform", "")
        print("  %-10s parent=%-12s text=%-34r transform=%s"
              % (gid, pid, txt(t)[:34], tr[:44]))
print("total <text>:", n)

print("\n=== text outside axes (figure-level) ===")
for g in root.iter(CS + "g"):
    gid = g.get("id", "")
    if gid.startswith("text_"):
        for t in g.iter(CS + "text"):
            print("  %s: %r  attrs=%s" % (gid, txt(t), dict(t.attrib)))

print("\n=== <image> elements ===")
for im in root.iter(CS + "image"):
    h = im.get("{http://www.w3.org/1999/xlink}href") or im.get("href") or ""
    print("  id=%s parent=%s x=%s y=%s w=%s h=%s href=%s"
          % (im.get("id"), im.getparent().get("id"), im.get("x"), im.get("y"),
             im.get("width"), im.get("height"), h[:40]))

print("\n=== defs content ===")
for d in root.iter(CS + "defs"):
    print("  defs under %s: %s" % (d.getparent().get("id", "root"),
                                   [ch.tag.split('}')[-1] for ch in d]))

print("\n=== axes_10 (heatmap) tree ===")
for g in root.iter(CS + "g"):
    if g.get("id") == "axes_10":
        walk(g, 0, 3)
print("\n=== axes_11 (colorbar) tree ===")
for g in root.iter(CS + "g"):
    if g.get("id") == "axes_11":
        walk(g, 0, 3)
print("\n=== axes_1 tree ===")
for g in root.iter(CS + "g"):
    if g.get("id") == "axes_1":
        walk(g, 0, 3)

print("\n=== distinct styles/colours ===")
styles = collections.Counter()
for e in root.iter():
    if not isinstance(e.tag, str):
        continue
    s = e.get("style") or ""
    if s:
        styles[s] += 1
for s, c in styles.most_common(22):
    print("  %5d  %s" % (c, s[:120]))
