import sys, math, re
import numpy as np
from PIL import Image, ImageDraw
sys.argv=['x']; exec(open('make_e30.py').read().split("wall=")[0])   # reuse projected polylines P
# rasterise projected lines, thicken, fill -> silhouette mask
pts=[[(x*sc+ox,y*sc+oy) for x,y in pl] for pl in P]
S=1; W2,H2=int(W*S),int(H*S)
im=Image.new('L',(W2,H2),0); d=ImageDraw.Draw(im)
for pl in pts: d.line([(x*S,y*S) for x,y in pl],fill=255,width=5)
m=np.array(im)>0
# fill holes: flood fill outside
from collections import deque
out=np.zeros_like(m); q=deque([(0,0)]); out[0,0]=True
while q:
    y,x=q.popleft()
    for dy,dx in((1,0),(-1,0),(0,1),(0,-1)):
        ny,nx=y+dy,x+dx
        if 0<=ny<H2 and 0<=nx<W2 and not out[ny,nx] and not m[ny,nx]: out[ny,nx]=True; q.append((ny,nx))
sil=~out
ys,xs=np.where(sil); x0,x1,y0,y1=xs.min(),xs.max(),ys.min(),ys.max()
sil=sil[y0:y1+1,x0:x1+1]
h,w=sil.shape; print("bbox ratio w:h = %.2f"%(w/h))
for L_cm in (100,95,90):
    cm=L_cm/w                    # cm per pixel
    H_cm=h*cm; area=sil.sum()*cm*cm/1e4
    print(f"\nlength {L_cm} cm -> height {H_cm:.0f} cm, silhouette area {area:.2f} m2")
    for T in (31,30):
        tp=int(T/cm)
        best=None
        for h1 in range(max(1,h-tp),min(tp,h-1)+1,3):      # bottom band height h1 (<=tp), top band h-h1 (<=tp)
            n=0
            for band in (sil[h-h1:], sil[:h-h1]):
                cols=np.where(band.any(axis=0))[0]
                if len(cols)==0: continue
                # greedy cover occupied columns with tiles of width tp
                i=0; c=0
                occ=band.any(axis=0)
                x=0
                while x<w:
                    if occ[x]: c+=1; x+=tp
                    else: x+=1
                n+=c
            if best is None or n<best[0]: best=(n,h1*cm)
        print(f"  tile {T} cm: min pieces with 2 bands = {best[0]} (bottom band {best[1]:.0f} cm)")

print("\n--- vertical strips, each piece may be rotated on the bed ---")
import itertools
def fits(piece,cm,Tw=31,Th=30):
    ys,xs=np.where(piece)
    if len(xs)==0: return True
    P=np.stack([xs,ys],1)*cm
    for a in np.radians(np.arange(0,180,3)):
        c,s=np.cos(a),np.sin(a)
        u=P[:,0]*c+P[:,1]*s; v=-P[:,0]*s+P[:,1]*c
        if (u.max()-u.min()<=Tw and v.max()-v.min()<=Th) or (u.max()-u.min()<=Th and v.max()-v.min()<=Tw): return True
    return False
for L_cm in (100,):
    cm=L_cm/w
    for k in (3,4,5):
        found=None
        step=max(1,int(w/50))
        cuts_range=range(step,w,step)
        for cuts in itertools.combinations(cuts_range,k-1):
            edges=(0,)+cuts+(w,)
            if all(fits(sil[:,edges[i]:edges[i+1]],cm) for i in range(k)):
                found=[round(e*cm) for e in edges]; break
        print(f"{k} vertical strips (rotation allowed):", found if found else "no fit")
