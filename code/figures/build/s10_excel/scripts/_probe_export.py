import os
import win32com.client as win32
app=win32.DispatchEx("Excel.Application"); app.Visible=True; app.DisplayAlerts=False
wb=app.Workbooks.Open(os.path.abspath("work/office/probe.xlsx"),UpdateLinks=0)
co=wb.Sheets("Chart_a").ChartObjects(1); w,h=co.Width,co.Height
co.Width,co.Height=900,700
co.Chart.Export(os.path.abspath("work/office/probe.png"),"PNG")
co.Width,co.Height=w,h
wb.Close(SaveChanges=False)
try: app.Quit()
except Exception: pass
print("ok")
