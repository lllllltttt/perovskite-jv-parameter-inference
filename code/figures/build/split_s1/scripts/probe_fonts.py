# -*- coding: utf-8 -*-
import json
import os
import win32com.client as win32

rows = json.load(open("work/probe_fonts.json"))
app = win32.DispatchEx("PowerPoint.Application")
app.Visible = True
app.DisplayAlerts = 1
pres = app.Presentations.Add()
pres.PageSetup.SlideWidth = 120.0
pres.PageSetup.SlideHeight = 120.0
for i, (name, w, h) in enumerate(rows, start=1):
    sl = pres.Slides.Add(i, 12)
    s = sl.Shapes.AddPicture(os.path.abspath("work/probe_%s.svg" % name), 0, -1, 0, 0, w, h)
pres.SaveAs(os.path.abspath("work/ppt/probe_fonts.pptx"))
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
p2 = app2.Presentations.Open(os.path.abspath("work/ppt/probe_fonts.pptx"), WithWindow=-1)
for i, (name, w, h) in enumerate(rows, start=1):
    p2.Slides(i).Export(os.path.abspath("work/ppt/font_%s.png" % name), "PNG", 1000, 1000)
try:
    p2.Close()
except Exception as e:
    print("(close: %s)" % e)
try:
    app2.Quit()
except Exception as e:
    print("(quit: %s)" % e)
print("done")
