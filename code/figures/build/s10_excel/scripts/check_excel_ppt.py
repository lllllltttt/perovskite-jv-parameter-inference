# -*- coding: utf-8 -*-
"""Real Microsoft Excel / PowerPoint checks for the workbook."""
import hashlib, os, sys, time
import numpy as np
import win32com.client as win32

XLSX = os.path.abspath("Figure_comparison_editable.xlsx")
WORK = os.path.abspath("work/office"); os.makedirs(WORK, exist_ok=True)

def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()

before = md5(XLSX)
app = win32.DispatchEx("Excel.Application")
app.Visible = True
app.DisplayAlerts = False
wb = app.Workbooks.Open(XLSX, UpdateLinks=0)
print("opened:", wb.Name, "sheets:", wb.Sheets.Count,
      [wb.Sheets(i).Name for i in range(1, wb.Sheets.Count + 1)])
print("after open, file md5 unchanged:", md5(XLSX) == before)

for name in ("Chart_a", "Chart_b"):
    ws = wb.Sheets(name)
    n = ws.ChartObjects().Count
    co = ws.ChartObjects(1)
    ch = co.Chart
    print("%-8s chartobjects=%d  series=%d  type=%s  size=%.0fx%.0f pt"
          % (name, n, ch.SeriesCollection().Count,
             [ch.SeriesCollection(i).ChartType for i in range(1, ch.SeriesCollection().Count + 1)],
             co.Width, co.Height))
    # error bars present?
    eb = 0
    for i in range(1, ch.SeriesCollection().Count + 1):
        ser = ch.SeriesCollection(i)
        try:
            if ser.ErrorBars is not None:
                eb += 1
        except Exception:
            pass
    print("         series with error bars:", eb)
    # axis limits
    print("         y axis min/max: %.4f / %.4f" % (ch.Axes(2).MinimumScale, ch.Axes(2).MaximumScale))

# export PDF
pdf = os.path.join(WORK, "excel_export.pdf")
wb.ExportAsFixedFormat(0, pdf)
print("pdf:", pdf, os.path.getsize(pdf), "bytes")

# resize test: +20% then back
co = wb.Sheets("Chart_a").ChartObjects(1)
w0, h0 = co.Width, co.Height
co.Width, co.Height = w0 * 1.2, h0 * 1.2
pdf2 = os.path.join(WORK, "excel_export_big.pdf")
wb.ExportAsFixedFormat(0, pdf2)
print("pdf after resize:", os.path.getsize(pdf2), "bytes  (%.0f x %.0f -> %.0f x %.0f)"
      % (w0, h0, co.Width, co.Height))
co.Width, co.Height = w0, h0

# copy chart to PowerPoint as an editable chart
ppt = win32.DispatchEx("PowerPoint.Application")
ppt.Visible = True
pres = ppt.Presentations.Add()
sl = pres.Slides.Add(1, 12)
wb.Sheets("Chart_a").ChartObjects(1).Copy()
time.sleep(0.5)
shp = sl.Shapes.PasteSpecial(ppPasteChart=1)[0] if False else None
try:
    from win32com.client import constants  # not available; use raw int
except Exception:
    pass
shp = sl.Shapes.PasteSpecial(1)[0]      # 1 = ppPasteChart? see below
print("pasted shape type:", shp.Type, "has chart:", getattr(shp, "HasChart", "?"))
img = os.path.join(WORK, "ppt_slide.png")
sl.Export(img, "PNG", 1600, 900)
pres.SaveAs(os.path.join(WORK, "chart_copy.pptx"))
try: pres.Close()
except Exception: pass
try: ppt.Quit()
except Exception: pass

try: wb.Close(SaveChanges=False)
except Exception as e: print("(close:", e, ")")
try: app.Quit()
except Exception as e: print("(quit:", e, ")")
print("png:", img, os.path.getsize(img))
