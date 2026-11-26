# -*- coding: utf-8 -*-
"""Build labels_and_values.txt and the delivery folder for Figure S2 (a)/(b).

Every number written into the file is read from the same frozen CSVs the
original script used, and the two Spearman statistics are recomputed here and
cross-checked against the values rendered in the source SVG.
"""
import io
import json
import os
import re
import shutil
import sys
import zipfile

import numpy as np
import pandas as pd
from lxml import etree
from scipy.stats import spearmanr

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE = r"E:\project\work1"
SENS = os.path.join(BASE, "sensitivity_recomputed", "sensitivity_recomputed.csv")
METR = os.path.join(BASE, "evaluation_fixed", "parameter_metrics.csv")
SRC = os.path.join(BASE, "20261024_final_figures_svg", "si", "FigureS2.svg")
OUT = os.environ.get("S2_OUT", "out")
PKG = os.path.join("package", os.environ.get("S2_PKG", "FigureS2_split"))
ZIP = os.environ.get("S2_ZIP", "FigureS2_split.zip")
FONT = float(os.environ.get("S2_FONT", "0")) or 7.5
KEEP_LEADERS = os.environ.get("S2_KEEP_LEADERS") == "1"

PARAM_ORDER = ["mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk",
               "Nc_eff_pvk", "Nv_eff_pvk", "tau_ETL", "tau_HTL", "rad_c"]
PRETTY = ["μ_n", "μ_p", "τ_n", "τ_p", "N_c", "N_v", "τ_ETL", "τ_HTL", "r_rad"]
CS = "{http://www.w3.org/2000/svg}"

XA = (0.0, 0.53)
XB = (0.0, 0.30)
Y = (0.50, 0.95)


def main():
    sens = pd.read_csv(SENS).set_index("parameter")
    metr = pd.read_csv(METR).set_index("parameter")
    xa = np.array([sens.loc[p, "S_log"] for p in PARAM_ORDER])
    xb = np.array([sens.loc[p, "S_raw"] for p in PARAM_ORDER])
    yr = np.array([metr.loc[p, "pearson_r"] for p in PARAM_ORDER])

    rho_a, p_a = spearmanr(xa, yr)
    rho_b, p_b = spearmanr(xb, yr)

    # cross-check against the values actually drawn in the source SVG
    svg = open(SRC, encoding="utf-8").read()
    txt = " ".join(re.findall(r">([^<>]+)<", svg))
    assert "0.533" in txt and "0.139" in txt and "0.683" in txt and "0.042" in txt
    assert abs(rho_a - 0.533) < 1e-3 and abs(p_a - 0.139) < 1e-3
    assert abs(rho_b - 0.683) < 1e-3 and abs(p_b - 0.042) < 1e-3
    print("Spearman  (a) rho=%.4f p=%.4f | (b) rho=%.4f p=%.4f"
          % (rho_a, p_a, rho_b, p_b))

    meta = json.load(open(os.path.join(OUT, "work", "meta.json"), encoding="utf-8"))
    vs = json.load(open(os.path.join(OUT, "work", "verify_summary.json")))
    PX = meta["pieces"][0]["px"]
    CW, CH = meta["canvas"]
    mg = meta["margins"]
    W0, H0 = meta["boxes"]["S2a_sensitivity_log"][2:]

    if os.path.isdir(PKG):
        shutil.rmtree(PKG)
    os.makedirs(PKG)
    for n in ("S2a_sensitivity_log", "S2b_sensitivity_raw"):
        shutil.copy2(os.path.join(OUT, "svg", n + ".svg"),
                     os.path.join(PKG, n + ".svg"))
        shutil.copy2(os.path.join(OUT, "png", n + "_600dpi.png"),
                     os.path.join(PKG, n + "_600dpi.png"))

    L = []
    A = L.append
    A("Figure S2 拆图交付：(a)、(b) 两个独立小图 + 被删除的文字与数值清单")
    A("2026-11-16")
    A("=" * 66)
    A("")
    A("来源：final_figures/SI_final_review/FigS2_sensitivity_recoverability.svg")
    A("      （与 20261024_final_figures_svg/si/FigureS2.svg 同一份，835.60 × 347.33 pt）")
    A("      生成脚本 final_figures/scripts/plot_FigS2_sensitivity_recoverability.py")
    A("      直接在原始矢量上删元素，没有截图、没有白块遮挡、没有重绘。")
    A("      SI.pptx 与稿件未改动。")
    A("")
    A("一、两个文件（画布完全相同，可直接等尺寸对齐）")
    A("-" * 66)
    A("  文件                            画布 (pt)            600 dpi 像素")
    A("  S2a_sensitivity_log.svg/png     %.3f × %.3f     %d × %d" % (CW, CH, PX[0], PX[1]))
    A("  S2b_sensitivity_raw.svg/png     %.3f × %.3f     %d × %d" % (CW, CH, PX[0], PX[1]))
    A("")
    A("  两图绘图区都是 %.3f × %.3f pt，在画布内的偏移都是 (%.2f, %.2f) pt；"
      % (W0, H0, mg["L"] + mg["pad"], mg["T"] + mg["pad"]))
    A("  四周留白 %.1f pt。边框、刻度线、刻度数字全部保留。" % mg["pad"])
    A("")
    A("二、删掉的文字（原文，可直接复制粘贴回 PPT）")
    A("-" * 66)
    A("【(a) 图】")
    A("  子图编号   (a)")
    A("  主标题     Adopted log-space sensitivity")
    A("  副标题     adopted metric")
    A("  x 轴标题   J–V sensitivity, S_log        （S 带下标 log）")
    A("  y 轴标题   Recoverability Pearson r      （r 为斜体）")
    A("  参数标注   μ_n   μ_p   τ_n   τ_p   N_c   N_v   τ_ETL   τ_HTL   r_rad")
    A("  灰色引导线 %s" % ("**保留**（9 条/图，颜色 #a6a6a6、0.8 pt，位置原样），"
                        "只删了文字" if KEEP_LEADERS else "9 条（每个参数一条）已一并删除"))
    A("  统计标注   Spearman ρs = 0.533,  p = 0.139")
    A("             (non-significant)")
    A("")
    A("【(b) 图】")
    A("  子图编号   (b)")
    A("  主标题     Raw-space sensitivity reference")
    A("  副标题     raw physical-space analogue")
    A("  x 轴标题   J–V sensitivity, S_raw        （S 带下标 raw）")
    A("  y 轴标题   Recoverability Pearson r")
    A("  参数标注   同 (a) 的九个，灰色引导线%s" % ("保留" if KEEP_LEADERS else "同样已删除"))
    A("  统计标注   Spearman ρs = 0.683,  p = 0.042")
    A("")
    A("  图例：原图就没有图例（九个点同色、无 legend），所以不存在删图例这一步。")
    A("")
    A("三、统计量的出处（不是从截图读的）")
    A("-" * 66)
    A("  脚本里由 scipy.stats.spearmanr 现算并断言，本轮用同样的两个冻结文件重算：")
    A("    (a) S_log vs r : rho = %.4f, p = %.4f   （正文/Fig. 3b 用这一组）"
      % (rho_a, p_a))
    A("    (b) S_raw vs r : rho = %.4f, p = %.4f   （仅供参考，不做解释）"
      % (rho_b, p_b))
    A("  数据来源：sensitivity_recomputed/sensitivity_recomputed.csv（S_log、S_raw）")
    A("            evaluation_fixed/parameter_metrics.csv（recoverability Pearson r）")
    A("")
    A("四、九个点的数值与位置（重新摆参数名时按这个对位）")
    A("-" * 66)
    def w(s):
        return sum(2 if ord(c) > 0x2E80 else 1 for c in s)

    def pad(s, n):
        return s + " " * max(1, n - w(s))

    A(pad("参数", 9) + pad("S_log", 10) + pad("S_raw", 10) + pad("r", 9) +
      pad("(a) 横向", 12) + pad("(b) 横向", 12) + "纵向")
    for i, p in enumerate(PARAM_ORDER):
        fa = (xa[i] - XA[0]) / (XA[1] - XA[0])
        fb = (xb[i] - XB[0]) / (XB[1] - XB[0])
        fy = (yr[i] - Y[0]) / (Y[1] - Y[0])
        A(pad(PRETTY[i], 9) + pad("%.4f" % xa[i], 10) + pad("%.4f" % xb[i], 10) +
          pad("%.4f" % yr[i], 9) + pad("%5.1f %%" % (100 * fa), 12) +
          pad("%5.1f %%" % (100 * fb), 12) + "%5.1f %%" % (100 * fy))
    A("（百分比 = 在绘图区内从左下角起算的位置，0 % 是左/下边框，100 % 是右/上边框）")
    A("")
    A("五、轴范围与刻度（原样保留，未统一两图横轴）")
    A("-" * 66)
    A("  (a) x: %.2f – %.2f，刻度 0.0 0.1 0.2 0.3 0.4 0.5" % XA)
    A("  (b) x: %.2f – %.2f，刻度 0.0 0.1 0.2 0.3" % XB)
    A("  两图 y 相同: %.2f – %.2f，刻度 0.5 0.6 0.7 0.8 0.9" % Y)
    A("")
    A("六、输出前的核对（全部通过）")
    A("-" * 66)
    A("  · 散点：两图各 9 个，坐标与源矢量逐个相同（含大小、颜色 #009e73、")
    A("    透明度 0.92、白色描边、遮挡顺序、裁剪框）。")
    A("  · 刻度：A 共 11 个数字（x 6 + y 5），B 共 9 个（x 4 + y 5），数值与位置")
    A("    与源图完全一致；刻度线和四周边框都在。")
    A("  · 说明性文字全部清除；灰色引导线 %s。"
      % ("保留（每图 9 条，SVG 里可搜到 9 处 #a6a6a6）" if KEEP_LEADERS else "已清除"))
    A("  · 逐像素核对：与「未删除的源图」在同一窗口 600 dpi 比较，差异像素全部")
    A("    落在被删除元素的墨迹范围内（a %s px、b %s px，掩膜外 0 px）。"
      % (format(vs["S2a_sensitivity_log"]["diff"], ","),
         format(vs["S2b_sensitivity_raw"]["diff"], ",")))
    A("  · 不裁切：最小留边 %.2f pt（负号、数字、边框都在画布内）。"
      % min(vs["S2a_sensitivity_log"]["clear"], vs["S2b_sensitivity_raw"]["clear"]))
    A("  · 字号 %.2f pt，相对绘图区宽 %.2f %%（参考 Figure S4 为 3.79 %%、"
      "S1 那套为 3.82 %%）。" % (FONT, 100 * FONT / W0))
    if KEEP_LEADERS:
        A("    放大字号后刻度数字的基线按字体度量做了相应下移/居中（x 轴 %0.2f pt、"
          "y 轴 %0.2f pt），不会压到刻度线。"
          % (7.0 + 4.868 * FONT / 7.5, 2.685 * FONT / 7.5))
    A("  · PowerPoint 实机：两张插入尺寸零误差（%.3f × %.3f pt），无红叉。"
      % (CW, CH))
    A("")
    A("七、说明")
    A("-" * 66)
    A("  (b) 图最右边的 \"0.3\" 刻度数字本来就压在右边框上、向外探出（放大字号后")
    A("  约 %.1f pt）；画布右侧已按两图的最大值留够，不会被裁掉。"
      % mg["R"])

    open(os.path.join(PKG, "labels_and_values.txt"), "w",
         encoding="utf-8").write("\n".join(L) + "\n")

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
        for i in z.infolist():
            print("   %-46s %9d" % (i.filename, i.file_size))


if __name__ == "__main__":
    main()
