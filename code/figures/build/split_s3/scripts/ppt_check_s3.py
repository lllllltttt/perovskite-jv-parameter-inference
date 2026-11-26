import json, os
import numpy as np
from PIL import Image
import win32com.client as win32

META = json.load(open("out/work/meta.json", encoding="utf-8"))
OUT = os.path.abspath("work/ppt")
os.makedirs(OUT, exist_ok=True)
SW = max(p["win"][2] for p in META["pieces"]); SH = max(p["win"][3] for p in META["pieces"])

app = win32.DispatchEx("PowerPoint.Application"); app.Visible = True; app.DisplayAlerts = 1
pres = app.Presentations.Add(); pres.PageSetup.SlideWidth = SW; pres.PageSetup.SlideHeight = SH
for i, p in enumerate(META["pieces"], start=1):
    sl = pres.Slides.Add(i, 12)
    shp = sl.Shapes.AddPicture(os.path.abspath(p["svg"]), 0, -1, 0, 0, p["win"][2], p["win"][3])
    print("insert %-4s asked %8.3f x %8.3f  got %8.3f x %8.3f" % (p["name"], p["win"][2], p["win"][3], shp.Width, shp.Height))
pptx = os.path.join(OUT, "s3_check.pptx"); pres.SaveAs(pptx)
try: pres.Close()
except Exception as e: print("(close: %s)" % e)
try: app.Quit()
except Exception as e: print("(quit: %s)" % e)

app2 = win32.DispatchEx("PowerPoint.Application"); app2.Visible = True
p2 = app2.Presentations.Open(pptx, WithWindow=-1)
print("reopened: %d slides" % p2.Slides.Count)
for i, p in enumerate(META["pieces"], start=1):
    s = p2.Slides(i); pic = s.Shapes(1)
    wpx = int(round(p["win"][2] * 600 / 72)); hpx = int(round(p["win"][3] * 600 / 72))
    png = os.path.join(OUT, p["name"] + ".png"); s.Export(png, "PNG", wpx, hpx)
    a = np.asarray(Image.open(png).convert("RGB")).astype(int)
    red = int(((a[..., 0] > 235) & (a[..., 1] < 35) & (a[..., 2] < 35)).sum())
    print("slide %d %-4s shape %8.3f x %8.3f  export %dx%d  red px %d" % (i, p["name"], pic.Width, pic.Height, wpx, hpx, red))
try: p2.Close()
except Exception as e: print("(close: %s)" % e)
try: app2.Quit()
except Exception as e: print("(quit: %s)" % e)
