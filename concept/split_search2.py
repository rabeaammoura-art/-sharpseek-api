import numpy as np, math, json, random
from multiprocessing import Pool
from scipy import ndimage as ndi
from scipy.spatial import ConvexHull
mask=np.load("e30_ref/mask_940.npy"); S=4
H4,W4=mask.shape[0]//S,mask.shape[1]//S
ms=mask[:H4*S,:W4*S].reshape(H4,S,W4,S).any(axis=(1,3))
RR,CC=np.indices(ms.shape); XS=(CC+0.5)*S/10.0; YS=(mask.shape[0]/10.0)-(RR+0.5)*S/10.0   # cm, y up
TW,TH=31.0,30.0
def fits(pts):
    if len(pts)<3: return True
    h=pts[ConvexHull(pts).vertices]
    for a in np.radians(np.arange(0,180,3)):
        c,s=np.cos(a),np.sin(a); u=h[:,0]*c+h[:,1]*s; v=-h[:,0]*s+h[:,1]*c
        if u.max()-u.min()<=TW and v.max()-v.min()<=TH: return True
    return False
def evaluate(lines):
    lab=np.zeros(ms.shape,int)
    for i,(th,d) in enumerate(lines): lab+=((XS*math.cos(th)+YS*math.sin(th))>d).astype(int)<<i
    lab=np.where(ms,lab,-1); N=0; small=0
    for L in np.unique(lab[ms]):
        comp,nc=ndi.label(lab==L,structure=np.ones((3,3)))
        for j in range(1,nc+1):
            c_=comp==j; cells=c_.sum()
            if cells<3: continue
            if cells<40: small+=1
            if not fits(np.stack([XS[c_],YS[c_]],1)): return None
            N+=1
    seam=((lab[:,1:]!=lab[:,:-1])&(lab[:,1:]>=0)&(lab[:,:-1]>=0)).sum()+((lab[1:]!=lab[:-1])&(lab[1:]>=0)&(lab[:-1]>=0)).sum()
    return (N+0.3*small, float(seam), lines)
def trial(a):
    k,seed,cnt=a; r=random.Random(seed); best=None
    for _ in range(cnt):
        lines=[]
        for _i in range(k):
            th=math.radians(r.uniform(0,180)); px_,py_=r.uniform(8,86),r.uniform(5,42)
            lines.append((th,px_*math.cos(th)+py_*math.sin(th)))
        e=evaluate(lines)
        if e and (best is None or e[:2]<best[:2]): best=e
    return best
if __name__=="__main__":
    res=[]
    with Pool(4) as p:
        for k,cnt in ((2,300),(3,500),(4,500),(5,400)):
            rs=[x for x in p.map(trial,[(k,s*11+k,cnt) for s in range(8)]) if x]
            if rs:
                b=min(rs,key=lambda x:x[:2]); res.append((k,b)); print(f"k={k} cuts: score {b[0]:.1f}, material-crossings {b[1]:.0f}",flush=True)
            else: print(f"k={k} cuts: no solution",flush=True)
    b=min(res,key=lambda kb:kb[1][:2]); json.dump({"k":b[0],"score":b[1][0],"lines":b[1][2]},open("e30_ref/split_best.json","w")); print("BEST",b[0],b[1][0],flush=True)
