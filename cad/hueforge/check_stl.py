import numpy as np,sys
d=np.fromfile(sys.argv[1],dtype=np.uint8)[84:].view([('n','<f4',3),('v','<f4',(3,3)),('a','<u2')])
V=d['v'].reshape(-1,3)
u,inv=np.unique(np.round(V,4),axis=0,return_inverse=True); F=inv.reshape(-1,3)
E=np.concatenate([F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]])
key=lambda e: e[:,0].astype(np.int64)*10**8+e[:,1]
fwd=np.unique(key(E),return_counts=True); rev=key(E[:,::-1])
print('tris',len(F),'verts',len(u))
print('directed edges used >1 times:',(fwd[1]>1).sum())
print('edges without opposite partner:',(~np.isin(key(E),rev)).sum())
# signed volume
v0,v1,v2=d['v'][:,0].astype(np.float64),d['v'][:,1].astype(np.float64),d['v'][:,2].astype(np.float64)
print('volume mm3',np.einsum('ij,ij->i',v0,np.cross(v1,v2)).sum()/6, 'bbox',V.min(0),V.max(0))
