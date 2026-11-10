"""Recover the flat layer shapes (base / pink level 1+2 / yellow) from the three exported STLs when G6.pkl is gone: recover_from_stl.py R.pkl <dir with maryam_*.stl>. Needs networkx."""
import sys, pickle; sys.path.insert(0,'/home/user/-sharpseek-api/cad')
import numpy as np, trimesh, shapely
from shapely.ops import unary_union
from shapely.geometry import Polygon
import newborn_plaque as n
P=sys.argv[2].rstrip('/')+'/'
def sec(name,z):
    m=trimesh.load(P+name); s=m.section(plane_origin=[0,0,z],plane_normal=[0,0,1])
    p,_=s.to_planar() if hasattr(s,'to_planar') else s.to_2D()
    T=_
    polys=[]
    for pg in p.polygons_full:
        polys.append(pg)
    g=unary_union(polys)
    # back to world xy
    from shapely.affinity import affine_transform
    g=affine_transform(g,[T[0,0],T[0,1],T[1,0],T[1,1],T[0,3],T[1,3]])
    return m,g
mb,base=sec('maryam_base.stl',1.2)
mm,top=sec('maryam_main.stl',3.9)
_,low=sec('maryam_main.stl',3.0)
ma,Y=sec('maryam_accent.stl',3.0)
for nm,m in (('base',mb),('main',mm),('accent',ma)): print(nm,m.bounds.round(2).tolist(),m.is_watertight)
for nm,g in (('base',base),('top',top),('low',low),('Y',Y)): print(nm,round(g.area,1),g.bounds)
pickle.dump({'base':base,'top':top,'low':low,'Y':Y},open(sys.argv[1],'wb'))
