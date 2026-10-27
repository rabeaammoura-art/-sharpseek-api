import sys,time; sys.path.insert(0,'.')
import trimesh,numpy as np
import teddy_edit as te, base_mods
W='/tmp/claude-0/-home-user--sharpseek-api/c69ab67c-81c4-5df2-a89e-e3b545ae3b81/scratchpad/v4/'
t0=time.time()
T=trimesh.load(W+'teddy_stage1.stl')
T=base_mods.back_and_cable(T); print('back+cable',len(T.faces),T.is_watertight,round(time.time()-t0))
T=te.carve_details(T,max_edge=0.5); print('smile+paws',len(T.faces),T.is_watertight,round(time.time()-t0))
T.export(W+'teddy_stage2.stl')
