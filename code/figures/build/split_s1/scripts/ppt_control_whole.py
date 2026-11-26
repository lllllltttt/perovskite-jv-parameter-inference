# -*- coding: utf-8 -*-
"""Control: put the WHOLE text-free figure (one picture, no splitting) into
PowerPoint and export it at the same resolution.  If the same sub-pixel
offsets appear here, they belong to PowerPoint's SVG renderer, not to the
split.  Runs under anaconda python (pywin32).
"""
import os

import win32com.client as win32

OUT = os.path.abspath("work/ppt")
os.makedirs(OUT, exist_ok=True)
pptx = os.path.join(OUT, "control_whole.pptx")
png = os.path.join(OUT, "control_whole.png")
SVG = os.path.abspath("out/svg/_preview_no_text.svg")
W, H = 972.212, 510.466

app = win32.DispatchEx("PowerPoint.Application")
app.Visible = True
app.DisplayAlerts = 1
pres = app.Presentations.Add()
pres.PageSetup.SlideWidth = W
pres.PageSetup.SlideHeight = H
slide = pres.Slides.Add(1, 12)
shp = slide.Shapes.AddPicture(SVG, 0, -1, 0, 0, W, H)
print("shape %.4f x %.4f at (%.4f,%.4f)"
      % (shp.Width, shp.Height, shp.Left, shp.Top))
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
pres2.Slides(1).Export(png, "PNG", 8102, 4254)
print("exported", png, os.path.getsize(png))
try:
    pres2.Close()
except Exception as e:
    print("(close: %s)" % e)
try:
    app2.Quit()
except Exception as e:
    print("(quit: %s)" % e)
