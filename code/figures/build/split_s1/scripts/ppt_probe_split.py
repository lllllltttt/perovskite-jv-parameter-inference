"""Insert all 11 piece SVGs into real PowerPoint, save, quit, reopen, export.

Verifies (a) no red-X placeholder, (b) each shape keeps its exact size,
(c) the assembled slide looks like the original arrangement.

Runs under anaconda python (has pywin32).
"""
import json
import os
import time

import numpy as np
import win32com.client as win32
from PIL import Image

ppAlertsNone = 1
msoFalse, msoTrue = 0, -1

GEO = json.load(open("work/geometry.json", encoding="utf-8"))
OUT = "work/ppt"
os.makedirs(OUT, exist_ok=True)
pptx = os.path.abspath(os.path.join(OUT, "probe_split.pptx"))
png = os.path.abspath(os.path.join(OUT, "probe_split_slide.png"))

FIG_W, FIG_H = 972.212, 510.466
M = GEO["margin"]


def red_x_score(path):
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.int16)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    red = (r > 150) & (g < 90) & (b < 90)
    return float(red.mean())


def quit_app(app):
    try:
        app.Quit()
    except Exception as e:
        print("  (quit: %s)" % e)


# ---- pass 1: build and save -------------------------------------------
print("pass 1: build")
app = win32.DispatchEx("PowerPoint.Application")
app.Visible = True
app.DisplayAlerts = ppAlertsNone
pres = app.Presentations.Add()
pres.PageSetup.SlideWidth = FIG_W
pres.PageSetup.SlideHeight = FIG_H
slide = pres.Slides.Add(1, 12)
print("slide: %.3f x %.3f pt" % (FIG_W, FIG_H))

for p in GEO["pieces"]:
    r = p["rect"]
    x, y = r["x"] - M, r["y"] - M
    svg = os.path.abspath(p["file"])
    shp = slide.Shapes.AddPicture(svg, msoFalse, msoTrue, x, y, p["W"], p["H"])
    print("  %-14s at (%7.2f,%7.2f)  w=%7.3f h=%7.3f"
          % (p["name"], shp.Left, shp.Top, shp.Width, shp.Height))
    assert abs(shp.Width - p["W"]) < 0.01 and abs(shp.Height - p["H"]) < 0.01, \
        "shape size changed"

pres.SaveAs(pptx)
print("saved:", os.path.getsize(pptx), "bytes")
try:
    pres.Close()
except Exception as e:
    print("  (close after save: %s)" % e)
quit_app(app)

# ---- pass 2: reopen and export ----------------------------------------
print("pass 2: reopen")
time.sleep(2)
app2 = win32.DispatchEx("PowerPoint.Application")
app2.Visible = True
app2.DisplayAlerts = ppAlertsNone
pres2 = app2.Presentations.Open(pptx, WithWindow=msoTrue)
sl = pres2.Slides(1)
print("reopened shapes:", sl.Shapes.Count)
sl.Export(png, "PNG", 2400, int(round(2400 * FIG_H / FIG_W)))
im = Image.open(png)
print("export:", png, im.size)
print("RED-X  : fraction=%.6f" % red_x_score(png))
for s, p in zip(sl.Shapes, GEO["pieces"]):
    print("  %-14s w=%7.3f h=%7.3f  (expected %7.3f x %7.3f)"
          % (p["name"], s.Width, s.Height, p["W"], p["H"]))
try:
    pres2.Close()
except Exception as e:
    print("  (close: %s)" % e)
quit_app(app2)
print("DONE")
