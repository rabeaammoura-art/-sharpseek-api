import math, json, numpy as np
from build123d import BuildSketch, BuildPart, Polygon, extrude, export_stl, Plane
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
src=open('pieces_e30.py').read().split("# cm coords (Y up)")[0].replace("from build123d import BuildSketch, BuildPart, Polygon, extrude, export_stl, Plane","")
exec(src)
import contourpy
from scipy import ndimage as ndi
lines=json.load(open('split_best.json'))['lines']
R,C=np.indices(m.shape); X=C/PXCM; Y=(Hp-1-R)/PXCM
lab=np.zeros(m.shape,int)
for i,(th,d) in enumerate(lines): lab+=((X*math.cos(th)+Y*math.sin(th))>d).astype(int)<<i
def rdp(pts,eps):
    if len(pts)<3: return pts
    a,b=np.array(pts[0]),np.array(pts[-1]); ab=b-a; n=np.hypot(*ab)
    dist=[abs(ab[0]*(p[1]-a[1])-ab[1]*(p[0]-a[0]))/n if n else np.hypot(p[0]-a[0],p[1]-a[1]) for p in pts[1:-1]]
    i=int(np.argmax(dist))
    if dist[i]>eps: return rdp(pts[:i+2],eps)[:-1]+rdp(pts[i+1:],eps)
    return [pts[0],pts[-1]]
def best_rot(pts,Tw=310,Th=300):
    P_=np.array(pts); best=None
    for a in np.radians(np.arange(0,180,1)):
        c,s=np.cos(a),np.sin(a); u=P_[:,0]*c+P_[:,1]*s; v=-P_[:,0]*s+P_[:,1]*c
        du,dv=u.max()-u.min(),v.max()-v.min(); score=max(du/Tw,dv/Th)
        if best is None or score<best[0]: best=(score,a,du,dv)
    return best
comps=[]
for L in np.unique(lab[m]):
    cl,n=ndi.label(m&(lab==L))
    for j in range(1,n+1):
        c_=cl==j
        if c_.sum()>=800: comps.append(c_)           # >= 8 cm2
# order left->right by centroid x
comps.sort(key=lambda c_: np.where(c_)[1].mean())
letters="ABCDEFGH"; info=[]
for idx,c_ in enumerate(comps):
    gen=contourpy.contour_generator(z=np.pad(c_.astype(float),1)); ln=max(gen.lines(0.5),key=len)
    pts=[(x-1,(Hp-1)-(y-1)) for x,y in ln][:-1]; pts=rdp(pts+[pts[0]],0.4)[:-1]
    sc_,a,du,dv=best_rot(pts); co,si=math.cos(a),math.sin(a)
    rp=[(x*co+y*si,-x*si+y*co) for x,y in pts]; mnx=min(p[0] for p in rp); mny=min(p[1] for p in rp)
    rp=[(x-mnx,y-mny) for x,y in rp]
    name=f"e30_{letters[idx]}"
    with BuildPart() as bp:
        with BuildSketch(Plane.XY): Polygon(*rp,align=None)
        extrude(amount=3)
    export_stl(bp.part,f"pieces/{name}.stl")
    ys_,xs_=np.where(c_); info.append((letters[idx],c_.sum()/100,du/10,dv/10,sc_<=1,xs_.mean()/10,(Hp-1-ys_.mean())/10))
    print(f"{letters[idx]}: area {c_.sum()/100:.0f} cm2, on plate {du/10:.1f} x {dv/10:.1f} cm, fits: {sc_<=1}")
# picture
fig,ax=plt.subplots(figsize=(13,7.2)); cols=["#e07a5f","#81b29a","#f2cc8f","#3d405b","#9b5de5","#00b4d8"]
img=np.ones(m.shape+(3,))*0.96
for idx,c_ in enumerate(comps):
    rgb=matplotlib.colors.to_rgb(cols[idx%6]); img[c_]=rgb
ax.imshow(img,extent=[0,Wp/10,0,Hp/10],origin="upper",aspect="equal")
for pl in P:
    q=np.array([[ (p[0]-x0)*k, (y1-p[1])*k ] for p in pl]); ax.plot(q[:,0],q[:,1],color="#111",lw=1.1)
for t in info: ax.text(t[5],t[6],f"{t[0]}\n{t[2]:.0f}×{t[3]:.0f}",ha="center",va="center",fontsize=13,fontweight="bold",color="white" if t[0] in "DE" else "#111",bbox=dict(boxstyle="round",fc=(1,1,1,.55),ec="none"))
ax.set_xticks(range(0,95,10)); ax.set_yticks(range(0,50,10)); ax.set_xticks(range(0,95,5),minor=True); ax.set_yticks(range(0,50,5),minor=True)
ax.grid(True,which="major",color="#bbb",lw=.8); ax.grid(True,which="minor",color="#ddd",lw=.4)
ax.set_xlabel("cm"); ax.set_ylabel("cm"); ax.set_xlim(0,94); ax.set_ylim(0,Hp/10)
ax.set_title("E30 3/4 · 94 cm · 6 pieces, 3 straight cuts (label = piece, size on the plate in cm)")
fig.tight_layout(); fig.savefig("e30_split.png",dpi=110)
