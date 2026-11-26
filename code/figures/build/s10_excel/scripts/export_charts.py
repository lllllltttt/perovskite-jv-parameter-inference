# -*- coding: utf-8 -*-
import os
import win32com.client as win32
XLSX=os.path.abspath("Figure_comparison_editable.xlsx")
WORK=os.path.abspath("work/office"); os.makedirs(WORK,exist_ok=True)
app=win32.DispatchEx("Excel.Application"); app.Visible=True; app.DisplayAlerts=False
wb=app.Workbooks.Open(XLSX,UpdateLinks=0)
for name in ("Chart_a","Chart_b"):
    ch=wb.Sheets(name).ChartObjects(1).Chart
    p=os.path.join(WORK,name+".png")
    ch.Export(p,"PNG")
    print(name,"->",p,os.path.getsize(p))
    # also a big version
    co=wb.Sheets(name).ChartObjects(1)
    w,h=co.Width,co.Height
    co.Width,co.Height=w*1.6,h*1.6
    ch.Export(os.path.join(WORK,name+"_big.png"),"PNG")
    co.Width,co.Height=w,h
    print(name,"big ->",os.path.getsize(os.path.join(WORK,name+"_big.png")))
wb.Close(SaveChanges=False)
try: app.Quit()
except Exception as e: print("(quit:",e,")")
