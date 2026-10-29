import numpy as np, cv2, json, sys
from scipy import ndimage as ndi
from skimage.morphology import skeletonize, disk
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
import shapely

SRC='/root/.claude/uploads/a57135a0-8d19-5b2d-990f-f37d913efb05/d6ffc96b-image.jpg'
OUT='/tmp/claude-0/-home-user--sharpseek-api/a57135a0-8d19-5b2d-990f-f37d913efb05/scratchpad/out'
W_MM=900.0; T_MM=5.0; MINW=2.5; BRIDGE=3.0
UP=3
img=cv2.imread(SRC,cv2.IMREAD_GRAYSCALE)
h0,w0=img.shape
mm_px=W_MM/(w0*UP)
H_MM=h0*W_MM/w0
big=cv2.resize(img,(w0*UP,h0*UP),interpolation=cv2.INTER_CUBIC)
mask=(big<128)
# remove specks (area in mm^2)
lab,n=ndi.label(mask,structure=np.ones((3,3)))
areas=ndi.sum(mask,lab,range(1,n+1))
min_area_mm2=25.0
keep=np.zeros(n+1,bool); keep[1:]=areas*mm_px**2>=min_area_mm2
print('components raw',n,'kept',keep.sum())
mask=keep[lab]
ys,xs=np.nonzero(mask)
y0,y1,x0,x1=ys.min(),ys.max()+1,xs.min(),xs.max()+1
mask=mask[y0:y1,x0:x1]
mm_px=W_MM/(x1-x0)
H_MM=(y1-y0)*mm_px
print('crop px',x1-x0,y1-y0,'H_MM',H_MM)
# fill pin-holes smaller than 25mm2 (white specks inside black)
inv=~mask
l2,n2=ndi.label(inv)
a2=ndi.sum(inv,l2,range(1,n2+1))
fill=np.zeros(n2+1,bool); fill[1:]=a2*mm_px**2<25.0
mask|=fill[l2]
# enforce min line width: union skeleton thickened to MINW
r=int(np.ceil(MINW/2/mm_px))
sk=skeletonize(mask)
thick=cv2.dilate(sk.astype(np.uint8),cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*r+1,2*r+1)))>0
mask|=thick
# light smoothing
m8=mask.astype(np.uint8)*255
m8=cv2.GaussianBlur(m8,(0,0),1.5); mask=m8>127
# connect components with bridges (MST, nearest points)
def components(m):
    return ndi.label(m,structure=np.ones((3,3)))
lab,n=components(mask)
print('components before bridging',n)
bridges=[]
if n>1:
    # boundary points per component
    pts=[]
    edge=mask & ~ndi.binary_erosion(mask)
    ys,xs=np.nonzero(edge); ls=lab[ys,xs]
    from scipy.spatial import cKDTree
    P=np.stack([xs,ys],1)
    groups=[P[ls==i] for i in range(1,n+1)]
    trees=[cKDTree(g) for g in groups]
    # candidate edges: for each pair, nearest distance (use subsample for speed)
    import itertools
    cand=[]
    for i in range(n):
        for j in range(i+1,n):
            d,k=trees[j].query(groups[i][::2] if len(groups[i])>2000 else groups[i])
            a=np.argmin(d); src=(groups[i][::2] if len(groups[i])>2000 else groups[i])[a]
            cand.append((d[a],i,j,src,groups[j][k[a]]))
    cand.sort(key=lambda c:c[0])
    par=list(range(n))
    def f(x):
        while par[x]!=x: par[x]=par[par[x]]; x=par[x]
        return x
    for d,i,j,a,b in cand:
        if f(i)!=f(j):
            par[f(i)]=f(j); bridges.append((a,b,d*mm_px))
    bw=int(round(BRIDGE/mm_px))
    m8=mask.astype(np.uint8)*255
    for a,b,d in bridges:
        cv2.line(m8,tuple(int(v) for v in a),tuple(int(v) for v in b),255,bw,cv2.LINE_8)
    mask=m8>127
    print('bridges',len(bridges),'max len mm',max(b[2] for b in bridges),'sum',sum(b[2] for b in bridges))
lab,n=components(mask); print('components after',n)
# vectorize
cs,hier=cv2.findContours(mask.astype(np.uint8),cv2.RETR_CCOMP,cv2.CHAIN_APPROX_NONE)
hier=hier[0]
def topoly(c):
    p=c[:,0,:].astype(float)*mm_px
    p[:,1]=H_MM-p[:,1]   # flip y
    return p
polys=[]
for i,c in enumerate(cs):
    if hier[i][3]!=-1 or len(c)<4: continue
    shell=topoly(c)
    holes=[]; k=hier[i][2]
    while k!=-1:
        if len(cs[k])>=4: holes.append(topoly(cs[k]))
        k=hier[k][0]
    pg=Polygon(shell,holes)
    if not pg.is_valid: pg=pg.buffer(0)
    polys.append(pg)
geom=unary_union(polys)
geom=geom.simplify(0.15,preserve_topology=True)
geom=geom.buffer(0)
polys=list(geom.geoms) if isinstance(geom,MultiPolygon) else [geom]
print('polygons',len(polys),'holes',sum(len(p.interiors) for p in polys),'verts',sum(len(p.exterior.coords)+sum(len(r.coords) for r in p.interiors) for p in polys))
# min width check in vector: opening by MINW/2 - tiny tolerance should preserve area
tol=0.03
opened=geom.buffer(-(MINW/2-tol)).buffer(MINW/2-tol)
lost=geom.difference(opened).area
print('area mm2',geom.area,'area lost by opening(2.5mm)',lost, 'frac',lost/geom.area)
# components
print('vector components',len(polys))
import pickle; pickle.dump((polys,W_MM,H_MM,T_MM),open(OUT+'/geom.pkl','wb'))
