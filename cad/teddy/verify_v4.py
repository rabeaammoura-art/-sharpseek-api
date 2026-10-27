"""Read-only verification of the v4 STLs: integrity, base, fit/pull, walls, overhangs, mass."""
import sys,glob,time
import numpy as np, trimesh
sys.path.insert(0,'.')
import teddy_edit as te
OUT='out/'
T=trimesh.load(OUT+'teddy_rear_heart_LED_v4.stl'); L=trimesh.load(OUT+'heart_front_lithophane_v4.stl')
print('== integrity')
for n,m in (('teddy',T),('litho',L)):
    e=np.sort(m.edges,axis=1); u,c=np.unique(e,axis=0,return_counts=True)
    ar=m.area_faces; tr=m.triangles
    el=np.stack([np.linalg.norm(tr[:,0]-tr[:,1],axis=1),np.linalg.norm(tr[:,1]-tr[:,2],axis=1),np.linalg.norm(tr[:,2]-tr[:,0],axis=1)],1)
    asp=el.max(1)**2/(4*np.sqrt(3)*np.maximum(ar,1e-12))
    comps=len(trimesh.graph.connected_components(m.face_adjacency,nodes=np.arange(len(m.faces))))
    print(' %s: faces %d  watertight %s  winding %s  volume-ok %s  open edges %d  non-manifold %d  components %d  area<1e-6: %d  sliver>1000: %d  vol %.0f mm3  bbox %s'%(n,len(m.faces),m.is_watertight,m.is_winding_consistent,m.is_volume,(c==1).sum(),(c>2).sum(),comps,(ar<1e-6).sum(),(asp>1000).sum(),m.volume,np.round(m.bounds[1]-m.bounds[0],1).tolist()))
print('== mass (PLA 1.24, PETG 1.27 g/cm3):  teddy %.0f g / %.0f g   litho %.0f g / %.0f g'%(T.volume*1.24e-3,T.volume*1.27e-3,L.volume*1.24e-3,L.volume*1.27e-3))
print('== fit')
def vol(a,b):
    r=te.boolean('intersection',[a,b]); return float(r.volume) if len(r.faces) else 0.0
print(' seated interference: %.3f mm3'%vol(T,L))
for d in [0.05,0.2,1,3,5,7,8,12,25]:
    Ld=L.copy(); Ld.apply_translation([0,-d,0]); print('  pulled %5.2f mm: overlap %.2f mm3'%(d,vol(T,Ld)))
V=L.vertices; sel=np.where(V[:,1]>774.2)[0]; rng=np.random.default_rng(0); sel=rng.choice(sel,min(5000,len(sel)),replace=False)
from trimesh.proximity import closest_point
_,d,_=closest_point(T,V[sel]); print(' litho rim/bridge/skirt clearance to teddy percentiles 0/1/5/50/95:',np.round(np.percentile(d,[0,1,5,50,95]),3))
print('== base')
res=0.25; xs=np.arange(783,941,res); ys=np.arange(760,917,res); X,Y=np.meshgrid(xs,ys)
o=np.c_[X.ravel(),Y.ravel(),np.full(X.size,-20.)]
loc,ir,_=T.ray.intersects_location(o,np.tile([0,0,1.],(len(o),1)),multiple_hits=False)
Zb=np.full(X.size,np.nan); Zb[ir]=loc[:,2]; Zb=Zb.reshape(X.shape); cov=np.isfinite(Zb)
flat=(Zb<=0.02); print(' footprint %.0f mm2, flat (within 0.02 mm of z=0): %.0f mm2'%(cov.sum()*res*res,flat.sum()*res*res))
from scipy.ndimage import label
lab,n=label(flat); sz=np.bincount(lab.ravel())[1:]; print(' flat regions:',n,'areas',np.round(np.sort(sz)[::-1][:4]*res*res))
com=T.center_mass; print(' COM',np.round(com,1).tolist())
ys_,xs_=np.where(lab==(np.argmax(sz)+1))
from scipy.spatial import ConvexHull; from shapely.geometry import Polygon,Point
pts=np.c_[xs[xs_],ys[ys_]]; P=Polygon(pts[ConvexHull(pts).vertices]); print(' COM inside support polygon:',P.contains(Point(com[:2])),' margin %.1f mm, tip-over %.1f deg'%(P.exterior.distance(Point(com[:2])),np.degrees(np.arctan2(P.exterior.distance(Point(com[:2])),com[2]))))
print('== cable path / vent')
for y in (847,880):
    loc,_,_=T.ray.intersects_location([[X0:=861.43,y,-5.]],[[0,0,1.]],multiple_hits=True); print(' ray up at y=%d, hits z:'%y,np.round(np.sort(loc[:,2]),1)[:8])
print('== walls (ray inward from the outer surface; first hit = other side of the wall)')
rng=np.random.default_rng(1)
pts,fi=trimesh.sample.sample_surface(T,40000,seed=1)
nrm=T.face_normals[fi]
org=pts-nrm*0.02
loc,ir,_=T.ray.intersects_location(org,-nrm,multiple_hits=False)
th=np.full(len(pts),np.nan); th[ir]=np.linalg.norm(loc-org[ir],axis=1)
ok=np.isfinite(th)
print(' sampled %d points; thickness percentiles 0.5/1/5/25/50 (mm):'%ok.sum(),np.round(np.percentile(th[ok],[0.5,1,5,25,50]),2))
print(' share of surface with wall thinner than 1.6 mm: %.1f%%, thinner than 1.0: %.1f%%'%(100*(th[ok]<1.6).mean(),100*(th[ok]<1.0).mean()))
print('== overhangs (upright print)')
nz=T.face_normals[:,2]; ang=np.degrees(np.arccos(np.clip(-nz,-1,1))); over=90-ang; zc=T.triangles_center[:,2]
for thr in (45,60): 
    fl=(ang<90)&(over>thr)&(zc>0.3); print(' overhang >%d deg: %.0f mm2'%(thr,T.area_faces[fl].sum()))
