exec(open('make_e30.py').read().split("W,H=1100,560")[0])
LEN=94.0
x0,x1,y0,y1=min(xs),max(xs),min(ys),max(ys)
k=LEN/(x1-x0)                       # cm per projected unit
Hcm=(y1-y0)*k; PX=10.0              # 10 px per cm
mx,my=90,90                          # margins (axis space)
Wc,Hc=int(LEN*PX)+mx+60,int(Hcm*PX)+my+110
def tx(x): return mx+(x-x0)*k*PX
def ty(y): return 60+(y-y0)*k*PX
base=60+Hcm*PX
pl=" ".join("M"+" L".join(f"{tx(x):.1f},{ty(y):.1f}" for x,y in p) for p in P)
g=[];lab=[]
for c in range(0,int(LEN)+1,10):
    X=mx+c*PX; g.append(f'<line x1="{X}" y1="60" x2="{X}" y2="{base}" stroke="#cfc8ba" stroke-width="1"/>')
    lab.append(f'<text x="{X}" y="{base+24}" text-anchor="middle">{c}</text>')
for c in range(0,int(Hcm)+1,10):
    Y=base-c*PX; g.append(f'<line x1="{mx}" y1="{Y}" x2="{mx+LEN*PX}" y2="{Y}" stroke="#cfc8ba" stroke-width="1"/>')
    lab.append(f'<text x="{mx-12}" y="{Y+5}" text-anchor="end">{c}</text>')
tk=''.join(f'<line x1="{mx+c*PX}" y1="{base}" x2="{mx+c*PX}" y2="{base+(10 if c%10 else 16)}" stroke="#222"/>' for c in range(0,int(LEN)+1,5))
tk+=''.join(f'<line x1="{mx}" y1="{base-c*PX}" x2="{mx-(10 if c%10 else 16)}" y2="{base-c*PX}" stroke="#222"/>' for c in range(0,int(Hcm)+1,5))
bx0,bx1=mx,mx+LEN*PX
dim=(f'<g stroke="#c0392b" stroke-width="1.5" fill="#c0392b" font-size="17" font-weight="700">'
 f'<line x1="{bx0}" y1="{base+48}" x2="{bx1}" y2="{base+48}" marker-start="url(#ar)" marker-end="url(#ar)"/>'
 f'<text x="{(bx0+bx1)/2}" y="{base+72}" text-anchor="middle" stroke="none">{LEN:.0f} cm</text>'
 f'<line x1="{bx1+34}" y1="60" x2="{bx1+34}" y2="{base}" marker-start="url(#ar)" marker-end="url(#ar)"/>'
 f'<text x="{bx1+46}" y="{(60+base)/2}" stroke="none" transform="rotate(90 {bx1+46} {(60+base)/2})" text-anchor="middle">{Hcm:.0f} cm</text></g>')
svg=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {Wc} {Hc}" width="{Wc}" height="{Hc}" font-family="Helvetica,Arial,sans-serif">
<defs><marker id="ar" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#c0392b" stroke="none"/></marker></defs>
<rect width="{Wc}" height="{Hc}" fill="#f4f0e8"/>
<text x="{Wc/2}" y="32" text-anchor="middle" font-size="24" font-weight="700" fill="#222">E30 3/4 · {LEN:.0f} × {Hcm:.0f} cm (1 grid square = 10 cm)</text>
{''.join(g)}
<line x1="{mx}" y1="60" x2="{mx}" y2="{base}" stroke="#222" stroke-width="2"/><line x1="{mx}" y1="{base}" x2="{mx+LEN*PX}" y2="{base}" stroke="#222" stroke-width="2"/>
{tk}
<g font-size="15" fill="#222">{''.join(lab)}</g>
<path d="{pl}" fill="none" stroke="#111" stroke-width="2.6" stroke-linejoin="round" stroke-linecap="round"/>
{dim}
<text x="{Wc-20}" y="{Hc-14}" text-anchor="end" font-size="14" fill="#666">Concept · generic proportions</text>
</svg>'''
open('e30_dims.svg','w').write(svg); print(Wc,Hc,round(Hcm,1))
