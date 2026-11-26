# -*- coding: utf-8 -*-
"""Verification for S7a ... S7f."""
import io, json, os, re, sys
import numpy as np
from lxml import etree
from PIL import Image
if (getattr(sys.stdout,"encoding","") or "").lower().replace("-","")!="utf8":
    sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8")
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import split_s7 as S
CS="{http://www.w3.org/2000/svg}"; XL="{http://www.w3.org/1999/xlink}"
OUT="out"; FAIL=[]
def ok(c,l,d=""):
    print("  %s  %s%s"%("PASS" if c else "FAIL",l,("  "+d) if d else ""))
    if not c: FAIL.append(l)
def main():
    meta=json.load(open(os.path.join(OUT,"work","meta.json"),encoding="utf-8"))
    src=etree.parse(S.SRC).getroot()
    idmap={e.get("id"):e for e in src.iter() if e.get("id")}
    order={i:k for k,i in enumerate(idmap)}
    CW,CH=meta["canvas"]

    print("="*74); print("A  every label is an outline path, no <text> left")
    for p in meta["pieces"]:
        root=etree.parse(p["svg"]).getroot()
        n_text=len(list(root.iter(CS+"text")))
        n_glyph=len([g for g in root.iter(CS+"g") if g.get("class")=="glyphs"])
        ok(n_text==0 and n_glyph>=10, "%-4s %d <text>, %d outline labels"%(p["name"],n_text,n_glyph))

    print("\n"+"="*74); print("B  identical canvas across the six")
    offs=[]
    for p in meta["pieces"]:
        vb=[float(v) for v in etree.parse(p["svg"]).getroot().get("viewBox").split()]
        ax=idmap[p["axes"]]
        cl=[i for i in S.ref_ids(ax) if i in idmap and idmap[i].tag==CS+"clipPath"]
        rect=idmap[cl[0]].find(CS+"rect")
        bx=[float(rect.get(k)) for k in ("x","y","width","height")]
        offs.append((round(bx[0]-vb[0],4),round(bx[1]-vb[1],4),vb[2],vb[3],bx[2],bx[3]))
    dev=max(max(abs(a[i]-b[i]) for i in range(6)) for a in offs for b in offs)
    ok(dev<0.005 and abs(offs[0][2]-CW)<1e-3 and abs(offs[0][3]-CH)<1e-3,
       "canvas %.3f x %.3f, plot %.3f x %.3f, max dev %.4f"%(offs[0][2],offs[0][3],offs[0][4],offs[0][5],dev))

    print("\n"+"="*74); print("C  curves / frame / reference line byte-identical")
    def sig(root):
        out=[]
        for e in root.iter():
            if not isinstance(e.tag,str) or e.tag not in (CS+"path",CS+"use"): continue
            p=e.getparent(); bad=False
            while p is not None:
                pid=p.get("id") or ""
                if pid.startswith(("text_","legend")) or p.get("class")=="glyphs"                    or p.tag==CS+"defs":
                    bad=True; break
                p=p.getparent()
            if bad: continue
            out.append(("use",e.get(XL+"href"),e.get("x"),e.get("y"),e.get("style")) if e.tag==CS+"use"
                       else ("path",e.get("d"),e.get("style")))
        return out
    for p in meta["pieces"]:
        a0=sig(idmap[p["axes"]]); a1=sig(etree.parse(p["svg"]).getroot())
        ok(a0==a1, "%-4s %d data paths identical"%(p["name"],len(a1)))

    print("\n"+"="*74); print("D  pixel check: only text/legend ink differs from the source")
    for p in meta["pieces"]:
        win=tuple(p["win"])
        ref=etree.fromstring(etree.tostring(src.find(".//"+CS+"g[@id='figure_1']")))
        S.cut(ref)                       # same deletions, but keep <text>
        rp=S.build([ref],win,idmap,order,os.path.join(OUT,"work",p["name"]+"_ref.svg"))
        S.render(rp,os.path.join(OUT,"work",p["name"]+"_ref.png"),600)
        md=etree.Element(CS+"svg",nsmap={None:"http://www.w3.org/2000/svg","xlink":"http://www.w3.org/1999/xlink"})
        md.set("width","%.4f"%(win[2]*96/72)); md.set("height","%.4f"%(win[3]*96/72))
        md.set("viewBox","%.4f %.4f %.4f %.4f"%win)
        g=etree.SubElement(md,CS+"g")
        probe=etree.fromstring(etree.tostring(src.find(".//"+CS+"g[@id='figure_1']")))
        rm=S.cut(probe)
        keep={i for i,_ in rm}
        b2=etree.fromstring(etree.tostring(src.find(".//"+CS+"g[@id='figure_1']")))
        for e in b2.iter(CS+"g"):
            eid=e.get("id") or ""
            if eid in keep or eid.startswith("legend"):
                g.append(etree.fromstring(etree.tostring(e)))
        for root in (etree.parse(p["svg"]).getroot(),):
            for e in root.iter(CS+"g"):
                if (e.get("id") or "").startswith("legend"):
                    g.append(etree.fromstring(etree.tostring(e)))
        for root in (etree.parse(p["svg"]).getroot(),):
            for e in root.iter(CS+"g"):
                if e.get("class")=="glyphs":
                    g.append(etree.fromstring(etree.tostring(e)))
        mp=S.build([g],win,idmap,order,os.path.join(OUT,"work",p["name"]+"_mask.svg"))
        S.render(mp,os.path.join(OUT,"work",p["name"]+"_mask.png"),600)
        mask=((255-np.asarray(Image.open(os.path.join(OUT,"work",p["name"]+"_mask.png")).convert("L")).astype(int))>8)
        for _ in range(6):
            d=mask.copy(); d[1:,:]|=mask[:-1,:]; d[:-1,:]|=mask[1:,:]; d[:,1:]|=mask[:,:-1]; d[:,:-1]|=mask[:,1:]; mask=d
        A=np.asarray(Image.open(p["png"]).convert("L")).astype(int)
        B=np.asarray(Image.open(os.path.join(OUT,"work",p["name"]+"_ref.png")).convert("L")).astype(int)
        diff=np.abs(A-B)>40
        ok(int((diff&~mask).sum())==0,"%-4s %d px differ, all inside text ink"%(p["name"],int((diff&mask).sum())),
           "outside=%d"%(int((diff&~mask).sum())))

    print("\n"+"="*74); print("E  margins")
    for p in meta["pieces"]:
        im=np.asarray(Image.open(p["png"]).convert("L")).astype(int); mk=(255-im)>8
        rows=np.where(mk.any(axis=1))[0]; cols=np.where(mk.any(axis=0))[0]
        clear=min(cols[0],rows[0],im.shape[1]-1-cols[-1],im.shape[0]-1-rows[-1])/(600/72)
        ok(clear>1.0,"%-4s clearance %.2f pt"%(p["name"],clear))
    print("\nRESULT: %s (%d failures)"%("ALL PASS" if not FAIL else "FAIL",len(FAIL)))
    for f in FAIL: print("  FAILED:",f)
    sys.exit(1 if FAIL else 0)
main()
