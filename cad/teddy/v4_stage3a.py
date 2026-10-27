import sys,time,pickle; sys.path.insert(0,'.')
import trimesh,numpy as np
import hollow
W='/tmp/claude-0/-home-user--sharpseek-api/c69ab67c-81c4-5df2-a89e-e3b545ae3b81/scratchpad/v4/'
t0=time.time()
T=trimesh.load(W+'teddy_stage2.stl')
lo=(T.bounds[0]-1.0); hi=(T.bounds[1]+1.0)
occ,xs,ys,zs=hollow.occupancy(T,lo,hi); print('occupancy',occ.shape,'solid fraction %.3f'%occ.mean(),'volume est %.0f vs mesh %.0f'%(occ.sum()*hollow.H**3,T.volume),round(time.time()-t0))
f=hollow.cavity_field(occ,xs,ys,zs); print('field',f.shape,'cavity fraction %.3f'%(f>0).mean(),round(time.time()-t0))
np.save(W+'field.npy',f); np.save(W+'axes.npy',np.array([xs[0],ys[0],zs[0]]))
parts=hollow.cavity_mesh(f,xs,ys,zs); print('cavity components',len(parts),[ (len(p.faces),round(p.volume)) for p in parts],round(time.time()-t0))
for i,p in enumerate(parts): p.export(W+'cavity_%d.stl'%i)
