import numpy as np, math, sys
from multiprocessing import Pool
from porsche_split import load, count
ms,XS,YS=load("e30_ref/P_mask_1170.npy"); TW,TH=30.6,30.2; H=YS.max()
def job(a):
    xs_,y=a; lines=[(0.0,x) for x in xs_]
    if y is not None: lines.append((math.pi/2,y))
    n=count(ms,XS,YS,lines,TW,TH); return (n,xs_,y) if n else None
if __name__=="__main__":
    jobs=[((x1,x2,x3),y) for x1 in range(20,36,2) for x2 in range(50,68,2) for x3 in range(80,98,2) for y in (None,)+tuple(range(10,34,3))]
    jobs+=[((x1,x2,x3,x4),y) for x1 in range(22,32,3) for x2 in range(50,64,3) for x3 in range(78,92,3) for x4 in range(88,106,3) if x4>x3+6 for y in (None,)+tuple(range(10,34,4))]
    with Pool(4) as p: r=[x for x in p.map(job,jobs) if x]
    r.sort(key=lambda x:x[0]); print("feasible",len(r)); print(r[:3])
