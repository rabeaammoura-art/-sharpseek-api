"""Search for the fewest pieces (straight cuts) so each piece fits the H2D bed (31x30 cm, rotation allowed)."""
import numpy as np, math, sys, random, json
from multiprocessing import Pool
from scipy import ndimage as ndi
from scipy.spatial import ConvexHull
exec(open('pieces_e30.py').read().split("# cm coords (Y up)")[0].replace("from build123d import BuildSketch, BuildPart, Polygon, extrude, export_stl, Plane",""))
S=5                                              # downsample: 5 mm per cell
ms=m[::S,::S]; Hs,Ws=ms.shape
RR,CC=np.indices(ms.shape); XS=CC*S/10.0; YS=((Hp-1)-RR*S)/10.0   # cm, y up
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
    for i,(th,d) in enumerate(lines):
        n=(math.cos(th),math.sin(th)); lab+=((XS*n[0]+YS*n[1])>d).astype(int)<<i
    lab=np.where(ms,lab,-1)
    N=0; ok=True; small=0
    for L in np.unique(lab[ms]):
        comp,nc=ndi.label(lab==L)
        for j in range(1,nc+1):
            cm_=comp==j; area=cm_.sum()*(S/10)**2
            if area<8: continue                     # ignore specks
            if area<40: small+=1
            pts=np.stack([XS[cm_],YS[cm_]],1)
            if not fits(pts): ok=False
            N+=1
    if not ok: return None
    seam=((lab[:,1:]!=lab[:,:-1])&(lab[:,1:]>=0)&(lab[:,:-1]>=0)).sum()+((lab[1:]!=lab[:-1])&(lab[1:]>=0)&(lab[:-1]>=0)).sum()
    return (N+0.5*small, seam*S/10, lines)
def trial(args):
    k,seed,count=args; rnd=random.Random(seed); best=None
    for _ in range(count):
        lines=[]
        for _i in range(k):
            th=math.radians(rnd.uniform(0,180)); 
            px_,py_=rnd.uniform(8,86),rnd.uniform(5,40)
            lines.append((th,px_*math.cos(th)+py_*math.sin(th)))
        r=evaluate(lines)
        if r and (best is None or (r[0],r[1])<(best[0],best[1])): best=r
    return best
if __name__=="__main__":
    results=[]
    with Pool(4) as p:
        for k,cnt in ((3,600),(4,600),(5,500)):
            jobs=[(k,s*7+k,cnt) for s in range(8)]
            rs=[r for r in p.map(trial,jobs) if r]
            if rs:
                b=min(rs,key=lambda r:(r[0],r[1])); results.append((k,b)); print(f"k={k} cuts: best pieces={b[0]}, seam={b[1]:.0f} cm",flush=True)
            else: print(f"k={k} cuts: no solution found",flush=True)
    best=min(results,key=lambda kb:(kb[1][0],kb[1][1]))
    json.dump({"k":best[0],"score":best[1][0],"seam":best[1][1],"lines":best[1][2]},open("split_best.json","w"))
    print("BEST",best[0],best[1][0],best[1][1],flush=True)
