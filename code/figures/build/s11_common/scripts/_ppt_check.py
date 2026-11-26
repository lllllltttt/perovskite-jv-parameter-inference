import os, numpy as np
from PIL import Image
import win32com.client as win32
OUT=os.path.abspath("package/comparison_common_test")
W,H=244.54,169.79
app=win32.DispatchEx("PowerPoint.Application"); app.Visible=True; app.DisplayAlerts=1
pres=app.Presentations.Add(); pres.PageSetup.SlideWidth=W; pres.PageSetup.SlideHeight=H
for i,n in enumerate(("common_test_a","common_test_b"),start=1):
    sl=pres.Slides.Add(i,12)
    shp=sl.Shapes.AddPicture(os.path.join(OUT,n+".svg"),0,-1,0,0,W,H)
    print("insert %-14s asked %.2f x %.2f  got %.2f x %.2f"%(n,W,H,shp.Width,shp.Height))
pptx=os.path.abspath("work_ppt.pptx"); pres.SaveAs(pptx)
try: pres.Close()
except Exception: pass
try: app.Quit()
except Exception: pass
app2=win32.DispatchEx("PowerPoint.Application"); app2.Visible=True
p2=app2.Presentations.Open(pptx,WithWindow=-1)
for i,n in enumerate(("common_test_a","common_test_b"),start=1):
    s=p2.Slides(i); s.Export(os.path.abspath("work_ppt_%s.png"%n),"PNG",1600,1110)
    a=np.asarray(Image.open(os.path.abspath("work_ppt_%s.png"%n)).convert("RGB")).astype(int)
    print("slide %d %-14s red px %d"%(i,n,int(((a[...,0]>235)&(a[...,1]<35)&(a[...,2]<35)).sum())))
try: p2.Close()
except Exception: pass
try: app2.Quit()
except Exception: pass
