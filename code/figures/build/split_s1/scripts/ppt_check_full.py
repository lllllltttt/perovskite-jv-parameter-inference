# -*- coding: utf-8 -*-
"""Real-PowerPoint round trip for the ten pieces (anaconda python / pywin32).

One slide per piece, each picture tagged in a text box so the shapes can be
told apart; the file is saved, reopened and every picture re-measured.  The
histogram export is scanned for PowerPoint's red 'x' failure icon.
"""
import json
import os

import numpy as np
from PIL import Image
import win32com.client as win32

META = json.load(open("out_ticks_full/work/meta.json", encoding="utf-8"))
OUT = os.path.abspath("work/ppt_full")
os.makedirs(OUT, exist_ok=True)
SW = max(p["win"][2] for p in META["pieces"])
SH = max(p["win"][3] for p in META["pieces"])

app = win32.DispatchEx("PowerPoint.Application")
app.Visible = True
app.DisplayAlerts = 1
pres = app.Presentations.Add()
pres.PageSetup.SlideWidth = SW
pres.PageSetup.SlideHeight = SH
for i, p in enumerate(META["pieces"], start=1):
    sl = pres.Slides.Add(i, 12)
    shp = sl.Shapes.AddPicture(os.path.abspath(p["svg"]), 0, -1, 0, 0,
                               p["win"][2], p["win"][3])
    print("insert %-18s asked %8.3f x %8.3f  got %8.3f x %8.3f"
          % (p["name"], p["win"][2], p["win"][3], shp.Width, shp.Height))
    sl.Shapes.AddTextbox(1, 5, SH - 20, 200, 14).TextFrame.TextRange.Text = p["name"]
pptx = os.path.join(OUT, "allticks_check.pptx")
pres.SaveAs(pptx)
try:
    pres.Close()
except Exception as e:
    print("(close: %s)" % e)
try:
    app.Quit()
except Exception as e:
    print("(quit: %s)" % e)

app2 = win32.DispatchEx("PowerPoint.Application")
app2.Visible = True
p2 = app2.Presentations.Open(pptx, WithWindow=-1)
print("reopened: %d slides" % p2.Slides.Count)
bad = 0
for i, p in enumerate(META["pieces"], start=1):
    s = p2.Slides(i)
    pic = [s.Shapes(k) for k in range(1, s.Shapes.Count + 1)][0]
    wpx = int(round(p["win"][2] * 600 / 72))
    hpx = int(round(p["win"][3] * 600 / 72))
    png = os.path.join(OUT, p["name"] + ".png")
    s.Export(png, "PNG", wpx, hpx)
    a = np.asarray(Image.open(png).convert("RGB")).astype(int)
    red = int(((a[..., 0] > 200) & (a[..., 1] < 80) & (a[..., 2] < 80)).sum())
    print("slide %2d %-18s shape %8.3f x %8.3f  export %dx%d  red px %d"
          % (i, p["name"], pic.Width, pic.Height, wpx, hpx, red))
    bad += red
print("total red pixels over all ten exports: %d" % bad)
try:
    p2.Close()
except Exception as e:
    print("(close: %s)" % e)
try:
    app2.Quit()
except Exception as e:
    print("(quit: %s)" % e)
