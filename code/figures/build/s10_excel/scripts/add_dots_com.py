# -*- coding: utf-8 -*-
"""Add the per-seed dots as native XY series on the secondary axis.

Excel itself writes the combo-chart structure this way; doing it through the
Excel object model (instead of hand-editing chart XML) keeps the workbook
100 % native and avoids the category-axis pitfall.
"""
import os, sys
import win32com.client as win32

XLSX = os.path.abspath("Figure_comparison_editable.xlsx")
CFG = {   # sheet, x-orig, y-orig, x-exp, y-exp, first row, last row
    "Chart_a": ("U", "V", "W", "X", 3, 32, 0.82498, 0.1),
    "Chart_b": ("U", "V", "W", "X", 69, 98, 1.13538, 0.2),
}
XL_CATEGORY, XL_VALUE, XL_SECONDARY = 1, 2, 2
XL_XYSCATTER, XL_CIRCLE = -4169, -4142
XL_NONE = -4142

app = win32.DispatchEx("Excel.Application")
app.Visible = True
app.DisplayAlerts = False
wb = app.Workbooks.Open(XLSX, UpdateLinks=0)
ws = wb.Sheets("Data")

for sheet, (cx0, cy0, cx1, cy1, r0, r1, ymax, yunit) in CFG.items():
    ch = wb.Sheets(sheet).ChartObjects(1).Chart
    for (cx, cy) in ((cx0, cy0), (cx1, cy1)):
        s = ch.SeriesCollection().NewSeries()
        s.XValues = ws.Range("%s%d:%s%d" % (cx, r0, cx, r1))
        s.Values = ws.Range("%s%d:%s%d" % (cy, r0, cy, r1))
        s.ChartType = XL_XYSCATTER
        s.AxisGroup = XL_SECONDARY
        s.MarkerStyle = XL_CIRCLE
        s.MarkerSize = 3
        s.MarkerBackgroundColor = 0x000000
        s.MarkerForegroundColor = 0x000000
        try:
            s.Format.Fill.Transparency = 0.5
        except Exception as e:
            print("  (fill transparency:", e, ")")
        s.Format.Line.Visible = 0
    # secondary axes: match the primary limits, then hide them
    for kind in (XL_CATEGORY, XL_VALUE):
        ax = ch.Axes(kind, XL_SECONDARY)
        ax.HasTitle = False
        ax.TickLabelPosition = XL_NONE
        ax.MajorTickMark = XL_NONE
        ax.MinorTickMark = XL_NONE
        ax.Format.Line.Visible = 0
        ax.MajorGridlines.Format.Line.Visible = 0 if ax.HasMajorGridlines else 0
    xa = ch.Axes(XL_CATEGORY, XL_SECONDARY)
    ya = ch.Axes(XL_VALUE, XL_SECONDARY)
    xa.MinimumScale, xa.MaximumScale, xa.MajorUnit = -0.5, 5.5, 1
    ya.MinimumScale, ya.MaximumScale, ya.MajorUnit = 0.0, ymax, yunit
    print("  %s: series=%d" % (sheet, ch.SeriesCollection().Count))

wb.Save()
wb.Close(SaveChanges=False)
try:
    app.Quit()
except Exception:
    pass
print("saved with dots")
