import numpy as np, contourpy
from contourpy import FillType
from build123d import Face, Wire, Solid, Compound, export_stl
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
m=np.load("e30_ref/mask_1880.npy"); H,W=m.shape; PXMM=2.0            # 2 px per mm  (0.5 mm / px)
XC=np.arange(W)/PXMM/10; YC=(H-1-np.arange(H))/PXMM/10               # cm, y up
X,Y=np.meshgrid(XC,YC)
x1,x2,yc=31.0,62.5,30.0
reg=(X>x1).astype(int)+(X>x2).astype(int)+3*(Y>yc).astype(int)
def rdp(pts,eps):
    if len(pts)<3: return pts
    a,b=np.array(pts[0]),np.array(pts[-1]); ab=b-a; n=np.hypot(*ab)
    d=[abs(ab[0]*(p[1]-a[1])-ab[1]*(p[0]-a[0]))/n if n else np.hypot(p[0]-a[0],p[1]-a[1]) for p in pts[1:-1]]
    i=int(np.argmax(d))
    if d[i]>eps: return rdp(pts[:i+2],eps)[:-1]+rdp(pts[i+1:],eps)
    return [pts[0],pts[-1]]
names={0:"A1_front_low",1:"A2_mid_low",2:"A3_rear_low",3:"B1_front_up",4:"B2_mid_up",5:"B3_rear_up"}
info=[]; cols=["#e07a5f","#81b29a","#f2cc8f","#9b5de5","#00b4d8","#3d405b"]
for rid in range(6):
    sub=m&(reg==rid)
    if sub.sum()<400: continue
    ys,xs=np.where(sub); x0,y0=xs.min(),ys.min(); x1_,y1_=xs.max(),ys.max()
    sub=sub[y0:y1_+1,x0:x1_+1]; h,w=sub.shape
    gen=contourpy.contour_generator(z=np.pad(sub.astype(float),1),fill_type=FillType.OuterOffset)
    P,O=gen.filled(0.5,np.inf); solids=[]
    for pts,off in zip(P,O):
        rings=[]
        for a,b in zip(off[:-1],off[1:]):
            r=[((x-1)/PXMM,(h-1-(y-1))/PXMM) for x,y in pts[a:b]][:-1]; r=rdp(r+[r[0]],0.15)[:-1]
            if len(r)>=3: rings.append(r)
        if not rings: continue
        wf=lambda r:Wire.make_polygon([(x,y,0) for x,y in r],close=True)
        solids.append(Solid.extrude(Face(wf(rings[0]),[wf(q) for q in rings[1:]]),(0,0,4.0)))
    shp=Compound(solids); export_stl(shp,f"e30_ref/{names[rid]}.stl")
    info.append((names[rid],w/PXMM/10,h/PXMM/10,sub.sum()/PXMM**2/100,rid))
    print(f"{names[rid]}: {w/PXMM:.0f} x {h/PXMM:.0f} mm, material {sub.sum()/PXMM**2/100:.0f} cm2, volume {shp.volume/1000:.0f} cm3")
fig,ax=plt.subplots(figsize=(13,6.8))
img=np.ones((H,W,3))*0.97
for rid in range(6): img[m&(reg==rid)]=matplotlib.colors.to_rgb(cols[rid])
ax.imshow(img,extent=[0,W/PXMM/10,0,H/PXMM/10],origin="upper",interpolation="nearest")
for v in (x1,x2): ax.axvline(v,color="#c0392b",lw=2,ls="--")
ax.plot([0,94],[yc,yc],color="#c0392b",lw=2,ls="--")
for n_,w_,h_,a_,rid in info:
    cx=(0,x1,x2)[rid%3]; wd=((x1,x2-x1,94-x2))[rid%3]; cy=(0,yc)[rid//3]
    ax.text(cx+wd/2,(yc/2 if rid<3 else yc+(47-yc)/2),f"{n_.split('_')[0]}\n{w_:.0f}×{h_:.0f}",ha="center",va="center",fontsize=13,fontweight="bold",bbox=dict(boxstyle="round",fc=(1,1,1,.8),ec="none"))
ax.set_xticks(range(0,95,10)); ax.set_yticks(range(0,50,10)); ax.grid(True,color="#ccc",lw=.6); ax.set_xlabel("cm"); ax.set_ylabel("cm")
ax.set_title("E30 94 x 47 cm: 6 pieces. Cuts at x=31 and 62.5 cm, y=30 cm (red dashes). Labels: piece, size in cm")
fig.tight_layout(); fig.savefig("e30_ref/cut_plan.png",dpi=105)
