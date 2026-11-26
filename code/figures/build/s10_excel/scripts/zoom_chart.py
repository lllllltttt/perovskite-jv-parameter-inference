import os
import win32com.client as win32
XLSX=os.path.abspath("Figure_comparison_editable.xlsx")
WORK=os.path.abspath("work/office")
app=win32.DispatchEx("Excel.Application"); app.Visible=True; app.DisplayAlerts=False
wb=app.Workbooks.Open(XLSX,UpdateLinks=0)
co=wb.Sheets("Chart_a").ChartObjects(1)
w,h=co.Width,co.Height
co.Width,co.Height=900,700
ch=co.Chart
ch.Export(os.path.join(WORK,"Chart_a_huge.png"),"PNG")
co.Width,co.Height=w,h
wb.Close(SaveChanges=False)
try: app.Quit()
except Exception: pass
print("ok")
