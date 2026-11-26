# -*- coding: utf-8 -*-
"""Check the rendered panels against the frozen numbers."""
import re, sys
import numpy as np, pandas as pd
from lxml import etree
from PIL import Image
CS="{http://www.w3.org/2000/svg}"; XL="{http://www.w3.org/1999/xlink}"
ROOT=r"E:\project\work1\20261021_expanded_ratio_comparison_v2"
COORDS=["a_mu","r_mu","a_tau","r_tau","a_D","r_D"]
L,T,W,H=25.0,3.0,210.54,158.79
YL={"a":(0.0,0.82498),"b":(0.0,1.13538)}
MET={"a":"skill_mse","b":"rmse"}
FAIL=[]
def ok(c,l,d=""):
    print("  %s  %s%s"%("PASS" if c else "FAIL",l,("  "+d) if d else ""))
    if not c: FAIL.append(l)
def main():
    df=pd.read_csv(ROOT+r"\out\metrics\table_B_common_tests.csv")
    A=df[df.test_arm==df.model_arm]
    for k in ("a","b"):
        met=MET[k]; y0,y1=YL[k]
        r=etree.parse("out/comparison_%s.svg"%k).getroot()
        def val(y): return y0+(T+H-y)/H*(y1-y0)
        # bars
        bars=[]
        for g in r.iter(CS+"g"):
            p=g.find(".//"+CS+"path")
            if p is None: continue
            st=p.get("style") or ""
            if "fill: #3a5c94" in st or "fill: #ca7241" in st:
                n=[float(v) for v in re.findall(r"-?\d+\.?\d*",p.get("d"))]
                ys=n[1::2]
                bars.append(("#3a5c94" if "3a5c94" in st else "#ca7241",
                             max(ys), min(ys)))
        ok(len(bars)==12,"%s: %d bars"%(k,len(bars)))
        dev=0.0
        for arm,col in (("original","#3a5c94"),("expanded","#ca7241")):
            got=[val(top) for c,base,top in bars if c==col]
            # bars are emitted in x order
            want=[np.nanmean(A[(A.model_arm==arm)&(A.quantity==c)][met].astype(float))
                  for c in COORDS]
            dev=max(dev,max(abs(a-b) for a,b in zip(sorted(got),sorted(want))))
        ok(dev<0.002,"%s: bar heights match the data (max dev %.5f)"%(k,dev))
        # dots: <use> of the circle marker
        dots=[float(u.get("y")) for u in r.iter(CS+"use")
              if "fill-opacity" in (u.get("style") or "")]
        want=sum(len(A[(A.model_arm==arm)&(A.quantity==c)][met].astype(float))
                 for arm in ("original","expanded") for c in COORDS)
        ok(len(dots)==want,"%s: %d dots drawn (= %d seed values)"%(k,len(dots),want))
        dv=max(abs(y-vv) for y,vv in
               zip(sorted(val(y) for y in dots),sorted([v for arm in ("original","expanded")
                     for c in COORDS for v in A[(A.model_arm==arm)&(A.quantity==c)][met].astype(float)])))
        if dv>0.002:
            aa=sorted(val(y) for y in dots)
            bb=sorted([v for arm in ("original","expanded") for c in COORDS
                       for v in A[(A.model_arm==arm)&(A.quantity==c)][met].astype(float)])
            print("     DBG n=",len(aa),len(bb),"a",[round(x,4) for x in aa[:3]],[round(x,4) for x in aa[-3:]])
            print("     DBG b",[round(x,4) for x in bb[:3]],[round(x,4) for x in bb[-3:]])
        ok(dv<0.002,"%s: every dot sits at its seed value (max dev %.5f)"%(k,dv))
        # frame / ticks
        ok("stroke: #404040" in open("out/comparison_%s.svg"%k,encoding="utf-8").read(),
           "%s: dark grey frame present"%k)
        im=Image.open("out/comparison_%s.png"%k)
        ok(im.size==(1987,1414),"%s: png %dx%d = %.2f x %.2f pt"%(k,*im.size,
           im.size[0]*72/600,im.size[1]*72/600))
    print("\nRESULT:","ALL PASS" if not FAIL else "FAIL (%d)"%len(FAIL))
    for f in FAIL: print("  FAILED:",f)
    sys.exit(1 if FAIL else 0)
main()
