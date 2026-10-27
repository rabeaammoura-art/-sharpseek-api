import sys,time; sys.path.insert(0,'.')
import trimesh,numpy as np
import manifold3d as m3d
import teddy_edit as te
from heart import X0
W='/tmp/claude-0/-home-user--sharpseek-api/c69ab67c-81c4-5df2-a89e-e3b545ae3b81/scratchpad/v4/'
t0=time.time()
T=trimesh.load(W+'teddy_stage2.stl'); cav=trimesh.load(W+'cavity_full.stl')
mf=m3d.Manifold(m3d.Mesh(vert_properties=np.asarray(cav.vertices,dtype=np.float32),tri_verts=np.asarray(cav.faces,dtype=np.uint32)))
for tol in (0.1,0.15):
    s=mf.simplify(tol).to_mesh(); g=trimesh.Trimesh(np.asarray(s.vert_properties)[:,:3].astype(float),np.asarray(s.tri_verts),process=True)
    print('cavity simplify %.2f -> %d faces watertight %s'%(tol,len(g.faces),g.is_watertight))
cav=g
H=te.boolean('difference',[T,cav]); print('hollowed',len(H.faces),H.is_watertight,'volume %.0f cm3'%(H.volume/1000),round(time.time()-t0))
# vent: 2 mm hole from the trench ceiling (z=5) up into the cavity at a hidden spot
vent=trimesh.creation.cylinder(radius=1.0,height=8.0,sections=24,transform=trimesh.transformations.translation_matrix([X0,880.0,6.0]))
H2=te.boolean('difference',[H,vent]); print('vent cut: volume change %.1f mm3'%(H.volume-H2.volume),H2.is_watertight)
# connectivity of the cavity with the outside through the vent: ray up the vent axis
loc,_,_=H2.ray.intersects_location([[X0,880.0,-3.0]],[[0,0,1.0]],multiple_hits=True); print('ray up the vent axis hits at z =',np.round(np.sort(loc[:,2]),1)[:6])
H2.export(W+'teddy_stage3.stl'); print('exported',len(H2.faces),round(time.time()-t0))
