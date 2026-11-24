"""Enlarge an LED-channel sign (floor 2 mm + 1.6 mm outline walls) while keeping the channel width as it was.
Usage: python cad/scale_keep_channel.py IN.3mf OUT_BASENAME TARGET_SPAN_MM   (span of the channel centrelines; outer ~ target-6)
Method: medial axis of the channel at z=1..5, centre points scaled by k, discs of the ORIGINAL radius, walls re-offset."""
import trimesh,sys,numpy as np, shapely.geometry as g, shapely.ops as so, shapely.affinity as sa
from scipy.ndimage import distance_transform_edt, maximum_filter
from PIL import Image, ImageDraw
src,out,target=sys.argv[1],sys.argv[2],float(sys.argv[3])
m=list(trimesh.load(src).geometry.values())[0]
def sec(z):
  r=g.Polygon()
  for e in m.section([0,0,1],[0,0,z]).discrete: r=r.symmetric_difference(g.Polygon(e[:,:2]).buffer(0))
  return r
B=sec(1); C=B.difference(sec(5)); WALL=1.6
k=target/(B.bounds[2]-B.bounds[0])
px=0.04; x0,y0,x1,y1=C.bounds; Wd=int((x1-x0)/px)+6; H=int((y1-y0)/px)+6
im=Image.new('1',(Wd,H),0); d=ImageDraw.Draw(im)
for p in C.geoms:
  d.polygon([((x-x0)/px+3,(y-y0)/px+3) for x,y in p.exterior.coords],fill=1)
  for i in p.interiors: d.polygon([((x-x0)/px+3,(y-y0)/px+3) for x,y in i.coords],fill=0)
a=np.array(im)
from skimage.morphology import medial_axis, binary_opening, disk
a=binary_opening(a,disk(3))
ridge,dt=medial_axis(a,return_distance=True); dt=dt*px
gy,gx=np.gradient(distance_transform_edt(a)*px,px)
ridge&=(dt>0.3)&(np.hypot(gx,gy)<0.6)
ys,xs=np.nonzero(ridge)
cx=(xs-3)*px+x0; cy=(ys-3)*px+y0; r=dt[ys,xs]
discs=[g.Point(k*X,k*Y).buffer(R,16) for X,Y,R in zip(cx,cy,r)]
KC=sa.scale(C,k,k,origin=(0,0))
Cn=so.unary_union(discs).buffer(1.2,24).buffer(-1.2,24).intersection(KC).buffer(-1.2,24).buffer(1.2,24).simplify(0.02)
Bn=Cn.buffer(WALL,24)
print('k',round(k,3),'pieces',len(getattr(Bn,'geoms',[Bn])))
import manifold3d as mf
def ext(poly,h):
  meshes=[trimesh.creation.extrude_polygon(p,h) for p in getattr(poly,'geoms',[poly])]
  return trimesh.util.concatenate(meshes)
base=ext(Bn,10); cut=ext(Cn,9); cut.apply_translation([0,0,2])
res=trimesh.boolean.difference([base,cut],engine='manifold')
res.apply_translation(-res.bounds[0]); print(res.extents.round(1),'watertight',res.is_watertight)
res.export(out+'.stl'); res.export(out+'.3mf')
# preview
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
fig,ax=plt.subplots(1,2,figsize=(16,6))
for A,(bb,cc,t) in zip(ax,[(B,C,'original 174'),(Bn,Cn,f'new {target:.0f}')]):
  for P in bb.geoms: A.fill(*P.exterior.xy,color='0.35')
  for P in cc.geoms:
    A.fill(*P.exterior.xy,color='#ffd34d')
    for i in P.interiors: A.fill(*i.xy,color='0.35')
  A.set_aspect('equal'); A.set_title(t); A.axis('off')
ax[0].set_xlim(B.bounds[0]-2,B.bounds[0]+(Bn.bounds[2]-Bn.bounds[0])+2); ax[0].set_ylim(B.bounds[1]-2,B.bounds[1]+(Bn.bounds[3]-Bn.bounds[1])+2)
plt.tight_layout(); plt.savefig(out+'.png',dpi=90)
