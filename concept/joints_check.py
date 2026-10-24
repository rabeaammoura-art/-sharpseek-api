import numpy as np, glob
from build123d import import_stl
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
def tris(p):
    b=open(p,'rb').read(); n=int(np.frombuffer(b[80:84],'<u4')[0])
    a=np.frombuffer(b[84:84+50*n],dtype=np.dtype([('n','<f4',3),('v','<f4',(3,3)),('a','<u2')])); return a['v'].astype(float)
def top(t,col,ax,dy=0):
    z=t[:,:,2].max(); sel=t[(t[:,:,2]>z-0.01).all(1)]
    ax.add_collection(PolyCollection([[(x,y+dy) for x,y,_ in tr] for tr in sel],facecolors=col,edgecolors="none"))
sets=[("D_c015_male","D_c015_female","D 0.15"),("D_c020_male","D_c020_female","D 0.20"),("D_c030_male","D_c030_female","D 0.30"),("P_A","P_B","P half-lap+pin"),("K_A","K_B","K butterfly")]
fig,axs=plt.subplots(len(sets),1,figsize=(11,10)); 
for ax,(a,b,t) in zip(axs,sets):
    ta,tb=tris(f"joints/{a}.stl"),tris(f"joints/{b}.stl")
    top(ta,"#e07a5f",ax); top(tb,"#3d405b",ax)
    if t.startswith("K"): top(tris("joints/K_key.stl"),"#f2cc8f",ax)
    ax.set_xlim(-36,64); ax.set_ylim(-16,16); ax.set_aspect("equal"); ax.set_title(t+"  (assembled, top view, mm)",fontsize=10); ax.grid(True,lw=.3)
fig.tight_layout(); fig.savefig("joints/joints_preview.png",dpi=100)
# collision check
for a,b in (("D_c015_male","D_c015_female"),("D_c020_male","D_c020_female"),("D_c030_male","D_c030_female"),("P_A","P_B"),("K_A","K_key"),("K_B","K_key")):
    A=import_stl(f"joints/{a}.stl"); B=import_stl(f"joints/{b}.stl")
    try: v=(A&B).volume
    except Exception as e: v=f"err {e}"
    print(a,b,"overlap mm3:",v)
