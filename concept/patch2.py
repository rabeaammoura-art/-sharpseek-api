s=open('make_pieces.py').read()
# A) curved seams (DP)
a=s.index("lab=np.zeros((H,W),np.int8)"); b=s.index("def px(x,y)")
A='''from scipy import ndimage as ndi
BAND=3.0; WIDE=16.0                                         # seam may wander +-3 cm ; pads hide inside material wider than 16 mm
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
'''
s=s[:a]+A+s[b:]
# B) shapes + scoring helper, inserted after at()
anchor="# ---- find where each cut line crosses material, pick joint positions"
B='''def rrect(u0,u1,v0,v1,r=0.15):
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
'''
s=s.replace(anchor,B+anchor,1)
# C) joint search along the curved seam, scored by visible added area
a=s.index("joints=[]; step=0.02"); b=s.index('print(f"{TAG}: {len(joints)} joints"')
C='''joints=[]; step=0.02
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
'''
s=s[:a]+C+s[b:]
s=s.replace("MAXJ=5; MINSP=6.0","MAXJ=3; MINSP=6.0")
# D) building block uses shapes()
a=s.index("def rrect(u0,u1,v0,v1,r=0.2,n=6):"); b=s.index("def draw(mask,pts_world,val):")
s=s[:a]+s[b:]
a=s.index("    W2=lambda u,v:(pos[0]+(u*t[0]+v*nm[0])/10, pos[1]+(u*t[1]+v*nm[1])/10)         #"); b=s.index("    M[male]=draw(")
s=s[:a]+"    mpad,tab,fpad,sock=shapes(pos,n,t,1 if male==a else -1)\n"+s[b:]
open('make_pieces2.py','w').write(s)
