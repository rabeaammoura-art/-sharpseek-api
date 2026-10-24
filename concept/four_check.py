import numpy as np, math, sys, itertools
from multiprocessing import Pool
from scipy.spatial import ConvexHull
S=4; TW,TH=31.5,31.0
def load(L):
    mask=np.load(f"e30_ref/mask_{L}.npy"); H4,W4=mask.shape[0]//S,mask.shape[1]//S
    ms=mask[:H4*S,:W4*S].reshape(H4,S,W4,S).any(axis=(1,3))
    RR,CC=np.indices(ms.shape); return ms,(CC+0.5)*S/10.0,(mask.shape[0]/10.0)-(RR+0.5)*S/10.0
def fits(pts):
    if len(pts)<3: return True
    try: h=pts[ConvexHull(pts).vertices]
    except Exception: h=pts
    for a in np.radians(np.arange(0,180,3)):
        c,s=np.cos(a),np.sin(a); u=h[:,0]*c+h[:,1]*s; v=-h[:,0]*s+h[:,1]*c
        if u.max()-u.min()<=TW and v.max()-v.min()<=TH: return True
    return False
def job(args):
    L,cx,cy=args; ms,XS,YS=G[L]; best=None
    for t1 in range(-40,41,10):                      # near-vertical cut (deg from vertical)
        for t2 in range(-40,41,10):                  # near-horizontal cut
            a1=math.radians(t1); a2=math.radians(90+t2)
            n1=(math.cos(a1),math.sin(a1)); n2=(math.cos(a2),math.sin(a2))
            lab=(((XS-cx)*n1[0]+(YS-cy)*n1[1])>0).astype(int)+2*(((XS-cx)*n2[0]+(YS-cy)*n2[1])>0).astype(int)
            ok=True; N=0
            for l in range(4):
                c_=ms&(lab==l)
                if c_.sum()<3: continue
                N+=1
                if not fits(np.stack([XS[c_],YS[c_]],1)): ok=False; break
            if ok: return (L,cx,cy,t1,t2,N)
    return None
G={}
if __name__=="__main__":
    for L in (740,700,660,620):
        G[L]=load(L)
        with Pool(4) as p:
            r=[x for x in p.map(job,[(L,cx,cy) for cx in range(16,80,3) for cy in range(8,40,3)]) if x]
        print(f"length {L/10:.0f} cm: ", "4 pieces possible: "+str(r[0]) if r else "no 4-piece cut found",flush=True)
