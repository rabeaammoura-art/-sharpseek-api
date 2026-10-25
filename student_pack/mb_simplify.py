import sys, numpy as np, cv2, pickle
from PIL import Image
from shapely import affinity
sys.path.insert(0,'/home/user/-sharpseek-api/student_pack')
from trace import mask_to_geom
blur,thr,close,hole,opn,simp=map(float,sys.argv[1:7]); out=sys.argv[7]
im=np.array(Image.open('/root/.claude/uploads/be9cc890-d9f9-58e5-abf5-b88979c7d61a/b5d49ff4-image.png').convert('L'))[150:395,460:1070]
U=4; up=cv2.resize(im,None,fx=U,fy=U,interpolation=cv2.INTER_CUBIC)
up=cv2.GaussianBlur(up,(0,0),blur)
m=(up<thr).astype(np.uint8)
k=lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*int(r)+1,2*int(r)+1))
m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,k(close))
inv=1-m; n,lab,st,_=cv2.connectedComponentsWithStats(inv,connectivity=4)
for i in range(1,n):
    if st[i,4]<hole: m[lab==i]=1
m=cv2.morphologyEx(m,cv2.MORPH_OPEN,k(opn))
n,lab,st,_=cv2.connectedComponentsWithStats(m,connectivity=8)
keep=np.zeros_like(m)
for i in range(1,n):
    if st[i,4]>=3000: keep|=(lab==i).astype(np.uint8)
g=mask_to_geom(keep.astype(bool),1.0,keep.shape[0]); b=g.bounds
g=affinity.translate(g,-b[0],-b[1]).simplify(simp)
pickle.dump(g,open('/tmp/claude-0/mb/mb_geom2.pkl','wb'))
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch; from matplotlib.path import Path
fig,ax=plt.subplots(figsize=(12,5.2),dpi=110)
for p in (g.geoms if hasattr(g,'geoms') else [g]):
    v=list(p.exterior.coords); c=[1]+[2]*(len(v)-2)+[79]
    for i in p.interiors:
        q=list(i.coords); v+=q; c+=[1]+[2]*(len(q)-2)+[79]
    ax.add_patch(PathPatch(Path(v,c),fc='#111',ec='none'))
ax.set_xlim(0,g.bounds[2]);ax.set_ylim(0,g.bounds[3]);ax.set_aspect('equal');ax.axis('off')
fig.savefig(out,bbox_inches='tight',facecolor='white'); print('comps',len(g.geoms) if hasattr(g,'geoms') else 1)
