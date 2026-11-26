# -*- coding: utf-8 -*-
"""PowerPoint red-X check for the re-issued S3a_05."""
import os
import re

import numpy as np
from PIL import Image
import win32com.client as win32

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "out"))
WORK = os.path.abspath(os.path.join(HERE, "..", "work"))
f = os.path.join(OUT, "S3a_05.svg")
s = open(f, encoding="utf-8", errors="ignore").read(600)
m = re.search(r'width="([\d.]+)"\s+height="([\d.]+)"', s)
w_px, h_px = float(m.group(1)), float(m.group(2))
w, h = w_px * 72 / 96, h_px * 72 / 96

app = win32.DispatchEx("PowerPoint.Application")
app.Visible = True
app.DisplayAlerts = 1
pres = app.Presentations.Add()
pres.PageSetup.SlideWidth = 300
pres.PageSetup.SlideHeight = 220
sl = pres.Slides.Add(1, 12)
shp = sl.Shapes.AddPicture(f, 0, -1, 0, 0, w, h)
print("insert asked %.2f x %.2f  got %.2f x %.2f" % (w, h, shp.Width, shp.Height))
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
png = os.path.join(WORK, "ppt_check_01.png")
p2.Slides(1).Export(png, "PNG", int(w * 8), int(h * 8))
a = np.asarray(Image.open(png).convert("RGB")).astype(int)
red = int(((a[..., 0] > 235) & (a[..., 1] < 35) & (a[..., 2] < 35)).sum())
print("red px:", red)
try:
    p2.Close()
except Exception:
    pass
try:
    app2.Quit()
except Exception:
    pass
