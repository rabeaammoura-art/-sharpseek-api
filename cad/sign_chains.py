"""Sally-type sign, step 2: join branches into pen-stroke chains (CHAINS list, ids from sign_branches.py plot),
smooth (env SM, 0.8 approved), groove 5.2 on the original fat letter outline scaled to 250 mm.
Usage: python cad/sign_chains.py BRANCHES.pkl OUT_BASENAME ; then extrude floor 2 + letters 8 minus groove (see WORKLOG 2026-11-24)."""
import pickle,sys,numpy as np, shapely.geometry as g, shapely.ops as so, shapely.affinity as sa, trimesh
from scipy.interpolate import splprep, splev
d=pickle.load(open(sys.argv[1],'rb')); P=d['polys']; B,C,Wz=d['B'],d['C'],d['Wz']
out=sys.argv[2]; W_OUT=250; GROOVE=5.2
import os
CHAINS=[[3],[5],[4,7,0,1,2,0,16],[16,14,13,12,14,10],[11],[6],[9],[17],[8]]
SM=float(os.environ.get('SM','0.8'))
def chain(ids):
  pts=P[ids[0]].copy()
  if len(ids)>1:
    n=P[ids[1]]; e=[np.linalg.norm(pts[-1]-n[0]),np.linalg.norm(pts[-1]-n[-1]),np.linalg.norm(pts[0]-n[0]),np.linalg.norm(pts[0]-n[-1])]
    if np.argmin(e)>=2: pts=pts[::-1]
  for i in ids[1:]:
    n=P[i]
    if np.linalg.norm(pts[-1]-n[-1])<np.linalg.norm(pts[-1]-n[0]): n=n[::-1]
    pts=np.vstack([pts,n[1:]])
  return pts
def smooth(pts,s_per_pt):
  # resample every 0.5 mm then spline-smooth
  L=g.LineString(pts); n=max(int(L.length/0.5),4)
  r=np.array([L.interpolate(t).coords[0] for t in np.linspace(0,L.length,n)])
  r=r[np.r_[True,np.linalg.norm(np.diff(r,axis=0),axis=1)>1e-6]]
  tck,u=splprep(r.T,s=s_per_pt*len(r),k=3); x,y=splev(np.linspace(0,1,len(r)*4),tck); return np.c_[x,y]
k=W_OUT/(B.bounds[2]-B.bounds[0])
L=so.unary_union([C,Wz]); Bk=sa.scale(B,k,k,origin=(0,0)); Lk=sa.scale(L,k,k,origin=(0,0)).buffer(0)
lines=[]
for ids in CHAINS:
  s=SM if len(ids)>1 else 0.02
  lines.append(g.LineString(smooth(chain(ids),s)*k))
G=so.unary_union([l.buffer(GROOVE/2,32) for l in lines]).intersection(Lk.buffer(-1.6))
l1=lines[2].buffer(2.6); l2=lines[3].buffer(2.6)
print('l1-l2 groove gap (need>=1.6):',round(l1.difference(lines[3].buffer(9)).distance(l2.difference(lines[2].buffer(9))),2), 'l1 vs l2 near top:', round(sa.scale(g.LineString(chain([2])),k,k,origin=(0,0)).distance(sa.scale(g.LineString(chain([13])),k,k,origin=(0,0)))-5.2,2))
pickle.dump(dict(lines=lines,G=G,Bk=Bk,Lk=Lk),open(out+'_g.pkl','wb'))
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
fig,A=plt.subplots(figsize=(15,10))
for Q in getattr(Lk,'geoms',[Lk]):
  A.fill(*Q.exterior.xy,color='0.45')
  for i in Q.interiors: A.fill(*i.xy,color='w')
for Q in getattr(G,'geoms',[G]):
  A.fill(*Q.exterior.xy,color='#ffd34d')
  for i in Q.interiors: A.fill(*i.xy,color='0.45')
A.set_aspect('equal');A.axis('off');plt.tight_layout();plt.savefig(out+'.png',dpi=75)
