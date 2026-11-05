# Proportion sketch for approval: front view, rib section, plan (top) view.
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch, Polygon

P = dict(L_proj=325, H=140, lip_h=13, n_ribs=4, red_w=100, mid_w=120,
         clear_h=42, stud_dx=130, stud_x1=97, stud_from_top=73,
         box_h=85, D_body=38, R_wrap=136, A_wrap=50, R_end=15,
         nose_R=7, groove=8, stepout=3)
L,H=P["L_proj"],P["H"]; pitch=(H-P["lip_h"])/P["n_ribs"]
RED,AMB,CLR="#d7261e","#f39a1e","#e8eef2"
fig,ax=plt.subplots(1,3,figsize=(16,5.6),gridspec_kw=dict(width_ratios=[3.2,1,2.4]))

# ---- front view (RH lens, seen from behind the car; inboard end at left)
a=ax[0]; x1=P["red_w"]; x2=x1+P["mid_w"]
a.add_patch(Rectangle((0,0),x1,H,color=RED))
a.add_patch(Rectangle((x1,P["clear_h"]),P["mid_w"],H-P["clear_h"],color=RED))
a.add_patch(Rectangle((x1,0),P["mid_w"],P["clear_h"],color=CLR,ec="#999"))
a.add_patch(Rectangle((x2,0),L-x2,H,color=AMB))
for i in range(P["n_ribs"]+1):
    y=H-P["lip_h"]-i*pitch; a.plot([0,L],[y,y],color="k",lw=0.8)
a.plot([0,L],[H-P["lip_h"]/2]*2,color="k",lw=0.3,ls=":")
sy=H-P["stud_from_top"]
for sx in (P["stud_x1"],P["stud_x1"]+P["stud_dx"]):
    a.add_patch(Circle((sx,sy),3.5,color="k"))
a.add_patch(Rectangle((x1+4,P["clear_h"]+2),P["mid_w"]-8,P["box_h"],fill=False,ls="--",ec="k",lw=1))
a.text(x1+P["mid_w"]/2,P["clear_h"]+P["box_h"]/2,"inner box\n(ring optic)",ha="center",va="center",fontsize=8)
a.annotate("",(0,-12),(L,-12),arrowprops=dict(arrowstyle="<->"));a.text(L/2,-22,f"L_proj {L}",ha="center")
a.annotate("",(-12,0),(-12,H),arrowprops=dict(arrowstyle="<->"));a.text(-16,H/2,f"H {H}",rotation=90,ha="right",va="center")
for x,t in ((x1/2,"RED\n(tail)"),(x1+P["mid_w"]/2,"RED top /\nCLEAR bottom"),((x2+L)/2,"AMBER\n(wraps)")):
    a.text(x,H+8,t,ha="center",fontsize=8)
a.text(P["stud_x1"]+P["stud_dx"]/2,sy-11,f"studs {P['stud_dx']} apart",ha="center",fontsize=8)
a.text(4,H-P["lip_h"]+2,"seal lip",fontsize=7)
a.text(5,6,"corner radii: inboard top R25, bottom R5\noutboard top R8, bottom R30 (not drawn)",fontsize=6.5)
a.set_xlim(-40,L+10);a.set_ylim(-35,H+28);a.set_aspect("equal");a.axis("off")
a.set_title("Front view – RH lens (from behind the car)")

# ---- rib section (side profile at the inboard end)
a=ax[1]; pts=[(0,H),(-6,H),(-6,H-P["lip_h"])]
for i in range(P["n_ribs"]):
    top=H-P["lip_h"]-i*pitch; bot=top-pitch; zf=-(P["groove"]+14)-i*P["stepout"]; r=P["nose_R"]
    pts+=[(-P["groove"],top),(zf+r*0.3,bot+2*r)]       # upper face slopes outward going down
    cy=bot+r
    pts+=[((zf+r)-r*np.cos(t), cy+r*np.sin(t)) for t in np.linspace(np.pi/2,-np.pi/2,14)]  # convex nose
    pts+=[(-P["groove"],bot)]                          # undercut back into the groove
pts+=[(0,0),(0,H)]
a.add_patch(Polygon(pts,closed=True,fc=RED,ec="k",alpha=.85))
a.axvline(0,color="gray",ls="--",lw=.8); a.text(2,H/2,"flange plane\n(back)",fontsize=7,rotation=90,va="center")
a.text(-40,-14,f"{P['n_ribs']} ribs, pitch ≈{pitch:.0f}\nstep-out {P['stepout']}/rib (verify)",fontsize=7)
a.set_xlim(-48,12);a.set_ylim(-25,H+10);a.set_aspect("equal");a.axis("off");a.set_title("Rib section (side)")

# ---- plan view (top): straight part + amber wrap arc
a=ax[2]; xs=P["red_w"]+P["mid_w"]; R=P["R_wrap"]; A=np.radians(P["A_wrap"])
t=np.linspace(0,A,40); fx=np.r_[0,xs,xs+R*np.sin(t)]; fy=np.r_[0,0,-(R-R*np.cos(t))]
a.plot(fx,fy,color="k",lw=2,label="outer face (rib noses)")
a.plot([0,xs],[-P["D_body"]]*2,color="gray",lw=1.2,ls="--",label="back / flange line")
a.plot([0,0],[0,-P["D_body"]],color="gray",lw=1.2,ls="--")
a.plot(xs+R*np.sin(t)-P["D_body"]*np.sin(t),-(R-R*np.cos(t))-P["D_body"]*np.cos(t),color="gray",lw=1.2,ls="--")
a.axvspan(xs,xs+R*np.sin(A),color=AMB,alpha=.25)
dep=R*(1-np.cos(A))+P["D_body"]
a.text(xs+5,8,f"wrap R{R}, {P['A_wrap']}°",fontsize=8)
a.text(5,-P["D_body"]-12,f"body depth {P['D_body']}   total depth ≈{dep:.0f}",fontsize=8)
a.text(-4,6,f"inboard end R{P['R_end']} return",fontsize=7)
a.set_aspect("equal");a.set_ylim(-dep-30,25);a.set_xlim(-10,L+15);a.axis("off");a.legend(fontsize=7,loc="lower left")
a.set_title("Top view (plan) – wraps around the car corner")
plt.tight_layout();plt.savefig("w115_lens_plan_sketch.png",dpi=130)
print("depth",round(dep),"pitch",round(pitch,1))
