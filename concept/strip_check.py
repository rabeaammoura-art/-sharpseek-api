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
h,w=sil.shape

sil_s=sil[::10,::10]; hs,ws=sil_s.shape; cm=100/ws
def fits(piece,Tw=31,Th=30):
    ys,xs=np.where(piece)
    if len(xs)==0: return True
    P=np.stack([xs,ys],1)*cm
    for a in np.radians(np.arange(0,180,5)):
        c,s_=np.cos(a),np.sin(a)
        u=P[:,0]*c+P[:,1]*s_; v=-P[:,0]*s_+P[:,1]*c
        du,dv=u.max()-u.min(),v.max()-v.min()
        if (du<=Tw and dv<=Th) or (du<=Th and dv<=Tw): return True
    return False
pos=list(range(0,ws,3))+[ws]; n=len(pos)
ok=[[False]*n for _ in range(n)]
for i in range(n):
    for j in range(i+1,n):
        ok[i][j]=fits(sil_s[:,pos[i]:pos[j]])
        if not ok[i][j]: break
INF=99
dp=[INF]*n; dp[0]=0; prev=[None]*n
for j in range(1,n):
    for i in range(j):
        if ok[i][j] and dp[i]+1<dp[j]: dp[j]=dp[i]+1; prev[j]=i
j=n-1; cuts=[]
while j: cuts.append(round(pos[j]*cm)); j=prev[j]
print("min vertical strips (rotation allowed):",dp[n-1],"edges at cm:",sorted(cuts))
