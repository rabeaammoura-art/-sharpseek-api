"""E30 plate -> pieces with dovetail joints (male/female). usage: make_pieces.py LEN_CM TAG 'theta_deg,d_cm;theta_deg,d_cm;...'"""
import sys, math, subprocess, numpy as np, contourpy
from contourpy import FillType
from PIL import Image, ImageDraw
from scipy.spatial import ConvexHull
from build123d import Face, Wire, Solid, Compound, export_stl
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
LEN_CM=float(sys.argv[1]); TAG=sys.argv[2]
import os
COLOR=os.environ.get('COLOR','0')=='1'
from zones import zone_masks, ZONES
LINES=[(math.radians(float(a)),float(b)) for a,b in (s.split(",") for s in sys.argv[3].split(";"))]
PXMM=5.0                                                   # 5 px per mm  (0.2 mm / px)
param=int(round(LEN_CM*10*PXMM))                           # stl_to_mask scales to this many px
subprocess.run(["python3","stl_to_mask.py",str(param)],check=True,capture_output=True)
mat=np.load(f"e30_ref/{os.environ.get('MASKPFX','')}mask_{param}.npy"); H,W=mat.shape
T=4.0; CLR=0.2; TW,TH=32.0,31.5; MAXJ=3; MINSP=6.0     # thickness, clearance (mm), bed (cm), joints per seam, min spacing (cm)
xs=(np.arange(W)+0.5)/(PXMM*10); ys=(H-0.5-np.arange(H))/(PXMM*10)            # cm
from scipy import ndimage as ndi
import os
BAND=float(os.environ.get("BAND","3.0")); WIDE=16.0                                         # seam may wander +-3 cm ; pads hide inside material wider than 16 mm
edt=ndi.distance_transform_edt(mat)/PXMM*2                  # local material width, mm
cost=np.where(mat,2.0+58.0*np.clip(1-edt/WIDE,0,1),1.0).astype(np.float32)
def at_px(x,y):
    c=np.clip(np.rint(x*10*PXMM).astype(int),0,W-1); r=np.clip(np.rint(H-1-y*10*PXMM).astype(int),0,H-1); return c,r
SEAM={}
sg=np.arange(-160,160,0.1); dk=np.arange(-BAND,BAND+1e-9,0.1); ar=np.arange(len(dk))
for i,(th,d) in enumerate(LINES):
    n=(math.cos(th),math.sin(th)); t=(-math.sin(th),math.cos(th)); p0=(d*n[0],d*n[1])
    X=p0[0]+sg[:,None]*t[0]+dk[None,:]*n[0]; Y=p0[1]+sg[:,None]*t[1]+dk[None,:]*n[1]
    inside=(X>=0)&(X<=W/PXMM/10)&(Y>=0)&(Y<=H/PXMM/10); c,r=at_px(X,Y)
    C=np.where(inside,cost[r,c],1.0)+0.02*np.abs(dk)[None,:]
    dp=np.zeros_like(C); bp=np.zeros(C.shape,np.int16); dp[0]=C[0]
    for k in range(1,len(sg)):
        P_=np.pad(dp[k-1],1,constant_values=1e9); cand=np.stack([P_[:-2],P_[1:-1],P_[2:]])
        am=np.argmin(cand,axis=0); dp[k]=C[k]+cand[am,ar]; bp[k]=ar+(am-1)
    j=int(np.argmin(dp[-1])); path=np.zeros(len(sg),int)
    for k in range(len(sg)-1,-1,-1): path[k]=j; j=int(bp[k][j])
    delta=dk[path]; delta=np.convolve(np.pad(delta,25,mode='edge'),np.ones(51)/51,mode='valid')
    SEAM[i]=(sg,delta)
lab=np.zeros((H,W),np.int8)
for i,(th,d) in enumerate(LINES):
    n=(math.cos(th),math.sin(th)); t=(-math.sin(th),math.cos(th)); p0=(d*n[0],d*n[1])
    sg_,dl=SEAM[i]; S_=(xs[None,:]-p0[0])*t[0]+(ys[:,None]-p0[1])*t[1]; U_=(xs[None,:]-p0[0])*n[0]+(ys[:,None]-p0[1])*n[1]
    lab+=((U_>np.interp(S_,sg_,dl)).astype(np.int8)<<i)
mm2=np.bincount(lab[mat].ravel(),minlength=1<<len(LINES))/PXMM**2          # merge tiny regions (< 15 cm2) into their neighbour
for r_ in range(len(mm2)):
    if 0<mm2[r_]<1500 and os.environ.get("NOMERGE","0")!="1":
        reg=(lab==r_); dil=ndi.binary_dilation(reg,iterations=int(8*PXMM))&~reg
        nb=np.bincount(lab[dil&mat].ravel(),minlength=len(mm2)); nb[r_]=0
        if nb.sum()>0: lab[reg]=int(np.argmax(nb)); print("merged tiny region",r_,"->",int(np.argmax(nb)),"(%.0f mm2)"%mm2[r_])
def px(x,y): return (x*10*PXMM, H-1-y*10*PXMM)                                   # cm -> pixel (col,row)
def at(x,y):
    c=int(round(x*10*PXMM)); r=int(round(H-1-y*10*PXMM))
    return (c,r) if 0<=c<W and 0<=r<H else None
def rrect(u0,u1,v0,v1,r=0.15):
    pts=[]
    for cu,cv,a0 in ((u1-r,v1-r,0),(u0+r,v1-r,90),(u0+r,v0+r,180),(u1-r,v0+r,270)):
        pts+= [(cu+r*math.cos(math.radians(a0+q*15)),cv+r*math.sin(math.radians(a0+q*15))) for q in range(7)]
    return pts
def shapes(pos,n,t,sgn=1):
    nm=(sgn*n[0],sgn*n[1]); W2=lambda u,v:(pos[0]+(u*t[0]+v*nm[0])/10, pos[1]+(u*t[1]+v*nm[1])/10)
    mpad=[W2(u*10,v*10) for u,v in rrect(-0.8,0.8,-1.0,0.0)]; tab=[W2(*p) for p in ((-2.5,-0.5),(2.5,-0.5),(4.0,7.0),(-4.0,7.0))]
    fpad=[W2(u*10,v*10) for u,v in rrect(-0.8,0.8,0.0,1.3)]; sock=[W2(*p) for p in ((-(2.5+CLR),-0.3),(2.5+CLR,-0.3),(4.0+CLR,7.0+CLR),(-(4.0+CLR),7.0+CLR))]
    return mpad,tab,fpad,sock
def added_area(pos,n,t):
    c0,r0=int(pos[0]*10*PXMM),int(H-1-pos[1]*10*PXMM); R=int(30*PXMM); ys0,xs0=max(0,r0-R),max(0,c0-R)
    sub=mat[ys0:r0+R,xs0:c0+R]; im=Image.new('L',(sub.shape[1],sub.shape[0]),0); d=ImageDraw.Draw(im)
    for poly in shapes(pos,n,t)[:3]: d.polygon([(px(*p)[0]-xs0,px(*p)[1]-ys0) for p in poly],fill=255)
    return float(((np.array(im)>0)&~sub).sum())/PXMM**2
# ---- find where each cut line crosses material, pick joint positions
joints=[]; step=0.02
for i,(th,d) in enumerate(LINES):
    n0=(math.cos(th),math.sin(th)); t0=(-math.sin(th),math.cos(th)); p0=(d*n0[0],d*n0[1]); sg_,dl=SEAM[i]; runs=[]; cur=None
    dd=np.gradient(dl,sg_)
    for k in range(int(-160/step),int(160/step)):
        s_=k*step; de=float(np.interp(s_,sg_,dl)); sl=float(np.interp(s_,sg_,dd))
        x=p0[0]+s_*t0[0]+de*n0[0]; y=p0[1]+s_*t0[1]+de*n0[1]
        nn=math.hypot(1,sl); t=((t0[0]+sl*n0[0])/nn,(t0[1]+sl*n0[1])/nn); n=((n0[0]-sl*t0[0])/nn,(n0[1]-sl*t0[1])/nn)
        ca=at(x-0.1*n[0],y-0.1*n[1]); cb=at(x+0.1*n[0],y+0.1*n[1]); cm=at(x,y)
        ok=cm is not None and ca is not None and cb is not None and mat[cm[1],cm[0]]
        pair=(int(lab[ca[1],ca[0]]),int(lab[cb[1],cb[0]])) if ok else None
        if ok and (pair[0]^pair[1])!=(1<<i): ok=False
        if ok and cur and cur[0]==pair: cur[2]=s_; cur[3]=((x,y),n,t)
        elif ok: cur=[pair,s_,s_,((x,y),n,t)]; runs.append(cur)
        else: cur=None
    cand=[]
    for pair,s0,s1,(pos,n,t) in runs:
        w=(s1-s0)+step; sc=(s0+s1)/2; x,y=pos; good=True
        for off in (-1.3,1.3):
            for sd in (-0.9,0.9):
                q=at(x+off*t[0]+sd*n[0],y+off*t[1]+sd*n[1])
                if q is None or int(lab[q[1],q[0]]) not in pair: good=False
        if good and w>=0.4: cand.append((added_area(pos,n,t),i,pair,sc,pos,n,t))
    chosen={}
    for w,i_,pair,sc,pos,n_,t_ in sorted(cand,key=lambda c:c[0]):
        lst=chosen.setdefault(pair,[])
        if len(lst)<MAXJ and all(abs(sc-o[3])>=MINSP for o in lst): lst.append((w,i_,pair,sc,pos,n_,t_))
    for pair,lst in chosen.items(): joints+=lst
print(f"{TAG}: {len(joints)} joints",{k:len(v) for k,v in {p:[j for j in joints if j[2]==p] for p in set(j[2] for j in joints)}.items()})
# ---- build region masks + joints
M={r:(mat&(lab==r)) for r in np.unique(lab[mat])}
def _score(m):
    yy,xx=np.where(m[::10,::10]); P=np.stack([xx*10/PXMM,yy*10/PXMM],1)
    h=P[ConvexHull(P).vertices] if len(P)>3 else P; best=9
    for a in np.radians(np.arange(0,180,2)):
        c,s_=np.cos(a),np.sin(a); u=h[:,0]*c+h[:,1]*s_; v=-h[:,0]*s_+h[:,1]*c; best=min(best,max((u.max()-u.min())/(TW*10),(v.max()-v.min())/(TH*10)))
    return best
SC={r:_score(M[r]) for r in M}
def draw(mask,pts_world,val):
    im=Image.fromarray(mask.astype(np.uint8)*255); ImageDraw.Draw(im).polygon([px(*p) for p in pts_world],fill=255 if val else 0); return np.array(im)>0
for idx,(w,i,pair,sc,pos,n,t) in enumerate(joints):
    a,b=pair; male,female=(a,b) if SC[a]<=SC[b] else (b,a); nm=n if male==a else (-n[0],-n[1])
    mpad,tab,fpad,sock=shapes(pos,n,t,1 if male==a else -1)
    M[male]=draw(draw(M[male],mpad,1),tab,1); M[female]=draw(draw(M[female],fpad,1),sock,0)
names={r:chr(65+i) for i,r in enumerate(sorted(M))}
# overlap between pieces (should be only 0)
ov=sum(int((M[a]&M[b]).sum()) for a in M for b in M if a<b); print("overlap pixels between pieces:",ov)
U=np.zeros_like(mat)
for r_ in M: U|=M[r_]
print("visible added area mm2:",round(float((U&~mat).sum())/PXMM**2),"| material removed (sockets) mm2:",round(float((mat&~U).sum())/PXMM**2))
# ---- polygonise, rotate to fit the bed, export
def rdp(pts,eps):
    pts=np.array(pts); keep=np.zeros(len(pts),bool); keep[0]=keep[-1]=True; st=[(0,len(pts)-1)]
    while st:
        a,b=st.pop()
        if b<=a+1: continue
        pa,pb=pts[a],pts[b]; ab=pb-pa; nn=math.hypot(*ab); seg=pts[a+1:b]
        dd=np.abs(ab[0]*(seg[:,1]-pa[1])-ab[1]*(seg[:,0]-pa[0]))/nn if nn else np.hypot(*(seg-pa).T)
        k=int(np.argmax(dd))
        if dd[k]>eps: keep[a+1+k]=True; st+= [(a,a+1+k),(a+1+k,b)]
    return [tuple(p) for p in pts[keep]]
def best_rot(allpts):
    P=np.array(allpts); h=P[ConvexHull(P).vertices] if len(P)>3 else P; best=None
    for a in np.radians(np.arange(0,180,1)):
        c,s=np.cos(a),np.sin(a); u=h[:,0]*c+h[:,1]*s; v=-h[:,0]*s+h[:,1]*c; du,dv=u.max()-u.min(),v.max()-v.min()
        sc=max(du/(TW*10),dv/(TH*10))
        if best is None or sc<best[0]: best=(sc,a,du,dv)
    return best
files=[]; rows=[]; cfiles=[]
ZM=zone_masks(mat.shape,PXMM,LEN_CM) if COLOR else None
for r in sorted(M):
    m=M[r]; yy,xx=np.where(m); y0,y1,x0,x1=yy.min(),yy.max(),xx.min(),xx.max(); sub=m[y0:y1+1,x0:x1+1]; h,w=sub.shape
    gen=contourpy.contour_generator(z=np.pad(sub.astype(float),1),fill_type=FillType.OuterOffset); P,O=gen.filled(0.5,np.inf)
    polys=[]
    for pts,off in zip(P,O):
        rings=[]
        for a_,b_ in zip(off[:-1],off[1:]):
            rg=[((x-1)/PXMM,(h-1-(y-1))/PXMM) for x,y in pts[a_:b_]][:-1]
            if len(rg)>=3: rings.append(rdp(rg+[rg[0]],0.05)[:-1])
        if rings: polys.append(rings)
    allp=[p for rings in polys for p in rings[0]]; sc_,ang,du,dv=best_rot(allp); c,s=math.cos(ang),math.sin(ang)
    rot=lambda q:(q[0]*c+q[1]*s,-q[0]*s+q[1]*c)
    mn=(min(rot(p)[0] for p in allp),min(rot(p)[1] for p in allp)); tr=lambda q:(rot(q)[0]-mn[0],rot(q)[1]-mn[1],0)
    sol=[]
    for rings in polys:
        wf=lambda rg:Wire.make_polygon([tr(p) for p in rg],close=True)
        sol.append(Solid.extrude(Face(wf(rings[0]),[wf(q) for q in rings[1:]]),(0,0,T)))
    f=f"e30_ref/{TAG}_{names[r]}.stl"; export_stl(Compound(sol),f); files.append(f)
    if COLOR:
        def part(mask_full,z0,hh,fname):
            sub=mask_full[y0:y1+1,x0:x1+1]
            if sub.sum()<50: return
            gen=contourpy.contour_generator(z=np.pad(sub.astype(float),1),fill_type=FillType.OuterOffset); P2,O2=gen.filled(0.5,np.inf); sl=[]
            for pts,off in zip(P2,O2):
                rings=[]
                for a_,b_ in zip(off[:-1],off[1:]):
                    rg=[((x-1)/PXMM,(h-1-(y-1))/PXMM) for x,y in pts[a_:b_]][:-1]
                    if len(rg)>=3: rings.append(rdp(rg+[rg[0]],0.05)[:-1])
                if not rings: continue
                wfz=lambda rg:Wire.make_polygon([(rot(p)[0]-mn[0],rot(p)[1]-mn[1],z0) for p in rg],close=True)
                sl.append(Solid.extrude(Face(wfz(rings[0]),[wfz(q) for q in rings[1:]]),(0,0,hh)))
            if sl: export_stl(Compound(sl),fname); cfiles.append(fname)
        zany=np.zeros_like(m)
        for zn,(col,_) in ZONES.items():
            zk=m&ZM[zn]; zany|=zk; part(zk,2.8,4.2,f"e30_ref/{TAG}_{names[r]}_{col}.stl")
        part(m,0.0,2.8,f"e30_ref/{TAG}_{names[r]}_black_base.stl"); part(m&~zany,2.8,1.2,f"e30_ref/{TAG}_{names[r]}_black_top.stl")
    rows.append((names[r],du/10,dv/10,sc_<=1,sub.sum()/PXMM**2/100)); print(f"  piece {names[r]}: {du/10:.1f} x {dv/10:.1f} cm on plate, fits {sc_<=1}, material {sub.sum()/PXMM**2/100:.0f} cm2")
# ---- overview picture
fig,ax=plt.subplots(figsize=(13,6.8)); cols=["#e07a5f","#81b29a","#f2cc8f","#9b5de5","#00b4d8","#3d405b","#6a994e","#bc4749"]
img=np.ones(M[sorted(M)[0]][::5,::5].shape+(3,))*0.97
for k,r in enumerate(sorted(M)): sm=M[r][::5,::5]; img[sm]=matplotlib.colors.to_rgb(cols[k%8])
ax.imshow(img,extent=[0,W/PXMM/10,0,H/PXMM/10],origin="upper",interpolation="nearest")
for w,i,pair,sc,pos,n,t in joints: ax.plot(*pos,marker="D",color="k",ms=7,mfc="yellow")
for k,r in enumerate(sorted(M)):
    yy,xx=np.where(M[r]); ax.text(xx.mean()/PXMM/10,(H-yy.mean())/PXMM/10,names[r],fontsize=18,fontweight="bold",ha="center",bbox=dict(boxstyle="round",fc=(1,1,1,.8),ec="none"))
ax.set_xticks(range(0,int(LEN_CM)+1,10)); ax.set_yticks(range(0,int(H/PXMM/10)+1,10)); ax.grid(True,color="#ccc",lw=.5); ax.set_xlabel("cm"); ax.set_ylabel("cm")
ax.set_title(f"{TAG}: {LEN_CM:.0f} cm, {len(M)} pieces, {len(joints)} dovetail joints (yellow diamonds)"); fig.tight_layout(); fig.savefig(f"e30_ref/{TAG}_plan.png",dpi=100)
open(f"e30_ref/{TAG}_files.txt","w").write("\n".join(files))
if COLOR: open(f"e30_ref/{TAG}_colorfiles.txt","w").write("\n".join(cfiles))
