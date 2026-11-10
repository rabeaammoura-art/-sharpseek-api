# usage: python 1_extract_holder_parts.py <holder.3mf>   (run inside work/)
# Splits a Bambu 3MF holder (base / figure / controller dummy) into p_Base.ply, p_Knight.ply, p_Ctrl.ply
import zipfile,re,sys,numpy as np,trimesh
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
z=zipfile.ZipFile(sys.argv[1])
t=z.read('3D/Objects/object_6.model').decode()
objs=re.split(r'<object ',t)[1:]
top=z.read('3D/3dmodel.model').decode()
tr=[np.array(x.split(),float) for x in re.findall(r'<component [^>]*transform="([^"]+)"',top)]
names=['Base','Knight','Ctrl']; out={}
for o,T,n in zip(objs,tr,names):
    V=np.array(re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"',o),dtype=float)
    F=np.array(re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"',o),dtype=int)
    M=np.eye(4); M[:3,:3]=T[:9].reshape(3,3).T; M[:3,3]=T[9:]
    m=trimesh.Trimesh(V,F,process=False); m.apply_transform(M); m.export(f'p_{n}.ply'); out[n]=m
    print(n,np.round(m.bounds,1).tolist())
fig,ax=plt.subplots(1,3,figsize=(18,8))
for a,(i,j,t_) in zip(ax,[(0,2,'front XZ'),(1,2,'side YZ'),(0,1,'top XY')]):
    for n,c in zip(names,['g','r','b']):
        v=out[n].vertices[::8]; a.scatter(v[:,i],v[:,j],s=0.3,c=c,alpha=.5)
    a.set_aspect('equal');a.grid(True);a.set_title(t_)
plt.savefig('mw.png',dpi=65)
