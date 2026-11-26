"""Write out/labels_and_values.txt: every string that was deleted from Figure S1.

All values are transcribed from the <text> nodes of the SVG that PowerPoint
itself embeds in slide 1 (ppt/media/image2.svg).  Nothing is recomputed,
re-rounded or invented.
"""
import io
import json
import re
import sys
from lxml import etree

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

CS = "{http://www.w3.org/2000/svg}"
SRC = "work/slide1_image2.svg"
OUT = "out/labels_and_values.txt"

root = etree.parse(SRC).getroot()
parent = {c: p for p in root.iter() for c in p}


def owner(e):
    while e in parent:
        e = parent[e]
        i = e.get("id") or ""
        if re.match(r"axes_\d+$", i):
            return i
    return "figure"


def text_of(gid):
    g = [e for e in root.iter(CS + "g") if e.get("id") == gid][0]
    return "".join(g.itertext())


# --- heatmap matrix -----------------------------------------------------
cells = []
for k in range(65, 146):
    g = [e for e in root.iter(CS + "g") if e.get("id") == "text_%d" % k][0]
    t = g.find(CS + "text")
    cells.append((float(t.get("y")), float(t.get("x")), t.text, t.get("fill", "")))
cells.sort(key=lambda c: (round(c[0], 2), round(c[1], 2)))
assert len(cells) == 81, len(cells)
mat = [cells[i * 9:(i + 1) * 9] for i in range(9)]
white = [(r + 1, c + 1) for r in range(9) for c in range(9)
         if mat[r][c][3] == "#FFFFFF"]

PARAM = ["μn", "μp", "τn", "τp", "Nc", "Nv", "τ_ETL", "τ_HTL", "r_rad"]
FILES = ["S1a_01_mu_n", "S1a_02_mu_p", "S1a_03_tau_n", "S1a_04_tau_p",
         "S1a_05_Nc", "S1a_06_Nv", "S1a_07_tau_ETL", "S1a_08_tau_HTL",
         "S1a_09_r_rad"]

YTICK = {
    "axes_1": ["0", "500", "1,000", "1,500", "2,000", "2,500"],
    "axes_4": ["0", "500", "1,000", "1,500", "2,000", "2,500"],
    "axes_7": ["0", "500", "1,000", "1,500", "2,000"],
}
XTICK = {
    "axes_7": ["−12", "−11", "−10", "−9", "−8"],
    "axes_8": ["−14", "−13", "−12", "−11", "−10"],
    "axes_9": ["−12", "−11", "−10", "−9"],
}
XTITLE = {"axes_7": "log₁₀(τ_ETL)", "axes_8": "log₁₀(τ_HTL)",
          "axes_9": "log₁₀(r_rad)"}

L = []
w = L.append

w("=" * 78)
w("Figure S1 拆分交付 —— 被删掉的文字与原图数值（可直接复制回 PowerPoint）")
w("=" * 78)
w("")
w("来源：E:\\project\\work1\\SI\\SI.pptx 第 1 页嵌入的原始矢量图（ppt/media/image2.svg）")
w("日期：2026-11-16")
w("")
w("本文件里的每一个字符都逐字抄自原图 SVG 的 <text> 节点：没有重算、没有重新取整、")
w("没有补上原图没显示的刻度。负号是原图用的 U+2212（数学减号 −），不是连字符 -。")
w("")
w("-" * 78)
w("0  原图结构")
w("-" * 78)
w("")
w("  (a) 左栏：3×3 共 9 个参数分布直方图")
w("      总标题  Retained parameter distributions")
w("      样本量  N = 102,046            （灰色 #555555）")
w("  (b) 右栏：9×9 Spearman 相关热图 + 1 条竖直色条")
w("      总标题  Pairwise log-space Spearman correlation")
w("")
w("  拆出的 11 个无文字文件（顺序＝原图从左到右、从上到下）：")
for i, f in enumerate(FILES):
    w("    %-15s  (a) 第 %d 行第 %d 列   %s" % (f, i // 3 + 1, i % 3 + 1, PARAM[i]))
w("    %-15s  (b) 热图本体" % "S1b_heatmap")
w("    %-15s  (b) 色条（单独一条，方便你调间距）" % "S1b_colorbar")
w("")
w("-" * 78)
w("1  需要放回去的文字")
w("-" * 78)
w("")
w("1.1 总标题")
w("")
w("    (a)  Retained parameter distributions")
w("    N = 102,046")
w("    (b)  Pairwise log-space Spearman correlation")
w("")
w("1.2 每个直方图上方的参数名（原图 9 个都在绘图区上方居中）")
w("")
w("    文件            原图 SVG 字符      建议在 PowerPoint 里写成")
w("    -------------   ----------------   ------------------------")
for f, p in zip(FILES, PARAM):
    w("    %-15s   %-16s   %s" % (f, p, p.replace("_", " ")))
w("")
w("    说明：原图里 μ、τ 后面跟的是斜体下标（n、p、c、v），N 的下标是 c/v，")
w("          后三个是 τ 下标 ETL / HTL 和 r 下标 rad。用 PowerPoint 的")
w("          「下标」按钮或公式编辑器输入即可。")
w("")
w("1.3 y 轴（只有最左一列有）")
w("")
w("    y 轴标题：Count（旋转 90°，只有 S1a_01_mu_n / S1a_04_tau_p / S1a_07_tau_ETL）")
w("")
w("    y 刻度数字（原图只在最左一列显示）：")
w("      S1a_01_mu_n    : " + " / ".join(YTICK["axes_1"]))
w("      S1a_04_tau_p   : " + " / ".join(YTICK["axes_4"]))
w("      S1a_07_tau_ETL : " + " / ".join(YTICK["axes_7"]) + "     ← 原图没有 2,500")
w("")
w("    中间一列和最右一列原图既没有 y 刻度数字，也没有 y 刻度线（不是被裁掉）。")
w("")
w("1.4 x 轴（只有最下一行有数字和标题）")
w("")
for k, f in (("axes_7", FILES[6]), ("axes_8", FILES[7]), ("axes_9", FILES[8])):
    w("      %-15s x 刻度 %s" % (f, " / ".join(XTICK[k])))
    w("      %-15s x 轴标题 %s" % ("", XTITLE[k]))
w("")
w("    上两行原图只画了刻度线，没有刻度数字，也没有 x 轴标题。")
w("")
w("1.5 热图 (b) 与色条")
w("")
w("    x 轴刻度标签（左→右，原图旋转 45°）：")
w("      " + "   ".join(PARAM))
w("    y 轴刻度标签（上→下）：")
w("      " + "   ".join(PARAM))
w("    色条刻度（下→上）：−1.0 / −0.5 / 0.0 / 0.5 / 1.0")
w("    色条标题：Spearman ρ（旋转 90°）")
w("")
w("    热图与色条的刻度线在原图里就没有（line2d 是空的），所以拆出来的图里也没有。")
w("")
w("-" * 78)
w("2  热图 9×9 相关系数矩阵（原样：两位小数，含 -0.00）")
w("-" * 78)
w("")
w("    顺序＝原图从左到右、从上到下。\"-0.00\" 是原图的写法，没有改成 0.00。")
w("")
hdr = "          " + "".join("%8s" % p for p in PARAM)
w(hdr)
for r in range(9):
    w("    %-6s" % PARAM[r] + "".join("%8s" % mat[r][c][2] for c in range(9)))
w("")
w("    原图字色：深色块上用白字（#FFFFFF），其余用 #1A1A1A。白字单元格（行,列）：")
w("      " + "  ".join("(%d,%d)" % (r, c) for r, c in white))
w("")
w("    纯文本版（方便直接粘贴到 Excel，制表符分隔）：")
w("")
w("\t".join([""] + PARAM))
for r in range(9):
    w("\t".join([PARAM[r]] + [mat[r][c][2] for c in range(9)]))
w("")
w("-" * 78)
w("3  几何尺寸（在 PowerPoint 里按这个大小放，拼出来和原图一致）")
w("-" * 78)
w("")
w("    9 个直方图   画布 137.569 × 127.162 pt = 48.53 × 44.86 mm = 1.911 × 1.766 in")
w("                 绘图区（外框内沿）125.569 × 115.162 pt，四周留 6 pt")
w("                 九个文件的画布与绘图区位置完全相同，直接对齐即可拼 3×3")
w("    热图         画布 379.758 × 379.758 pt = 133.96 × 133.96 mm（正方形）")
w("                 绘图区 367.758 × 367.758 pt，四周留 6 pt")
w("    色条         画布 33.600 × 379.758 pt = 11.85 × 133.96 mm")
w("                 色条框 21.6 × 367.758 pt，四周留 6 pt（与热图同高，底边对齐）")
w("")
w("    原图里各面板的位置（图内坐标，pt）：")
w("      x 起点 44.2399 / 209.992 / 375.743    列间距 165.752")
w("      y 起点 35.4384 / 198.969 / 362.5      行间距 163.531")
w("      热图 x 539.402，色条 x 907.16（两者之间没有间隙）")
w("")
w("    原图字号没有保存在 SVG 里（PowerPoint 存回 SVG 时把 font-size 丢了），")
w("    但按 PowerPoint 自己渲染的原图 PNG 量，刻度数字/热图数值的字高约 7.8–8.2 pt")
w("    （约合 11 pt 字号），字体是 matplotlib 默认的 DejaVu Sans。")
w("")

with open(OUT, "w", encoding="utf-8", newline="\r\n") as f:
    f.write("\n".join(L))
print("wrote", OUT, len("\n".join(L)), "chars")
print("white cells:", white)
