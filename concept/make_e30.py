import math
# ---------- E30 (2-door) wire model, metres. x=front(+), y=left(+), z=up. Near side = +y.
def M(pts): return [(x,-y,z) for x,y,z in pts]          # mirror to far side
L=[]                                                      # polylines (3D)
def add(p,mirror=False):
    L.append(p)
    if mirror: L.append(M(p))
def circle(c,r,plane="xz",n=60,a0=0,a1=2*math.pi):
    cx,cy,cz=c; pts=[]
    for i in range(n+1):
        a=a0+(a1-a0)*i/n
        pts.append((cx+r*math.cos(a),cy,cz+r*math.sin(a)))
    return pts
# hood
add([(2.10,0.74,0.72),(0.98,0.72,0.95)],True)           # hood side edges
add([(0.98,0.72,0.95),(0.98,-0.72,0.95)])                # cowl
add([(2.10,0.74,0.72),(2.12,0.0,0.73),(2.10,-0.74,0.72)])# hood front edge
# nose / headlights / kidneys
for s in (1,-1):
    y0,y1=0.34,0.76
    add([(2.09,s*y0,0.61),(2.09,s*y1,0.61),(2.09,s*y1,0.71),(2.09,s*y0,0.71),(2.09,s*y0,0.61)])
    add(circle((2.09,s*0.47,0.66),0.040,n=24)); add(circle((2.09,s*0.63,0.66),0.040,n=24))
    add([(2.10,s*0.07,0.61),(2.10,s*0.25,0.61),(2.10,s*0.25,0.71),(2.10,s*0.07,0.71),(2.10,s*0.07,0.61)])
    add([(2.10,s*0.16,0.61),(2.10,s*0.16,0.71)])
add([(2.10,0.0,0.61),(2.10,0.0,0.71)])
# bumper
add([(2.17,-0.80,0.58),(2.17,0.80,0.58),(1.80,0.83,0.58)])
add([(2.17,-0.80,0.33),(2.17,0.80,0.33),(1.80,0.83,0.33)])
add([(2.17,-0.80,0.58),(2.17,-0.80,0.33)]); add([(2.17,0.80,0.58),(2.17,0.80,0.33)])
add([(2.17,-0.80,0.46),(2.17,0.80,0.46),(1.80,0.83,0.46)])
add([(2.12,-0.45,0.38),(2.12,0.45,0.38)])               # air dam slot
# fender / shoulder line
add([(2.08,0.80,0.67),(1.30,0.84,0.80),(0.75,0.84,0.93),(0.20,0.82,0.96),(-1.40,0.80,0.98),(-2.05,0.78,0.95)])
add([(2.08,0.78,0.68),(2.06,0.82,0.60),(1.80,0.83,0.58)])
# side lower crease & sill
add([(1.70,0.85,0.55),(-1.70,0.85,0.55)])
add([(0.98,0.84,0.34),(-0.98,0.84,0.34)])
# doors
add([(0.72,0.84,0.95),(0.72,0.84,0.38)]); add([(-0.62,0.84,0.97),(-0.62,0.84,0.38)])
add([(0.72,0.84,0.38),(-0.62,0.84,0.38)])
add([(-0.06,0.86,0.89),(-0.30,0.86,0.89)])               # handle
add([(0.80,0.84,1.01),(0.84,0.93,1.04),(0.76,0.93,1.06),(0.74,0.84,1.03)])  # mirror
# greenhouse
add([(0.95,0.77,0.97),(0.22,0.60,1.37),(-0.85,0.60,1.37),(-1.22,0.74,0.99),(0.95,0.77,0.97)])  # side glass
add([(0.95,-0.77,0.97),(0.22,-0.60,1.37)])                 # far A-pillar
add([(0.22,0.60,1.37),(0.22,-0.60,1.37)]); add([(-0.85,0.60,1.37),(-0.85,-0.60,1.37)])           # roof edges
add([(-0.85,0.60,1.37),(-1.38,0.72,1.00)])         # rear glass
# trunk / rear
add([(-1.38,0.72,1.00),(-2.10,0.74,0.98),(-2.10,0.74,0.95)])
add([(-2.05,0.82,0.92),(-2.05,0.82,0.74),(-1.82,0.82,0.74),(-1.82,0.82,0.92)])                    # tail lamp side
add([(-2.17,0.80,0.58),(-1.80,0.83,0.58)]); add([(-2.17,0.80,0.33),(-1.80,0.83,0.33)])
add([(-2.17,0.80,0.58),(-2.17,0.80,0.33)])
# arches + wheels
for cx in (1.29,-1.29):
    add(circle((cx,0.84,0.31),0.385,n=40,a0=0,a1=math.pi))
    add(circle((cx,0.80,0.31),0.31,n=48)); add(circle((cx,0.80,0.31),0.21,n=40)); add(circle((cx,0.80,0.31),0.05,n=16))
    for k in range(5):
        a=math.radians(k*72+18)
        add([(cx+0.07*math.cos(a),0.80,0.31+0.07*math.sin(a)),(cx+0.20*math.cos(a),0.80,0.31+0.20*math.sin(a))])
# far front wheel peeking under bumper skipped
# ---------- camera
az,el,D=math.radians(34),math.radians(9),13.0
tgt=(0.0,0.0,0.75)
c=(tgt[0]+D*math.cos(az)*math.cos(el),tgt[1]+D*math.sin(az)*math.cos(el),tgt[2]+D*math.sin(el))
def norm(v): n=math.sqrt(sum(a*a for a in v)); return tuple(a/n for a in v)
def cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
dot=lambda a,b:sum(x*y for x,y in zip(a,b))
f=norm(tuple(t-cc for t,cc in zip(tgt,c))); r=norm(cross(f,(0,0,1))); u=cross(r,f)
def proj(p):
    d=tuple(a-b for a,b in zip(p,c)); z=dot(d,f)
    return dot(d,r)/z, -dot(d,u)/z
P=[[proj(p) for p in pl] for pl in L]
xs=[x for pl in P for x,_ in pl]; ys=[y for pl in P for _,y in pl]
W,H=1100,560; sc=min((W-80)/(max(xs)-min(xs)),(H-80)/(max(ys)-min(ys)))
ox=(W-(max(xs)-min(xs))*sc)/2-min(xs)*sc; oy=(H-(max(ys)-min(ys))*sc)/2-min(ys)*sc
def path(pl): return "M"+" L".join(f"{x*sc+ox:.1f},{y*sc+oy:.1f}" for x,y in pl)
d=" ".join(path(pl) for pl in P)
wall="#d9d1c3"
svg=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1300 860" width="1300" height="860">
<defs><filter id="ps" x="-5%" y="-5%" width="110%" height="115%"><feDropShadow dx="6" dy="10" stdDeviation="9" flood-color="#000" flood-opacity=".4"/></filter>
<linearGradient id="pg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#202226"/><stop offset="1" stop-color="#121316"/></linearGradient></defs>
<rect width="1300" height="860" fill="{wall}"/>
<text x="650" y="62" font-family="Helvetica,Arial,sans-serif" font-size="32" font-weight="700" fill="#222" text-anchor="middle">E30 · design-lines wall art, 3/4 front view</text>
<text x="650" y="94" font-family="Helvetica,Arial,sans-serif" font-size="18" fill="#555" text-anchor="middle">Line-cut plate, no backlight: the wall shows through the cuts</text>
<g transform="translate(100,150)">
<rect width="{W}" height="{H}" rx="10" fill="url(#pg)" filter="url(#ps)"/>
<g fill="none" stroke-linejoin="round" stroke-linecap="round">
<path d="{d}" stroke="#000" stroke-width="5.5" opacity=".55" transform="translate(1.6,1.8)"/>
<path d="{d}" stroke="{wall}" stroke-width="3.6"/>
</g></g>
<text x="650" y="790" font-family="Helvetica,Arial,sans-serif" font-size="17" fill="#555" text-anchor="middle">A3 plate (297×420 mm) · 3 mm · generic proportions of an E30 coupe, final lines would be traced from official drawings</text>
</svg>'''
open("e30_lines_concept.svg","w").write(svg)
