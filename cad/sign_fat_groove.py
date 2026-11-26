"""LED-channel sign: keep the ORIGINAL letter outline (scaled to W_OUT mm wide) and cut a constant-width LED groove
along the centre of each stroke (medial axis of the original channel). Counters stay open, floor 2 mm, height 10.
Usage: python cad/sign_fat_groove.py IN.3mf OUT_BASENAME W_OUT_MM GROOVE_MM   (e.g. 250 5.2)"""
import trimesh,sys,numpy as np, shapely.geometry as g, shapely.ops as so, shapely.affinity as sa
from scipy.ndimage import distance_transform_edt
from PIL import Image, ImageDraw
from skimage.morphology import medial_axis, opening, disk
src,out,W_OUT,GROOVE=sys.argv[1],sys.argv[2],float(sys.argv[3]),float(sys.argv[4])
m=list(trimesh.load(src).geometry.values())[0]
def sec(z):
  r=g.Polygon()
  for e in m.section([0,0,1],[0,0,z]).discrete: r=r.symmetric_difference(g.Polygon(e[:,:2]).buffer(0))
  return r
B=sec(1); Wz=sec(5); C=B.difference(Wz); L=so.unary_union([C,Wz])  # L = letter strokes (without counters)
k=W_OUT/(B.bounds[2]-B.bounds[0])
px=0.04; x0,y0,x1,y1=C.bounds; Wd=int((x1-x0)/px)+6; H=int((y1-y0)/px)+6
im=Image.new('1',(Wd,H),0); d=ImageDraw.Draw(im)
for p in C.geoms:
  d.polygon([((x-x0)/px+3,(y-y0)/px+3) for x,y in p.exterior.coords],fill=1)
  for i in p.interiors: d.polygon([((x-x0)/px+3,(y-y0)/px+3) for x,y in i.coords],fill=0)
a=opening(np.array(im),disk(3))
ridge,dt=medial_axis(a,return_distance=True); dt=dt*px
gy,gx=np.gradient(distance_transform_edt(a)*px,px)
ridge&=(dt>0.3)&(np.hypot(gx,gy)<0.6)
ys,xs=np.nonzero(ridge); cx=(xs-3)*px+x0; cy=(ys-3)*px+y0
G=so.unary_union([g.Point(k*X,k*Y).buffer(GROOVE/2,16) for X,Y in zip(cx,cy)])
Bk=sa.scale(B,k,k,origin=(0,0)); Lk=sa.scale(L,k,k,origin=(0,0)).buffer(0)
G=G.buffer(1.0,24).buffer(-1.0,24).intersection(Lk.buffer(-1.6)).buffer(-1.0,24).buffer(1.0,24)
import manifold3d
def ext(poly,h): return trimesh.util.concatenate([trimesh.creation.extrude_polygon(p,h) for p in getattr(poly,'geoms',[poly])])
floor=ext(Bk,2); top=ext(Lk.difference(G),8); top.apply_translation([0,0,2])
res=trimesh.boolean.union([floor,top],engine='manifold'); res.apply_translation(-res.bounds[0])
print('k',round(k,3),res.extents.round(1),'watertight',res.is_watertight)
res.export(out+'.stl'); res=trimesh.load(out+'.stl'); res.merge_vertices(); trimesh.repair.fill_holes(res); res.update_faces(res.nondegenerate_faces()); res.remove_unreferenced_vertices(); trimesh.repair.fix_normals(res)
print('repaired watertight',res.is_watertight); res.export(out+'.stl'); res.export(out+'.3mf')
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
fig,A=plt.subplots(figsize=(15,10))
for P in Bk.geoms:
  A.fill(*P.exterior.xy,color='0.45')
  for i in P.interiors: A.fill(*i.xy,color='w')
for P in getattr(G,'geoms',[G]):
  A.fill(*P.exterior.xy,color='#ffd34d')
  for i in P.interiors: A.fill(*i.xy,color='0.55')
A.set_aspect('equal');A.axis('off');A.set_title(f'{W_OUT:.0f} mm wide, letter shape as original, LED groove {GROOVE} mm (yellow)',fontsize=14)
plt.tight_layout();plt.savefig(out+'.png',dpi=75)
