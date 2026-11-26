# -*- coding: utf-8 -*-
"""Second round of root-attribute variants (anaconda python)."""
import os

import win32com.client as win32

OUT = os.path.abspath("work/ppt/variants")
SVGS = [
    ("v4_vbpx", "work/variants/v4_vbpx.svg", 137.569, 127.162),
    ("v2_nowh", "work/variants/v2_nowh.svg", 137.569, 127.162),
    ("v5_heat_nowh", "work/variants/v5_heat_nowh.svg", 379.758, 379.758),
    ("v6_heat_px", "out/svg/S1b_heatmap.svg", 379.758, 379.758),
]

app = win32.DispatchEx("PowerPoint.Application")
app.Visible = True
app.DisplayAlerts = 1
pres = app.Presentations.Add()
pres.PageSetup.SlideWidth = 400.0
pres.PageSetup.SlideHeight = 400.0
info = []
for i, (name, rel, w, h) in enumerate(SVGS, start=1):
    sl = pres.Slides.Add(i, 12)
    s = sl.Shapes.AddPicture(os.path.abspath(rel), 0, -1, 10, 10, w, h)
    print("%-14s %.4f x %.4f" % (name, s.Width, s.Height))
    info.append((i, name))
pres.SaveAs(os.path.join(OUT, "variants2.pptx"))
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
p2 = app2.Presentations.Open(os.path.join(OUT, "variants2.pptx"), WithWindow=-1)
for i, name in info:
    p2.Slides(i).Export(os.path.join(OUT, name + ".png"), "PNG", 3333, 3333)
try:
    p2.Close()
except Exception as e:
    print("(close: %s)" % e)
try:
    app2.Quit()
except Exception as e:
    print("(quit: %s)" % e)
print("done")
