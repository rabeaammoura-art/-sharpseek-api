"""v2 flat preview: ONE pink (light+dark merged), 3 filaments (white / pink / yellow). Decor traced on the left half and MIRRORED, strong clean-up."""
import sys, pickle; sys.path.insert(0,'/home/user/-sharpseek-api/cad')
import numpy as np, contourpy
from scipy import ndimage as ndi
from PIL import Image, ImageDraw
from shapely import affinity
from shapely.geometry import Polygon, box, Point
from shapely.ops import unary_union
import newborn_plaque as n
lab=np.load('lab.npy'); sil=np.load('sil.npy'); H,W=lab.shape
X0,X1,Y0,Y1=262,1173,18,1059
CX,CY=(X0+X1)/2,(Y0+Y1)/2; S=245.0/(X1-X0+1)
AX=723.0                                           # symmetry axis of the decor in picture px
def to_mm(g): return affinity.translate(affinity.scale(g,S,-S,origin=(0,0)),-CX*S,CY*S)
def px_to_mm(x,y): return ((x-CX)*S,-(y-CY)*S)
AXM=px_to_mm(AX,0)[0]
def mirror(g): return affinity.scale(g,-1,1,origin=(AXM,0))
def polys(mask,sigma=1.5,min_area=8):
    m=ndi.gaussian_filter(mask.astype(float),sigma)
    gen=contourpy.contour_generator(z=m,fill_type=contourpy.FillType.OuterOffset)
    pts,offs=gen.filled(0.5,1.5); out=[]
    for p,o in zip(pts,offs):
        rings=[p[o[i]:o[i+1]] for i in range(len(o)-1)]
        if len(rings[0])<4: continue
        pg=Polygon(rings[0],[r for r in rings[1:] if len(r)>=4]).buffer(0)
        if pg.area>=min_area: out.append(pg)
    return to_mm(unary_union(out)) if out else Polygon()
def clean(g,close=0.4,open_=0.3,min_a=3.0):
    g=g.buffer(close,join_style=1).buffer(-close,join_style=1).buffer(-open_,join_style=1).buffer(open_,join_style=1)
    return n.only_polygons(unary_union([p for p in (g.geoms if hasattr(g,'geoms') else [g]) if p.area>=min_a]))
def chaikin(coords,it=3):
    pts=list(coords)[:-1]
    for _ in range(it):
        new=[]
        for i in range(len(pts)):
            p,q=np.array(pts[i]),np.array(pts[(i+1)%len(pts)])
            new+= [tuple(0.75*p+0.25*q),tuple(0.25*p+0.75*q)]
        pts=new
    return pts+[pts[0]]
def smooth(g,tol=0.28,it=3,min_a=2.0):
    out=[]
    for p in (g.geoms if hasattr(g,'geoms') else [g]):
        if p.is_empty or p.area<min_a: continue
        p=p.simplify(tol)
        if p.is_empty or p.geom_type!='Polygon': continue
        ext=Polygon(chaikin(p.exterior.coords,it),[chaikin(r.coords,it) for r in p.interiors if Polygon(r).area>1.0]).buffer(0)
        out.append(ext)
    return unary_union(out)
def zone(x0,y0,x1,y1):
    z=np.zeros((H,W),bool); z[y0:y1,x0:x1]=True; return z
yel=(lab==4); pink=((lab==2)|(lab==3)|ndi.binary_dilation(yel,iterations=3)&(lab!=1)|ndi.binary_dilation(yel,iterations=2)); line=(lab==3)
# regions to treat separately (px)
kitty=zone(540,60,910,255)|zone(572,255,885,440); bowz=zone(548,872,895,1045)
pills={'weight':(338,614,722,735),'length':(726,614,1106,735),'time':(338,742,722,865),'date':(726,742,1108,865)}
cut=zone(515,430,925,580)
for (x0,y0,x1,y1) in pills.values(): cut|=zone(x0-8,y0-8,x1+8,y1+8)
OUT=n.rrect(0,0,280,280,28); INN=n.rrect(0,0,258,258,12)         # square plate: fits the existing 280 box
band=INN.difference(INN.buffer(-9)).buffer(0.3)
def drop_band(g): return unary_union([p for p in (g.geoms if hasattr(g,'geoms') else [g]) if not p.within(band)])
def pxmask(g):
    im=Image.new('L',(W,H),0); d=ImageDraw.Draw(im)
    for p in (g.geoms if hasattr(g,'geoms') else [g]):
        d.polygon([((x/S)+CX,(-y/S)+CY) for x,y in p.exterior.coords],fill=1)
    return np.array(im).astype(bool)
inn=ndi.binary_erosion(pxmask(INN),iterations=16)
live=sil&inn
# --- decor (butterflies, flowers, leaves, cloud ring, bottom leaves): LEFT half traced, mirrored ---
left=zone(0,0,int(AX),H)
yy,xx=np.mgrid[0:H,0:W]
fl_c=(xx-504)**2+(yy-319)**2<=55**2                       # left flower is drawn parametric (petals merge when traced)
lightdil=ndi.binary_dilation(lab==2,iterations=2)|ndi.binary_dilation(yel,iterations=3)
decor_mask=lightdil&sil&live&~kitty&~cut&~bowz&~fl_c&zone(375,375,1075,625)
half=smooth(clean(polys(decor_mask&left)))
decor=drop_band(unary_union([half,mirror(half)]))
from shapely.ops import transform as sh_transform
def stretch_x(g,x0=40.0,f=1.0):
    return sh_transform(lambda x,y,z=None:(np.where(np.abs(x)<=x0,x,np.sign(x)*(x0+(np.abs(x)-x0)*f)),y),g)
decor=n.only_polygons(stretch_x(decor))
from shapely.geometry import LineString
def leaf(b,t,w,n=48):
    b=np.array(b,float); t=np.array(t,float); L=np.linalg.norm(t-b); u=(t-b)/L; v=np.array([-u[1],u[0]])
    ts=np.linspace(0,1,n); hw=(w/2)*np.sin(np.pi*ts**0.8)**0.85
    left=[tuple(b+u*L*a+v*h) for a,h in zip(ts,hw)]; right=[tuple(b+u*L*a-v*h) for a,h in zip(ts[::-1],hw[::-1])]
    return Polygon(left+right).buffer(1.2).buffer(-1.2)
def ell(cx,cy,a,b,ang):
    e=Point(cx,cy).buffer(1,48); e=affinity.scale(e,b,a,origin=(cx,cy)); return affinity.rotate(e,ang,origin=(cx,cy))
def stem(pts,w): return LineString(pts).buffer(w/2,cap_style=1)
# -- left butterfly (px)
bf_wings=unary_union([ell(407,160,55,40,-26),ell(379,222,26,38,-8),ell(492,222,33,45,10),ell(440,260,33,20,25)])
bf_body=unary_union([ell(437,224,33,14,44),Point(457,185).buffer(14,32),stem([(462,172),(466,146)],7),Point(466,136).buffer(12,32),stem([(465,181),(482,170),(497,164)],7),Point(503,162).buffer(11,32)])
# -- left side sprig + flower stem
side=unary_union([stem([(474,424),(445,394),(422,364),(412,342)],9),leaf((420,362),(408,299),30),leaf((420,368),(333,325),44),leaf((452,410),(350,412),38),stem([(466,358),(468,415)],9)])
# -- left bottom sprig
bot=unary_union([stem([(562,947),(520,946),(480,943),(440,940)],8),leaf((440,940),(358,903),34),leaf((482,941),(441,897),24),leaf((534,944),(494,896),25),leaf((462,948),(402,986),27),leaf((522,950),(478,992),27)])
BFS,SDS=-63,0          # px: butterflies / bottom sprigs move out 17 mm, side sprigs + flowers follow the stretched cloud (5.4 mm)
bf_wings=affinity.translate(bf_wings,BFS,0); bf_body=affinity.translate(bf_body,BFS,0); side=affinity.translate(side,SDS,0)
bot=affinity.scale(bot,1.3,1.0,origin=(562,947))       # sprig longer instead of moved: still touches the bow
par_pink=to_mm(unary_union([bf_wings,side,bot]).difference(bf_body)); par_yel=to_mm(bf_body)
par_pink_l=n.only_polygons(par_pink); par_yel_l=n.only_polygons(par_yel)
decor=unary_union([decor,par_pink_l,mirror(par_pink_l)])
import math
fc=px_to_mm(504,319); petals=[Point(fc[0]+31*S*math.cos(math.radians(a)),fc[1]+31*S*math.sin(math.radians(a))).buffer(25*S,32) for a in (90,18,-54,-126,162)]
flower_l=unary_union(petals+[Point(*fc).buffer(22*S,32)]); fcen_l=Point(*fc).buffer(17*S,32)
flower_l=affinity.translate(flower_l,SDS*S,0); fcen_l=affinity.translate(fcen_l,SDS*S,0)
decor=unary_union([decor,flower_l,mirror(flower_l)])
yhalf=smooth(clean(polys(yel&live&~kitty&~bowz&left&~fl_c,1.2),0.2,0.2,0.5),0.2,3)
ydecor=unary_union([fcen_l,mirror(fcen_l),par_yel_l,mirror(par_yel_l)])
# --- Kitty (head, bow, paws, dress): traced as it is (not symmetric), lines = dark pink = raised ---
kit_fill=smooth(clean(polys(pink&live&kitty&~cut,1.4)))
kit_line=smooth(clean(polys(line&live&kitty&~cut,1.2),0.15,0.2,1.0),0.2,2)
kit_y=clean(polys(yel&kitty&live,1.2),0.2,0.2,0.5)
# --- bottom bow: left half mirrored; lines raised ---
bl=zone(0,0,int(AX),H)
bow_fill_h=smooth(clean(polys(pink&live&bowz&bl,1.4)))
bow_fill_h=n.only_polygons(unary_union([Polygon(p.exterior) if Polygon(p.exterior).area<400 or True else p for p in (bow_fill_h.geoms if hasattr(bow_fill_h,'geoms') else [bow_fill_h])])); bow_fill=unary_union([bow_fill_h,mirror(bow_fill_h)])
bow_line_h=clean(polys(line&live&bowz&bl,1.2),0.15,0.2,1.0); bow_line=unary_union([bow_line_h,mirror(bow_line_h)])
heart=clean(polys(yel&bowz,1.2),0.2,0.2,2.0)
# --- pills / frame (parametric) ---
PR=[]
for (x0,y0,x1,y1) in pills.values():
    x0,x1=(x0-57,x1) if x0<718 else (x0,x1+57)
    cxp,cyp=px_to_mm((x0+x1)/2,(y0+y1)/2); wmm,hmm=(x1-x0)*S,(y1-y0)*S
    PR.append(n.rrect(cxp,cyp,wmm,hmm,hmm/2).difference(n.rrect(cxp,cyp,wmm-2*4.2,hmm-2*4.2,hmm/2-4.2)))
frame=OUT.difference(INN)
# --- text and icons (real font, generator icons) ---
def fitbox(geom,cx_px,cy_px,w_px,h_px):
    minx,miny,maxx,maxy=geom.bounds; sc=min(w_px*S/(maxx-minx),h_px*S/(maxy-miny))
    g=affinity.scale(geom,sc,sc,origin=(0,0)); minx,miny,maxx,maxy=g.bounds; tx,ty=px_to_mm(cx_px,cy_px)
    return affinity.translate(g,tx-(minx+maxx)/2,ty-(miny+maxy)/2)
def txt(t,kind=None,segs=None):
    g,_=n.text_line(segs or [(t,10,kind)],'ar',True); return g
T=[('weight','الوزن',('3.4','كغم'),(452,686,95,112),(601,646,83,30),(604,693,136,34)),
   ('length','الطول',('49','سم'),(829,672,102,82),(985,646,95,30),(984,693,112,34)),
   ('time','الساعة',('4:35','م'),(452,803,88,88),(601,775,112,30),(604,822,126,34)),
   ('date','التاريخ',('12/03/2024',None),(826,803,92,88),(987,775,93,30),(984,822,188,34))]
texts=[fitbox(txt('مريم','name'),718,505,381,118)]
for key,lbl,val,(ix,iy,iw,ih),(lx,ly,lw,lh),(vx,vy,vw,vh) in T:
    sh=-28 if ix<718 else 28; ix+=sh; lx+=sh; vx+=sh
    texts.append(fitbox(n.ICONS[key](1.0),ix,iy,iw,ih))
    texts.append(fitbox(txt(lbl,'word'),lx,ly,lw,lh))
    segs=[(val[0],10,'num')]+([(val[1],10,'word')] if val[1] else [])
    texts.append(fitbox(txt(None,segs=segs),vx,vy,vw,vh))
level2=n.only_polygons(unary_union([frame,kit_line,bow_line]+texts))
level1=n.only_polygons(unary_union([drop_band(decor),drop_band(kit_fill),drop_band(bow_fill)]+PR))
YALL=n.only_polygons(unary_union([ydecor,kit_y,heart]))
level1=n.only_polygons(level1.difference(YALL))
level1=n.only_polygons(unary_union([p for p in (level1.geoms if hasattr(level1,'geoms') else [level1]) if p.area>=1.5]))
G={'pink1':level1.difference(level2.buffer(0)) if False else level1,'pink2':level2,'yellow':YALL}
pickle.dump(G,open('G6.pkl','wb'))
print({k:round(v.area) for k,v in G.items()})
# --- preview ---
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MP
ref=np.array(Image.open('ref.png').convert('RGB'))[Y0:Y1+1,X0:X1+1]
OFFX=CX-521
def patches(ax,alpha=1.0,shade=True,offx=None):
    offx=X0 if offx is None else offx
    cols=[('base',OUT,'#ffffff'),('pink1',G['pink1'],'#f77fb5'),('pink2',G['pink2'],'#e0559a' if shade else '#f77fb5'),('yellow',G['yellow'],'#f9d000')]
    for nm,g,c in cols:
        for p in (g.geoms if hasattr(g,'geoms') else [g]):
            verts=[];codes=[]
            for r in [p.exterior]+list(p.interiors):
                pts=[((x/S)+CX-offx,(-y/S)+CY-Y0) for x,y in r.coords]; verts+=pts; codes+=[MP.MOVETO]+[MP.LINETO]*(len(pts)-2)+[MP.CLOSEPOLY]
            ax.add_patch(PathPatch(MP(verts,codes),fc=c,ec='none',alpha=alpha))
h,w=ref.shape[:2]
fig,axs=plt.subplots(1,2,figsize=((w+1042)/200,h/200),dpi=100)
for a in axs: a.set_xlim(0,w);a.set_ylim(h,0);a.axis('off')
axs[1].set_xlim(0,1042);
axs[0].imshow(ref); axs[0].set_title('reference',fontsize=9)
axs[1].set_facecolor('#dddddd'); patches(axs[1],offx=OFFX); axs[1].set_title('flat design v4 (280 x 280, fits the box): white / pink / yellow (darker pink = same filament, raised higher)',fontsize=8)
fig.tight_layout(pad=0.4); fig.savefig('flat_preview6.png')
fig2=plt.figure(figsize=(1042/100,h/100),dpi=100); a=fig2.add_axes([0,0,1,1]); a.set_xlim(0,1042);a.set_ylim(h,0);a.axis('off'); fig2.patch.set_facecolor('#e6e6e6'); patches(a,offx=OFFX); fig2.savefig('flat_only6.png')
