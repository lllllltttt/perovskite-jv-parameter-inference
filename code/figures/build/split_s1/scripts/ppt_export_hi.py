# -*- coding: utf-8 -*-
"""Re-export the saved probe slide from PowerPoint at ~600 dpi.

Runs under anaconda python (pywin32).  Does not modify the saved pptx.
"""
import os
import sys

import win32com.client as win32

OUT = os.path.abspath("work/ppt/probe_split_slide_hi.png")
SRC = os.path.abspath("work/ppt/probe_split.pptx")

app = win32.DispatchEx("PowerPoint.Application")
app.Visible = True
app.DisplayAlerts = 1
pres = app.Presentations.Open(SRC, WithWindow=-1)
try:
    pres.Slides(1).Export(OUT, "PNG", 8102, 4254)
    print("exported", OUT, os.path.getsize(OUT), "bytes")
except Exception as e:
    print("export failed:", e)
try:
    pres.Close()
except Exception as e:
    print("(close: %s)" % e)
try:
    app.Quit()
except Exception as e:
    print("(quit: %s)" % e)
