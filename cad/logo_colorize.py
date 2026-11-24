#!/usr/bin/env python3
"""Split the owner's flat 3D ZT logo 3MF (two 0.6 mm objects) into NAVY and ORANGE polygons using the colour picture.

    python cad/logo_colorize.py LOGO.3mf PICTURE.webp OUT.pkl [PREVIEW.png]

The picture (RGBA, transparent background) is fitted onto the 3D object footprint (Nelder-Mead on IoU), pixels are classified
orange/navy, the ZONE TECH object is split: ZONE navy, TECH + underline bar orange. OUT.pkl = (navy_wkb, orange_wkb, foot_wkb, uc, vc)
in logo mm (v up). Inputs are the owner's brand files and are NOT in git; keep OUT.pkl under cad/out/ (git-ignored).
"""
import sys
import zipfile,re,numpy as np
from PIL import Image,ImageFilter,ImageDraw
from shapely.geometry import Polygon,box,MultiPolygon
from shapely.ops import unary_union
from scipy import ndimage as ndi
from scipy.optimize import minimize
lz=zipfile.ZipFile(sys.argv[1])
lt=lz.read('3D/3dmodel.model').decode()
foot={};allv=[]
for m in re.finditer(r'<object id="(\d+)" name="([^"]+)".*?</object>',lt,re.S):
    s=m.group(0);v=np.array(re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"',s),float);allv.append(v)
    tr=np.array(re.findall(r'v1="(\d+)" v2="(\d+)" v3="(\d+)"',s),int)
    polys=[]
    for t in tr:
        if all(abs(v[i][2]-0.6)<1e-3 for i in t):
            p=Polygon([(round(v[i][0],4),round(v[i][1],4)) for i in t])
            if p.area>1e-9: polys.append(p)
    foot[m.group(2)]=unary_union(polys)
    print(m.group(2),foot[m.group(2)].geom_type,round(foot[m.group(2)].area,1))
allv=np.vstack(allv);uc=(allv[:,0].min()+allv[:,0].max())/2;vc=(allv[:,1].min()+allv[:,1].max())/2
G3=foot['3D_With_White_Border'];GT=foot['ZONE_TECH_InterBlack']
# ---- raster of 3D footprint
P=10;u0,u1,v0,v1=0,72,12,86
Wp,Hp=(u1-u0)*P,(v1-v0)*P
def rast(g):
    im=Image.new('L',(Wp,Hp),0);d=ImageDraw.Draw(im)
    gs=g.geoms if hasattr(g,'geoms') else [g]
    for p in gs:
        d.polygon([((x-u0)*P,(v1-y)*P) for x,y in p.exterior.coords],fill=255)
        for r in p.interiors: d.polygon([((x-u0)*P,(v1-y)*P) for x,y in r.coords],fill=0)
    return np.array(im)>0
M=rast(G3);Mf=ndi.binary_fill_holes(M)
img=Image.open(sys.argv[2]).convert('RGBA')
A=np.array(img);ink=A[...,3]>128;ink[935:]=False
rgb=A[...,:3].astype(int)
uu=(np.arange(Wp)+0.5)/P+u0;vv=v1-(np.arange(Hp)+0.5)/P
UU,VV=np.meshgrid(uu,vv)
def sample(p,arr):
    a,b,tx,ty=p
    px=np.clip(((UU-tx)/a).astype(int),0,arr.shape[1]-1);py=np.clip(((ty-VV)/b).astype(int),0,arr.shape[0]-1)
    ok=(((UU-tx)/a)>=0)&(((UU-tx)/a)<arr.shape[1])&(((ty-VV)/b)>=0)&(((ty-VV)/b)<arr.shape[0])
    return arr[py,px]*(ok[...,None] if arr.ndim==3 else ok)
def cost(p):
    s=sample(p,ink.astype(float));return -( (s>0.5)&Mf).sum()/(((s>0.5)|Mf).sum())
p0=[0.0681,0.0714,3.37-185*0.0681,82.63]
best=minimize(cost,p0,method='Nelder-Mead',options=dict(xatol=1e-4,fatol=1e-5,maxiter=400))
print('IoU',-best.fun,best.x, 'init',-cost(p0))
p=best.x
col=sample(p,rgb).astype(int);r,g,b=col[...,0],col[...,1],col[...,2]
lab=np.full(r.shape,-1,np.int8)  # 1 orange 0 navy
lab[(r>b+40)]=1
lab[(b>=r)&(b>g)]=0
unk=(lab<0)|~Mf
idx=ndi.distance_transform_edt(unk,return_distances=False,return_indices=True)
lab=lab[idx[0],idx[1]]
lab=np.array(Image.fromarray((lab.astype('uint8')*255)).filter(ImageFilter.MedianFilter(9)))>127
lab&=Mf
orange_ras=lab
# raster -> polygons (run merged boxes)
def ras2poly(m):
    boxes=[]
    for y in range(m.shape[0]):
        row=m[y];d=np.diff(np.r_[0,row.astype(np.int8),0]);st=np.where(d==1)[0];en=np.where(d==-1)[0]
        for s,e in zip(st,en): boxes.append(box(u0+s/P,v1-(y+1)/P,u0+e/P,v1-y/P))
    return unary_union(boxes)
OR=ras2poly(orange_ras)
G3_or=G3.intersection(OR);G3_na=G3.difference(OR)
# text: split ZONE / TECH / underline bar
bar=GT.intersection(box(-1,0,80,3.2));let=GT.intersection(box(-1,3.2,80,20))
pcs=list(let.geoms) if hasattr(let,'geoms') else [let]
pcs=[q for q in pcs if q.area>0.5]
xs=sorted(pcs,key=lambda q:q.bounds[0])
gaps=[(xs[i+1].bounds[0]-xs[i].bounds[2],i) for i in range(len(xs)-1)];gi=max(gaps)[1]
print('letters',len(xs),'gap',round(max(gaps)[0],2),'ZONE n',gi+1,'TECH n',len(xs)-gi-1)
zone=unary_union(xs[:gi+1]);tech=unary_union(xs[gi+1:]+[bar])
navy=unary_union([G3_na,zone]);orange=unary_union([G3_or,tech])
print('areas navy',round(navy.area,1),'orange',round(orange.area,1),'total',round(G3.area+GT.area,1))
import pickle
pickle.dump((navy.wkb,orange.wkb,unary_union([G3,GT]).wkb,uc,vc),open(sys.argv[3],'wb'))
# preview (reading view)
S=12;Wc,Hc=72*S,86*S
pv=Image.new('RGB',(Wc,Hc),(255,255,255));dd=ImageDraw.Draw(pv)
def draw(gm,c):
    gs=gm.geoms if hasattr(gm,'geoms') else [gm]
    for q in gs:
        if q.geom_type!='Polygon': continue
        dd.polygon([(x*S,(85-y)*S) for x,y in q.exterior.coords],fill=c)
        for r_ in q.interiors: dd.polygon([(x*S,(85-y)*S) for x,y in r_.coords],fill=(255,255,255))
draw(navy,(28,52,160));draw(orange,(255,110,20))
if len(sys.argv)>4: pv.save(sys.argv[4])
