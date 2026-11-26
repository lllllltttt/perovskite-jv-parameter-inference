# -*- coding: utf-8 -*-
"""Insert the two performance SVGs into PowerPoint, save, reopen, export and
scan for the red-X failure marker."""
import glob
import os
import re

import numpy as np
from PIL import Image
import win32com.client as win32

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "out"))
WORK = os.path.abspath(os.path.join(HERE, "..", "work"))
files = sorted(glob.glob(os.path.join(OUT, "performance_*.svg")))
dims = {}
for f in files:
    s = open(f, encoding="utf-8", errors="ignore").read(600)
    m = re.search(r'width="([\d.]+)(?:pt)?"\s+height="([\d.]+)', s)
    dims[f] = (float(m.group(1)), float(m.group(2)))

app = win32.DispatchEx("PowerPoint.Application")
app.Visible = True
app.DisplayAlerts = 1
pres = app.Presentations.Add()
pres.PageSetup.SlideWidth = 300
pres.PageSetup.SlideHeight = 220
for i, f in enumerate(files, start=1):
    sl = pres.Slides.Add(i, 12)
    w, h = dims[f]
    shp = sl.Shapes.AddPicture(f, 0, -1, 0, 0, w, h)
    print("insert %-26s asked %7.2f x %7.2f  got %7.2f x %7.2f" % (
        os.path.basename(f), w, h, shp.Width, shp.Height))
pptx = os.path.join(WORK, "ppt_check.pptx")
pres.SaveAs(pptx)
try:
    pres.Close()
except Exception:
    pass
try:
    app.Quit()
except Exception:
    pass

app2 = win32.DispatchEx("PowerPoint.Application")
app2.Visible = True
p2 = app2.Presentations.Open(pptx, WithWindow=-1)
bad = 0
for i, f in enumerate(files, start=1):
    s = p2.Slides(i)
    w, h = dims[f]
    png = os.path.join(WORK, "ppt_check_%02d.png" % i)
    s.Export(png, "PNG", int(w * 8), int(h * 8))
    a = np.asarray(Image.open(png).convert("RGB")).astype(int)
    red = int(((a[..., 0] > 235) & (a[..., 1] < 35) & (a[..., 2] < 35)).sum())
    bad += red
    print("slide %2d %-26s red px %d" % (i, os.path.basename(f), red))
print("TOTAL red:", bad)
try:
    p2.Close()
except Exception:
    pass
try:
    app2.Quit()
except Exception:
    pass
