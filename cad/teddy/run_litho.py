import sys,glob
sys.path.insert(0,'.')
import trimesh
import heart,litho
U='/root/.claude/uploads/c69ab67c-81c4-5df2-a89e-e3b545ae3b81/'
S='/tmp/claude-0/-home-user--sharpseek-api/c69ab67c-81c4-5df2-a89e-e3b545ae3b81/scratchpad/out/'
T=trimesh.load(glob.glob(U+'*teddy_rear*')[0])
H=heart.heart_from_teddy(T)
m,_=litho.build(H,U+'5330ae15-image.jpg',(861.43,50.0))
print(len(m.faces),m.is_watertight,m.volume,m.bounds)
m.export(S+'litho_v2.stl')
