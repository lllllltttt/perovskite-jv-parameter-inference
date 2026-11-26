# -*- coding: utf-8 -*-
"""Build Figure_comparison_editable.xlsx — two native Excel charts that
reproduce Figure S9 of the SI (own-distribution skill and error).

Everything is read from the frozen result table the original figure script
uses (20261021_expanded_ratio_comparison_v2/out/metrics/table_B_common_tests.csv)
and cross-checked against its figures/figure_values.csv:

    bar height      = mean of the 5 seeds for that arm x coordinate
    error bar       = sample standard deviation over the 5 seeds (ddof = 1)
    small dots      = every individual seed value (10 per bar)

Charts are native: clustered column series + custom error bars whose values
are cell references + marker-only scatter series on hidden secondary axes
(x of the scatter = category index +- 0.18 so the dots sit on their bar).
"""
import io
import json
import os
import sys

import numpy as np
import pandas as pd
import xlsxwriter

if (getattr(sys.stdout, "encoding", "") or "").lower().replace("-", "") != "utf8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = r"E:\project\work1\20261021_expanded_ratio_comparison_v2"
CSV = os.path.join(ROOT, "out", "metrics", "table_B_common_tests.csv")
FVC = os.path.join(ROOT, "figures", "figure_values.csv")
OUTDIR = r"E:\project\work1\20261117_figs9_excel"
XLSX = os.path.join(OUTDIR, "Figure_comparison_editable.xlsx")

COORDS = ["a_mu", "r_mu", "a_tau", "r_tau", "a_D", "r_D"]
LABELS = ["a_μ", "r_μ", "a_τ", "r_τ", "a_D", "r_D"]
ARMS = [("original", "original 0.2–5 (own test)"),
        ("expanded", "expanded 0.05–20 (own test)")]
C_OLD, C_NEW = "#0072B2", "#D55E00"

# y ranges taken from the source SVG (plot-box top / tick spacing), so the
# charts keep their own original limits; major units as in the original.
YMAX = {"skill": 0.82498, "rmse": 1.13538}
YUNIT = {"skill": 0.1, "rmse": 0.2}
NSEED = 5                # seeds per arm (20261021-20261025)
W = 0.36                 # bar width of the original figure (category units)
HALF = W / 2.0           # 0.18 -> bar centres at i +- 0.18


def load():
    df = pd.read_csv(CSV)
    A = df[df["test_arm"] == df["model_arm"]].copy()
    data = {}
    for key, metric in (("skill", "skill_mse"), ("rmse", "rmse")):
        data[key] = {}
        for arm, _lab in ARMS:
            per = {}
            for c in COORDS:
                v = A[(A["model_arm"] == arm) &
                      (A["quantity"] == c)][metric].astype(float).to_numpy()
                assert len(v) == NSEED, (key, arm, c, len(v))
                per[c] = dict(mean=float(np.nanmean(v)),
                              sd=float(np.nanstd(v, ddof=1)),
                              vals=[float(x) for x in v])
            data[key][arm] = per
    return A, data


def check_against_figure_values(data):
    fv = pd.read_csv(FVC)
    fv = fv[fv["figure"] == "fig02"]
    for key, metric in (("skill", "skill_mse_mean"), ("rmse", "rmse_mean")):
        for arm, _ in ARMS:
            g = fv[(fv["metric"] == metric) & (fv["arm"] == arm)]
            for c in COORDS:
                want = float(g[g["coordinate"] == c]["value"].iloc[0])
                got = data[key][arm][c]["mean"]
                assert abs(want - got) < 5e-6, (key, arm, c, want, got)
    # the dots must be the plotted seed values too
    for arm, _ in ARMS:
        g = fv[(fv["metric"] == "skill_mse") & (fv["arm"] == arm)]
        for c in COORDS:
            # NB: the original export put the plotted value in the
            # "seed_index" column and the index in "value" - use seed_index.
            want = sorted(g[g["coordinate"] == c]["seed_index"].astype(float).tolist())
            got = sorted(data["skill"][arm][c]["vals"])
            assert len(want) == len(got) == NSEED
            assert max(abs(a - b) for a, b in zip(want, got)) < 5e-6, (arm, c)
    print("  cross-check vs figure_values.csv: bars, sd and dots agree")


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    A, data = load()
    check_against_figure_values(data)

    wb = xlsxwriter.Workbook(XLSX)
    wb.set_properties({"title": "Figure S9 own-distribution skill and error",
                       "comments": "values from table_B_common_tests.csv"})
    head = wb.add_format({"bold": True})
    num4 = wb.add_format({"num_format": "0.0000"})
    num3 = wb.add_format({"num_format": "0.000"})
    txt = wb.add_format({"valign": "top"})

    ds = wb.add_worksheet("Data")

    # ---------------- raw rows ------------------------------------------
    ds.write(0, 0, "Raw rows used by the figure  (test_arm == model_arm, "
                   "six paired coordinates, 5 seeds each)", head)
    cols = ["test_arm", "model_arm", "seed", "coordinate", "skill_mse", "rmse"]
    for j, c in enumerate(cols):
        ds.write(2, j, c, head)
    rows = A[A["quantity"].isin(COORDS)][
        ["test_arm", "model_arm", "seed", "quantity", "skill_mse", "rmse"]]
    rows = rows.sort_values(["model_arm", "quantity", "seed"])
    r = 3
    for _, row in rows.iterrows():
        ds.write(r, 0, row["test_arm"])
        ds.write(r, 1, row["model_arm"])
        ds.write_number(r, 2, int(row["seed"]))
        ds.write(r, 3, row["quantity"])
        ds.write_number(r, 4, float(row["skill_mse"]), num4)
        ds.write_number(r, 5, float(row["rmse"]), num4)
        r += 1
    n_raw = r - 3
    print("  raw rows written:", n_raw)

    # ---------------- summary -------------------------------------------
    S0 = 1                          # column B start (0-based col index)
    ds.write(0, 8, "Summary: mean over the 5 seeds (bar height) and sample "
                   "SD, ddof=1 (error bar)", head)
    for j, c in enumerate(["coordinate", "arm", "skill_mean", "skill_sd",
                           "rmse_mean", "rmse_sd"]):
        ds.write(2, 8 + j, c, head)
    sr = 3
    for arm, _ in ARMS:
        for c in COORDS:
            ds.write(sr, 8, c)
            ds.write(sr, 9, arm)
            ds.write_number(sr, 10, data["skill"][arm][c]["mean"], num4)
            ds.write_number(sr, 11, data["skill"][arm][c]["sd"], num4)
            ds.write_number(sr, 12, data["rmse"][arm][c]["mean"], num4)
            ds.write_number(sr, 13, data["rmse"][arm][c]["sd"], num4)
            sr += 1

    # ---------------- chart data blocks ---------------------------------
    # block A (skill): P..X  rows 3..62 ; block B (rmse) below it
    def block(title, key, r0):
        ds.write(r0, 15, title, head)
        hdr = ["coordinate", "orig_mean", "orig_sd", "exp_mean", "exp_sd",
               "x_orig", "y_orig", "x_exp", "y_exp"]
        for j, h in enumerate(hdr):
            ds.write(r0 + 1, 15 + j, h, head)
        for i, c in enumerate(COORDS):
            ds.write(r0 + 2 + i, 15, c)
            ds.write_number(r0 + 2 + i, 16, data[key]["original"][c]["mean"], num4)
            ds.write_number(r0 + 2 + i, 17, data[key]["original"][c]["sd"], num4)
            ds.write_number(r0 + 2 + i, 18, data[key]["expanded"][c]["mean"], num4)
            ds.write_number(r0 + 2 + i, 19, data[key]["expanded"][c]["sd"], num4)
        rr = r0 + 2
        for i, c in enumerate(COORDS):
            for v in data[key]["original"][c]["vals"]:
                ds.write_number(rr, 20, i - HALF)
                ds.write_number(rr, 21, v, num4)
                rr += 1
        rr = r0 + 2
        for i, c in enumerate(COORDS):
            for v in data[key]["expanded"][c]["vals"]:
                ds.write_number(rr, 22, i + HALF)
                ds.write_number(rr, 23, v, num4)
                rr += 1
        return dict(r0=r0, cats=(r0 + 2, r0 + 7))

    blkA = block("Chart A data — Skill_MSE", "skill", 0)
    blkB = block("Chart B data — RMSE (physical log10)", "rmse", 66)

    ds.set_column("A:F", 12)
    ds.set_column("I:N", 13)
    ds.set_column("P:X", 11)

    # ---------------- chart factory -------------------------------------
    def make_chart(blk, key, ymax, yunit):
        r0 = blk["r0"]
        chart = wb.add_chart({"type": "column"})
        for k, (arm, lab) in enumerate(ARMS):
            col_mean = 16 + 2 * k          # Q/S
            col_sd = 17 + 2 * k            # R/T
            chart.add_series({
                "name": lab,
                "categories": ["Data", r0 + 2, 15, r0 + 7, 15],
                "values": ["Data", r0 + 2, col_mean, r0 + 7, col_mean],
                "fill": {"color": C_OLD if k == 0 else C_NEW,
                         "transparency": 15},
                "border": {"none": True},
                "gap": 40,
                "overlap": 0,
                "y_error_bars": {
                    "type": "custom",
                    "plus_values": "=Data!${c}${a}:${c}${b}".format(
                        c=chr(ord("A") + col_sd), a=r0 + 3, b=r0 + 8),
                    "minus_values": "=Data!${c}${a}:${c}${b}".format(
                        c=chr(ord("A") + col_sd), a=r0 + 3, b=r0 + 8),
                    "plus_data": [data[key][arm][c]["sd"] for c in COORDS],
                    "minus_data": [data[key][arm][c]["sd"] for c in COORDS],
                    "end_style": 1,
                    "line": {"color": "#000000", "width": 0.8},
                },
            })
        # dots: added later by Excel itself (scripts/add_dots_com.py) so the
        # combo chart gets exactly the structure Excel writes natively
        if not os.environ.get("WITH_DOTS"):
            return chart
        dots = wb.add_chart({"type": "scatter", "subtype": "marker"})
        for k, (arm, _lab) in enumerate(ARMS):
            cx, cy = 20 + 2 * k, 21 + 2 * k
            dots.add_series({
                "categories": ["Data", r0 + 2, cx, r0 + 1 + 6 * NSEED, cx],
                "values": ["Data", r0 + 2, cy, r0 + 1 + 6 * NSEED, cy],
                "marker": {"type": "circle", "size": 3,
                           "fill": {"color": "#000000", "transparency": 50},
                           "border": {"none": True}},
                "line": {"none": True},
                "x2_axis": True, "y2_axis": True,
            })
        # secondary axes belong to the combined chart
        dots.set_x2_axis({"visible": False, "min": -0.5, "max": 5.5,
                          "major_unit": 1})
        dots.set_y2_axis({"visible": False, "min": 0.0, "max": ymax,
                          "major_unit": yunit})
        chart.combine(dots)

        chart.set_legend({"none": True})
        chart.set_title({"none": True})
        chart.set_size({"width": 470, "height": 375})
        chart.set_chartarea({"border": {"color": "#000000", "width": 0.5},
                             "fill": {"color": "#FFFFFF"}})
        chart.set_plotarea({"border": {"color": "#000000", "width": 0.5},
                            "fill": {"color": "#FFFFFF"},
                            "layout": {"x": 0.13, "y": 0.05,
                                       "width": 0.85, "height": 0.92}})
        chart.set_x_axis({
            "label_position": "none",          # numbers gone, tick marks kept
            "major_tick_mark": "outside",
            "minor_tick_mark": "none",
            "line": {"color": "#000000", "width": 0.5},
            "major_unit": 1,
            "min": -0.5, "max": 5.5,
        })
        chart.set_y_axis({
            "min": 0.0, "max": ymax, "major_unit": yunit,
            "major_tick_mark": "outside", "minor_tick_mark": "none",
            "line": {"color": "#000000", "width": 0.5},
            "num_font": {"name": "Arial", "size": 7, "color": "#000000"},
            "num_format": "0.0",
            "major_gridlines": {"visible": True,
                                "line": {"color": "#D9D9D9", "width": 0.5,
                                         "dash_type": "round_dot"}},
        })
        return chart

    ca = make_chart(blkA, "skill", YMAX["skill"], YUNIT["skill"])
    cb = make_chart(blkB, "rmse", YMAX["rmse"], YUNIT["rmse"])

    sha = wb.add_worksheet("Chart_a")
    sha.insert_chart("B2", ca)
    shb = wb.add_worksheet("Chart_b")
    shb.insert_chart("B2", cb)
    for sh in (sha, shb):          # one chart per printed page, nothing cut
        sh.set_landscape()
        sh.set_paper(9)            # A4
        sh.fit_to_pages(1, 1)
        sh.set_margins(0.4, 0.4, 0.4, 0.4)
        sh.hide_gridlines(2)

    # ---------------- Notes ---------------------------------------------
    ns = wb.add_worksheet("Notes")
    ns.set_column("A:A", 118)
    lines = [
        ("Figure S9 — own-distribution comparison of Skill_MSE and RMSE "
         "(physical log10). Source data and figure script", True),
        ("", False),
        ("数据来源 / source", True),
        ("  脚本: 20261021_expanded_ratio_comparison_v2/scripts/05_figures.py "
         "(fig02_skill_and_error)", False),
        ("  数据: out/metrics/table_B_common_tests.csv，取 test_arm = model_arm "
         "的行（各自分布上的自测）", False),
        ("  交叉核对: figures/figure_values.csv 里的 skill_mse_mean / rmse_mean "
         "与每个 seed 的散点值，全部一致", False),
        ("  每个臂每个坐标 5 个 seed（20261021–20261025）；六个坐标顺序 "
         "a_μ, r_μ, a_τ, r_τ, a_D, r_D", False),
        ("", False),
        ("统计定义 / definitions", True),
        ("  柱高 = 5 个 seed 的算术平均（nanmean）", False),
        ("  误差棒 = 5 个 seed 的样本标准差（ddof = 1），上下各 1×SD，"
         "不是标准误、不是置信区间", False),
        ("  小圆点 = 每一个 seed 的原始值，每个柱子 5 个点，未抽稀、未抖动", False),
        ("  散点用隐藏的次坐标轴定位：x = 类别序号 ∓0.18（与柱中心一致），"
         "y 轴范围与主轴完全相同，所以缩放后仍然对齐", False),
        ("", False),
        ("供复制的文字 / copy-ready text", True),
        ("  (a) 标题: (a) Skill_MSE (higher is better)", False),
        ("  (b) 标题: (b) RMSE in physical log10 (lower is better)", False),
        ("  (a) 纵轴标题: Skill_MSE", False),
        ("  (b) 纵轴标题: RMSE (log10 units)", False),
        ("  横轴标题: 无", False),
        ("  横轴类别（六组）: a_μ、r_μ、a_τ、r_τ、a_D、r_D", False),
        ("  图例（两行）: original 0.2–5 (own test)  /  "
         "expanded 0.05–20 (own test)", False),
        ("  图例色块: original #0072B2（蓝）、expanded #D55E00（橙）", False),
        ("", False),
        ("图表结构 / how the sheets are built", True),
        ("  Chart A (Skill_MSE): 纵轴 0 – 0.825，刻度 0.1；"
         "Chart B (RMSE): 纵轴 0 – 1.135，刻度 0.2（各自沿用原图范围）", False),
        ("  柱: 簇状柱形，蓝色/橙色，间隙宽度 40%（对应原图柱宽 0.36、两组相邻）", False),
        ("  误差棒: 自定义 → 引用 Data 表的 sd 列（黑色 0.8 pt，有端帽）", False),
        ("  圆点: 次坐标轴散点，仅标记（黑色、3 pt、50% 透明）", False),
        ("  网格线: 浅灰 #D9D9D9 0.5 pt 点线，仅水平", False),
        ("  边框: 图表区与绘图区各 0.5 pt 黑框，白底", False),
        ("", False),
        ("修改提示", True),
        ("  改柱高/误差棒：直接改 Data 表的 mean / sd 列（Q–T 列，两个块各 6 行），"
         "图表自动更新。", False),
        ("  改散点：改 U–X 列（x 与 y 各 30 行）。", False),
        ("  两个图表的绘图区大小已在 XML 里固定为相同比例，改图表大小后仍一致。", False),
    ]
    for i, (t, b) in enumerate(lines):
        ns.write(i, 0, t, head if b else txt)

    wb.close()
    print("  wrote", XLSX, os.path.getsize(XLSX), "bytes")
    json.dump({k: {arm: {c: data[k][arm][c] for c in COORDS} for arm, _ in ARMS}
               for k in data}, open(os.path.join(OUTDIR, "work_values.json"),
                                    "w"), indent=1)


if __name__ == "__main__":
    main()
