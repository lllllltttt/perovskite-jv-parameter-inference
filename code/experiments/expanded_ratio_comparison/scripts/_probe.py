import numpy as np, pandas as pd, hashlib, json, os
NEW = r"E:\project\work1\20261021\JV_database_9D_interface_lifetimes-newratio.csv"
OLD = r"E:\project\work1\data\JV_database_9D_interface_lifetimes-2.csv"
PARAMS = ["mu_n_pvk","mu_p_pvk","tau_n_pvk","tau_p_pvk","Nc_eff_pvk","Nv_eff_pvk","tau_ETL","tau_HTL","rad_c"]

def load(p):
    df = pd.read_csv(p)
    return df

new = load(NEW); old = load(OLD)
print("new", new.shape, "old", old.shape)
print("cols equal:", list(new.columns)==list(old.columns))
for nm,df in (("new",new),("old",old)):
    jc=[c for c in df.columns if c.startswith("J_")]
    P=df[PARAMS].to_numpy(float); J=df[jc].to_numpy(float)
    print(f"--- {nm}: Jcols={len(jc)} first={jc[0]} last={jc[-1]}")
    print("  ID dtype",df.Sample_ID.dtype,"unique",df.Sample_ID.is_unique,"n",len(df),
          "min",df.Sample_ID.min(),"max",df.Sample_ID.max())
    print("  finite J",np.isfinite(J).all(),"finite P",np.isfinite(P).all(),"pos P",(P>0).all())
    print("  J range",J.min(),J.max(),"J[:,0] range",J[:,0].min(),J[:,0].max())
    print("  param ranges")
    for i,c in enumerate(PARAMS):
        print("   %-10s %.6e %.6e"%(c,P[:,i].min(),P[:,i].max()))
    # filter rules
    m1=J[:,0]>0; m2=(np.diff(np.sign(J),axis=1)<0).any(axis=1); m3=np.isfinite(J).all(axis=1); m4=(np.diff(J,axis=1)<=0.2).all(axis=1)
    print("  filter pass:",(m1&m2&m3&m4).sum(),"of",len(df)," m1",m1.sum(),"m2",m2.sum(),"m3",m3.sum(),"m4",m4.sum())
    # exact duplicate parameter vectors
    from collections import Counter
    key=[tuple(r) for r in P]
    c=Counter(key); print("  dup param vectors:",sum(v-1 for v in c.values() if v>1), "groups",sum(1 for v in c.values() if v>1))
    # duplicate J rows
    h=[hashlib.md5(np.ascontiguousarray(r,dtype=np.float64).tobytes()).hexdigest() for r in J]
    ch=Counter(h); print("  dup J rows:",sum(v-1 for v in ch.values() if v>1))
