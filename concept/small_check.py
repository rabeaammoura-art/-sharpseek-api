import numpy as np, math, random
exec(open('sizes_check.py').read().split('if __name__')[0])
import split_search2 as _s
for L in (330,400,450,500):
    G[L]=load(L); ms,XS,YS=G[L]
    one=ok_labels(L,np.zeros(ms.shape,int))
    best=None; r=random.Random(L)
    for _ in range(1500):
        th=math.radians(r.uniform(0,180)); d=r.uniform(8,L/10-8)*math.cos(th)+r.uniform(4,L/20)*math.sin(th)
        lab=((XS*math.cos(th)+YS*math.sin(th))>d).astype(int); n=ok_labels(L,lab)
        if n: best=n; break
    print(f"{L/10:.0f} cm: single piece fits = {bool(one)}; 2-piece straight cut found = {bool(best)}",flush=True)
