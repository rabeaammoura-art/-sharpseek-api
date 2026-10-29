import trimesh, numpy as np, pickle
from shapely.geometry import Polygon
from shapely.ops import unary_union
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path
OUT='out'
m=trimesh.load(OUT+'/BMW_E30_wall_art_900mm.stl')
ext=m.extents
print('extents mm',ext,'aspect',ext[0]/ext[1],'source aspect',1152/864)
print('watertight',m.is_watertight,'winding ok',m.is_winding_consistent,'volume>0',m.volume>0,'euler',m.euler_number)
print('connected bodies (faces graph):',len(m.split(only_watertight=False)))
print('degenerate faces',int((m.area_faces<1e-9).sum()))
# min feature width: 2D section at mid-height, opening test
sec=m.section(plane_origin=[0,0,2.5],plane_normal=[0,0,1]); p2,_=sec.to_planar()
rings=pickle.load(open(OUT+'/rings.pkl','rb'))
# rebuild polygon via even-odd
from shapely.geometry import Polygon
polys=[Polygon(r) for r in rings]; polys.sort(key=lambda p:-p.area)
g=None
from shapely import symmetric_difference_all
g=symmetric_difference_all(polys)
r=1.25-0.05
op=g.buffer(-r).buffer(r)
lost=g.difference(op)
big=[x for x in (lost.geoms if hasattr(lost,'geoms') else [lost]) if x.area>2.0]
print('area',g.area,'lost-by-opening',lost.area,'regions >2mm2 :',len(big))
print('thinnest-ish: min inscribed width via erosion survives at r=%.2f'%r, not g.buffer(-r).is_empty)
fig,ax=plt.subplots(figsize=(14,9.2),dpi=130)
verts=[];codes=[]
for rg in rings:
    verts+=list(rg)+[rg[0]];codes+=[Path.MOVETO]+[Path.LINETO]*(len(rg)-1)+[Path.CLOSEPOLY]
ax.add_patch(PathPatch(Path(verts,codes),fc='#222',ec='none'))
ax.set_xlim(-10,910);ax.set_ylim(-10,ext[1]+10);ax.set_aspect('equal');ax.set_facecolor('#f2efe8');ax.axis('off')
ax.set_title('BMW E30 wall art - 900 x %.1f x 5 mm  (single connected body)'%ext[1])
fig.savefig(OUT+'/preview.png',bbox_inches='tight');
# 3D-ish shaded preview
sc=m.scene(); 
