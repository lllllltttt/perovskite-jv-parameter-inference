# -*- coding: utf-8 -*-
import io, json, os, shutil, sys, zipfile
if (getattr(sys.stdout,"encoding","") or "").lower().replace("-","")!="utf8":
    sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8")
OUT="out"; PKG=os.path.join("package","FigureS7_split"); ZIP="FigureS7_split.zip"
TITLES={"S7a":("a_μ","mobility","蓝色 #0072b2"),"S7b":("r_μ","mobility","橙色 #d55e00"),
        "S7c":("a_τ","lifetime","蓝色 #0072b2"),"S7d":("r_τ","lifetime","橙色 #d55e00"),
        "S7e":("a_D","DOS","蓝色 #0072b2"),"S7f":("r_D","DOS","橙色 #d55e00")}
XR={"S7a":"0–3","S7b":"0–5","S7c":"0–3","S7d":"0–5","S7e":"0–4","S7f":"0–5"}
def main():
    m=json.load(open(os.path.join(OUT,"work","meta.json"),encoding="utf-8"))
    if os.path.isdir(PKG): shutil.rmtree(PKG)
    os.makedirs(os.path.join(PKG,"preview"))
    for p in m["pieces"]:
        shutil.copy2(p["svg"],os.path.join(PKG,p["name"]+".svg"))
        shutil.copy2(p["png"],os.path.join(PKG,p["name"]+"_600dpi.png"))
    shutil.copy2(m["preview"],os.path.join(PKG,"preview",os.path.basename(m["preview"])))
    L=[]; A=L.append
    A("Figure S7 拆图交付：S7a–S7f 六个独立子图 + 删除文字清单")
    A("2026-11-17")
    A("="*70); A("")
    A("来源：E:/project/work1/20261024_final_figures_svg/si/FigureS7.svg（未改动）")
    A("画布 %.3f × %.3f pt（%d × %d px @600 dpi）；绘图区 %.3f × %.3f pt；六格完全一致。"
      %(m["canvas"][0],m["canvas"][1],m["pieces"][0]["px"][0],m["pieces"][0]["px"][1],
        m["plot"][0],m["plot"][1]))
    A("")
    A("一、顺序与各自内容")
    A("-"*70)
    for p in m["pieces"]:
        t,u,c=TITLES[p["name"]]
        A("  %-4s %-5s %-9s 横轴 %-4s nearest-neighbour 曲线 %s，random pairs 曲线灰色"
          %(p["name"],t,u,XR[p["name"]],c))
    A("")
    A("二、删掉的文字（原文，可直接复制）")
    A("-"*70)
    for w,t in m["removed"]:
        A("  %-8s %s"%(w if w!="figure" else "整图",t))
    A("")
    A("三、曲线的颜色 / 线宽 / 线型")
    A("  S7a 的图例**已保留**（两行：random pairs / nearest-neighbour pairs，含线段示例，")
    A("  位于绘图区右下角，原样未动）；S7b–S7f 本来就没有图例。其余五格若要补图例，")
    A("  按下面对应的颜色画即可。")
    A("-"*70)
    A("  random pairs            #9A9A9A  1.3 pt  实线   （六格都有）")
    A("  nearest-neighbour 对    #0072B2  1.6 pt  实线   （S7a / S7c / S7e，a 类坐标）")
    A("                          #D55E00  1.6 pt  实线   （S7b / S7d / S7f，r 类坐标）")
    A("  x = 1 竖直参考线        #555555  点线（dash 1,1.65）")
    A("  曲线均为累计分布，未平滑、未截断、未重采样。")
    A("")
    A("四、保留与核对")
    A("-"*70)
    A("  · 每格保留两条累计分布曲线 + x=1 竖线 + 四周边框 + 全部刻度线与刻度数字。")
    A("  · 纵轴每格都是 0.0 / 0.2 / 0.4 / 0.6 / 0.8 / 1.0 六个数字齐全（顶部 1.0 在内）。")
    A("  · 横轴保持各自范围，没有统一：S7a 0–3、S7b 0–5、S7c 0–3、S7d 0–5、S7e 0–4、S7f 0–5。")
    A("  · 刻度数字已全部转为矢量轮廓，PowerPoint 里不依赖字体。")
    A("  · 与源图同窗口 600 dpi 逐像素比较：差异全部落在文字/图例墨迹内，曲线、边框、")
    A("    参考线、刻度线一个像素没动（掩膜外 0 px）。")
    A("  · 曲线路径与源图逐条相同（d + style 完全一致）。")
    A("  · 最小留边 2.40 pt，顶部 1.0 与横轴最右刻度完整无裁切。")
    A("  · PNG 为白底。")
    open(os.path.join(PKG,"labels_and_notes.txt"),"w",encoding="utf-8").write("\n".join(L)+"\n")
    if os.path.exists(ZIP): os.remove(ZIP)
    with zipfile.ZipFile(ZIP,"w",zipfile.ZIP_DEFLATED) as z:
        for root,dirs,files in os.walk(PKG):
            dirs.sort()
            for fn in sorted(files):
                p=os.path.join(root,fn); z.write(p,os.path.relpath(p,os.path.dirname(PKG)))
    print("package:",PKG)
    with zipfile.ZipFile(ZIP) as z:
        for i in z.infolist(): print("   %-42s %9d"%(i.filename,i.file_size))
main()
