"""Sally sign step 3: join the S to the a with a lying l-style loop (spline points in centred, 250-mm coords), wire hole 4.5 at the y stem (106.6,-32.4).
Usage: python cad/sign_s_join.py STEP2_g.pkl OUT_BASENAME 0.3 ; then extrude floor 2 (minus hole) + letters 8 minus groove, drop zero-volume bodies."""
import pickle,sys,numpy as np, shapely.geometry as g, shapely.ops as so
from scipy.interpolate import splprep, splev
v=pickle.load(open(sys.argv[1],'rb')); lines,Lk,Bk=v['lines'],v['Lk'],v['Bk']
T=np.array([-112.8,0.3])
S=np.array(lines[0].coords)
if np.linalg.norm(S[0]-T)<np.linalg.norm(S[-1]-T): S=S[::-1]
Sl=g.LineString(S); S=np.array([Sl.interpolate(t).coords[0] for t in np.arange(0,Sl.length-0.5,0.8)])
arc=[(-108.5+5*np.cos(np.radians(a)),0+5*np.sin(np.radians(a))) for a in (165,140,115,90,65,52)]
con=[(-99,-0.7),(-91,-7.1),(-83,-13.5),(-75,-19.3),(-66,-22.6),(-56,-23),(-47,-20.5),(-41,-17),(-37.5,-13)]
P=np.vstack([S,arc,con])
w=np.ones(len(P)); 
tck,u=splprep(P.T,s=float(sys.argv[3]) if len(sys.argv)>3 else 2.0,k=3); x,y=splev(np.linspace(0,1,1500),tck); Sc=g.LineString(np.c_[x,y])
# body: original letters + path tail (last part of S + connector) with even width
tail=g.LineString([p for p in Sc.coords if p[0]<-30 and (p[1]>-25)][0:])  # unused
dS=Sc.project(g.Point(-112.8,-12)); seg=so.substring(Sc,dS,Sc.length)
L=so.unary_union([Lk,seg.buffer(5.0,32)])
R=g.Point(-110,2).buffer(22)
L=so.unary_union([L.difference(R),L.intersection(R).buffer(0.5,32).buffer(-0.5,32)]).buffer(0.05,16).buffer(-0.05,16)
def fillsmall(P,a=30):
  out=[]
  for Q in getattr(P,'geoms',[P]): out.append(g.Polygon(Q.exterior,[i for i in Q.interiors if g.Polygon(i).area>a]))
  return so.unary_union(out)
L=fillsmall(L)
print('holes',[round(g.Polygon(i).area) for Q in getattr(L,'geoms',[L]) for i in Q.interiors])
hole=g.Point(106.6,-32.4).buffer(2.25,32)
G=so.unary_union([Sc.buffer(2.6,32)]+[l.buffer(2.6,32) for l in lines[1:]]).intersection(L.buffer(-1.6))
B=so.unary_union([Bk,L])
pickle.dump(dict(G=G,Lk=L,Bk=B,hole=hole),open(sys.argv[2]+'_g.pkl','wb'))
from PIL import Image, ImageDraw
px=0.25; x0,y0,x1,y1=L.bounds; x0-=8;y0-=8;x1+=8;y1+=8; W=int((x1-x0)/px); H=int((y1-y0)/px)
def rast(poly):
  t=Image.new('1',(W,H),0); d=ImageDraw.Draw(t)
  for Q in getattr(poly,'geoms',[poly]):
    d.polygon([((a-x0)/px,(y1-b)/px) for a,b in Q.exterior.coords],fill=1)
    for i in Q.interiors: d.polygon([((a-x0)/px,(y1-b)/px) for a,b in i.coords],fill=0)
  return np.array(t)
l=rast(L); gg=rast(G); h=rast(hole)
img=np.full((H,W,3),255,np.uint8); img[l]=(110,110,115); img[gg&l]=(255,211,77); img[h]=(20,20,20)
Image.fromarray(img).save(sys.argv[2]+'.png')
c=img[int((y1-30)/px):int((y1+30)/px), 0:int((-25-x0)/px)]
Image.fromarray(c).resize((c.shape[1]*2,c.shape[0]*2)).save(sys.argv[2]+'_zoom.png')
