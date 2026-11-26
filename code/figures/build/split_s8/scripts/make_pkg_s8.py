# -*- coding: utf-8 -*-
import io, json, os, shutil, sys, zipfile
if (getattr(sys.stdout,"encoding","") or "").lower().replace("-","")!="utf8":
    sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8")
OUT="out"; PKG=os.path.join("package","FigureS8_split"); ZIP="FigureS8_split.zip"
def main():
    m=json.load(open(os.path.join(OUT,"work","meta.json"),encoding="utf-8"))
    if os.path.isdir(PKG): shutil.rmtree(PKG)
    os.makedirs(os.path.join(PKG,"preview"))
    for p in m["pieces"]:
        shutil.copy2(p["svg"],os.path.join(PKG,p["name"]+".svg"))
        shutil.copy2(p["png"],os.path.join(PKG,p["name"]+"_600dpi.png"))
    shutil.copy2(m["preview"],os.path.join(PKG,"preview",os.path.basename(m["preview"])))
    L=[]; A=L.append
    A("Figure S8 拆图交付：S8_01–S8_06 六个独立子图 + 删除文字清单")
    A("2026-11-17")
    A("="*70); A("")
    A("来源：E:/project/work1/20261024_final_figures_svg/si/FigureS8.svg（未改动）")
    A("画布 %.3f × %.3f pt（%d × %d px @600 dpi）；绘图区 %.3f × %.3f pt；六格完全一致。"
      %(m["canvas"][0],m["canvas"][1],m["pieces"][0]["px"][0],m["pieces"][0]["px"][1],
        m["plot"][0],m["plot"][1]))
    A("")
    A("顺序（2×3，从左到右、从上到下）：")
    A("  S8_01  log10 g_μ（mobility 共享尺度）   —— 图例保留")
    A("  S8_02  log10 g_τ（lifetime）")
    A("  S8_03  log10 g_D（DOS）")
    A("  S8_04  mobility ratio q_μ             —— 图例保留")
    A("  S8_05  lifetime ratio q_τ")
    A("  S8_06  DOS ratio q_D")
    A("")
    A("一、删掉的文字（原文，可直接复制）")
    A("-"*70)
    for w,t in m["removed"]:
        A("  %-8s %s"%(w,t))
    A("")
    A("二、保留下来的图例（按你的要求）")
    A("-"*70)
    A("  S8_01：两行，线段示例 + 文字，位于绘图区内左下：")
    A("         original 0.2–5 (n=102046)     蓝线 #0072B2，1.6 pt 实线")
    A("         expanded 0.05–20 (n=24274)    橙线 #D55E00，1.6 pt 实线")
    A("  S8_04：一行，灰色方块示例 + 文字，位于绘图区内右上：")
    A("         old ratio range 0.2–5        灰块 #999999（对应图中的灰色阴影带）")
    A("  S8_02 / 03 / 05 / 06 本来就没有图例。")
    A("  说明：图例里的文字在源 SVG 里就是矢量轮廓，本次未改动，PowerPoint 里不会跑字。")
    A("")
    A("三、保留与核对")
    A("-"*70)
    A("  · 全部阶梯密度曲线（蓝 original / 橙 expanded）、灰色阴影带、四周边框、")
    A("    刻度线与刻度数字均原样保留；数据、轴范围、配色、线宽、线型未动。")
    A("  · 刻度数字在源 SVG 里本来就是矢量轮廓（<use> 引用字形），PowerPoint 不依赖字体。")
    A("  · 与源图同窗口 600 dpi 逐像素比较：差异全部落在被删的轴标题墨迹内，")
    A("    掩膜外 0 px；曲线路径与源图逐条相同（d + style 一致）。")
    A("  · 六格画布与绘图区偏移完全一致（偏差 0.0000 pt）；最小留边 2.52 pt。")
    open(os.path.join(PKG,"labels_and_notes.txt"),"w",encoding="utf-8").write("\n".join(L)+"\n")
    if os.path.exists(ZIP): os.remove(ZIP)
    with zipfile.ZipFile(ZIP,"w",zipfile.ZIP_DEFLATED) as z:
        for root,dirs,files in os.walk(PKG):
            dirs.sort()
            for fn in sorted(files):
                p=os.path.join(root,fn); z.write(p,os.path.relpath(p,os.path.dirname(PKG)))
    print("package:",PKG)
    for i in zipfile.ZipFile(ZIP).infolist(): print("   %-40s %9d"%(i.filename,i.file_size))
main()
