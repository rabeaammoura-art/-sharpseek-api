import numpy as np, trimesh
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
def view(meshes,colors,name,azim,elev,res=0.35,center=(861.4,838.8,100),size=(240,240),light=None,backlit=None):
    S='/tmp/claude-0/-home-user--sharpseek-api/c69ab67c-81c4-5df2-a89e-e3b545ae3b81/scratchpad/'
    az,el=np.radians(azim),np.radians(elev)
    # camera direction (from camera toward scene): azim 0 = looking along +y (front view), positive turns camera to +x side
    d=np.array([-np.sin(az)*np.cos(el),np.cos(az)*np.cos(el),-np.sin(el)])
    d=np.array([np.sin(az)*np.cos(el)*-1, np.cos(az)*np.cos(el), -np.sin(el)])
    d/=np.linalg.norm(d)
    right=np.cross(d,[0,0,1.]);right/=np.linalg.norm(right)
    up=np.cross(right,d)
    W,H=int(size[0]/res),int(size[1]/res)
    us=(np.arange(W)-W/2)*res; vs=(H/2-np.arange(H))*res
    U,V=np.meshgrid(us,vs)
    c=np.array(center)
    o=c+U[...,None]*right+V[...,None]*up-d*600
    o=o.reshape(-1,3); dirs=np.tile(d,(len(o),1))
    D=np.full(len(o),np.inf);N=np.zeros((len(o),3));C=np.zeros((len(o),3))
    for m,col in zip(meshes,colors):
        loc,ir,it=m.ray.intersects_location(o,dirs,multiple_hits=False)
        dist=np.linalg.norm(loc-o[ir],axis=1)
        upd=dist<D[ir]; ii=ir[upd]; D[ii]=dist[upd]; N[ii]=m.face_normals[it[upd]]; C[ii]=col
    Ld=-d+0.6*(-right)+0.8*up if light is None else light
    Ld=Ld/np.linalg.norm(Ld)
    nn=N*np.sign(-(N@d))[:,None]
    lam=np.clip(nn@Ld,0,1)
    img=np.where(np.isinf(D)[:,None],1.0,(0.28+0.72*lam)[:,None]*C)
    img=np.clip(img.reshape(H,W,3),0,1)
    plt.figure(figsize=(size[0]/size[1]*8,8));plt.imshow(img);plt.axis('off');plt.tight_layout(pad=0);plt.savefig(S+name,dpi=80);plt.close()
