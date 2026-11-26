# -*- coding: utf-8 -*-
import os
import win32com.client as win32

OUT = os.path.abspath("work/ppt/variants")
SVGS = [
    ("v7_pxvb", "work/variants/v7_pxvb.svg", 137.569, 127.162),
    ("v0_px", "out/svg/S1a_01_mu_n.svg", 137.569, 127.162),
]
app = win32.DispatchEx("PowerPoint.Application")
app.Visible = True
app.DisplayAlerts = 1
pres = app.Presentations.Add()
pres.PageSetup.SlideWidth = 137.569
pres.PageSetup.SlideHeight = 127.162
for i, (name, rel, w, h) in enumerate(SVGS, start=1):
    sl = pres.Slides.Add(i, 12)
    s = sl.Shapes.AddPicture(os.path.abspath(rel), 0, -1, 0, 0, w, h)
    print("%-10s %.4f x %.4f" % (name, s.Width, s.Height))
pres.SaveAs(os.path.join(OUT, "variants3.pptx"))
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
p2 = app2.Presentations.Open(os.path.join(OUT, "variants3.pptx"), WithWindow=-1)
for i, (name, rel, w, h) in enumerate(SVGS, start=1):
    p2.Slides(i).Export(os.path.join(OUT, name + "_b.png"), "PNG", 1146, 1060)
try:
    p2.Close()
except Exception as e:
    print("(close: %s)" % e)
try:
    app2.Quit()
except Exception as e:
    print("(quit: %s)" % e)
print("done")
