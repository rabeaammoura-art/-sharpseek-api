import sys, numpy as np, cv2, pickle
from PIL import Image
from shapely import affinity
from skimage.morphology import skeletonize
sys.path.insert(0,'/home/user/-sharpseek-api/student_pack')
from trace import mask_to_geom
blur,thr,close,rad,out=float(sys.argv[1]),float(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4]),sys.argv[5]
im=np.array(Image.open('/root/.claude/uploads/be9cc890-d9f9-58e5-abf5-b88979c7d61a/b5d49ff4-image.png').convert('L'))[150:395,460:1070]
up=cv2.resize(im,None,fx=4,fy=4,interpolation=cv2.INTER_CUBIC); up=cv2.GaussianBlur(up,(0,0),blur)
k=lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*r+1,2*r+1))
m=(up<thr).astype(np.uint8)
m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,k(close))
dt=cv2.distanceTransform(m,cv2.DIST_L2,5); sk=((m>0)&~(dt>rad)).astype(np.uint8)
# drop short skeleton fragments
n,lab,st,_=cv2.connectedComponentsWithStats(sk,connectivity=8)
for i in range(1,n):
    if st[i,4]<3000: sk[lab==i]=0
d=cv2.morphologyEx(sk,cv2.MORPH_OPEN,k(3))
g=mask_to_geom(d.astype(bool),1.0,d.shape[0]); b=g.bounds
g=affinity.translate(g,-b[0],-b[1]).simplify(1.0)
pickle.dump(g,open('/tmp/claude-0/mb/mb_geom4.pkl','wb'))
print('area frac',g.area/(g.bounds[2]*g.bounds[3]), 'parts',len(g.geoms) if hasattr(g,'geoms') else 1)
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch; from matplotlib.path import Path
fig,ax=plt.subplots(figsize=(12,5.2),dpi=110)
for p in (g.geoms if hasattr(g,'geoms') else [g]):
    v=list(p.exterior.coords); c=[1]+[2]*(len(v)-2)+[79]
    for i in p.interiors:
        q=list(i.coords); v+=q; c+=[1]+[2]*(len(q)-2)+[79]
    ax.add_patch(PathPatch(Path(v,c),fc='#111',ec='none'))
ax.set_xlim(0,g.bounds[2]);ax.set_ylim(0,g.bounds[3]);ax.set_aspect('equal');ax.axis('off')
fig.savefig(out,bbox_inches='tight',facecolor='white')
