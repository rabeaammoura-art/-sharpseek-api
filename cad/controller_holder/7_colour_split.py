# usage: ../../../.venv-cad/bin/python ../7_colour_split.py   (run inside work/, reads holder_final.stl) -> holder_4colour.3mf
# ROUGH colour split by height bands for a time estimate (real painting is done in Bambu Studio):
# slot 1 red = shirt + socks, slot 2 green = base + shorts, slot 3 skin = legs / forearms / head, slot 4 black = shoes + hair.
import sys,pathlib,trimesh,numpy as np
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from threemf import build_project_settings, write_bambu_3mf
M=trimesh.load('holder_final.stl')
def box(z0,z1,y0=-200,y1=200):
    b=trimesh.creation.box([400,y1-y0,z1-z0]); b.apply_translation([0,(y0+y1)/2,(z0+z1)/2]); return b
def cut(b): return M.intersection(b,engine='manifold')
top=M.bounds[1][2]+1
regs=[('base',box(-1,9.9),2),('shoes',box(9.9,20),4),('socks',box(20,40),1),('knees',box(40,51),3),('shorts',box(51,76),2),
      ('shirt',box(76,118,-4,200),1),('forearms',box(76,118,-200,-4),3),('face',box(118,141),3),('hair',box(141,top),4)]
parts=[]
for n,b,slot in regs:
    p=cut(b); parts.append((n,p,slot)); print(n,slot,round(p.volume/1000,1),'cm3')
print('sum',round(sum(p.volume for _,p,_ in parts)/1000,1),'of',round(M.volume/1000,1))
tpl=(pathlib.Path(__file__).resolve().parents[1]/'config'/'bambu_project_4fil_pla.config').read_bytes()
cx,cy=120.0,160.0
ps=build_project_settings(tpl,['#D21F2B','#1E8A3C','#E0AC88','#101010'],(215.0,140.0,40.0))
write_bambu_3mf('holder_4colour.3mf',parts,center=(cx,cy),name='holder_4colour',project_settings=ps)
