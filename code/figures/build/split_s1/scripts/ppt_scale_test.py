# -*- coding: utf-8 -*-
"""Scale test: the same histogram piece at 1x and 2x on one slide.

If PowerPoint's vertical compression is proportional to the picture size, the
2x copy is compressed twice as much in pt; if it is a fixed rasterisation
offset, both are compressed by the same amount.
"""
import os

import win32com.client as win32

OUT = os.path.abspath("work/ppt")
pptx = os.path.join(OUT, "probe_scale.pptx")
png = os.path.join(OUT, "probe_scale.png")
SVG = os.path.abspath("out/svg/S1a_01_mu_n.svg")
W, H = 137.569, 127.162
SLIDE_W, SLIDE_H = 300.0, 420.0

app = win32.DispatchEx("PowerPoint.Application")
app.Visible = True
app.DisplayAlerts = 1
pres = app.Presentations.Add()
pres.PageSetup.SlideWidth = SLIDE_W
pres.PageSetup.SlideHeight = SLIDE_H
slide = pres.Slides.Add(1, 12)
for (x, y, k) in ((10.0, 10.0, 1.0), (10.0, 160.0, 2.0)):
    s = slide.Shapes.AddPicture(SVG, 0, -1, x, y, W * k, H * k)
    print("k=%.1f  %.4f x %.4f at (%.2f,%.2f)" % (k, s.Width, s.Height, s.Left, s.Top))
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
app2.DisplayAlerts = 1
pres2 = app2.Presentations.Open(pptx, WithWindow=-1)
pres2.Slides(1).Export(png, "PNG", int(round(SLIDE_W * 600 / 72)),
                       int(round(SLIDE_H * 600 / 72)))
print("exported", png)
try:
    pres2.Close()
except Exception as e:
    print("(close: %s)" % e)
try:
    app2.Quit()
except Exception as e:
    print("(quit: %s)" % e)
