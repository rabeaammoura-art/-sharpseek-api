import numpy as np, math, itertools, sys
from multiprocessing import Pool
from scipy.spatial import ConvexHull
S=4; TW,TH=30.6,30.2
G={}
def load(L):
    mask=np.load(f"e30_ref/mask_{L}.npy"); H4,W4=mask.shape[0]//S,mask.shape[1]//S
    ms=mask[:H4*S,:W4*S].reshape(H4,S,W4,S).any(axis=(1,3)); RR,CC=np.indices(ms.shape)
    return ms,(CC+0.5)*S/10.0,(mask.shape[0]/10.0)-(RR+0.5)*S/10.0
def fits(pts):
    if len(pts)<3: return True
    try: h=pts[ConvexHull(pts).vertices]
    except Exception: h=pts
    for a in np.radians(np.arange(0,180,3)):
        c,s=np.cos(a),np.sin(a); u=h[:,0]*c+h[:,1]*s; v=-h[:,0]*s+h[:,1]*c
        if u.max()-u.min()<=TW and v.max()-v.min()<=TH: return True
    return False
def ok_labels(L,lab):
    ms,XS,YS=G[L]; n=0
    for l in np.unique(lab[ms]):
        c_=ms&(lab==l)
        if c_.sum()<3: continue
        n+=1
        if not fits(np.stack([XS[c_],YS[c_]],1)): return 0
    return n
def f4(a):
    L,cx,cy=a; ms,XS,YS=G[L]
    for t1 in range(-40,41,10):
        for t2 in range(-40,41,10):
            a1=math.radians(t1); a2=math.radians(90+t2)
            lab=(((XS-cx)*math.cos(a1)+(YS-cy)*math.sin(a1))>0).astype(int)+2*(((XS-cx)*math.cos(a2)+(YS-cy)*math.sin(a2))>0).astype(int)
            n=ok_labels(L,lab)
            if n: return (n,("cross",cx,cy,t1,t2))
def fv(a):                       # vertical cuts xs + one horizontal cut y
    L,xs_,y=a; ms,XS,YS=G[L]; lab=(YS>y).astype(int)*8
    for i,x in enumerate(xs_): lab=lab+(XS>x).astype(int)
    n=ok_labels(L,lab)
    if n: return (n,("grid",xs_,y))
def best(L,jobs,fn):
    with Pool(4) as p: r=[x for x in p.map(fn,jobs) if x]
    return min(r,key=lambda x:x[0]) if r else None
if __name__=="__main__":
    for L in (620,660,700,740,780,820,860,900,940):
        G[L]=load(L); res=[]
        r=best(L,[(L,cx,cy) for cx in range(16,80,4) for cy in range(8,40,4)],f4)
        if r: res.append(r)
        r=best(L,[(L,(x1,x2),y) for x1 in range(18,32,2) for x2 in range(36,64,2) for y in range(12,34,2)],fv)
        if r: res.append(r)
        r=best(L,[(L,(x1,x2,x3),y) for x1 in range(18,31,3) for x2 in range(38,62,3) for x3 in range(56,90,3) if x1<x2<x3 for y in range(12,34,3)],fv)
        if r: res.append(r)
        b=min(res,key=lambda x:x[0]) if res else None
        print(f"{L/10:.0f} cm -> {b[0] if b else '>8'} pieces  {b[1] if b else ''}",flush=True)
