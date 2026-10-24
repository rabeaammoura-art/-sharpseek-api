"""Split the E30 silhouette along the user's red cut lines into 3 mm STL pieces (94 cm long)."""
import math, sys, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
import contourpy
from build123d import BuildSketch, BuildPart, Polygon, extrude, export_stl, Plane
exec(open('make_e30.py').read().split("W,H=1100,560")[0])
LEN=94.0; PXCM=10                                   # 1 px = 1 mm
x0,x1,y0,y1=min(xs),max(xs),min(ys),max(ys); k=LEN/(x1-x0)
Wp=int(LEN*PXCM)+1; Hp=int((y1-y0)*k*PXCM)+1
def px(p): return ((p[0]-x0)*k*PXCM,(p[1]-y0)*k*PXCM)
im=Image.new('L',(Wp,Hp),0); d=ImageDraw.Draw(im)
for pl in P: d.line([px(p) for p in pl],fill=255,width=4)
m=np.array(im)>0
def _disk(r):
    y,x=np.ogrid[-r:r+1,-r:r+1]; return x*x+y*y<=r*r
m=ndi.binary_closing(np.pad(m,60),structure=_disk(35))[60:-60,60:-60]
m=ndi.binary_fill_holes(m)
m=ndi.binary_opening(m,iterations=2)
print("silhouette area m2: %.3f"%(m.sum()/1e6))   # px = mm2 -> m2 = px/1e6
# cm coords (Y up)
R,C=np.indices(m.shape); X=C/PXCM; Y=(Hp-1-R)/PXCM
cuts=[  # from the user's sketch: (X cm, Y cm) points, diagonal cuts top->bottom
 [(21,29.8),(25,21.3),(30,12.8),(35,3.3),(38,-5.2)],
 [(36.5,41.8),(44,36.3),(48.5,27.8),(53,15.3),(59,2.3),(63.5,-9.5)],
 [(54.5,44.6),(60,38.8),(64,29.8),(70,19.3),(77,9.3),(84,-2.7),(88,-13.2)],
 [(66.5,45.8),(73,41.3),(79,31.3),(84,21.3),(89.5,3.3),(93.5,-11.2)]]
hor=[(15.5,23),(22,25),(35,27),(50,28.8),(62,30.5),(75,33),(92,38)]
import os
DIAG=[int(i) for i in os.environ.get('DIAG','0,1,2,3').split(',') if i!='']; USEHOR=os.environ.get('HOR','1')=='1'; EXPORT=os.environ.get('EXPORT','1')=='1'
strip=np.zeros(m.shape,int)
for c in [cuts[i] for i in DIAG]:
    ys_=[p[1] for p in c][::-1]; xs_=[p[0] for p in c][::-1]
    strip+= (X>np.interp(Y,ys_,xs_)).astype(int)
hx=[p[0] for p in hor]; hy=[p[1] for p in hor]
upper=(Y>np.interp(X,hx,hy)).astype(int) if USEHOR else np.zeros(m.shape,int)
reg=strip*2+upper
def rdp(pts,eps):
    if len(pts)<3: return pts
    a,b=np.array(pts[0]),np.array(pts[-1]); ab=b-a; n=np.hypot(*ab)
    dist=[abs(ab[0]*(p[1]-a[1])-ab[1]*(p[0]-a[0]))/n if n else np.hypot(*(np.array(p)-a)) for p in pts[1:-1]]
    i=int(np.argmax(dist))
    if dist[i]>eps: return rdp(pts[:i+2],eps)[:-1]+rdp(pts[i+1:],eps)
    return [pts[0],pts[-1]]
def best_rot(pts,Tw=310,Th=300):
    P_=np.array(pts); best=None
    for a in np.radians(np.arange(0,180,1)):
        c,s=np.cos(a),np.sin(a); u=P_[:,0]*c+P_[:,1]*s; v=-P_[:,0]*s+P_[:,1]*c
        du,dv=u.max()-u.min(),v.max()-v.min()
        for (w_,h_,sw) in ((du,dv,0),(dv,du,1)):
            score=max(w_/Tw,h_/Th)
            if best is None or score<best[0]: best=(score,a,w_,h_)
    return best
out=[]; names=[]
for rid in np.unique(reg[m]):
    mk=(m&(reg==rid)); lab,n=ndi.label(mk)
    for j in range(1,n+1):
        comp=lab==j
        if comp.sum()<4000: continue                      # < 40 cm2: ignore specks
        gen=contourpy.contour_generator(z=np.pad(comp.astype(float),1))
        lines=gen.lines(0.5); ln=max(lines,key=len)
        pts=[(x-1,y-1) for x,y in ln][:-1]
        pts=[(x,(Hp-1)-y) for x,y in pts]               # y up, mm
        pts=rdp(pts+[pts[0]],0.4)[:-1]
        sc_,a,w_,h_=best_rot(pts)
        c,s=math.cos(a),math.sin(a)
        rp=[(x*c+y*s,-x*s+y*c) for x,y in pts]
        mnx=min(p[0] for p in rp); mny=min(p[1] for p in rp)
        rp=[(x-mnx,y-mny) for x,y in rp]
        area=comp.sum()/100
        name=f"e30_piece_s{rid//2}{'u' if rid%2 else 'l'}_{j}"
        print(f"{name}: area {area:.0f} cm2, bbox after rotation {max(p[0] for p in rp)/10:.1f} x {max(p[1] for p in rp)/10:.1f} cm, fits 31x30: {sc_<=1}")
        if not EXPORT: names.append((name,sc_<=1,area)); continue
        with BuildPart() as bp:
            with BuildSketch(Plane.XY): Polygon(*rp,align=None)
            extrude(amount=3)
        export_stl(bp.part,f"pieces/{name}.stl"); names.append((name,sc_<=1,area))
print("pieces:",len(names),"| all fit:",all(n[1] for n in names))
