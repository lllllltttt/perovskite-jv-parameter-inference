import json, os
import numpy as np
from PIL import Image
import win32com.client as win32
meta = json.load(open("out_final/work/meta.json", encoding="utf-8"))
win = meta["win"]; OUT = os.path.abspath("work/ppt_final"); os.makedirs(OUT, exist_ok=True)
app = win32.DispatchEx("PowerPoint.Application"); app.Visible = True; app.DisplayAlerts = 1
pres = app.Presentations.Add(); pres.PageSetup.SlideWidth = win[2]; pres.PageSetup.SlideHeight = win[3]
sl = pres.Slides.Add(1, 12)
shp = sl.Shapes.AddPicture(os.path.abspath("out_final/svg/S3b_final.svg"), 0, -1, 0, 0, win[2], win[3])
print("insert asked %8.3f x %8.3f  got %8.3f x %8.3f" % (win[2], win[3], shp.Width, shp.Height))
pptx = os.path.join(OUT, "s3b_final.pptx"); pres.SaveAs(pptx)
try: pres.Close()
except Exception as e: print("(close: %s)" % e)
try: app.Quit()
except Exception as e: print("(quit: %s)" % e)
app2 = win32.DispatchEx("PowerPoint.Application"); app2.Visible = True
p2 = app2.Presentations.Open(pptx, WithWindow=-1)
s = p2.Slides(1); pic = s.Shapes(1)
wpx = int(round(win[2] * 600 / 72)); hpx = int(round(win[3] * 600 / 72))
png = os.path.join(OUT, "S3b_final.png"); s.Export(png, "PNG", wpx, hpx)
a = np.asarray(Image.open(png).convert("RGB")).astype(int)
red = int(((a[..., 0] > 235) & (a[..., 1] < 35) & (a[..., 2] < 35)).sum())
print("shape %8.3f x %8.3f  export %dx%d  red px %d" % (pic.Width, pic.Height, wpx, hpx, red))
b = np.asarray(Image.open("out_final/png/S3b_final_600dpi.png").convert("RGB")).astype(int)
d = np.abs(a - b).max(axis=2)
print("max px diff vs SVG render: %d, pixels>60: %d of %d" % (d.max(), (d > 60).sum(), d.size))
try: p2.Close()
except Exception as e: print("(close: %s)" % e)
try: app2.Quit()
except Exception as e: print("(quit: %s)" % e)
