# -*- coding: utf-8 -*-
import io, json, os, re, sys
import numpy as np
from lxml import etree
from PIL import Image
if (getattr(sys.stdout, "encoding", "") or "").lower().replace("-", "") != "utf8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_s3b_v4 as B
CS="{http://www.w3.org/2000/svg}"; XL="{http://www.w3.org/1999/xlink}"
OUT="out_v4"; FAIL=[]
def ok(c,l,d=""):
    print("  %s  %s%s"%("PASS" if c else "FAIL",l,("  "+d) if d else ""))
    if not c: FAIL.append(l)
def txt(e): return re.sub(r"\s+"," ","".join(e.itertext()).replace("\xa0"," ")).strip()
def main():
    meta=json.load(open(os.path.join(OUT,"work","meta.json"),encoding="utf-8")); win=tuple(meta["win"])
    src=etree.parse(B.SRC).getroot()
    idmap={e.get("id"):e for e in src.iter() if e.get("id")}
    order={i:k for k,i in enumerate(idmap)}
    got=etree.parse(os.path.join(OUT,"svg","S3b_final.svg")).getroot(); body=got.find(CS+"g")[0]
    s0=src.find(".//"+CS+"g[@id='figure_1']")
    ax0=s0.find(".//"+CS+"g[@id='axes_1']")

    print("="*76); print("A  typography")
    tk=[t.get("font-size") for g in body.iter(CS+"g")
        if (g.get("id") or "").startswith(("xtick_","ytick_")) for t in g.iter(CS+"text")]
    lg=body.find(".//"+CS+"g[@id='legend_1']")
    lf=sorted({t.get("font-size") for t in lg.iter(CS+"text")})
    ok(set(tk)=={"10.5"}, "tick numbers %s (S3a uses 10.5)"%sorted(set(tk)))
    ok(lf==["8.68"], "legend text %s pt (6.2 x 1.4)"%lf)
    rows=sorted(float(t.get("y")) for t in lg.iter(CS+"text"))
    pitch=min(b-a for a,b in zip(rows,rows[1:]))
    ok(pitch>8.68*0.716+1.0, "legend rows keep %.2f pt pitch (glyph cap 6.2 pt)"%pitch)
    ok(not any(k in txt(t) for t in body.iter(CS+"text") for k in ("Voltage","RMSE across","noise floor")),
       "the three texts are gone")

    print("\n"+"="*76); print("B  data graphics byte-identical")
    def sig(root, skip_legend):
        out=[]
        for e in root.iter():
            if not isinstance(e.tag,str) or e.tag not in (CS+"path",CS+"use"): continue
            p=e.getparent(); bad=False
            while p is not None:
                if p.tag==CS+"text": bad=True; break
                if skip_legend and (p.get("id") or "").startswith("legend"): bad=True; break
                p=p.getparent()
            if bad: continue
            out.append(("use",e.get(XL+"href"),e.get("x"),e.get("y"),e.get("style")) if e.tag==CS+"use"
                       else ("path",e.get("d"),e.get("style")))
        return out
    a=sig(s0,True); b=sig(body,True)
    ok(a==b, "%d curve/frame/tick paths identical (d + style)"%len(b))
    # legend samples: the scaled shapes of the originals
    p0=[p.get("d") for p in lg0.iter(CS+"path")] if (lg0:=ax0.find(".//"+CS+"g[@id='legend_1']")) is not None else []
    p1=[p.get("d") for p in lg.iter(CS+"path")]
    def inv(d):
        n=[float(v) for v in re.findall(r"-?\d+\.?\d*",d)]
        out=[]
        for i in range(0,len(n),2):
            out.append(round((n[i]-B.LEG_X0)/B.K+B.LEG_X0,3)); out.append(round((n[i+1]-B.LEG_Y0)/B.K+B.LEG_Y0,3))
        return out
    ok(len(p1)==3 and all(abs(u-v)<0.01 for d0,d1 in zip(p0,p1) for u,v in zip(inv(d1),[float(x) for x in re.findall(r"-?\d+\.?\d*",d0)])),
       "3 legend samples = originals scaled x%.2f about the legend corner"%B.K)

    print("\n"+"="*76); print("C  pixel check: only texts and the legend differ")
    ref=B.build([etree.fromstring(etree.tostring(s0))],win,idmap,order,os.path.join(OUT,"work","ref.svg"))
    B.render(ref,os.path.join(OUT,"work","ref.png"),600)
    probe=etree.fromstring(etree.tostring(s0))
    rm=B.cut(probe)
    keep={i for i,_ in rm}
    md=etree.Element(CS+"svg",nsmap={None:"http://www.w3.org/2000/svg","xlink":"http://www.w3.org/1999/xlink"})
    md.set("width","%.4f"%(win[2]*96/72)); md.set("height","%.4f"%(win[3]*96/72))
    md.set("viewBox","%.4f %.4f %.4f %.4f"%win)
    g=etree.SubElement(md,CS+"g")
    # deleted texts + the whole legend + every tick label group
    b2=etree.fromstring(etree.tostring(s0)); B.font_attrs(b2)
    for e in b2.iter(CS+"g"):           # the deleted texts, where they used to be
        eid=e.get("id") or ""
        if eid in keep: g.append(etree.fromstring(etree.tostring(e)))
    # where the labels used to be in the source
    for e in b2.iter(CS+"g"):
        eid=e.get("id") or ""
        if eid.startswith(("xtick_","ytick_")) or eid.startswith("legend"):
            g.append(etree.fromstring(etree.tostring(e)))
    # the labels as they are now: tick groups and the legend, taken from the piece
    for e in body.iter(CS+"g"):
        eid=e.get("id") or ""
        if eid.startswith(("xtick_","ytick_")) or eid.startswith("legend"):
            g.append(etree.fromstring(etree.tostring(e)))
    mp=B.build([g],win,idmap,order,os.path.join(OUT,"work","mask.svg"))
    B.render(mp,os.path.join(OUT,"work","mask.png"),600)
    mask=((255-np.asarray(Image.open(os.path.join(OUT,"work","mask.png")).convert("L")).astype(int))>8)
    for _ in range(6):
        d=mask.copy(); d[1:,:]|=mask[:-1,:]; d[:-1,:]|=mask[1:,:]; d[:,1:]|=mask[:,:-1]; d[:,:-1]|=mask[:,1:]; mask=d
    A=np.asarray(Image.open(os.path.join(OUT,"png","S3b_final_600dpi.png")).convert("L")).astype(int)
    Bb=np.asarray(Image.open(os.path.join(OUT,"work","ref.png")).convert("L")).astype(int)
    diff=np.abs(A-Bb)>40
    ok(int((diff&~mask).sum())==0, "%d px differ, all inside text/legend ink"%(int((diff&mask).sum())),
       "outside=%d"%(int((diff&~mask).sum())))

    print("\n"+"="*76); print("D  canvas and margins")
    im=Image.open(os.path.join(OUT,"png","S3b_final_600dpi.png"))
    ok(im.size==(5811,2980), "PNG %dx%d px = 697.326 x 357.616 pt"%(im.size[0],im.size[1]))
    mk=(255-A)>8; rows_=np.where(mk.any(axis=1))[0]; cols_=np.where(mk.any(axis=0))[0]
    clear=min(cols_[0],rows_[0],A.shape[1]-1-cols_[-1],A.shape[0]-1-rows_[-1])/(600/72)
    ok(clear>1.0, "clearance %.2f pt"%(clear))
    print("\nRESULT: %s (%d failures)"%("ALL PASS" if not FAIL else "FAIL",len(FAIL)))
    for f in FAIL: print("  FAILED:",f)
    sys.exit(1 if FAIL else 0)
main()
