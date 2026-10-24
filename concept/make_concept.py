BODY="M40,210 L40,182 Q46,166 82,161 L190,151 Q232,100 302,88 L470,88 Q542,92 592,140 L700,153 Q750,161 760,186 L762,212 Q762,224 750,226 L50,226 Q40,226 40,210 Z"
WIN="M214,148 Q250,110 305,102 L462,102 Q516,106 556,146 Z"
WIN_PILLAR="M392,102 L398,102 L402,146 L388,146 Z"
LINE="M92,188 Q300,172 700,184"
ARCH=lambda cx:f"M{cx-60},226 A60,60 0 0 1 {cx+60},226 Z"
def mask(id,shapes):
    return f'<mask id="{id}"><rect x="0" y="0" width="800" height="260" fill="#fff"/>{shapes}</mask>'
cut='fill="#000" stroke="#000"'
defs=f'''
{mask("mBody",f'<path d="{WIN}" {cut}/><path d="{ARCH(190)}" {cut}/><path d="{ARCH(610)}" {cut}/><path d="{LINE}" fill="none" stroke="#000" stroke-width="5" stroke-linecap="round"/><path d="M330,230 L560,230" stroke="#000" stroke-width="0"/>')}
{mask("mDet",'<g/>')}
<filter id="sh" x="-10%" y="-10%" width="130%" height="140%"><feDropShadow dx="6" dy="9" stdDeviation="5" flood-color="#000" flood-opacity=".55"/></filter>
<filter id="sh2" x="-10%" y="-10%" width="130%" height="140%"><feDropShadow dx="3" dy="5" stdDeviation="3" flood-color="#000" flood-opacity=".5"/></filter>
'''
def wheel(cx):
    s=''
    for i in range(5):
        s+=f'<rect x="{cx-5}" y="{226-44}" width="10" height="30" rx="5" fill="#000" transform="rotate({i*72} {cx} 226)"/>'
    return f'<g mask="url(#mw{cx})"><circle cx="{cx}" cy="226" r="50" fill="#e8e8e8"/></g>'
wheel_defs=''.join(mask(f"mw{cx}",''.join(f'<rect x="{cx-6}" y="{226-42}" width="12" height="28" rx="6" fill="#000" transform="rotate({i*72} {cx} 226)"/>' for i in range(5))+f'<circle cx="{cx}" cy="226" r="9" fill="#000"/>') for cx in (190,610))
L1=f'<path d="{BODY}" fill="#1b1f2a"/>'
L2=f'<path d="{BODY}" fill="#c0392b" mask="url(#mBody)"/>'
L3=('<path d="M722,160 L752,170 L752,178 L716,172 Z" fill="#ffd54a"/>'
    '<path d="M44,176 L62,168 L66,178 L44,186 Z" fill="#ff5a4d"/>'
    '<path d="M708,196 L752,196 M708,203 L752,203 M708,210 L752,210" stroke="#222" stroke-width="3"/>'
    '<path d="M300,108 L300,146 M470,106 L470,146" stroke="#c0392b" stroke-width="0"/>'
    '<path d="M246,168 L420,166 M440,166 L520,168" stroke="#222" stroke-width="2.5" fill="none"/>'
    '<path d="M508,146 L540,150 L536,158 L506,156 Z" fill="#222"/>')
L4=wheel(190)+wheel(610)
def layer(inner,dx,dy,f="sh2",extra=""):
    return f'<g transform="translate({dx},{dy})" filter="url(#{f})" {extra}>{inner}</g>'
bg='<rect width="1600" height="1000" fill="#efe9df"/>'
txt=lambda x,y,t,s=22,w=400,c="#222",a="start":f'<text x="{x}" y="{y}" font-family="Helvetica,Arial,sans-serif" font-size="{s}" font-weight="{w}" fill="{c}" text-anchor="{a}">{t}</text>'
out=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1000" width="1600" height="1000"><defs>{defs}{wheel_defs}</defs>',bg]
out.append(txt(800,64,"Car Code Layers — concept",38,700,a="middle"))
out.append(txt(800,98,"Layered hollow wall art · each layer reveals one part of the car's design",20,400,"#555","middle"))
# exploded
names=['Layer 1: silhouette (back plate)','Layer 2: body, windows &amp; lines cut out','Layer 3: lights, grille, details','Layer 4: wheels']
cols=[L1,L2,L3,L4]
out.append(txt(60,150,"1 · Exploded view (layers)",26,700))
pos=[(50,200),(130,300),(210,400),(290,500)]
for i,((x,y),c,n) in enumerate(zip(pos,cols,names)):
    out.append(f'<g transform="translate({x},{y}) matrix(0.62,0,-0.2,0.62,0,0)" filter="url(#sh2)">'
               f'<rect x="10" y="60" width="780" height="190" rx="10" fill="#fff" fill-opacity="{0.35 if i else 0.0}" stroke="#999" stroke-dasharray="8 6"/>{c}</g>')
    out.append(txt(x+520,y+110,n,16,400,"#333"))
# assembled
out.append(txt(1000,150,"2 · Assembled (4–6 mm spacers)",26,700))
out.append('<g transform="translate(940,200) scale(0.7)">'
 '<rect x="-25" y="-35" width="880" height="400" rx="14" fill="#2a2118"/>'
 '<rect x="-12" y="-22" width="854" height="374" rx="8" fill="#d8cfc0"/>'
 f'<g transform="translate(20,40)">{layer(L1,0,0,"sh2")}{layer(L2,5,-4,"sh")}{layer(L3,10,-8,"sh2")}{layer(L4,10,-8,"sh2")}</g></g>')
out.append(txt(1230,560,"Shadows between layers create the depth",18,400,"#555","middle"))
# bottom notes
out.append(txt(60,760,"Materials",26,700))
notes=["• Printed on your Bambu H2D: 1.2–2 mm per layer, a different filament color per layer (no painting)",
       "• Or CNC/laser-cut 3 mm plywood/MDF for a wood look",
       "• 4–6 mm spacers between layers + frame → real depth, optional LED strip behind (Premium)",
       "• Sizes: A4 / A3 · 3–6 layers · Custom: customer's own car from a photo"]
for i,n in enumerate(notes): out.append(txt(60,805+i*34,n,20,400,"#333"))
out.append(txt(800,960,"Illustrative generic coupe — real models would be traced from official side/front views",16,400,"#777","middle"))
out.append('</svg>')
open("car_code_layers_concept.svg","w").write("\n".join(out))
