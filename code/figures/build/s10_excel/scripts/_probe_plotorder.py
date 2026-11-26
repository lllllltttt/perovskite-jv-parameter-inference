import os, shutil
import win32com.client as win32
src="Figure_comparison_editable.xlsx"; tmp=os.path.abspath("work/office/probe3.xlsx")
shutil.copy2(src,tmp)
app=win32.DispatchEx("Excel.Application"); app.Visible=True; app.DisplayAlerts=False
wb=app.Workbooks.Open(tmp,UpdateLinks=0)
ch=wb.Sheets("Chart_a").ChartObjects(1).Chart
for i in range(1,ch.SeriesCollection().Count+1):
    s=ch.SeriesCollection(i)
    print(i,"type",s.ChartType,"order",s.PlotOrder)
# try: scatter series to the front
for i in (3,4):
    try:
        ch.SeriesCollection(i).PlotOrder=1
        print("set series",i,"order 1 ->",ch.SeriesCollection(i).PlotOrder)
    except Exception as e:
        print("order fail",i,e)
co=wb.Sheets("Chart_a").ChartObjects(1); w,h=co.Width,co.Height
co.Width,co.Height=900,700
co.Chart.Export(os.path.abspath("work/office/probe3.png"),"PNG")
co.Width,co.Height=w,h
wb.Close(SaveChanges=False)
try: app.Quit()
except Exception: pass
print("done")
