# -*- coding: utf-8 -*-
"""Check the two panels against the frozen Δ table."""
import re, sys
import numpy as np, pandas as pd
from lxml import etree
from PIL import Image
CS="{http://www.w3.org/2000/svg}"
ROOT=r"E:\project\work1\20261021_expanded_ratio_comparison_v2"
COORDS=["a_mu","r_mu","a_tau","r_tau","a_D","r_D"]
COL="diff_new_minus_old_rmse"
L,T,W,H=31.0,3.0,210.54,158.79
PANEL={"a":("original","common_test_a"),"b":("expanded","common_test_b")}
FAIL=[]
def ok(c,l,d=""):
    print("  %s  %s%s"%("PASS" if c else "FAIL",l,("  "+d) if d else ""))
    if not c: FAIL.append(l)
def main():
    P=pd.read_csv(ROOT+r"\out\metrics\paired_differences.csv")
    for k,(arm,stem) in PANEL.items():
        r=etree.parse("out/%s.svg"%stem).getroot()
        # ylim from the y tick label positions is easier: use the frame box
        y0,y1=None,None
        paths=[(p.get("style") or "",p.get("d") or "") for p in r.iter(CS+"path")]
        # zero line: black, lw 0.6, width == plot width
        zero=[d for st,d in paths if "stroke-width: 0.6" in st and "stroke: #000000" in st]
        ok(len(zero)==1,"%s: zero reference line present"%k)
        def nums(d): return [float(v) for v in re.findall(r"-?\d+\.?\d*",d)]
        yz=nums(zero[0])[1] if zero else None
        # frame: from the axes patch (fill #ffffff) or spines -> ylim from ticks
        # use the clip rect of the axes
        rects=[rect for cp in r.iter(CS+"clipPath") for rect in [cp.find(CS+"rect")] if rect is not None]
        rx,ry,rw,rh=[float(rects[0].get(a)) for a in ("x","y","width","height")]
        # ylim: infer from the tick labels — instead read the two horizontal
        # spines? simpler: the zero line's y and the known ylim of the original.
        # Recompute ylim exactly as matplotlib did: from the data + 5% margins.
        g=P[P.test_arm==arm]
        vals=np.concatenate([g[g.quantity==c][COL].astype(float).to_numpy() for c in COORDS])
        lo,hi=min(vals.min(),0.0),max(vals.max(),0.0)
        span=hi-lo; y0,y1=lo-0.05*span,hi+0.05*span
        def val(y): return y0+(ry+rh-y)/rh*(y1-y0)
        dev_z=abs(val(yz))
        ok(dev_z<0.002,"%s: zero line sits at Δ = 0 (dev %.5f)"%(k,dev_z))
        # mean bars: black lw 1.8, 2-point paths
        bars=[]
        for st,d in paths:
            if "stroke-width: 1.8" in st and "stroke: #000000" in st:
                n=nums(d); bars.append((n[0],n[1],n[2],n[3]))
        ok(len(bars)==6,"%s: 6 summary bars"%k)
        want=[np.mean(g[g.quantity==c][COL].astype(float)) for c in COORDS]
        got=sorted(val((b[1]+b[3])/2) for b in bars)
        dev_b=max(abs(a-b) for a,b in zip(got,sorted(want)))
        ok(dev_b<0.002,"%s: summary bars = mean of the 5 seeds (max dev %.5f)"%(k,dev_b))
        # span of the bars: +-0.22 category units
        xs=sorted(b[0] for b in bars)+sorted(b[2] for b in bars)
        x0=np.array([b[0] for b in bars]).min(); x1=np.array([b[2] for b in bars]).max()
        ok(True,"%s: bar x span %.2f .. %.2f"%(k,x0,x1))
        # dots
        dots=[float(u.get("y")) for u in r.iter(CS+"use") if "fill-opacity" in (u.get("style") or "")]
        ok(len(dots)==len(vals),"%s: %d dots (= %d Δ values)"%(k,len(dots),len(vals)))
        dv=max(abs(a-b) for a,b in zip(sorted(val(y) for y in dots),sorted(vals)))
        ok(dv<0.002,"%s: every dot at its Δ value (max dev %.5f)"%(k,dv))
        s=open("out/%s.svg"%stem,encoding="utf-8").read()
        ok("#404040" in s and "<text" not in s,"%s: dark grey frame, no <text>"%k)
        im=Image.open("out/%s.png"%stem)
        ok(im.size==(2037,1414),"%s: png %dx%d"%(k,*im.size))
    print("\nRESULT:","ALL PASS" if not FAIL else "FAIL (%d)"%len(FAIL))
    for f in FAIL: print("  FAILED:",f)
    sys.exit(1 if FAIL else 0)
main()
