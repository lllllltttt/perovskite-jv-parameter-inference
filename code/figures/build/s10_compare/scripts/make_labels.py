# -*- coding: utf-8 -*-
"""Write labels_and_values.txt and assemble the delivery folder + zip."""
import io, json, os, shutil, sys, zipfile
import numpy as np, pandas as pd
if (getattr(sys.stdout,"encoding","") or "").lower().replace("-","")!="utf8":
    sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8")
ROOT=r"E:\project\work1\20261021_expanded_ratio_comparison_v2"
OUT=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"out")
PKG=os.path.join(os.path.dirname(OUT),"package","comparison_figures_S9")
ZIP=os.path.join(os.path.dirname(OUT),"comparison_figures_S9.zip")
COORDS=["a_mu","r_mu","a_tau","r_tau","a_D","r_D"]
NAME={"a_mu":"a_μ","r_mu":"r_μ","a_tau":"a_τ","r_tau":"r_τ","a_D":"a_D","r_D":"r_D"}
def main():
    df=pd.read_csv(os.path.join(ROOT,"out","metrics","table_B_common_tests.csv"))
    A=df[df.test_arm==df.model_arm]
    if os.path.isdir(PKG): shutil.rmtree(PKG)
    os.makedirs(PKG)
    for stem in ("comparison_a","comparison_b"):
        shutil.copy2(os.path.join(OUT,stem+".svg"),os.path.join(PKG,stem+".svg"))
        shutil.copy2(os.path.join(OUT,stem+".png"),os.path.join(PKG,stem+"_600dpi.png"))
    shutil.copy2(os.path.join(os.path.dirname(OUT),"scripts","comparison_figures_S9.py"),
                 os.path.join(PKG,"comparison_figures_S9.py"))
    L=[];A_=L.append
    A_("Figure S9 对比图 —— 两个独立子图（comparison_a / comparison_b）")
    A_("2026-11-17")
    A_("="*70); A_("")
    A_("来源：原始脚本 20261021_expanded_ratio_comparison_v2/scripts/05_figures.py（fig02）")
    A_("      数据 out/metrics/table_B_common_tests.csv，取 test_arm = model_arm 的自测行")
    A_("      已与 figures/figure_values.csv 交叉核对（所有柱高与散点一致）")
    A_("      数据、统计方法、柱宽、组间距均沿用原脚本，未重新训练、未按截图估值")
    A_("")
    A_("一、原始标题与轴标题（本版已删除，可直接复制回 PPT）")
    A_("-"*70)
    A_("  (a) 标题:   (a) Skill_MSE (higher is better)")
    A_("  (b) 标题:   (b) RMSE in physical log10 (lower is better)")
    A_("  (a) 纵轴:   Skill_MSE")
    A_("  (b) 纵轴:   RMSE (log10 units)")
    A_("  横轴标题:   原图没有")
    A_("")
    A_("二、六个参数名称（顺序与原图一致）")
    A_("-"*70)
    A_("  a_μ、r_μ、a_τ、r_τ、a_D、r_D")
    A_("")
    A_("三、图例（两行，原图在整幅图底部居中）")
    A_("-"*70)
    A_("  original 0.2–5 (own test)")
    A_("  expanded 0.05–20 (own test)")
    A_("")
    A_("四、两种配色")
    A_("-"*70)
    A_("  original   #3A5C94（蓝）   alpha = 1（不透明，显示即为该色值）")
    A_("  expanded   #CA7241（橙）   alpha = 1")
    A_("")
    A_("五、误差棒 / 散点 / 网格 / 边框的定义")
    A_("-"*70)
    A_("  柱高     = 该臂该坐标 5 次运行（seed 20261021–20261025）的算术平均")
    A_("  误差棒   = 同样 5 次运行的样本标准差（ddof = 1），上下各 1×SD")
    A_("             不是标准误、不是置信区间；黑色 0.8 pt、端帽 2 pt")
    A_("  小圆点   = 每一次运行的原始值，每柱 5 个；黑色、2.4 pt、alpha 0.55")
    A_("  网格线   = 无（本版已去掉绘图区内的网格线）")
    A_("  边框     = 四边完整矩形，#404040、0.5 pt；刻度线仅左/下，向外 3.5 pt")
    A_("  刻度数字 = 8 pt Arial；SVG 中已转为矢量轮廓")
    A_("")
    A_("六、各柱数值（mean ± SD，供核对）")
    A_("-"*70)
    A_("  %-6s %-6s %-22s %-22s"%("面板","参数","original 0.2–5","expanded 0.05–20"))
    for panel,met in (("a","skill_mse"),("b","rmse")):
        for c in COORDS:
            o=A[(A.model_arm=="original")&(A.quantity==c)][met].astype(float)
            e=A[(A.model_arm=="expanded")&(A.quantity==c)][met].astype(float)
            A_("  %-6s %-6s %.4f ± %.4f        %.4f ± %.4f"
               %(panel,NAME[c],np.nanmean(o),np.nanstd(o,ddof=1),
                 np.nanmean(e),np.nanstd(e,ddof=1)))
    A_("")
    A_("七、版式")
    A_("-"*70)
    A_("  两个子图绘图区 210.54 × 158.79 pt，完全相同；外边距也相同")
    A_("  画布 238.54 × 169.79 pt；600 dpi PNG = 1987 × 1414 px、白底")
    A_("  纵轴：a 0 – 0.825（每 0.1）；b 0 – 1.135（每 0.2），沿用原图，未强行统一")
    A_("  横轴：六组等距，刻度短线位于每组蓝橙柱子的正中间；参数名已删除")
    A_("  图内不含任何标题、轴标题、参数名、图例、数值标签")
    open(os.path.join(PKG,"labels_and_values.txt"),"w",encoding="utf-8").write("\n".join(L)+"\n")
    if os.path.exists(ZIP): os.remove(ZIP)
    with zipfile.ZipFile(ZIP,"w",zipfile.ZIP_DEFLATED) as z:
        for fn in sorted(os.listdir(PKG)):
            z.write(os.path.join(PKG,fn),"comparison_figures_S9/"+fn)
    print("package:",PKG)
    for i in zipfile.ZipFile(ZIP).infolist(): print("   %-44s %8d"%(i.filename,i.file_size))
main()
