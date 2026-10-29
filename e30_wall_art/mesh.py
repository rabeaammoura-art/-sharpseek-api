import pickle, numpy as np, trimesh
from manifold3d import Manifold, CrossSection, FillRule
OUT='out'
polys,W,H,T=pickle.load(open(OUT+'/geom.pkl','rb'))
rings=[]
for p in polys:
    rings.append(np.array(p.exterior.coords)[:-1])
    for r in p.interiors: rings.append(np.array(r.coords)[:-1])
allp=np.vstack(rings); mn=allp.min(0); k=W/(allp[:,0].max()-mn[0])
rings=[(r-mn)*k for r in rings]
cs=CrossSection(rings,FillRule.EvenOdd)
man=Manifold.extrude(cs,T)
mm=man.to_mesh()
m=trimesh.Trimesh(vertices=mm.vert_properties[:,:3],faces=mm.tri_verts,process=False)
m.export(OUT+'/BMW_E30_wall_art_900mm.stl')
print('bounds',m.bounds.tolist()); print('watertight',m.is_watertight,'winding',m.is_winding_consistent,'volume',m.volume,'faces',len(m.faces))
print('bodies',len(m.split(only_watertight=False)), 'genus',man.genus())

import pickle as pk
pk.dump(rings,open(OUT+'/rings.pkl','wb'))
