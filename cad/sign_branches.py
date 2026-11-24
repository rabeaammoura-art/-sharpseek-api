"""Sally-type sign, step 1: medial-axis branches of the original LED channel -> pickle + numbered plot.
Usage: python cad/sign_branches.py IN.3mf OUT.pkl OUT.png"""
import trimesh,sys,numpy as np, shapely.geometry as g, shapely.ops as so, pickle
from scipy.ndimage import distance_transform_edt, convolve
from PIL import Image, ImageDraw
from skimage.morphology import skeletonize, opening, disk
src=sys.argv[1]
m=list(trimesh.load(src).geometry.values())[0]
def sec(z):
  r=g.Polygon()
  for e in m.section([0,0,1],[0,0,z]).discrete: r=r.symmetric_difference(g.Polygon(e[:,:2]).buffer(0))
  return r
B=sec(1); Wz=sec(5); C=B.difference(Wz)
px=0.06; x0,y0,x1,y1=C.bounds; Wd=int((x1-x0)/px)+6; H=int((y1-y0)/px)+6
im=Image.new('1',(Wd,H),0); d=ImageDraw.Draw(im)
for p in C.geoms:
  d.polygon([((x-x0)/px+3,(y-y0)/px+3) for x,y in p.exterior.coords],fill=1)
  for i in p.interiors: d.polygon([((x-x0)/px+3,(y-y0)/px+3) for x,y in i.coords],fill=0)
a=opening(np.array(im),disk(2))
from skimage.morphology import medial_axis
sk=medial_axis(np.ascontiguousarray(a,dtype=bool))
# prune spurs: iteratively remove endpoints N times, then regrow? simple: compute branches and drop short end-branches
def nb(sk):
  k=np.ones((3,3));k[1,1]=0; return convolve(sk.astype(int),k,mode='constant')*sk
import networkx as nx
ys,xs=np.nonzero(sk); G=nx.Graph(); S=set(zip(ys,xs))
for y,x in S:
  for dy in(-1,0,1):
    for dx in(-1,0,1):
      if (dy or dx) and (y+dy,x+dx) in S: G.add_edge((y,x),(y+dy,x+dx))
# collapse 4-cliques artifacts: use degree on simplified
def branches(G):
  nodes=[n for n in G if G.degree(n)!=2]; seen=set(); out=[]
  for n in nodes:
    for nb_ in G[n]:
      if (n,nb_) in seen: continue
      path=[n,nb_]; prev,cur=n,nb_
      while G.degree(cur)==2:
        nx_=[q for q in G[cur] if q!=prev][0]; prev,cur=cur,nx_; path.append(cur)
      seen.add((path[-1],path[-2])); seen.add((n,nb_)); out.append(path)
  return out
toW=lambda p:((p[1]-3)*px+x0,(p[0]-3)*px+y0)
# prune short end spurs repeatedly
for it in range(5):
  br=branches(G); rem=0
  for p in br:
    L=len(p)*px
    ends=[G.degree(p[0])==1,G.degree(p[-1])==1]
    if any(ends) and not all(ends) and L<4.0:
      for q in p[:-1] if ends[0] else p[1:]:
        if G.degree(q)<=2 or q in (p[0],p[-1]): 
          if q in G and G.degree(q)<=2: G.remove_node(q); rem+=1
  if not rem: break
br=[b for b in branches(G) if len(b)>3]
polys=[np.array([toW(q) for q in b]) for b in br]
pickle.dump(dict(polys=polys,B=B,C=C,Wz=Wz),open(sys.argv[2],'wb'))
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
fig,ax=plt.subplots(figsize=(20,13))
for P in C.geoms:
  ax.plot(*P.exterior.xy,'0.6',lw=.5)
  for i in P.interiors: ax.plot(*i.xy,'0.6',lw=.5)
for i,p in enumerate(polys):
  ax.plot(p[:,0],p[:,1],lw=1.5); mid=p[len(p)//2]; ax.text(mid[0],mid[1],str(i),fontsize=11,color='k',weight='bold')
ax.set_aspect('equal');plt.tight_layout();plt.savefig(sys.argv[3],dpi=60)
print(len(polys),[round(len(p)*px,1) for p in polys])
