import math
BODY="M40,210 L40,182 Q46,166 82,161 L190,151 Q232,100 302,88 L470,88 Q542,92 592,140 L700,153 Q750,161 760,186 L762,212 Q762,224 750,226 L50,226 Q40,226 40,210 Z"
WIN="M214,148 Q250,110 305,102 L462,102 Q516,106 556,146 Z"
DESIGN=[BODY,WIN,"M92,188 Q300,172 700,184","M398,102 L402,146",
 "M722,160 L752,170 L752,178 L716,172 Z","M44,176 L62,168 L66,178 L44,186 Z",
 "M708,196 L752,196 M708,203 L752,203 M708,210 L752,210","M246,168 L420,166 M440,166 L520,168",
 "M508,146 L540,150 L536,158 L506,156 Z"]
def arch(cx,r=60): return f"M{cx-r},226 A{r},{r} 0 0 1 {cx+r},226"
def wheel(cx,cy=226,r=46):
    s=f'<circle cx="{cx}" cy="{cy}" r="{r}"/><circle cx="{cx}" cy="{cy}" r="9"/>'
    for i in range(5):
        a=math.radians(i*72-90); s+=f'<line x1="{cx+12*math.cos(a):.1f}" y1="{cy+12*math.sin(a):.1f}" x2="{cx+38*math.cos(a):.1f}" y2="{cy+38*math.sin(a):.1f}"/>'
    return s
def lines(cls=""):
    return ''.join(f'<path d="{d}"/>' for d in DESIGN)+f'<path d="{arch(190)}"/><path d="{arch(610)}"/>'+wheel(190)+wheel(610)
# --- string art: sample silhouette (upper contour & baseline)
def q(p0,p1,p2,n=14):
    return [((1-t)**2*p0[0]+2*(1-t)*t*p1[0]+t*t*p2[0],(1-t)**2*p0[1]+2*(1-t)*t*p1[1]+t*t*p2[1]) for t in [i/n for i in range(n)]]
def l(p0,p1,n=6): return [(p0[0]+(p1[0]-p0[0])*t/n,p0[1]+(p1[1]-p0[1])*t/n) for t in range(n)]
top=(l((40,182),(40,182),1)+q((40,182),(46,166),(82,161),3)+l((82,161),(190,151),8)+q((190,151),(232,100),(302,88),12)
    +l((302,88),(470,88),12)+q((470,88),(542,92),(592,140),12)+l((592,140),(700,153),8)+q((700,153),(750,161),(760,186),4))
bot=[(55+695*i/(len(top)-1),226) for i in range(len(top))]
nails_top=top[::2]
nails_bot=bot[::2]
def thread():
    s=''
    for i,(x,y) in enumerate(top):
        for d in (-4,0,4):
            j=min(max(i+d,0),len(bot)-1); bx,by=bot[j]
            s+=f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{bx:.0f}" y2="{by}"/>'
    return s
def ring(cx,cy=226,r=50,n=36,step=11):
    pts=[(cx+r*math.cos(2*math.pi*i/n),cy+r*math.sin(2*math.pi*i/n)) for i in range(n)]
    return ''.join(f'<line x1="{pts[i][0]:.0f}" y1="{pts[i][1]:.0f}" x2="{pts[(i+step)%n][0]:.0f}" y2="{pts[(i+step)%n][1]:.0f}"/>' for i in range(n)),pts
T=lambda x,y,t,s=20,w=400,c="#222",a="start":f'<text x="{x}" y="{y}" font-family="Helvetica,Arial,sans-serif" font-size="{s}" font-weight="{w}" fill="{c}" text-anchor="{a}">{t}</text>'
o=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1100" width="1600" height="1100"><defs>'
'<filter id="glow" x="-5%" y="-5%" width="110%" height="110%"><feGaussianBlur stdDeviation="5"/></filter>'
'<filter id="sh" x="-10%" y="-10%" width="130%" height="140%"><feDropShadow dx="4" dy="6" stdDeviation="3" flood-color="#000" flood-opacity=".55"/></filter>'
'<clipPath id="plate"><rect x="0" y="0" width="800" height="270"/></clipPath></defs>',
 '<rect width="1600" height="1100" fill="#efe9df"/>',
 T(800,58,"Car design-lines wall art — concept",36,700,a="middle"),
 T(800,92,"Only the car's signature lines remain. The rest is empty: the wall and the light do the drawing",19,400,"#555","middle")]
# A: CNC-cut backlit
ox,oy,sc=60,200,0.85
o.append(T(ox,oy-50,"A · Line-cut plate (CNC / laser / printed), backlit",24,700))
o.append(f'<g transform="translate({ox},{oy}) scale({sc})"><rect x="-30" y="-30" width="860" height="330" rx="12" fill="#14161c"/>'
 f'<g transform="translate(0,5)" fill="none" stroke="#ffb54a" stroke-width="7" stroke-linejoin="round" stroke-linecap="round" filter="url(#glow)" opacity=".8">{lines()}</g>'
 f'<g transform="translate(0,5)" fill="none" stroke="#fff3d6" stroke-width="3" stroke-linejoin="round" stroke-linecap="round">{lines()}</g></g>')
# B: string art
bx,by=60,640
o.append(T(bx,by-50,"B · String art on a wood board (nails + thread)",24,700))
r1,p1=ring(190);r2,p2=ring(610)
nails=''.join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="2.6"/>' for x,y in nails_top+nails_bot+p1+p2)
o.append(f'<g transform="translate({bx},{by}) scale({sc})"><rect x="-30" y="-30" width="860" height="330" rx="12" fill="#b98c5a"/><rect x="-30" y="-30" width="860" height="330" rx="12" fill="none" stroke="#6b4a26" stroke-width="5"/>'
 f'<g transform="translate(0,5)"><g stroke="#8d1d12" stroke-width="1.1" opacity=".95">{thread()}</g>'
 f'<g stroke="#8d1d12" stroke-width="0.9">{r1}{r2}</g>'
 f'<g fill="none" stroke="#2a1a0c" stroke-width="3" stroke-linejoin="round"><path d="{WIN}" fill="#b98c5a"/></g>'
 f'<g fill="#3a2a18">{nails}</g></g></g>')
# C: layered thin line plates
cx_,cy_=840,200
o.append(T(cx_,cy_-50,"C · Two thin line layers 5 mm apart (depth + shadow)",24,700))
def layer(stroke,w,dx,dy,sub):
    return f'<g transform="translate({dx},{dy})" filter="url(#sh)" fill="none" stroke="{stroke}" stroke-width="{w}" stroke-linejoin="round" stroke-linecap="round">{sub}</g>'
back=''.join(f'<path d="{d}"/>' for d in [BODY,"M92,188 Q300,172 700,184"])+f'<path d="{arch(190)}"/><path d="{arch(610)}"/>'
front=''.join(f'<path d="{d}"/>' for d in [WIN,"M398,102 L402,146"]+DESIGN[4:])+wheel(190)+wheel(610)
o.append(f'<g transform="translate({cx_},{cy_}) scale({sc})"><rect x="-30" y="-30" width="860" height="330" rx="12" fill="#e9e3d8" stroke="#2a2118" stroke-width="10"/>'
 f'<g transform="translate(0,5)">{layer("#1b1f2a",6,0,0,back)}{layer("#c0392b",5,8,-6,front)}</g></g>')
# notes
o.append(T(860,680,"Why it works",24,700))
for i,t in enumerate(["• Recognizable from lines alone: roofline, beltline, arches, light signature","• Thin = fast print, low material cost (A3 ≈ 2–3 mm plate)","• Backlit (LED strip behind) → glows at night, 'wow' effect","• Same file: print on H2D, or send to CNC/laser for wood/acrylic","• Custom: customer's car → lines traced from a photo"]):
    o.append(T(860,720+i*36,t,19,400,"#333"))
o.append(T(800,1070,"Illustrative generic coupe",15,400,"#777","middle"))
o.append('</svg>')
open("car_lines_concept.svg","w").write("\n".join(o))
