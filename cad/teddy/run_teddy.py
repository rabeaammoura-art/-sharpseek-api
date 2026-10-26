import sys,glob,time
sys.path.insert(0,'.')
import trimesh
import heart,teddy_edit as te
U='/root/.claude/uploads/c69ab67c-81c4-5df2-a89e-e3b545ae3b81/'
S='/tmp/claude-0/-home-user--sharpseek-api/c69ab67c-81c4-5df2-a89e-e3b545ae3b81/scratchpad/out/'
T=trimesh.load(glob.glob(U+'*teddy_rear*')[0])
H=heart.heart_from_teddy(T)
t=time.time()
a=te.new_frame(T,H); print('frame',a.is_watertight,a.volume,time.time()-t)
b=te.seal_back_and_bottom_channel(a); print('seal',b.is_watertight,b.volume,time.time()-t)
b.export(S+'teddy_stage_b.stl')
c=te.carve_details(b); print('carve',len(c.faces),c.is_watertight,c.volume,time.time()-t)
c.export(S+'teddy_v2_raw.stl')
