"""Maryam plaque, backlit (glow_cap method): opaque white base with openings, translucent pink / yellow caps on top. PRIVATE (picture + character): scratch only."""
import sys, pickle, math; sys.path.insert(0,'/home/user/-sharpseek-api/cad')
from pathlib import Path
import numpy as np, trimesh
from shapely.geometry import box
from shapely.ops import unary_union
import newborn_plaque as n
from threemf import build_project_settings, write_bambu_3mf
OUTDIR=Path(sys.argv[1] if len(sys.argv)>1 else 'lit_out'); OUTDIR.mkdir(parents=True,exist_ok=True)
G=pickle.load(open('G6.pkl','rb'))
SIZE=280; BASE_H=2.4; CAP=1.2; FR=1.8; OVL=n.CAP_OVERLAP
OUT=n.rrect(0,0,280,280,28); INN=n.rrect(0,0,258,258,12)
frame=OUT.difference(INN)
Y=G['yellow']
l2=n.only_polygons(G['pink2'].difference(frame.buffer(0.01)).difference(Y))
l1=n.only_polygons(G['pink1'].difference(l2.buffer(0.0)).difference(Y).difference(frame.buffer(0.01)))
frame_g=frame
def minpoly(g,a): return n.only_polygons(unary_union([p for p in (g.geoms if hasattr(g,'geoms') else [g]) if p.area>=a]))
l1=minpoly(l1,2.0); l2=minpoly(l2,0.5)
# openings under every cap (frame has none); parts smaller than the cap by OVL, big spans get base ribs
holes=[]
for g in (l1,l2,Y):
    h=g.buffer(-OVL,join_style=1)
    for p in (h.geoms if hasattr(h,'geoms') else [h]):
        if not p.is_empty and p.area>0.3: holes.append(n.add_ribs(p,1.0))
nut_name,nut=n.fix_spec(SIZE)
pockets=unary_union([n.hexagon(x,y,nut['af']+0.3) for x,y in n.fix_points(SIZE)])
base_g=n.only_polygons(OUT.difference(unary_union(holes)).difference(pockets))
base_g=n.only_polygons(base_g.buffer(0.12,join_style=1).buffer(-0.06,join_style=1).simplify(0.02))     # clean slivers / near-duplicate vertices
base_g=minpoly(base_g,1.5)
def clean_rings(p):
    from shapely.geometry import Polygon
    return Polygon(p.exterior,[r for r in p.interiors if Polygon(r).area>0.5])
base_g=unary_union([clean_rings(p) for p in (base_g.geoms if hasattr(base_g,'geoms') else [base_g])])
layers={'base':[(base_g,0,BASE_H)],
        'main':[(l1,BASE_H,BASE_H+CAP),(l2,BASE_H,BASE_H+FR),(frame_g,BASE_H,BASE_H+FR)],
        'accent':[(Y,BASE_H,BASE_H+CAP)],'animal':[]}
parts=[]
for slot,role in enumerate(('base','main','accent'),start=1):
    m=n.to_mesh(layers[role]); m.export(OUTDIR/f'maryam_{role}.stl'); parts.append((role,m,slot))
    print(role,len(m.faces),'faces vol',round(m.volume),'watertight',m.is_watertight,'bounds',m.bounds.round(1).tolist())
# base islands (white pieces cut off by the openings)
bl=[p for p in (base_g.geoms if hasattr(base_g,'geoms') else [base_g])]
areas=sorted(p.area for p in bl); print('base pieces',len(bl),'smallest areas',[round(a,1) for a in areas[:8]])
petg=(Path('/home/user/-sharpseek-api/cad')/'config'/'bambu_project_4fil_petg.config').read_bytes()
cols=['#F5F5F5','#F77FB5','#F9D000','#808080']
plate_x=144.0; tower=(round(plate_x+140+3,1),120,14)
write_bambu_3mf(OUTDIR/'maryam_lit_280.3mf',parts,center=(plate_x,160.0),name='maryam_lit_280',project_settings=build_project_settings(petg,cols,tower))
pickle.dump({'layers':layers,'holes':holes},open('L.pkl','wb'))
print('wrote 3MF; tower',tower)
