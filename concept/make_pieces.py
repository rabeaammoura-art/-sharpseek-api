"""E30 plate -> pieces with dovetail joints (male/female). usage: make_pieces.py LEN_CM TAG 'theta_deg,d_cm;theta_deg,d_cm;...'"""
import sys, math, subprocess, numpy as np, contourpy
from contourpy import FillType
from PIL import Image, ImageDraw
from scipy.spatial import ConvexHull
from build123d import Face, Wire, Solid, Compound, export_stl
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
LEN_CM=float(sys.argv[1]); TAG=sys.argv[2]
LINES=[(math.radians(float(a)),float(b)) for a,b in (s.split(",") for s in sys.argv[3].split(";"))]
PXMM=5.0                                                   # 5 px per mm  (0.2 mm / px)
param=int(round(LEN_CM*10*PXMM))                           # stl_to_mask scales to this many px
subprocess.run(["python3","stl_to_mask.py",str(param)],check=True,capture_output=True)
mat=np.load(f"e30_ref/mask_{param}.npy"); H,W=mat.shape
T=4.0; CLR=0.2; TW,TH=32.0,31.5; MAXJ=5; MINSP=6.0     # thickness, clearance (mm), bed (cm), joints per seam, min spacing (cm)
xs=(np.arange(W)+0.5)/(PXMM*10); ys=(H-0.5-np.arange(H))/(PXMM*10)            # cm
lab=np.zeros((H,W),np.int8)
for i,(th,d) in enumerate(LINES): lab+=(((xs[None,:]*math.cos(th)+ys[:,None]*math.sin(th))>d).astype(np.int8)<<i)
def px(x,y): return (x*10*PXMM, H-1-y*10*PXMM)                                   # cm -> pixel (col,row)
def at(x,y):
    c=int(round(x*10*PXMM)); r=int(round(H-1-y*10*PXMM))
    return (c,r) if 0<=c<W and 0<=r<H else None
# ---- find where each cut line crosses material, pick joint positions
joints=[]; step=0.02
for i,(th,d) in enumerate(LINES):
    n=(math.cos(th),math.sin(th)); t=(-math.sin(th),math.cos(th)); p0=(d*n[0],d*n[1]); runs=[]; cur=None
    for k in range(int(-160/step),int(160/step)):
        s=k*step; x,y=p0[0]+s*t[0],p0[1]+s*t[1]
        ca=at(x-0.1*n[0],y-0.1*n[1]); cb=at(x+0.1*n[0],y+0.1*n[1]); cm=at(x,y)
        ok=cm is not None and ca is not None and cb is not None and mat[cm[1],cm[0]]
        pair=(int(lab[ca[1],ca[0]]),int(lab[cb[1],cb[0]])) if ok else None
        if ok and (pair[0]^pair[1])!=(1<<i): ok=False
        if ok and cur and cur[0]==pair: cur[2]=s
        elif ok: cur=[pair,s,s]; runs.append(cur)
        else: cur=None
    cand=[]
    for pair,s0,s1 in runs:
        w=(s1-s0)+step; sc=(s0+s1)/2; x,y=p0[0]+sc*t[0],p0[1]+sc*t[1]
        good=True                                                                  # stay away from other seams (pad must sit inside the pair)
        for off in (-1.3,1.3):
            for sd in (-0.9,0.9):
                q=at(x+off*t[0]+sd*n[0],y+off*t[1]+sd*n[1])
                if q is None or int(lab[q[1],q[0]]) not in pair: good=False
        if good and w>=0.4: cand.append((w,i,pair,sc,(x,y),n,t))
    chosen={}
    for w,i_,pair,sc,pos,n_,t_ in sorted(cand,key=lambda c:-c[0]):
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
def rrect(u0,u1,v0,v1,r=0.2,n=6):
    pts=[]
    for cu,cv,a0 in ((u1-r,v1-r,0),(u0+r,v1-r,90),(u0+r,v0+r,180),(u1-r,v0+r,270)):
        pts+= [(cu+r*math.cos(math.radians(a0+q*15)),cv+r*math.sin(math.radians(a0+q*15))) for q in range(7)]
    return pts
def draw(mask,pts_world,val):
    im=Image.fromarray(mask.astype(np.uint8)*255); ImageDraw.Draw(im).polygon([px(*p) for p in pts_world],fill=255 if val else 0); return np.array(im)>0
for idx,(w,i,pair,sc,pos,n,t) in enumerate(joints):
    a,b=pair; male,female=(a,b) if SC[a]<=SC[b] else (b,a); nm=n if male==a else (-n[0],-n[1])
    W2=lambda u,v:(pos[0]+(u*t[0]+v*nm[0])/10, pos[1]+(u*t[1]+v*nm[1])/10)         # (u along seam, v male->female) mm -> world cm
    mpad=[W2(u*10,v*10) for u,v in rrect(-0.9,0.9,-1.2,0.0)]; tab=[W2(*p) for p in ((-3,-0.5),(3,-0.5),(5,8.5),(-5,8.5))]
    fpad=[W2(u*10,v*10) for u,v in rrect(-0.9,0.9,0.0,1.6)]; sock=[W2(*p) for p in ((-(3+CLR),-0.3),(3+CLR,-0.3),(5+CLR,8.5+CLR),(-(5+CLR),8.5+CLR))]
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
files=[]; rows=[]
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
