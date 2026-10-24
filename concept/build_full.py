"""Full-size E30 plate: 94 cm long, 3 mm thick, design lines cut through (2.5 mm slots), bridges where parts would float."""
import math, json, numpy as np
from build123d import Face, Wire, Solid, Compound, export_stl
import contourpy
from contourpy import FillType
from scipy import ndimage as ndi
from PIL import Image, ImageDraw
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
src=open('pieces_e30.py').read().split("# cm coords (Y up)")[0]
src=src.replace("from build123d import BuildSketch, BuildPart, Polygon, extrude, export_stl, Plane","")
src=src.replace("PXCM=10","PXCM=20").replace("width=4)","width=8)").replace("_disk(35)","_disk(70)").replace("iterations=2","iterations=4")
exec(src)                       # -> P (projected polylines), k, x0,y0, Wp,Hp, px(), m (silhouette, 0.5 mm / px)
PXMM=PXCM/10.0                  # px per mm
SLOT=2.5; BR=4.0; THICK=3.0
slot=Image.new('L',(Wp,Hp),0); sd=ImageDraw.Draw(slot)
for pl in P:
    pts=[px(p) for p in pl]
    if math.dist(pts[0],pts[-1])<1e-6 and len(pts)>3:              # closed loop: leave a gap so the inside stays attached
        cut=BR*PXMM; acc=0
        while len(pts)>2 and acc<cut: acc+=math.dist(pts[-1],pts[-2]); pts.pop()
    sd.line(pts,fill=255,width=int(SLOT*PXMM),joint="curve")
slots=np.array(slot)>0
mat=m&~slots
def comps(mask):
    lab,n=ndi.label(mask); sizes=ndi.sum(mask,lab,range(1,n+1)); return lab,n,sizes
lab,n,sizes=comps(mat); main=int(np.argmax(sizes))+1
bridges=0
while True:
    lab,n,sizes=comps(mat)
    if n<=1: break
    main=int(np.argmax(sizes))+1
    others=[i for i in range(1,n+1) if i!=main]
    isl=lab==others[int(np.argmax([sizes[i-1] for i in others]))]
    mainmask=lab==main
    dist,idx=ndi.distance_transform_edt(~mainmask,return_indices=True)
    d_i=np.where(isl,dist,np.inf); p=np.unravel_index(np.argmin(d_i),d_i.shape)
    q=(idx[0][p],idx[1][p])
    bi=Image.fromarray(mat.astype('uint8')*255); ImageDraw.Draw(bi).line([(p[1],p[0]),(q[1],q[0])],fill=255,width=int(BR*PXMM))
    mat=np.array(bi)>0; bridges+=1
    if bridges>60: break
# tiny specks out
lab,n,sizes=comps(mat)
for i in range(1,n+1):
    if sizes[i-1]<30*PXMM*PXMM: mat[lab==i]=False
print("islands bridged:",bridges,"| material area %.3f m2"%(mat.sum()/PXMM/PXMM/1e6))
def rdp(pts,eps):
    if len(pts)<3: return pts
    a,b=np.array(pts[0]),np.array(pts[-1]); ab=b-a; nn=np.hypot(*ab)
    dist=[abs(ab[0]*(p[1]-a[1])-ab[1]*(p[0]-a[0]))/nn if nn else np.hypot(p[0]-a[0],p[1]-a[1]) for p in pts[1:-1]]
    i=int(np.argmax(dist))
    if dist[i]>eps: return rdp(pts[:i+2],eps)[:-1]+rdp(pts[i+1:],eps)
    return [pts[0],pts[-1]]
def solid_from_mask(mask,rot=None):
    gen=contourpy.contour_generator(z=np.pad(mask.astype(float),1),fill_type=FillType.OuterOffset)
    pts_list,off_list=gen.filled(0.5,np.inf)
    solids=[]
    for pts,off in zip(pts_list,off_list):
        rings=[]
        for a,b in zip(off[:-1],off[1:]):
            r=[((x-1)/PXMM,(Hp-1-(y-1))/PXMM) for x,y in pts[a:b]][:-1]       # mm, y up
            r=rdp(r+[r[0]],0.25)[:-1]; rings.append(r)
        rings=[r for r in rings if len(r)>=3]
        if rot: rings=[[rot(x,y) for x,y in r] for r in rings]
        yield rings
def build(mask,rot=None,shift=(0,0)):
    out=[]
    for rings in solid_from_mask(mask,rot):
        w=lambda r:Wire.make_polygon([(x+shift[0],y+shift[1],0) for x,y in r],close=True)
        f=Face(w(rings[0]),[w(h) for h in rings[1:]])
        out.append(Solid.extrude(f,(0,0,THICK)))
    return Compound(out) if len(out)>1 else out[0]
full=build(mat); export_stl(full,"e30_full_94cm_3mm.stl")
bb=full.bounding_box(); print("STL size mm: %.1f x %.1f x %.1f"%(bb.size.X,bb.size.Y,bb.size.Z),"| volume %.0f cm3"%(full.volume/1000))
# preview with cm axes
fig,ax=plt.subplots(figsize=(13,6.4))
ax.imshow(np.where(mat,0.12,0.97),cmap="gray",vmin=0,vmax=1,extent=[0,Wp/PXCM,0,Hp/PXCM],origin="upper",interpolation="nearest")
ax.set_xticks(range(0,95,10)); ax.set_yticks(range(0,50,10)); ax.set_xticks(range(0,95,5),minor=True); ax.set_yticks(range(0,50,5),minor=True)
ax.grid(True,which="major",color="#c9a",lw=.7); ax.set_xlabel("cm"); ax.set_ylabel("cm")
ax.set_title("E30 full plate · %.0f x %.0f cm · 3 mm · cut lines %.1f mm · %d bridges"%(Wp/PXCM,Hp/PXCM,SLOT,bridges))
fig.tight_layout(); fig.savefig("e30_full_preview.png",dpi=110)
np.save("/tmp/e30_mat.npy",mat)
