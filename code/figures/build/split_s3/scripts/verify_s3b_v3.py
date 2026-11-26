# -*- coding: utf-8 -*-
import io, json, os, re, sys
import numpy as np
from lxml import etree
from PIL import Image
if (getattr(sys.stdout, "encoding", "") or "").lower().replace("-", "") != "utf8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_s3b_v3 as B
CS="{http://www.w3.org/2000/svg}"; XL="{http://www.w3.org/1999/xlink}"
OUT="out_v3"; FAIL=[]
def ok(c,l,d=""):
    print("  %s  %s%s"%("PASS" if c else "FAIL",l,("  "+d) if d else ""))
    if not c: FAIL.append(l)
def txt(e): return re.sub(r"\s+"," ","".join(e.itertext()).replace("\xa0"," ")).strip()
def main():
    meta=json.load(open(os.path.join(OUT,"work","meta.json"),encoding="utf-8"))
    win=tuple(meta["win"])
    src=etree.parse(B.SRC).getroot()
    idmap={e.get("id"):e for e in src.iter() if e.get("id")}
    order={i:k for k,i in enumerate(idmap)}
    got=etree.parse(os.path.join(OUT,"svg","S3b_final.svg")).getroot()
    body=got.find(CS+"g")[0]
    s0=src.find(".//"+CS+"g[@id='figure_1']")

    print("="*76); print("A  exactly three texts removed, everything else kept")
    texts=[txt(t) for t in body.iter(CS+"text")]
    gone=[txt(t) for t in s0.iter(CS+"text")]
    missing=sorted(set(gone)-set(texts)); extra=sorted(set(texts)-set(gone))
    ok(len(missing)==3 and not extra, "removed %s"%missing, "extra=%s"%extra if extra else "")
    ok(all(not any(k in t for t in texts) for k in ("Voltage","RMSE across","noise floor")),
       "no axis-title / noise-floor text left")
    lg=body.find(".//"+CS+"g[@id='legend_1']")
    n_lab=len([g for g in lg if (g.get("id") or "").startswith("text_")]) if lg is not None else 0
    n_samp=len([g for g in lg if (g.get("id") or "").startswith("line2d_")]) if lg is not None else 0
    ok(lg is not None and n_lab==3 and n_samp==3,
       "legend kept: %d samples + %d labels, font %s"%(n_samp,n_lab,
          [t.get("font-size") for t in lg.iter(CS+"text")][:1]))
    fs=sorted({t.get("font-size") for g in body.iter(CS+"g")
               if (g.get("id") or "").startswith(("xtick_","ytick_"))
               for t in g.iter(CS+"text")})
    ok(fs==["7.5"], "tick numbers unchanged: font-size %s"%fs)

    print("\n"+"="*76); print("B  curves / reference lines / axes byte-identical")
    def sig(root):
        out=[]
        for e in root.iter():
            if not isinstance(e.tag,str) or e.tag not in (CS+"path",CS+"use"): continue
            if e.tag==CS+"use":
                out.append(("use",e.get(XL+"href"),e.get("x"),e.get("y"),e.get("style")))
            else:
                out.append(("path",e.get("d"),e.get("style")))
        return out
    a=sig(s0); b=sig(body)
    ok(a==b, "%d path/use elements identical (d + style)"%len(b))

    print("\n"+"="*76); print("C  pixel check: only the three deleted texts differ")
    ref=B.build([etree.fromstring(etree.tostring(s0))],win,idmap,order,
                os.path.join(OUT,"work","ref.svg"))
    B.render(ref,os.path.join(OUT,"work","ref.png"),600)
    # mask = the three removed text groups rendered alone
    probe=etree.fromstring(etree.tostring(s0))
    rm=B.cut(probe)
    keep={i for i,_ in rm}
    maskdoc=etree.Element(CS+"svg",nsmap={None:"http://www.w3.org/2000/svg","xlink":"http://www.w3.org/1999/xlink"})
    maskdoc.set("width","%.4f"%(win[2]*96/72)); maskdoc.set("height","%.4f"%(win[3]*96/72))
    maskdoc.set("viewBox","%.4f %.4f %.4f %.4f"%win)
    g=etree.SubElement(maskdoc,CS+"g")
    body2=etree.fromstring(etree.tostring(s0)); B.font_attrs(body2)
    for e in body2.iter(CS+"g"):
        if e.get("id") in keep: g.append(etree.fromstring(etree.tostring(e)))
    mp=B.build([g],win,idmap,order,os.path.join(OUT,"work","mask.svg"))
    B.render(mp,os.path.join(OUT,"work","mask.png"),600)
    mask=((255-np.asarray(Image.open(os.path.join(OUT,"work","mask.png")).convert("L")).astype(int))>8)
    for _ in range(6):
        d=mask.copy(); d[1:,:]|=mask[:-1,:]; d[:-1,:]|=mask[1:,:]; d[:,1:]|=mask[:,:-1]; d[:,:-1]|=mask[:,1:]; mask=d
    A=np.asarray(Image.open(os.path.join(OUT,"png","S3b_final_600dpi.png")).convert("L")).astype(int)
    Bb=np.asarray(Image.open(os.path.join(OUT,"work","ref.png")).convert("L")).astype(int)
    diff=np.abs(A-Bb)>40
    ok(int((diff&~mask).sum())==0, "%d px differ, all inside the deleted text ink"%(int((diff&mask).sum())),
       "outside=%d"%(int((diff&~mask).sum())))

    print("\n"+"="*76); print("D  margins")
    mk=(255-A)>8; rows=np.where(mk.any(axis=1))[0]; cols=np.where(mk.any(axis=0))[0]
    clear=min(cols[0],rows[0],A.shape[1]-1-cols[-1],A.shape[0]-1-rows[-1])/(600/72)
    ok(clear>1.0,"clearance %.2f pt"%(clear))
    print("\nRESULT: %s (%d failures)"%("ALL PASS" if not FAIL else "FAIL",len(FAIL)))
    for f in FAIL: print("  FAILED:",f)
    sys.exit(1 if FAIL else 0)
main()
