import os
import win32com.client as win32
app=win32.DispatchEx("Excel.Application"); app.Visible=False; app.DisplayAlerts=False
wb=app.Workbooks.Open(os.path.abspath("Figure_comparison_editable.xlsx"),UpdateLinks=0)
for sh in ("Data","Notes"):
    ws=wb.Sheets(sh)
    print("==",sh,"used:",ws.UsedRange.Address)
ws=wb.Sheets("Data")
for r in (1,3,4,5):
    print("row%d:"%r,[ws.Cells(r,c).Value for c in range(1,7)])
print("summary hdr:",[ws.Cells(3,c).Value for c in range(9,15)])
print("summary r4:",[ws.Cells(4,c).Value for c in range(9,15)])
nt=wb.Sheets("Notes")
n=nt.UsedRange.Rows.Count
print("notes rows:",n)
for r in (1,3,5,9,12,16,22):
    v=nt.Cells(r,1).Value
    if v: print("  ",str(v)[:90])
wb.Close(SaveChanges=False)
try: app.Quit()
except Exception: pass
