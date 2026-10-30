import numpy as np, math, sys
from multiprocessing import Pool
from porsche_split import load, count
ms,XS,YS=load("e30_ref/P_mask_900.npy"); TW,TH=float(sys.argv[1]),float(sys.argv[2]); H=YS.max()
def job(a):
    xs_,y,tilt=a; lines=[]
    for x in xs_: lines.append((math.radians(tilt),x*math.cos(math.radians(tilt))+(H/2)*math.sin(math.radians(tilt))))
    if y is not None: lines.append((math.pi/2,y))
    n=count(ms,XS,YS,lines,TW,TH)
    return (n,xs_,y,tilt) if n else None
if __name__=="__main__":
    jobs=[((x1,x2),y,t) for x1 in range(22,42,2) for x2 in range(50,72,2) for y in (None,)+tuple(range(8,32,2)) for t in (0,)]
    jobs+=[((x1,x2,x3),y,0) for x1 in range(20,36,3) for x2 in range(40,60,3) for x3 in range(60,82,3) for y in (None,)+tuple(range(8,30,3))]
    with Pool(4) as p: r=[x for x in p.map(job,jobs) if x]
    r.sort(key=lambda x:x[0]); print("limits",TW,TH,"| feasible found:",len(r)); print(r[:3])
