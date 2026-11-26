# -*- coding: utf-8 -*-
"""Full Office check: Excel open / values / PDF / resize, PowerPoint paste."""
import hashlib, os, time
import numpy as np
import win32com.client as win32

XLSX = os.path.abspath("Figure_comparison_editable.xlsx")
WORK = os.path.abspath("work/office"); os.makedirs(WORK, exist_ok=True)
md5 = lambda p: hashlib.md5(open(p, "rb").read()).hexdigest()

before = md5(XLSX)
app = win32.DispatchEx("Excel.Application"); app.Visible = True; app.DisplayAlerts = False
wb = app.Workbooks.Open(XLSX, UpdateLinks=0)
print("1) opened without repair:", wb.Name, "| sheets:", wb.Sheets.Count,
      [wb.Sheets(i).Name for i in range(1, wb.Sheets.Count + 1)],
      "| file unchanged:", md5(XLSX) == before)

expect = {  # mean values straight from the source table
 "Chart_a": {"original": [0.7641,0.1410,0.7417,0.0729,0.7027,0.0491],
             "expanded": [0.7796,0.1409,0.7238,0.1262,0.6539,0.0888]},
 "Chart_b": {"original": [0.4257,0.2985,1.0376,0.3068,0.3714,0.3221],
             "expanded": [0.4085,0.3796,1.0716,0.3808,0.3857,0.4049]},
}
for sheet in ("Chart_a", "Chart_b"):
    ch = wb.Sheets(sheet).ChartObjects(1).Chart
    print("2) %s: series=%d types=%s" % (sheet, ch.SeriesCollection().Count,
          [ch.SeriesCollection(i).ChartType for i in range(1, 5)]))
    for i, arm in ((1, "original"), (2, "expanded")):
        v = np.array(ch.SeriesCollection(i).Values)
        d = np.max(np.abs(v - np.array(expect[sheet][arm])))
        print("   %-9s bar heights max |diff| = %.5f" % (arm, d))
        assert d < 5e-4
    # error bars still reference cells?
    print("   y axis:", round(ch.Axes(2).MinimumScale, 4), "->",
          round(ch.Axes(2).MaximumScale, 4))
print("   dots: series 3/4 are XY scatter on the secondary axis:",
      [ch.SeriesCollection(i).AxisGroup for i in (3, 4)])

pdf = os.path.join(WORK, "excel_export.pdf")
wb.ExportAsFixedFormat(0, pdf)
print("3) pdf written:", os.path.getsize(pdf), "bytes")

co = wb.Sheets("Chart_a").ChartObjects(1); w0, h0 = co.Width, co.Height
co.Width, co.Height = w0 * 1.25, h0 * 1.25
wb.ExportAsFixedFormat(0, os.path.join(WORK, "excel_export_big.pdf"))
co.Chart.Export(os.path.join(WORK, "Chart_a_resized.png"), "PNG")
co.Width, co.Height = w0, h0
print("4) resize ok: %.0fx%.0f -> %.0fx%.0f pt" % (w0, h0, w0*1.25, h0*1.25))

# ---- PowerPoint: paste as an editable chart -------------------------------
ppt = win32.DispatchEx("PowerPoint.Application"); ppt.Visible = True
pres = ppt.Presentations.Add()
sl = pres.Slides.Add(1, 12)
wb.Sheets("Chart_a").ChartObjects(1).Copy()
time.sleep(0.6)
shp = None
for mode in (0, 1, -1):        # try OLE object, then chart, then default
    try:
        sl.Shapes.PasteSpecial(mode)
        shp = sl.Shapes(sl.Shapes.Count)
        if getattr(shp, "HasChart", 0):
            break
    except Exception as e:
        print("   paste mode", mode, "failed:", e)
print("5) pasted shape:", shp.Name, "HasChart:", getattr(shp, "HasChart", "?"),
      "type:", shp.Type)
img = os.path.join(WORK, "ppt_slide.png")
sl.Export(img, "PNG", 1600, 1000)
pres.SaveAs(os.path.join(WORK, "chart_copy.pptx"))
try: pres.Close()
except Exception: pass
try: ppt.Quit()
except Exception: pass
print("   slide png:", os.path.getsize(img), "bytes")

try: wb.Close(SaveChanges=False)
except Exception as e: print("(wb close:", e, ")")
try: app.Quit()
except Exception as e: print("(excel quit:", e, ")")
