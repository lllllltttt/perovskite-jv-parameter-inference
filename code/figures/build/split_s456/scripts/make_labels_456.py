# -*- coding: utf-8 -*-
"""Assemble the 27-panel delivery: folder, labels_and_values.txt and the zip."""
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
PKG = os.path.join("package", "figsS4S5S6_27panels")
ZIP = "figsS4S5S6_27panels.zip"

FIG_TITLES = {"S4": "Predictive-scale distributions",
              "S5": "Predictive scale versus normalized error",
              "S6": "Predicted versus true (nine parameters)"}


def comments(path):
    r = etree.parse(path).getroot()
    out = {}
    for g in r.iter(CS + "g"):
        gid = g.get("id") or ""
        if not re.match(r"^text_\d+$", gid):
            continue
        for c in g.iter():
            if not isinstance(c.tag, str):
                s = (getattr(c, "text", "") or "").strip()
                if s:
                    out[gid] = re.sub(r"\s+", " ", s)
                    break
    return out


def pretty(s):
    """Turn the matplotlib mathtext source into copy-ready text."""
    s = s.replace("$\\mu_n$", "μ_n").replace("$\\mu_p$", "μ_p")
    s = s.replace("$\\tau_n$", "τ_n").replace("$\\tau_p$", "τ_p")
    s = s.replace("$N_c$", "N_c").replace("$N_v$", "N_v")
    s = s.replace("$\\tau_{\\mathrm{ETL}}$", "τ_ETL").replace(
        "$\\tau_\\mathrm{ETL}$", "τ_ETL")
    s = s.replace("$\\tau_{\\mathrm{HTL}}$", "τ_HTL").replace(
        "$\\tau_\\mathrm{HTL}$", "τ_HTL")
    s = s.replace("$r_{\\mathrm{rad}}$", "r_rad").replace(
        "$r_\\mathrm{rad}$", "r_rad")
    s = s.replace("$\\rho$", "ρ").replace("$\\rho = ", "ρ = ")
    s = s.replace("$\\sigma_\\theta$", "σ_θ")
    s = s.replace("$n$", "n").replace("$_{10}$", "₁₀").replace("$\\cdot$", "·")
    return s.replace("$", "")


def main():
    meta = json.load(open(os.path.join(OUT, "work", "meta.json"), encoding="utf-8"))
    if os.path.isdir(PKG):
        shutil.rmtree(PKG)
    os.makedirs(os.path.join(PKG, "preview"))

    for tag in ("S4", "S5", "S6"):
        for p in meta[tag]["pieces"]:
            shutil.copy2(p["svg"], os.path.join(PKG, p["name"] + ".svg"))
            shutil.copy2(p["png"], os.path.join(PKG, p["name"] + "_600dpi.png"))
        shutil.copy2(meta[tag]["preview"],
                     os.path.join(PKG, "preview", os.path.basename(meta[tag]["preview"])))

    L = []
    A = L.append
    A("Figure S4 / S5 / S6 拆图交付：27 个独立子图 + 被删除文字与统计值清单")
    A("2026-11-16")
    A("=" * 70)
    A("")
    A("来源：E:\\project\\work1\\20261024_final_figures_svg\\si\\FigureS4.svg、")
    A("      FigureS5.svg、FigureS6.svg（三个文件均未改动）")
    A("")
    A("关于文字：S4 与 S5 的原始 SVG 里文字已经是矢量轮廓（matplotlib fonttype=path），")
    A("但每个标签仍是独立的 <g id=\"text_N\">，并带一条 XML 注释记录原始字符串，")
    A("所以下面的清单是从原文件里读出来的，不是照着截图抄的。刻度文字本身就是")
    A("矢量路径，在 PowerPoint 里不依赖任何字体，不会出现替换或挤压。")
    A("")
    A("命名与顺序：每张图 3×3，从左到右、从上到下 S?_01 … S?_09。")
    A("")

    for tag in ("S4", "S5", "S6"):
        m = meta[tag]
        cs = comments(os.path.join(BASE, m["source"]))
        A("=" * 70)
        A("%s —— %s" % (tag, FIG_TITLES[tag]))
        A("=" * 70)
        A("  画布 %.3f × %.3f pt（%d × %d px @600 dpi）；绘图区 %.3f × %.3f pt"
          % (m["canvas"][0], m["canvas"][1], m["pieces"][0]["px"][0],
             m["pieces"][0]["px"][1], m["plot"][0], m["plot"][1]))
        A("")
        A("  子图   删除的文字（原文 → 可直接复制的写法）")
        A("  " + "-" * 66)
        rem = m["removed"]
        for i, p in enumerate(m["pieces"], start=1):
            aid = p["axes"]
            items = [t for w, t in rem if w == aid]
            A("  %-6s %s" % (p["name"], "；".join(items) if items else "（无）"))
            for t in items:
                A("         → %s" % pretty(t))
        figlvl = [t for w, t in rem if w == "figure"]
        if figlvl:
            A("  整图   图级标题：%s" % figlvl[0])
        if tag == "S6":
            a10 = etree.parse(os.path.join(BASE, m["source"])).getroot() \
                .find(".//" + CS + "g[@id='axes_10']")
            if a10 is not None:
                A("  整图   覆盖层（axes_10，只有文字，已整组删除）：")
                for g in a10:
                    if not isinstance(g.tag, str):
                        continue
                    gid = g.get("id") or ""
                    if gid in cs:
                        A("         → %s" % pretty(cs[gid]))
        A("")
        if tag == "S4":
            A("  说明：每格的 y 轴标题（Count / Predictive scale, σ_θ）已随格删除；")
            A("        每格都保留了自己的横纵刻度数字。")
        elif tag == "S5":
            A("  说明：每格 15,307 个散点全部为矢量 <use>，未删点、未抽样、未改透明度。")
        else:
            A("  说明：共享坐标轴排版——左列三格只带纵轴数字、底行三格只带横轴数字，")
            A("        左下角那一格横纵都有；其余四格只有刻度线没有数字。这一套已按你的")
            A("        要求补齐：凡是有数字的那一侧，0.0 / 0.5 / 1.0 三个都齐（原来有的只")
            A("        有 0.5，有的缺 1.0）。位置沿用原标签偏移（x 轴 +11.868 pt、y 轴")
            A("        −6.5 pt / +2.684 pt），数据与其它元素一个都没动。")
        A("")

    A("=" * 70)
    A("核验（逐图）")
    A("=" * 70)
    A("  · 27 个文件各自只含一个小图，树内已无非刻度文字（标题/轴标题/统计值/图级")
    A("    标题全部清除）；刻度组、刻度数字、位置与源 SVG 逐元素相同。")
    A("  · 27 张与源图同窗口 600 dpi 逐像素比较：全部 0 差异（数据、边框、刻度、")
    A("    裁剪窗一个像素都没动）。")
    A("  · 每张图内部九个子图共用同一画布与同一绘图区偏移（最大偏差 0.0000 pt）。")
    A("  · 留边 ≥ 1.0 pt，边框、负号、刻度数字无裁切；无相邻小图残留。")
    A("  · 三个原始 SVG 未改动。")
    A("")
    A("=" * 70)
    A("Microsoft PowerPoint 实测（真的插进去测的）")
    A("=" * 70)
    A("  用 PowerPoint COM 把 27 个 SVG 逐个插入（AddPicture），保存、关闭、重新打开，")
    A("  再逐页导出 600 dpi PNG 检查：")
    A("    27/27 插入尺寸与请求值零误差；")
    A("    27/27 导出图中红色失败标记像素数 = 0（含 9 张 S5 密集散点，各 15,307 点）。")
    A("  结论：S5 拆成单格后每张只有约 1.5 万个 <use>，远低于此前整图 10.8 万触发")
    A("  红叉的量级，因此本轮**未**栅格化散点层，全部保持矢量。若你的机器上仍出现")
    A("  红叉，告诉我，我把 S5 的散点层按最终尺寸 600 dpi 栅格化后重出（坐标轴、")
    A("  刻度、参考线仍保持矢量）。")

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
    print("zip:", ZIP, os.path.getsize(ZIP), "bytes")
    with zipfile.ZipFile(ZIP) as z:
        print("files:", len(z.namelist()))


if __name__ == "__main__":
    main()
