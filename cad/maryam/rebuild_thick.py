"""Rebuild the backlit Maryam plaque from R.pkl (recover_from_stl.py) with the Kitty line art grown by GROW mm per side (0 = identical rebuild, check): rebuild_thick.py 0.4 <outdir>. Needs manifold3d (without it the pink mesh is not watertight)."""
import sys, pickle; sys.path.insert(0,'/home/user/-sharpseek-api/cad')
from pathlib import Path
import numpy as np, trimesh
from shapely.geometry import box, Polygon
from shapely.ops import unary_union
import newborn_plaque as n
from threemf import build_project_settings, write_bambu_3mf
GROW=float(sys.argv[1]); OUTDIR=Path(sys.argv[2]); OUTDIR.mkdir(parents=True,exist_ok=True)
R=pickle.load(open('R.pkl','rb'))
SIZE=280; BASE_H=2.4; CAP=1.2; FR=1.8; OVL=n.CAP_OVERLAP
OUT=n.rrect(0,0,280,280,28); INN=n.rrect(0,0,258,258,12); frame=OUT.difference(INN)
Y=n.only_polygons(R['Y'])
def geoms(g): return list(g.geoms) if hasattr(g,'geoms') else [g]
def minpoly(g,a): return n.only_polygons(unary_union([p for p in geoms(g) if p.area>=a]))
l2=n.only_polygons(R['top'].difference(frame.buffer(0.05)))
l1=n.only_polygons(R['low'].difference(R['top'].buffer(0.01)))
def clean_rings(p): return Polygon(p.exterior,[r for r in p.interiors if Polygon(r).area>0.5])
kreg=box(-50,27.5,52,127)
kitty=[p for p in geoms(l2) if kreg.contains(p)]; rest=[p for p in geoms(l2) if not kreg.contains(p)]
print('kitty line pieces',len(kitty),'area',round(sum(p.area for p in kitty),1))
if GROW>0:
    kg=unary_union(kitty).buffer(GROW,join_style=1).difference(Y.buffer(0.3))
    kg=kg.buffer(0.06,join_style=1).buffer(-0.12,join_style=1).buffer(0.06,join_style=1)
    kg=unary_union([clean_rings(p) for p in geoms(n.only_polygons(kg))])
    l2=n.only_polygons(unary_union(rest+[kg]))
    l1=n.only_polygons(l1.difference(kg))
l1=minpoly(l1,2.0); l2=minpoly(l2,0.5)
holes=[]
for g in (l1,l2,Y):
    h=g.buffer(-OVL,join_style=1)
    for p in geoms(h):
        if not p.is_empty and p.area>0.3: holes.append(n.add_ribs(p,1.0))
nut_name,nut=n.fix_spec(SIZE)
pockets=unary_union([n.hexagon(x,y,nut['af']+0.3) for x,y in n.fix_points(SIZE)])
base_g=n.only_polygons(OUT.difference(unary_union(holes)).difference(pockets))
base_g=n.only_polygons(base_g.buffer(0.12,join_style=1).buffer(-0.06,join_style=1).simplify(0.02))
base_g=minpoly(base_g,1.5)
base_g=unary_union([clean_rings(p) for p in geoms(base_g)])
print('base area new',round(base_g.area,1),'old',round(R['base'].area,1))
caps=unary_union([l1,l2,Y,frame])
print('opening not covered by a cap mm2:',round(OUT.difference(base_g).difference(pockets.buffer(0.2)).difference(caps).area,3))
kopen=unary_union(holes).intersection(kreg).intersection(l2.buffer(0))
print('kitty line opening area mm2:',round(kopen.area,1))
layers={'base':[(base_g,0,BASE_H)],'main':[(l1,BASE_H,BASE_H+CAP),(l2,BASE_H,BASE_H+FR),(frame,BASE_H,BASE_H+FR)],'accent':[(Y,BASE_H,BASE_H+CAP)],'animal':[]}
parts=[]
for slot,role in enumerate(('base','main','accent'),start=1):
    m=n.to_mesh(layers[role]); m.export(OUTDIR/f'maryam_{role}.stl'); parts.append((role,m,slot))
    print(role,len(m.faces),'vol',round(m.volume),'watertight',m.is_watertight,m.bounds.round(1).tolist())
bl=geoms(base_g); print('base pieces',len(bl),'smallest',[round(a,1) for a in sorted(p.area for p in bl)[:6]])
petg=(Path('/home/user/-sharpseek-api/cad')/'config'/'bambu_project_4fil_petg.config').read_bytes()
cols=['#F5F5F5','#F77FB5','#F9D000','#808080']
plate_x=144.0; tower=(round(plate_x+140+3,1),120,14)
write_bambu_3mf(OUTDIR/'maryam_lit_280.3mf',parts,center=(plate_x,160.0),name='maryam_lit_280',project_settings=build_project_settings(petg,cols,tower))
pickle.dump({'layers':layers,'holes':holes,'l1':l1,'l2':l2,'Y':Y,'frame':frame,'base':base_g},open(OUTDIR/'L.pkl','wb'))
