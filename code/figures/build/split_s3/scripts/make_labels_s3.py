# -*- coding: utf-8 -*-
"""Assemble the Figure S3 delivery folder, the labels file and the zip."""
import io
import json
import os
import re
import shutil
import sys
import zipfile

from lxml import etree

if (getattr(sys.stdout, "encoding", "") or "").lower().replace("-", "") != "utf8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

CS = "{http://www.w3.org/2000/svg}"
OUT = "out"
BASE = r"E:\project\work1\20261024_final_figures_svg\si"
PKG = os.path.join("package", "FigureS3_split")
ZIP = "FigureS3_split.zip"


def ticks_of(tag, stem):
    """Per-axes-group tick labels, in document order."""
    r = etree.parse(os.path.join(BASE, stem + ".svg")).getroot()
    out = []
    for a in [g for g in r.iter(CS + "g") if (g.get("id") or "").startswith("axes_")]:
        xs, ys = [], []
        for g in a.iter(CS + "g"):
            gid = g.get("id") or ""
            if not gid.startswith(("xtick_", "ytick_")):
                continue
            t = next(g.iter(CS + "text"), None)
            if t is None:
                continue
            v = re.sub(r"\s+", " ", "".join(t.itertext())
                       .replace(" ", " ")).strip()
            (xs if gid.startswith("xtick_") else ys).append(v)
        if xs or ys:
            out.append((a.get("id"), xs, ys))
    return out


def main():
    meta = json.load(open(os.path.join(OUT, "work", "meta.json"), encoding="utf-8"))
    by = {m["name"]: m for m in meta["pieces"]}

    if os.path.isdir(PKG):
        shutil.rmtree(PKG)
    os.makedirs(PKG)
    for n in ("S3a", "S3b", "S3c"):
        shutil.copy2(by[n]["svg"], os.path.join(PKG, n + ".svg"))
        shutil.copy2(by[n]["png"], os.path.join(PKG, n + "_600dpi.png"))
    os.makedirs(os.path.join(PKG, "preview"), exist_ok=True)
    shutil.copy2(meta["preview"],
                 os.path.join(PKG, "preview", os.path.basename(meta["preview"])))

    L = []
    A = L.append
    A("Figure S3 拆图交付：S3a / S3b / S3c + 被删除文字、图例配色与统计值清单")
    A("2026-11-16")
    A("=" * 68)
    A("")
    A("来源与定位（按内容确认，不是按页码）")
    A("-" * 68)
    A("SI.pptx 里 Figure S3 不是一个页面，而是连续三页，各装一个部分：")
    A("  slide 3 → (a1)–(a6) 代表案例的 J–V 曲线（cycle-gap 分位：lowest / Q25 /")
    A("            median / Q75 / highest，外加 true-param control）")
    A("  slide 4 → RMS(AE) 随电压的曲线（三个对比）")
    A("  slide 5 → (c1)–(c4) 45 样本的循环差分布")
    A("这三页内嵌的矢量图与 20261024_final_figures_svg/si/FigureS3a/b/c.svg 的")
    A("viewBox 完全一致（到 1e-5 pt），单元几何也逐个吻合，所以本次直接用原始")
    A("matplotlib SVG 作源（矢量、文字可编辑）。没有截图、没有白块遮挡、没有重绘；")
    A("SI.pptx 与稿件均未改动。")
    A("")
    A("一、三个文件")
    A("-" * 68)
    for n in ("S3a", "S3b", "S3c"):
        m = by[n]
        A("  %-4s  %8.3f × %8.3f pt   600 dpi = %d × %d px"
          % (n, m["win"][2], m["win"][3], m["px"][0], m["px"][1]))
    A("  preview/FigureS3_split_preview_600dpi.png   按原顺序（a → b → c）纵向排列")
    A("")
    A("二、删掉的文字（原文，可直接复制回 PPT）")
    A("-" * 68)
    A("【S3a】")
    A("  面板编号   (a1)  (a2)  (a3)  (a4)  (a5)  (a6)")
    A("  面板标题   cycle-gap lowest # 12058")
    A("             cycle-gap Q25 # 4077")
    A("             cycle-gap median # 595")
    A("             cycle-gap Q75 # 695")
    A("             cycle-gap highest # 14499")
    A("             true-param control # 595")
    A("  副标题     cg = 0.27 mA cm⁻²   （a1）")
    A("             cg = 1.68 mA cm⁻²   （a2）")
    A("             cg = 2.56 mA cm⁻²   （a3）")
    A("             cg = 5.64 mA cm⁻²   （a4）")
    A("             cg = 54.10 mA cm⁻²  （a5）")
    A("             rRMSE = 1.23e-07 mA cm⁻²  （a6）")
    A("  轴标题     J (mA cm⁻²)   —— y 轴，左列三个面板各一个")
    A("             V (V)         —— x 轴，底行三个面板各一个")
    A("  内嵌图     zoom: 0–1.2 V  （a5 里的放大图；放大图本身保留）")
    A("  图例       target / decoder / COMSOL(pred θ) / COMSOL(true θ) —— 整块删除")
    A("")
    A("【S3b】")
    A("  轴标题     Voltage (V)")
    A("             RMSE across 45 samples (mA cm⁻²)")
    A("  图内说明   noise floor = 0.21 mA cm⁻²（文字删除；0.21 的灰色虚线保留）")
    A("  图例       decoder vs target / COMSOL(pred) vs target /")
    A("             decoder vs COMSOL(pred) —— 整块删除")
    A("")
    A("【S3c】")
    A("  面板编号   (c1)  (c2)  (c3)  (c4)")
    A("  轴标题     cycle gap, full 0–1.3 V (mA cm⁻²)   （c1 x）")
    A("             count                              （c1 y）")
    A("             cycle gap (mA cm⁻²)                （c2 y、c3 y、c4 y）")
    A("             param log₁₀-RMSE (post-hoc)        （c3 x）")
    A("             mean predicted σ                   （c4 x）")
    A("  类别轴文字 0–1.0 V、>1.0 V  （c2 的 x 轴；文字删除，刻度线保留）")
    A("  统计标注   median 2.56                （c1，全样本循环差中位数）")
    A("             0.47  /  5.30              （c2，两个箱的中位数标注）")
    A("             ρ = -0.03 (p = 0.86)       （c3）")
    A("             ρ = 0.12 (p = 0.44)        （c4）")
    A("  图例       无")
    A("")
    A("三、图例与颜色 / 线型对应（取自源 SVG 的 legend 采样线）")
    A("-" * 68)
    A("  S3a：target              #22262b  实线")
    A("       decoder             #0072b2  实线")
    A("       COMSOL(pred θ)      #d55e00  虚线（dash 7.4/3.2）")
    A("       COMSOL(true θ)      #009e73  点线（dash 2/3.3）")
    A("  S3b：decoder vs target            #0072b2  实线")
    A("       COMSOL(pred) vs target      #d55e00  虚线（7.4/3.2）")
    A("       decoder vs COMSOL(pred)     #009e73  点线（2/3.3）")
    A("  S3c：无图例。配色：(c1) 柱 #0072b2、中位数竖虚线 #d55e00；")
    A("       (c2) 两个箱 #0072b2 / #d55e00、灰连线 #999999；")
    A("       (c3) 散点 #009e73；(c4) 散点 #56b4e9")
    A("")
    A("四、轴刻度（原样保留，未改范围）")
    A("-" * 68)
    for n, stem in (("S3a", "FigureS3a"), ("S3b", "FigureS3b"),
                    ("S3c", "FigureS3c")):
        A("  %s：" % n)
        for aid, xs, ys in ticks_of(n, stem):
            A("    %-8s x: %-38s y: %s"
              % (aid, " ".join(xs) if xs else "—（无 x 刻度数字）",
                 " ".join(ys) if ys else "—"))
    A("  注：axes_5 的列表里含它内部放大图（axes_6）的刻度，因此出现两组数字。")
    A("  注：S3a 是共享坐标轴排版，上排三格本来就没有 x 刻度数字、右两列本来只")
    A("      画 y 刻度数字；这一点与原图一致，未做任何增补。")
    A("  注：三张图都没有科学计数法倍率标注（已在源 SVG 里确认无 ×10ⁿ 类文字）。")
    A("")
    A("五、核验结果（全部通过）")
    A("-" * 68)
    A("  · 数据图形：路径/标记/矩形元素数量与原图逐一相同；逐元素比对 0 改动、0 丢失。")
    A("  · 刻度：刻度线与刻度数字的位置、数值与源图完全一致；S3c 的 2 个类别轴文字")
    A("    已删、对应刻度线保留。")
    A("  · 逐像素：与「未删文字的源图」同窗口 600 dpi 比较，差异像素全部落在被删")
    A("    元素的墨迹内（S3a 189,753 px、S3b 31,336 px、S3c 77,442 px，掩膜外 0 px）。")
    A("  · 边框不裁切：最小留边 2.52 pt（S3c 2.64 pt）。")
    A("  · a5 的内嵌放大图与其曲线原样保留（7 个 axes 组）。")
    A("  · PowerPoint 实机：三张插入尺寸零误差，无红叉。")
    A("")
    A("六、字号说明（未做任何缩放）")
    A("-" * 68)
    A("  全部沿用原图字号，没有像 S1 那样机械减半：")
    A("    S3a  刻度 10.5 pt，绘图区宽 186.09 pt → 5.64 %")
    A("    S3b  刻度  7.5 pt，绘图区宽 657.36 pt → 1.14 %")
    A("    S3c  刻度  7.5 pt，绘图区宽 189.85 pt → 3.95 %")
    A("  S3a 的刻度数字相对偏大是原图本来的设定（65 mm 宽的面板配 10.5 pt）。")
    A("  如果要三块统一到 Figure S4 那种 ~3.8 % 的比例，告诉我，我按同样流程重出。")
    A("")
    A("七、拆分粒度说明")
    A("-" * 68)
    A("  按图上的字母编号拆成三块：S3a（六格共享坐标轴的整体）、S3b、S3c（四格整体）。")
    A("  这样保持了原图的共享坐标轴排版和 a5 内嵌图，不需要给任何面板补画被隐藏的")
    A("  刻度数字。如果需要继续拆成 a1–a6 / c1–c4 单格（每格独立画布），说一声即可。")

    open(os.path.join(PKG, "labels_and_values_S3.txt"), "w",
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
            print("   %-52s %9d" % (i.filename, i.file_size))


if __name__ == "__main__":
    main()
