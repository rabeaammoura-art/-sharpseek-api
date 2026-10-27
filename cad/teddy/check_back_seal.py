import sys,trimesh,numpy as np
cx,cz=861.43,57.5
def report(path):
    T=trimesh.load(path)
    V=T.vertices; N=T.vertex_normals
    r=np.hypot(V[:,0]-cx,V[:,2]-cz)
    m=(V[:,1]>900)&(r<24)
    # reference smooth surface: poly fit (deg 4) on the annulus 14..24, evaluated analytically
    a=m&(r>14)
    dx,dz=V[a,0]-cx,V[a,2]-cz
    terms=lambda x,z:np.stack([x**i*z**k for i in range(5) for k in range(5-i)],-1)
    coef,*_=np.linalg.lstsq(terms(dx,dz),V[a,1],rcond=None)
    def f(x,z): return terms(x,z)@coef
    b=m&(r<13)
    x,z=V[b,0]-cx,V[b,2]-cz
    dy=V[b,1]-f(x,z)
    h=1e-3
    fx=(f(x+h,z)-f(x-h,z))/(2*h); fz=(f(x,z+h)-f(x,z-h))/(2*h)
    nref=np.c_[-fx,np.ones_like(fx),-fz]; nref/=np.linalg.norm(nref,axis=1,keepdims=True)
    ang=np.degrees(np.arccos(np.clip((N[b]*nref).sum(1),-1,1)))
    rb=r[b]
    print(path)
    print(' height dev from smooth surface: max %.3f mm, p99 %.3f'%(np.abs(dy).max(),np.percentile(np.abs(dy),99)))
    print(' vertex-normal dev: max %.2f deg, p99 %.2f deg, p50 %.2f'%(ang.max(),np.percentile(ang,99),np.median(ang)))
    for lo,hi in [(0,5),(5,7),(7,9),(9,11),(11,13)]:
        s=(rb>=lo)&(rb<hi)
        if s.any(): print('  r %2d-%2d: n=%5d max dev %.2f deg  height %.3f'%(lo,hi,s.sum(),ang[s].max(),np.abs(dy[s]).max()))
for p in sys.argv[1:]: report(p)
