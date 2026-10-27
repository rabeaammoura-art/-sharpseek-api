import sys,time; sys.path.insert(0,'.')
import trimesh,numpy as np
from scipy.ndimage import distance_transform_edt
from skimage import measure
import hollow
W='/tmp/claude-0/-home-user--sharpseek-api/c69ab67c-81c4-5df2-a89e-e3b545ae3b81/scratchpad/v4/'
T=trimesh.load(W+'teddy_stage2.stl'); h=0.8
lo=T.bounds[0]-1; hi=T.bounds[1]+1
occ,xs,ys,zs=hollow.occupancy(T,lo,hi,h)
X,Y,Z=np.meshgrid(xs,ys,zs,indexing='ij')
depth=distance_transform_edt(occ)*h-h/2
protect_box=(((X>815)&(X<908)&(Y>770)&(Y<796)&(Z>10)&(Z<100))|((X>848)&(X<876)&(Y>790)&(Y<925)&(Z<66)))
dprot=distance_transform_edt(~((~occ)&protect_box))*h-h/2
def solid_and_lattice(wall,pitch,pr,br,bdz):
    f=np.minimum(depth-wall,dprot-3.0)
    wrap=lambda v,c,p:((v-c+p/2)%p)-p/2
    dx=wrap(X,861.43,pitch);dy=wrap(Y,838.8,pitch);dz=wrap(Z,15.0,bdz)
    lat=np.minimum(np.hypot(dx,dy)-pr,np.minimum(np.abs(dy)+np.abs(dz)-br,np.abs(dx)+np.abs(dz)-br))
    return f,lat
def study(wall,pitch,pr,br,bdz):
    f0,lat=solid_and_lattice(wall,pitch,pr,br,bdz)
    fb=np.pad(f0,1,constant_values=-1)
    # shell-only cavity: surfaces whose solid side is overhanging
    v,fa,n,_=measure.marching_cubes(fb,0.0,spacing=(h,h,h)); v+=np.array([xs[0]-h,ys[0]-h,zs[0]-h])
    m=trimesh.Trimesh(v,fa,process=True)
    # cavity solid volume with lattice
    f1=np.minimum(f0,lat); cav=(f1>0).sum()*h**3; solid=occ.sum()*h**3-cav
    ceil=(m.face_normals[:,2]>0.707)     # cavity normal up = solid overhang >45deg (normals of marching cubes point to decreasing f? check sign below)
    return m,solid,ceil
def run(wall,pitch,pr,br,bdz,label=''):
    m,solid,_=study(wall,pitch,pr,br,bdz)
    sgn=1 if m.volume>0 else -1; nz=sgn*m.face_normals[:,2]
    c=m.triangles_center; a=m.area_faces
    wrap=lambda v,cc,p:((v-cc+p/2)%p)-p/2
    dx=wrap(c[:,0],861.43,pitch);dy=wrap(c[:,1],838.8,pitch);dz=wrap(c[:,2],15.0,bdz)
    d=np.minimum(np.hypot(dx,dy)-pr,np.minimum(np.abs(dy)+np.abs(dz)-br,np.abs(dx)+np.abs(dz)-br))
    s60=nz>0.866; s75=nz>0.966
    print('%-22s wall %.1f p%2d r%.1f b%.1f dz%2d: solid %4.0f cm3 -> PLA %3.0f g | steep(>60deg) ceiling %5.0f mm2: >10mm from a member %5.0f, >15mm %5.0f | flat(>75deg) %5.0f mm2: >10mm %5.0f, >15mm %5.0f'%(label,wall,pitch,pr,br,bdz,solid/1000,solid*1.24e-3,a[s60].sum(),a[s60&(d>10)].sum(),a[s60&(d>15)].sum(),a[s75].sum(),a[s75&(d>10)].sum(),a[s75&(d>15)].sum()))
run(2.0,1000,0.01,0.01,1000,'shell only (no lattice)')
run(1.6,1000,0.01,0.01,1000,'shell only 1.6')
run(2.4,22,4,5,30,'approved-ish')
run(2.0,24,3,4,30)
run(2.0,28,3,3.5,40)
run(2.4,28,3,3.5,60)
run(2.4,28,3,4,40)
run(2.0,28,3,4,40)
run(2.0,28,3,3.5,60)
