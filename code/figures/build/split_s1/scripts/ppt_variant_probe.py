# -*- coding: utf-8 -*-
"""Insert several candidate SVGs, one per slide, export each at 600 dpi and
measure the y-tick centres so the candidates can be compared numerically.

usage:  python scripts/ppt_variant_probe.py  (anaconda python)
"""
import os

import win32com.client as win32

OUT = os.path.abspath("work/ppt/variants")
os.makedirs(OUT, exist_ok=True)
SVGS = [
    ("v0_px", "out/svg/S1a_01_mu_n.svg"),
    ("v1_pt", "work/variants/v1_pt.svg"),
    ("v2_nowh", "work/variants/v2_nowh.svg"),
    ("v3_2dp", "work/variants/v3_2dp.svg"),
]
W, H = 137.569, 127.162

app = win32.DispatchEx("PowerPoint.Application")
app.Visible = True
app.DisplayAlerts = 1
pres = app.Presentations.Add()
pres.PageSetup.SlideWidth = W
pres.PageSetup.SlideHeight = H
slides = []
for i, (name, rel) in enumerate(SVGS, start=1):
    sl = pres.Slides.Add(i, 12)
    shp = sl.Shapes.AddPicture(os.path.abspath(rel), 0, -1, 0, 0, W, H)
    print("%-12s %.4f x %.4f at (%.2f,%.2f)"
          % (name, shp.Width, shp.Height, shp.Left, shp.Top))
    slides.append((i, name))
pres.SaveAs(os.path.join(OUT, "variants.pptx"))
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
app2.DisplayAlerts = 1
pres2 = app2.Presentations.Open(os.path.join(OUT, "variants.pptx"), WithWindow=-1)
for i, name in slides:
    png = os.path.join(OUT, name + ".png")
    pres2.Slides(i).Export(png, "PNG", int(round(W * 600 / 72)),
                          int(round(H * 600 / 72)))
    print("exported", png)
try:
    pres2.Close()
except Exception as e:
    print("(close: %s)" % e)
try:
    app2.Quit()
except Exception as e:
    print("(quit: %s)" % e)
