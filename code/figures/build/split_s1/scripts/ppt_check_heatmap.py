# -*- coding: utf-8 -*-
"""Real-PowerPoint round trip for the heat map piece (anaconda python / pywin32).

Insert -> read back the shape size -> save -> reopen -> export 600 dpi.
"""
import os

import win32com.client as win32

W, H = 426.00, 382.56
SVG = os.path.abspath("out/heatmap_numbers/S1b_heatmap_numbers.svg")
OUT = os.path.abspath("work/ppt")
os.makedirs(OUT, exist_ok=True)

app = win32.DispatchEx("PowerPoint.Application")
app.Visible = True
app.DisplayAlerts = 1
pres = app.Presentations.Add()
pres.PageSetup.SlideWidth = W
pres.PageSetup.SlideHeight = H
sl = pres.Slides.Add(1, 12)
shp = sl.Shapes.AddPicture(SVG, 0, -1, 0, 0, W, H)
print("inserted: %.4f x %.4f pt at (%.3f, %.3f)   tag=%s"
      % (shp.Width, shp.Height, shp.Left, shp.Top, shp.Tags.Count))
pres.SaveAs(os.path.join(OUT, "heatmap_check.pptx"))
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
p2 = app2.Presentations.Open(os.path.join(OUT, "heatmap_check.pptx"), WithWindow=-1)
s2 = p2.Slides(1)
print("reopened: %d shape(s), %.4f x %.4f pt"
      % (s2.Shapes.Count, s2.Shapes(1).Width, s2.Shapes(1).Height))
png = os.path.join(OUT, "heatmap_check.png")
s2.Export(png, "PNG", 3550, 3188)
print("exported", png)
try:
    p2.Close()
except Exception as e:
    print("(close: %s)" % e)
try:
    app2.Quit()
except Exception as e:
    print("(quit: %s)" % e)
