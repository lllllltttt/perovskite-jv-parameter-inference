import os, shutil
import win32com.client as win32
src="Figure_comparison_editable.xlsx"; tmp=os.path.abspath("work/office/probe2.xlsx")
shutil.copy2(src,tmp)
app=win32.DispatchEx("Excel.Application"); app.Visible=True; app.DisplayAlerts=False
wb=app.Workbooks.Open(tmp,UpdateLinks=0)
ws=wb.Sheets("Data"); ch=wb.Sheets("Chart_a").ChartObjects(1).Chart
n0=ch.SeriesCollection().Count
s=ch.SeriesCollection().NewSeries()
s.XValues=ws.Range("U3:U32")
s.Values=ws.Range("V3:V32")
s.ChartType=-4169          # xlXYScatter
s.AxisGroup=2              # xlSecondary
s.MarkerStyle=-4142        # xlMarkerStyleCircle
s.MarkerSize=6
s.MarkerBackgroundColor=255
s.MarkerForegroundColor=255
try: s.Format.Fill.Transparency=0
except Exception as e: print("fill transp:",e)
try: s.Format.Line.Visible=0
except Exception as e: print("line:",e)
print("series now:",ch.SeriesCollection().Count,"was",n0)
for i in range(1,ch.SeriesCollection().Count+1):
    print("  ",i,ch.SeriesCollection(i).ChartType,ch.SeriesCollection(i).AxisGroup)
wb.Save()
wb.Close(SaveChanges=False)
try: app.Quit()
except Exception: pass
print("saved probe2")
