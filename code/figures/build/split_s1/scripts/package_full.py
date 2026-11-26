# -*- coding: utf-8 -*-
"""Assemble the delivery folder + zip for the all-ticks Figure S1 set."""
import csv
import io
import json
import os
import shutil
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

SRC = "out_ticks_full"
PKG = os.path.join("package", "FigureS1_split_allticks")
DERIVED = "work/ticks_derived.json"
LOG = "work/verify_full.log"
ZIP = "FigureS1_split_allticks.zip"

NAMES = ["S1a_01_mu_n", "S1a_02_mu_p", "S1a_03_tau_n", "S1a_04_tau_p",
         "S1a_05_N_c", "S1a_06_N_v", "S1a_07_tau_ETL", "S1a_08_tau_HTL",
         "S1a_09_r_rad", "S1b_heatmap_numbers"]
PARAM = ["mu_n", "mu_p", "tau_n", "tau_p", "N_c", "N_v", "tau_ETL",
         "tau_HTL", "r_rad", "—"]


def main():
    d = json.load(open(DERIVED, encoding="utf-8"))

    if os.path.isdir(PKG):
        shutil.rmtree(PKG)
    for sub in ("svg", "png_600dpi", "preview"):
        os.makedirs(os.path.join(PKG, sub), exist_ok=True)

    for n in NAMES:
        shutil.copy2(os.path.join(SRC, "svg", n + ".svg"),
                     os.path.join(PKG, "svg", n + ".svg"))
        shutil.copy2(os.path.join(SRC, "png", n + "_600dpi.png"),
                     os.path.join(PKG, "png_600dpi", n + "_600dpi.png"))
    prev = os.path.join(SRC, "preview", "FigureS1_allticks_preview_600dpi.png")
    shutil.copy2(prev, os.path.join(PKG, "preview",
                                    "FigureS1_allticks_preview_600dpi.png"))

    # ---- tick_values.csv ------------------------------------------------
    with open(os.path.join(PKG, "tick_values.csv"), "w", newline="",
              encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["file", "parameter", "x_axis_view_min", "x_axis_view_max",
                    "x_ticks", "y_axis_view_max", "y_ticks",
                    "x_numbers_this_round", "y_numbers_this_round"])
        for k, n in enumerate(NAMES[:-1]):
            s = d[k]
            w.writerow([n + ".svg", PARAM[k],
                        "%.4f" % s["xlim"][0], "%.4f" % s["xlim"][1],
                        " ".join(s["xlabels"]),
                        "%.2f" % s["ylim"][1],
                        " ".join(s["ylabels"]),
                        "kept (already in source)" if s["row"] == 2 else "restored",
                        "kept (already in source)" if s["col"] == 0 else "restored"])

    # ---- labels_and_notes.txt ------------------------------------------
    L = []
    A = L.append
    A("Figure S1 拆图交付（九个直方图各自补齐横、纵轴刻度数字版）  2026-11-16")
    A("=" * 64)
    A("")
    A("来源：E:\\project\\work1\\SI\\SI.pptx 第 1 页内的矢量图（image2.svg，")
    A("      viewBox 972.212 × 510.466 pt）。SI.pptx 未被修改。")
    A("")
    A("一、这一轮做了什么")
    A("-" * 64)
    A("原图是「共享坐标轴」排版：x 轴刻度数字只画在底行，y 轴刻度数字和刻度线")
    A("只画在左列。这一轮把缺的刻度全部按各图自己的坐标补回：")
    A("")
    A("  · 第 1、2 行六个直方图：补回各自的 x 轴刻度数字（共 24 个数字）。")
    A("    x 轴刻度短线九张图本来就有，原样保留。")
    A("  · 第 2、3 列六个直方图：补回各自的 y 轴刻度数字与刻度短线")
    A("    （共 28 个数字 + 28 条 3 pt 短线），样式与左列完全一致")
    A("    （短线向外 3 pt，数字距轴线 6.5 pt，Arial 12）。")
    A("  · 左列三张的 y 轴数字、底行三张的 x 轴数字：原图就有，未改动。")
    A("")
    A("二、刻度值是算出来的，不是看着截图填的")
    A("-" * 64)
    A("依据：原始绘图脚本 final_figures/scripts/plot_FigS1_eda.py")
    A("      + 原始数据 data/JV_database_9D_interface_lifetimes-2.csv")
    A("      （N = 102,046 条保留样本，seed 42 的 LHS 之后）")
    A("脚本路径原样复现（同样的 3×3 gridspec、每图 60 个 bin、nice_ticks 规则、")
    A("matplotlib 自动留白），把九条坐标轴的 view 范围和刻度值从活的坐标轴上读回来。")
    A("")
    A("交叉核对（这是能证明「算的就是这张图」的关键）：")
    A("  · 九张图 x 轴刻度短线在图上的位置 vs 算出来的位置，最大偏差 0.0009 pt；")
    A("  · 左列三张的 y 轴刻度线与数字，位置最大偏差 0.0010 pt，文字逐个相同；")
    A("  · 九张图全部 540 根柱子的柱顶高度 vs「计数 ÷ 纵轴上限」，最大偏差 0.0011 pt。")
    A("柱子高度这一条同时锁定了第 2、3 列那六张「原先看不见」的纵轴范围。")
    A("")
    A("三、九个直方图各自的刻度（本轮实际写进图里的值）")
    A("-" * 64)
    def w(s):
        return sum(2 if ord(c) > 0x2E80 else 1 for c in s)

    def pad(s, n):
        return s + " " * max(1, n - w(s))

    def num(v, fmt):
        return fmt % v

    A(pad("参数", 10) + pad("x 轴显示范围 (log10)", 26) +
      pad("x 轴刻度", 28) + pad("y 轴显示范围", 16) + "y 轴刻度")
    for k, n in enumerate(NAMES[:-1]):
        s = d[k]
        xr = ("%.4f … %.4f" % tuple(s["xlim"])).replace("-", "−")
        A(pad(PARAM[k], 10) + pad(xr, 26) +
          pad("  ".join(s["xlabels"]), 28) +
          pad("0 … %.2f" % s["ylim"][1], 16) +
          "  ".join(s["ylabels"]))
    A("")
    A("说明：x 轴显示范围 = 数据范围两端各留 5%（matplotlib 默认），刻度只取落在")
    A("范围内的整数间距值，因此和底行三张的刻度并不通用 —— 每张都不同。")
    A("")
    A("四、纵轴为什么不能共用（按您的要求逐图核对过）")
    A("-" * 64)
    A("九张图的纵轴范围（0 … 上限）分别是：")
    A("  mu_n 2500.00 :  tau_n 2444.40 :  tau_p 2500.00")
    A("  mu_p 2345.70 :  tau_ETL 2106.30 :  tau_HTL 2163.00 :  r_rad 2151.45")
    A("  N_c 3264.45 :  N_v 3289.65")
    A("没有任何两张图的「范围 + 刻度」同时相同（刻度组合相同的几组，范围也各不相同），")
    A("所以九张全部保留各自的纵轴刻度数字，没有共用、也没有为了统一外观去改任何轴范围。")
    A("")
    A("两点如实说明（都是原图本来的样子，不是这一轮改的）：")
    A("  1. 左列三张的纵轴上限正好等于最高的一条刻度（mu_n/tau_p 的 2500），这是")
    A("     matplotlib 被显式指定刻度后把 view 拉到刻度上的结果；第 2、3 列那六张")
    A("     用的是默认 5% 留白（上限 = 峰值 × 1.05）。两套上限都原样保留。")
    A("  2. tau_n 的最高刻度候选值是 2500，但它的纵轴上限是 2444.40，2500 落在框外，")
    A("     所以该图纵轴刻度到 2000 为止 —— 没有把轴拉到 2500 去迁就刻度。")
    A("")
    A("五、仍然不含的文字（请在 PPT 里自己加）")
    A("-" * 64)
    A("· 九个参数名（μn、μp、τn、τp、Nc、Nv、τETL、τHTL、r_rad）")
    A("· y 轴标题 Count（左列）")
    A("· x 轴标题 log10(...)（底行）")
    A("· 图标题/子图编号 (a)、(b)、\"Retained parameter distributions\"、")
    A("  \"N = 102,046\"、\"Pairwise log-space Spearman correlation\"")
    A("图中现在只有数字（−6、1,000、23 这类），没有任何文字标签。")
    A("")
    A("六、尺寸与对齐（与上一轮完全相同，可以直接沿用上一轮的摆放）")
    A("-" * 64)
    A("九个直方图画布一律 171.840 × 139.200 pt（600 dpi = 1432 × 1160 px），")
    A("绘图区 125.569 × 115.162 pt，距画布左边 39.36 pt、上边 8.88 pt，九张完全一致。")
    A("热图/色条一片仍是 426.000 × 382.560 pt（3550 × 3188 px），与上一轮逐字节相同。")
    A("")
    A("七、验证")
    A("-" * 64)
    A("A 无残留文字、只剩数字；B 九张画布与绘图区偏移一致；C 保留元素与原矢量逐元素")
    A("相同（0 改动、0 丢失）；D 每张的刻度线/刻度数字个数、数值、位置与脚本+数据")
    A("一致；E 与上一轮矢量版 600 dpi 逐像素比较，差异全部落在新增文字的墨迹内；")
    A("F 全部墨迹在画布内（最小留边 2.88 pt）；G 540 根柱子柱顶与计数一致。")
    A("详见 verification_report.txt。PowerPoint 实机十张插入尺寸零误差、无红叉。")

    open(os.path.join(PKG, "labels_and_notes.txt"), "w",
         encoding="utf-8").write("\n".join(L) + "\n")

    shutil.copy2(LOG, os.path.join(PKG, "verification_report.txt"))

    # ---- zip -----------------------------------------------------------
    if os.path.exists(ZIP):
        os.remove(ZIP)
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(PKG):
            dirs.sort()
            for fn in sorted(files):
                p = os.path.join(root, fn)
                z.write(p, os.path.relpath(p, os.path.dirname(PKG)))

    print("package:", PKG)
    print("zip    :", ZIP, os.path.getsize(ZIP), "bytes")
    with zipfile.ZipFile(ZIP) as z:
        for i in z.infolist():
            print("   %-60s %9d" % (i.filename, i.file_size))


if __name__ == "__main__":
    main()
