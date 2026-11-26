# -*- coding: utf-8 -*-
"""Assemble the delivery folder + zip for the small-typography S1 set."""
import csv
import io
import json
import os
import shutil
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

SRC = "out_ticks_small"
PKG = os.path.join("package", "FigureS1_small_ticks")
DERIVED = "work/ticks_derived.json"
LOG = "work/verify_small.log"
ZIP = "FigureS1_small_ticks.zip"

NAMES = ["S1a_01_mu_n", "S1a_02_mu_p", "S1a_03_tau_n", "S1a_04_tau_p",
         "S1a_05_N_c", "S1a_06_N_v", "S1a_07_tau_ETL", "S1a_08_tau_HTL",
         "S1a_09_r_rad"]
PARAM = ["mu_n", "mu_p", "tau_n", "tau_p", "N_c", "N_v", "tau_ETL",
         "tau_HTL", "r_rad"]


def main():
    d = json.load(open(DERIVED, encoding="utf-8"))
    m = json.load(open(os.path.join(SRC, "work", "meta.json"), encoding="utf-8"))
    CW, CH = m["canvas"]
    mg = m["margins"]
    fs = m["font"]

    if os.path.isdir(PKG):
        shutil.rmtree(PKG)
    for sub in ("svg", "png_600dpi", "preview"):
        os.makedirs(os.path.join(PKG, sub), exist_ok=True)
    for n in NAMES:
        shutil.copy2(os.path.join(SRC, "svg", n + ".svg"),
                     os.path.join(PKG, "svg", n + ".svg"))
        shutil.copy2(os.path.join(SRC, "png", n + "_600dpi.png"),
                     os.path.join(PKG, "png_600dpi", n + "_600dpi.png"))
    shutil.copy2(os.path.join(SRC, "preview", "FigureS1_3x3_600dpi.png"),
                 os.path.join(PKG, "preview", "FigureS1_3x3_600dpi.png"))
    shutil.copy2("work/_cmp_ref_small.png",
                 os.path.join(PKG, "reference_comparison_with_FigureS4.png"))

    with open(os.path.join(PKG, "tick_values.csv"), "w", newline="",
              encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["file", "parameter", "x_axis_view_min", "x_axis_view_max",
                    "x_ticks", "y_axis_view_max", "y_ticks",
                    "plot_area_pt", "canvas_pt"])
        for k, n in enumerate(NAMES):
            s = d[k]
            w.writerow([n + ".svg", PARAM[k],
                        "%.4f" % s["xlim"][0], "%.4f" % s["xlim"][1],
                        " ".join(s["xlabels"]), "%.2f" % s["ylim"][1],
                        " ".join(s["ylabels"]),
                        "%.3f x %.3f" % (125.569, 115.162),
                        "%.3f x %.3f" % (CW, CH)])

    L = []
    A = L.append
    A("Figure S1 左侧九个直方图（刻度数字缩小版）  2026-11-16")
    A("=" * 64)
    A("")
    A("一、字号：为什么是 4.8 而不是 6.0")
    A("-" * 64)
    A("以「单个绘图区宽度相同」为基准，量了参考图 SI Figure S4（Predictive-scale")
    A("distributions 九宫格，文件 20261024_final_figures_svg/si/FigureS4.svg）：")
    A("")
    A("  参考图：刻度数字 8.0 pt，绘图区宽 211.00 pt  → 3.79 %（字体/绘图区宽）")
    A("  上一轮：刻度数字 12.0 pt，绘图区宽 125.569 pt → 9.56 %")
    A("  50 %  ：6.0 pt，同一绘图区          → 4.78 %（仍比参考宽 26 %）")
    A("  本轮  ：4.8 pt = 8.0 × 125.569/211.00 → 3.82 %  ← 采用")
    A("")
    A("实测字高（600 dpi 像素计，同样的取墨阈值）：")
    A("  参考图 6.24 pt 字高 / 211.00 pt 绘图区宽 = 2.96 %")
    A("  本轮   3.60 pt 字高 / 125.569 pt 绘图区宽 = 2.87 %   比值 0.97")
    A("即与参考图一致（差 3 %，在抗锯齿取阈的误差内）。字体 Arial、常规字重。")
    A("")
    A("二、随之收紧的间距与画布")
    A("-" * 64)
    A("  数字与轴的间距：y 方向由 6.50 pt 收到 5.08 pt（刻度 3 pt + 留白 2.08）；")
    A("                  x 方向基线由轴上 11.87 pt 收到 8.52 pt。")
    A("  留白 2.08 pt 是按参考图的 3.5 pt 留白 × 125.569/211.00 换算来的。")
    A("  画布：171.840 × 139.200 → %.3f × %.3f pt（四周留白 %.2f pt）。"
      % (CW, CH, mg["pad"]))
    A("  九个图仍共用同一个画布尺寸和同一个绘图区偏移 (%.2f, %.2f) pt。"
      % (mg["L"] + mg["pad"], mg["T"] + mg["pad"]))
    A("")
    A("三、没变的东西（已逐项验证）")
    A("-" * 64)
    A("  · 绘图区 125.569 × 115.162 pt、长宽比例、位置不变；")
    A("  · 柱子：60 个分箱、计数、颜色 #6C92C3 / 边 #3D5E8D、线宽全部不变；")
    A("    「去掉文字后 600 dpi 逐像素比对，与上一轮差异 0 像素」；")
    A("  · 轴范围、刻度位置、刻度数值不变（与脚本+数据一致：x 最大偏差 0.0009 pt，")
    A("    540 根柱顶与 count/ylim 最大偏差 0.0011 pt）；")
    A("  · 刻度线保留（3 pt，向外），九个图横纵轴刻度线和刻度数字都在；")
    A("  · 仍然没有 Count、参数名、轴标题、图标题、子图编号。")
    A("")
    A("四、每个直方图的刻度（数值与上一轮完全相同）")
    A("-" * 64)
    A("参数      x 轴显示范围 (log10)      x 轴刻度                    y 轴显示范围    y 轴刻度")
    for k, n in enumerate(NAMES):
        s = d[k]
        xr = ("%.4f … %.4f" % tuple(s["xlim"])).replace("-", "−")
        A("%-9s %-26s %-28s %-15s %s"
          % (PARAM[k], xr, "  ".join(s["xlabels"]),
             "0 … %.2f" % s["ylim"][1], "  ".join(s["ylabels"])))
    A("")
    A("五、放进 PPT 时请注意")
    A("-" * 64)
    A("画布变小了（171.84×139.20 → %.3f×%.3f pt），但绘图区尺寸没变。"
      % (CW, CH))
    A("按「原始大小」插入（即 %.3f × %.3f pt）时，绘图区仍是原来的物理尺寸，"
      % (CW, CH))
    A("九张图的箱体位置和相互间距可以直接沿用上一轮的摆放，只要九张用同一个尺寸。")
    A("")
    A("六、文件")
    A("-" * 64)
    A("  svg/                9 个 SVG（可直接在 PowerPoint 里「插入图片」，矢量）")
    A("  png_600dpi/         9 个 600 dpi PNG（1236 × 1090 px）")
    A("  preview/FigureS1_3x3_600dpi.png   3×3 预览，九个绘图区尺寸完全相同")
    A("  reference_comparison_with_FigureS4.png  左：本轮；右：Figure S4 按同一")
    A("                      绘图区宽度缩放，用于核对字号比例")
    A("  tick_values.csv     每张图的轴范围、刻度、画布尺寸")
    A("  verification_report.txt   A–H 八项验证")
    A("")
    A("七、验证结论")
    A("-" * 64)
    A("A 字体 Arial 4.8 / 常规字重 / 只有数字；B 九张画布与偏移一致；C 所有非文字")
    A("元素与原始矢量逐元素相同；D 刻度线/数字的个数、数值、位置与脚本+数据一致；")
    A("E 去文字后与上一轮逐像素 0 差异；F 全部墨迹在画布内（最小留边 2.52 pt）；")
    A("G 540 根柱顶不变；H 字号比例与参考图一致。PowerPoint 实机九张插入尺寸零误差、")
    A("无红叉，导出图与 SVG 渲染逐像素同位置。")

    open(os.path.join(PKG, "labels_and_notes.txt"), "w",
         encoding="utf-8").write("\n".join(L) + "\n")
    shutil.copy2(LOG, os.path.join(PKG, "verification_report.txt"))

    if os.path.exists(ZIP):
        os.remove(ZIP)
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(PKG):
            dirs.sort()
            for fn in sorted(files):
                p = os.path.join(root, fn)
                z.write(p, os.path.relpath(p, os.path.dirname(PKG)))
    print("package:", PKG)
    with zipfile.ZipFile(ZIP) as z:
        print("zip    :", ZIP, os.path.getsize(ZIP), "bytes,", len(z.namelist()), "files")
        for i in z.infolist():
            print("   %-58s %9d" % (i.filename, i.file_size))


if __name__ == "__main__":
    main()
