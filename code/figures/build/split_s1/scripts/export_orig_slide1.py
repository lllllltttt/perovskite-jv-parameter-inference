# -*- coding: utf-8 -*-
"""Export slide 1 of the original SI.pptx at ~600 dpi for reference."""
import os
import win32com.client as win32

SRC = os.path.abspath("SI_source_copy.pptx")
OUT = os.path.abspath("work/orig_slide1_600.png")
app = win32.DispatchEx("PowerPoint.Application")
app.Visible = True
app.DisplayAlerts = 1
p = app.Presentations.Open(SRC, WithWindow=-1)
sl = p.Slides(1)
w = p.PageSetup.SlideWidth
h = p.PageSetup.SlideHeight
print("slide %.3f x %.3f pt, shapes %d" % (w, h, sl.Shapes.Count))
for i in range(1, sl.Shapes.Count + 1):
    s = sl.Shapes(i)
    print("  shape %d: %.3f x %.3f at (%.3f,%.3f) type %d" % (i, s.Width, s.Height, s.Left, s.Top, s.Type))
sl.Export(OUT, "PNG", int(round(w * 600 / 72)), int(round(h * 600 / 72)))
print("exported", OUT, os.path.getsize(OUT))
try:
    p.Close()
except Exception as e:
    print("(close: %s)" % e)
try:
    app.Quit()
except Exception as e:
    print("(quit: %s)" % e)
