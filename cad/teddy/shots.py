import sys,trimesh,numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
S='/tmp/claude-0/-home-user--sharpseek-api/c69ab67c-81c4-5df2-a89e-e3b545ae3b81/scratchpad/'
def shot(meshes,name,box,res,axis='y',sign=1):
    # view along +y from front (default) ; axis 'y-' = from back ; 'z' = from below/ top
    (x0,x1,z0,z1)=box
    xs=np.arange(x0,x1,res); zs=np.arange(z1,z0,-res)
    X,Z=np.meshgrid(xs,zs)
    if axis=='y':
        o=np.c_[X.ravel(),np.full(X.size,600.),Z.ravel()]; d=[0,1.,0]
    elif axis=='-y':
        o=np.c_[(2*861.43-X).ravel(),np.full(X.size,1100.),Z.ravel()]; d=[0,-1.,0]
    elif axis=='up':  # from below looking up; X=x, Z=y
        o=np.c_[X.ravel(),Z.ravel(),np.full(X.size,-300.)]; d=[0,0,1.]
    D=np.full(X.size,np.inf);N=np.zeros((X.size,3))
    for m in meshes:
        loc,ir,it=m.ray.intersects_location(o,np.tile(d,(len(o),1)),multiple_hits=False)
        dist=np.linalg.norm(loc-o[ir],axis=1)
        upd=dist<D[ir]; ii=ir[upd]; D[ii]=dist[upd]; N[ii]=m.face_normals[it[upd]]
    L=np.array([-0.35,-0.6,0.7]) if axis=='y' else np.array([0.35,0.6,0.7])
    if axis=='up': L=np.array([0.3,0.3,-0.9])
    L=L/np.linalg.norm(L)
    sh=np.clip(np.abs(N@L),0,1)
    img=np.where(np.isinf(D)[...,None],1,0.15+0.85*sh[...,None]*np.array([0.95,0.75,0.55]))
    img=np.clip(img.reshape(X.shape+(3,)),0,1)
    fig=plt.figure(figsize=(11,11*(z1-z0)/(x1-x0)));plt.imshow(img,extent=[x0,x1,z0,z1]);plt.tight_layout();plt.savefig(S+name,dpi=70);plt.close()
