# -*- coding: utf-8 -*-
"""Turn the secondary X axis of each combo chart from a category axis into a
value axis.

xlsxwriter always writes the secondary X of a column+scatter combo as
<c:catAx>; Excel then lays the scatter points out as categories and ignores
their X values.  Excel's own combo charts use <c:valAx> there, so the block
that the scatterChart references is rewritten in place (-0.5..5.5, hidden).
"""
import re, sys, zipfile, shutil

XLSX = "Figure_comparison_editable.xlsx"
TMPL = ('<c:valAx><c:axId val="%s"/><c:scaling><c:orientation val="minMax"/>'
        '<c:min val="-0.5"/><c:max val="5.5"/></c:scaling><c:delete val="1"/>'
        '<c:axPos val="b"/><c:numFmt formatCode="General" sourceLinked="1"/>'
        '<c:majorTickMark val="none"/><c:minorTickMark val="none"/>'
        '<c:tickLblPos val="none"/><c:crossAx val="%s"/>'
        '<c:crosses val="autoZero"/><c:crossBetween val="midCat"/>'
        '<c:majorUnit val="1"/></c:valAx>')

tmp = XLSX + ".tmp"
zin = zipfile.ZipFile(XLSX)
zout = zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED)
patched = 0
for item in zin.infolist():
    data = zin.read(item.filename)
    if re.match(r"xl/charts/chart\d+\.xml$", item.filename):
        s = data.decode("utf-8")
        sc = re.search(r"<c:scatterChart>.*?</c:scatterChart>", s, re.S)
        if sc:
            ids = re.findall(r'<c:axId val="(\d+)"/>', sc.group(0))
            xid, yid = ids[0], ids[1]
            m = re.search(r'<c:catAx><c:axId val="%s"/>.*?</c:catAx>' % xid, s, re.S)
            if m:
                s = s[:m.start()] + (TMPL % (xid, yid)) + s[m.end():]
                patched += 1
        data = s.encode("utf-8")
    zout.writestr(item, data)
zout.close(); zin.close()
shutil.move(tmp, XLSX)
print("secondary X axis rewritten as valAx in %d chart(s)" % patched)
sys.exit(0 if patched == 2 else 1)
