"""Glue-free joint test coupons for 4 mm line-art plates (line width 4 mm, pad around the joint)."""
from build123d import *
T=4.0; LW=4.0
def poly(*p,**kw):                      # always counter-clockwise so the extrusion goes +Z
    a=sum(p[i][0]*p[(i+1)%len(p)][1]-p[(i+1)%len(p)][0]*p[i][1] for i in range(len(p)))
    return Polygon(*(p if a>0 else p[::-1]),align=None)
def ex(sk,z0=0,h=T): return Pos(0,0,z0)*extrude(sk,amount=h)
def line(x0,x1): return Pos((x0+x1)/2,0)*Rectangle(abs(x1-x0),LW)
def pad(x0,x1,w=18): return Pos((x0+x1)/2,0)*RectangleRounded(abs(x1-x0),w,2.0)
# ---- D: dovetail tab / socket (slides in along Z, locks against pulling apart in the plane)
def dovetail(c,name):
    tab=poly((-0.5,-3),(-0.5,3),(8.5,5),(8.5,-5),align=None)
    sock=poly((-0.3,-(3+c)),(-0.3,3+c),(8.5+c,5+c),(8.5+c,-(5+c)),align=None)
    male=ex(line(-34,-8)+pad(-14,0)+tab)
    female=ex(line(12,48)+pad(0,18)-sock)
    print("D",c,"overlap mm3:",round((male&female).volume,3)); export_stl(male,f"joints/D_c{int(c*100):03d}_male.stl"); export_stl(female,f"joints/D_c{int(c*100):03d}_female.stl")
for c in (0.15,0.20,0.30): dovetail(c,"D")
# ---- P: half-lap with snap pin (flush faces, pin locks it in Z)
c=0.20
A=ex(line(-34,-8)+pad(-16,0))+ex(pad(0,14),0,2)+Pos(7,0,2)*Cylinder(2.0,2.0,align=(Align.CENTER,Align.CENTER,Align.MIN))
B=ex(line(26,62)+pad(14,30))+ex(pad(0,14),2,2)
B=B-Pos(7,0,2)*Cylinder(2.0+c,2.0,align=(Align.CENTER,Align.CENTER,Align.MIN))
print("P overlap mm3:",round((A&B).volume,3)); export_stl(A,"joints/P_A.stl"); export_stl(B,"joints/P_B.stl")
# ---- K: butterfly (bow-tie) key across a flat seam, key can be a contrasting colour
def bow(cl): return poly((-12-cl,-6-cl),(-12-cl,6+cl),(0,3+cl),(12+cl,6+cl),(12+cl,-6-cl),(0,-3-cl),align=None)
KA=ex(line(-34,-10)+pad(-18,0,26)-bow(0.2)); KB=ex(line(10,34)+pad(0,18,26)-bow(0.2)); key=ex(bow(0.0),0,T-0.2)
print("K overlap mm3:",round((KA&key).volume,3),round((KB&key).volume,3)); export_stl(KA,"joints/K_A.stl"); export_stl(KB,"joints/K_B.stl"); export_stl(key,"joints/K_key.stl")
print("ok")
