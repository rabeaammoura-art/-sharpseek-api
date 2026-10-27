import sys,time; sys.path.insert(0,'.')
import trimesh,numpy as np
import manifold3d as m3d, fast_simplification as fs
import hollow, teddy_edit as te
W='/tmp/claude-0/-home-user--sharpseek-api/c69ab67c-81c4-5df2-a89e-e3b545ae3b81/scratchpad/v4/'
t0=time.time()
T=trimesh.load(W+'teddy_stage2.stl')
occ,xs,ys,zs=hollow.occupancy(T,T.bounds[0]-1.0,T.bounds[1]+1.0)
f=hollow.cavity_field(occ,xs,ys,zs); np.save(W+'field.npy',f)
parts=hollow.cavity_mesh(f,xs,ys,zs); print('components',len(parts),[(len(p.faces),round(p.volume)) for p in parts],round(time.time()-t0))
cav=parts[0]
mf=m3d.Manifold(m3d.Mesh(vert_properties=np.asarray(cav.vertices,dtype=np.float32),tri_verts=np.asarray(cav.faces,dtype=np.uint32)))
print('manifold ok',mf.status())
for tol in [0.02,0.05]:
    s=mf.simplify(tol).to_mesh(); g=trimesh.Trimesh(np.asarray(s.vert_properties)[:,:3].astype(float),np.asarray(s.tri_verts),process=True)
    print(' manifold simplify %.2f: faces %d watertight %s vol %.0f'%(tol,len(g.faces),g.is_watertight,g.volume))
for red in [0.8,0.9]:
    p,fc=fs.simplify(cav.vertices,cav.faces,target_reduction=red,agg=4); g=trimesh.Trimesh(p,fc,process=True)
    print(' fast_simplification %.0f%%: faces %d watertight %s vol %.0f'%(red*100,len(g.faces),g.is_watertight,g.volume))
cav.export(W+'cavity_full.stl')
