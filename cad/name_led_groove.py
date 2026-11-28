"""Name-on-letter piece (S block + raised cursive name): pen-stroke LED groove in the name. CHAINS = ids from cad/sign_branches.py style plot of the name section (z=27).
Usage: python cad/name_led_groove.py BRANCHES.pkl OUT_BASENAME WIDTH_MM (3 approved); name grown to width+2.4 where needed."""
import pickle,sys,os,numpy as np, shapely.geometry as g, shapely.ops as so
from scipy.interpolate import splprep, splev
d=pickle.load(open(sys.argv[1],'rb')); P=d['polys']; T=d['C']
out=sys.argv[2]; W=float(sys.argv[3]); WALL=1.2; SM=float(os.environ.get('SM','0.6'))
CHAINS=[[36,34,33],[16,17],[16,18,12,13],[24,2,1,21,23,1,3,5,6,7,5,4,31],[31,32,39,41],[41,20,19]]
def chain(ids):
  pts=P[ids[0]].copy()
  n=P[ids[1]]
  e=[min(np.linalg.norm(pts[-1]-n[0]),np.linalg.norm(pts[-1]-n[-1])),min(np.linalg.norm(pts[0]-n[0]),np.linalg.norm(pts[0]-n[-1]))]
  if e[1]<e[0]: pts=pts[::-1]
  for i in ids[1:]:
    n=P[i]
    if np.linalg.norm(pts[-1]-n[-1])<np.linalg.norm(pts[-1]-n[0]): n=n[::-1]
    pts=np.vstack([pts,n])
  return pts
def smooth(pts,s):
  L=g.LineString(pts); n=max(int(L.length/0.4),6)
  r=np.array([L.interpolate(t).coords[0] for t in np.linspace(0,L.length,n)])
  tck,u=splprep(r.T,s=s*len(r)*0.1,k=3); x,y=splev(np.linspace(0,1,len(r)*4),tck); return g.LineString(np.c_[x,y])
lines=[smooth(chain(c),SM) for c in CHAINS]
G=so.unary_union([l.buffer(W/2,32) for l in lines])
grow=max(0,(W+2*WALL-4.4)/2)
Tb=so.unary_union([T.buffer(grow,32),G.buffer(WALL,32)])
Tb=Tb.buffer(0.4,32).buffer(-0.4,32)
G=G.intersection(Tb.buffer(-WALL+0.01))
pickle.dump(dict(T=T,Tb=Tb,G=G,lines=lines),open(out+'.pkl','wb'))
from PIL import Image, ImageDraw
import trimesh
px=0.08; X0,Y0,X1,Y1=Tb.bounds; X0-=3;Y0-=3;X1+=3;Y1+=3; Wd=int((X1-X0)/px); H=int((Y1-Y0)/px)
def rast(Q0):
  t=Image.new('1',(Wd,H),0); dd=ImageDraw.Draw(t)
  for Q in getattr(Q0,'geoms',[Q0]):
    dd.polygon([((x-X0)/px,(Y1-y)/px) for x,y in Q.exterior.coords],fill=1)
    for i in Q.interiors: dd.polygon([((x-X0)/px,(Y1-y)/px) for x,y in i.coords],fill=0)
  return np.array(t)
img=np.full((H,Wd,3),255,np.uint8); img[rast(Tb)]=(95,95,100); img[rast(G)]=(255,211,77)
Image.fromarray(img).save(out+'.png')
