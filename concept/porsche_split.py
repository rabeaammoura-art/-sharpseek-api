import numpy as np, math, itertools, random, sys
from scipy.spatial import ConvexHull
S=4
def load(path):
    mask=np.load(path); H4,W4=mask.shape[0]//S,mask.shape[1]//S
    ms=mask[:H4*S,:W4*S].reshape(H4,S,W4,S).any(axis=(1,3)); RR,CC=np.indices(ms.shape)
    return ms,(CC+0.5)*S/10.0,(mask.shape[0]/10.0)-(RR+0.5)*S/10.0
def fits(pts,TW,TH):
    if len(pts)<3: return True
    try: h=pts[ConvexHull(pts).vertices]
    except Exception: h=pts
    for a in np.radians(np.arange(0,180,3)):
        c,s=np.cos(a),np.sin(a); u=h[:,0]*c+h[:,1]*s; v=-h[:,0]*s+h[:,1]*c
        if u.max()-u.min()<=TW and v.max()-v.min()<=TH: return True
    return False
def count(ms,XS,YS,lines,TW,TH):
    lab=np.zeros(ms.shape,int)
    for i,(th,d) in enumerate(lines): lab+=((XS*math.cos(th)+YS*math.sin(th))>d).astype(int)<<i
    n=0
    for l in np.unique(lab[ms]):
        c=ms&(lab==l)
        if c.sum()<3: continue
        n+=1
        if not fits(np.stack([XS[c],YS[c]],1),TW,TH): return 0
    return n
if __name__=="__main__":
    ms,XS,YS=load(sys.argv[1]); TW,TH=float(sys.argv[2]),float(sys.argv[3]); W=XS.max()
    print("limits",TW,TH)
    for name,cands in (
      ("2 pieces (1 straight cut)",[[(math.radians(a),o*math.cos(math.radians(a))+ (YS.max()/2)*math.sin(math.radians(a)))] for a in range(-60,61,5) for o in np.arange(15,W-15,1.0)]),
      ("3 pieces (2 cuts)",[[(math.radians(a1),x1*math.cos(math.radians(a1))+(YS.max()/2)*math.sin(math.radians(a1))),(math.radians(a2),x2*math.cos(math.radians(a2))+(YS.max()/2)*math.sin(math.radians(a2)))] for a1 in range(-30,31,10) for a2 in range(-30,31,10) for x1 in np.arange(20,50,1.5) for x2 in np.arange(50,80,1.5)]),
    ):
        hit=None
        for ln in cands:
            if count(ms,XS,YS,ln,TW,TH): hit=ln; break
        print(name,"->", "possible" if hit else "NOT possible", ([(round(math.degrees(t)),round(d,1)) for t,d in hit] if hit else ""),flush=True)
