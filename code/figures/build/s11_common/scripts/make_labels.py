# -*- coding: utf-8 -*-
import io, os, shutil, sys, zipfile
import numpy as np, pandas as pd
if (getattr(sys.stdout,"encoding","") or "").lower().replace("-","")!="utf8":
    sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8")
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT=r"E:\project\work1\20261021_expanded_ratio_comparison_v2"
OUT=os.path.join(BASE,"out"); PKG=os.path.join(BASE,"package","comparison_common_test")
ZIP=os.path.join(BASE,"comparison_common_test.zip")
COORDS=["a_mu","r_mu","a_tau","r_tau","a_D","r_D"]
NAME={"a_mu":"a_μ","r_mu":"r_μ","a_tau":"a_τ","r_tau":"r_τ","a_D":"a_D","r_D":"r_D"}
COL="diff_new_minus_old_rmse"
def main():
    P=pd.read_csv(os.path.join(ROOT,"out","metrics","paired_differences.csv"))
    if os.path.isdir(PKG): shutil.rmtree(PKG)
    os.makedirs(PKG)
    for stem in ("common_test_a","common_test_b"):
        shutil.copy2(os.path.join(OUT,stem+".svg"),os.path.join(PKG,stem+".svg"))
        shutil.copy2(os.path.join(OUT,stem+".png"),os.path.join(PKG,stem+"_600dpi.png"))
    shutil.copy2(os.path.join(BASE,"scripts","common_test_figures.py"),
                 os.path.join(PKG,"common_test_figures.py"))
    L=[];A=L.append
    A("Figure S9 配套对比图（fig03 共测集配对差）—— common_test_a / common_test_b")
    A("2026-11-17")
    A("="*70); A("")
    A("来源：原始脚本 20261021_expanded_ratio_comparison_v2/scripts/05_figures.py（fig03）")
    A("      数据 out/metrics/paired_differences.csv，列 diff_new_minus_old_rmse")
    A("      数据、统计口径、散点数量均沿用原脚本，未重算、未按截图估值、未重新训练")
    A("")
    A("一、原始标题与轴标题（本版已删除，可直接复制回 PPT）")
    A("-"*70)
    A("  (a) 标题:   (a) common original-range test")
    A("  (b) 标题:   (b) common expanded-range test")
    A("  纵轴标题:   Δ RMSE (log₁₀ units)      —— 原图只标在左图")
    A("  横轴标题:   原图没有")
    A("  底部说明:   Δ = expanded-trained − original-trained; negative means the")
    A("              expanded model has the smaller error")
    A("")
    A("二、六个参数名称（顺序与原图一致，本版已删除）")
    A("-"*70)
    A("  a_μ、r_μ、a_τ、r_τ、a_D、r_D")
    A("")
    A("三、Δ 的定义（保持原样）")
    A("-"*70)
    A("  Δ = expanded-trained − original-trained（列名 diff_new_minus_old_rmse）")
    A("  负值 = 用扩比模型训练时误差更小")
    A("  左图（common original-range test）全部为正；右图（common expanded-range test）全部为负")
    A("")
    A("四、图形元素与统计含义")
    A("-"*70)
    A("  小圆点   = 每个 seed 的 Δ 值，每组 5 个（20261021–20261025），未抖动、未抽稀")
    A("             颜色 #CA7241、直径 3 pt、alpha 0.6")
    A("  黑短横线 = 该组 5 个 Δ 的**算术平均**（原脚本 np.mean，不是中位数）")
    A("             黑色、1.8 pt、横跨类别中心 ±0.22")
    A("  零线     = y = 0 的黑色水平参考线（0.6 pt），保留在坐标范围内，不是边框")
    A("  网格     = 浅灰 #D9D9D9 点线、0.5 pt，仅水平")
    A("  边框     = 四边完整矩形 #404040、0.5 pt；刻度线只左/下，向外 3.5 pt")
    A("  刻度数字 = 8 pt Arial（与上一张拆分图一致）；SVG 中已转为矢量轮廓")
    A("")
    A("五、每组数值（Δ RMSE，供核对）")
    A("-"*70)
    A("  %-6s %-16s %-10s %s"%("面板","参数","均值","5 个 seed 值"))
    for arm,panel in (("original","a"),("expanded","b")):
        g=P[P.test_arm==arm]
        for c in COORDS:
            v=g[g.quantity==c][COL].astype(float).to_numpy()
            A("  %-6s %-16s %+0.4f     %s"%(panel,NAME[c],np.mean(v),
              "  ".join("%+0.4f"%x for x in v)))
    A("")
    A("六、版式")
    A("-"*70)
    A("  两图绘图区 210.54 × 158.79 pt 完全一致，外边距一致；画布 244.54 × 169.79 pt")
    A("  600 dpi PNG = 2037 × 1414 px、白底")
    A("  纵轴范围各自沿用原图（左 −0.015…0.325、右 −0.298…0.014），未强行统一")
    A("  零线与上下边界的距离保持原样；为此只补边框，没有改坐标范围")
    open(os.path.join(PKG,"labels_and_values.txt"),"w",encoding="utf-8").write("\n".join(L)+"\n")
    if os.path.exists(ZIP): os.remove(ZIP)
    with zipfile.ZipFile(ZIP,"w",zipfile.ZIP_DEFLATED) as z:
        for fn in sorted(os.listdir(PKG)):
            z.write(os.path.join(PKG,fn),"comparison_common_test/"+fn)
    print("package:",PKG)
    for i in zipfile.ZipFile(ZIP).infolist(): print("   %-46s %8d"%(i.filename,i.file_size))
main()
