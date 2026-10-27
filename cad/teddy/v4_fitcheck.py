import sys,trimesh,numpy as np
sys.path.insert(0,'.')
import teddy_edit as te
W='/tmp/claude-0/-home-user--sharpseek-api/c69ab67c-81c4-5df2-a89e-e3b545ae3b81/scratchpad/v4/'
T=trimesh.load(sys.argv[1] if len(sys.argv)>1 else W+'teddy_stage1.stl'); L=trimesh.load(sys.argv[2] if len(sys.argv)>2 else W+'litho_stage1.stl')
def vol(a,b):
    r=te.boolean('intersection',[a,b]); return float(r.volume) if len(r.faces) else 0.0
print('seated interference volume: %.3f mm3'%vol(T,L))
for d in [0.05,0.2,0.5,1,2,3,5,8,12,25]:
    Ld=L.copy(); Ld.apply_translation([0,-d,0]); print(' pulled %5.2f mm toward the viewer: overlap %.3f mm3'%(d,vol(T,Ld)))
for d in [0.05,0.1,0.3]:
    Ld=L.copy(); Ld.apply_translation([0,d,0]); print(' pushed %5.2f mm deeper: overlap %.3f mm3'%(d,vol(T,Ld)))
# clearance distribution (distance from litho rim surfaces to teddy)
from trimesh.proximity import closest_point
V=L.vertices; sel=np.where(V[:,1]>774.2)[0]; rng=np.random.default_rng(0); sel=rng.choice(sel,min(6000,len(sel)),replace=False)
_,d,_=closest_point(T,V[sel])
print('clearance of litho rim/skirt/bridge vertices to the teddy: percentiles 0/1/5/50/95:',np.round(np.percentile(d,[0,1,5,50,95]),3),' <0.15mm: %.1f%%'%(100*(d<0.15).mean()))
