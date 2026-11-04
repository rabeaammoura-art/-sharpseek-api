"""Dimensioned technical drawing of the 3-module wall art. usage: python drawing.py <stl_dir_master> <mod_dir>"""
import sys, json
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP, Rectangle
sys.path.insert(0, str(Path(__file__).parent)); import modular as M
BK, BU, k = M.load_master(sys.argv[1]); mod = Path(sys.argv[2]); V = json.loads((mod / "validation.json").read_text())
fig = plt.figure(figsize=(23.4, 16.5)); fig.patch.set_facecolor("white")
ax = fig.add_axes([0.04, 0.50, 0.92, 0.42])
def fill(ax, g, c):
    for p in (g.geoms if hasattr(g, "geoms") else [g]):
        ax.fill(*p.exterior.xy, color=c, lw=0)
        for h in p.interiors: ax.fill(*h.xy, color="white", lw=0)
fill(ax, BK, "#222"); fill(ax, BU, "#1d3fd0")
H = 211.0
for i, s in enumerate(M.SEAMS):
    ax.axvline(s, color="r", lw=0.8, ls="--"); ax.text(s, H+8, f"seam {i+1}  x={s:g}", color="r", ha="center", fontsize=9)
    for p in V["pads"][str(s)] if str(s) in V["pads"] else V["pads"][str(float(s))]:
        ax.add_patch(Rectangle((s-M.PWA, p["y0"]), M.PWA+M.PWB, p["y1"]-p["y0"], fill=False, ec="#e08000", lw=0.8))
edges = [0] + M.SEAMS + [600]
for i in range(3):
    ax.annotate("", (edges[i], -14), (edges[i+1], -14), arrowprops=dict(arrowstyle="<->", lw=0.8))
    ax.text((edges[i]+edges[i+1])/2, -22, f"module {i+1}: {edges[i+1]-edges[i]:g} mm (+ tab/pads)  |  {V['modules'][i]['size_xyz_mm'][0]:g} x {V['modules'][i]['size_xyz_mm'][1]:g} x {V['modules'][i]['size_xyz_mm'][2]:g} mm", ha="center", fontsize=9)
ax.annotate("", (0, -34), (600, -34), arrowprops=dict(arrowstyle="<->", lw=1)); ax.text(300, -42, "600", ha="center", fontsize=11, weight="bold")
ax.annotate("", (-10, 0), (-10, H), arrowprops=dict(arrowstyle="<->", lw=1)); ax.text(-14, H/2, "211", rotation=90, va="center", ha="right", fontsize=11, weight="bold")
ax.set_xlim(-30, 630); ax.set_ylim(-50, H+20); ax.set_aspect("equal"); ax.axis("off")
ax.set_title("FRONT VIEW (as seen on the wall)  -  orange = rear dovetail pads (hidden behind the lines)  -  red dashed = module seams", fontsize=11, loc="left")
# ---- section through a joint (x-z), seam at x=0
a2 = fig.add_axes([0.04, 0.06, 0.40, 0.36]); G = M.G; T = M.T
def tab_poly():
    xr, xt = -G/2-0.5, G/2+M.E
    return [(xr, M.ZC-M.half(0, xr)), (xt, M.ZC-M.half(0, xt)), (xt, M.ZC+M.half(0, xt)), (xr, M.ZC+M.half(0, xr))]
def pocket_poly():
    xm, xt = G/2, G/2+M.E+0.3
    return [(xm, M.ZC-M.half(0, xm)-M.C), (xt, M.ZC-M.half(0, xt)-M.C), (xt, M.ZC+M.half(0, xt)+M.C), (xm, M.ZC+M.half(0, xm)+M.C)]
def half0(x): return M.half(0.0, x)
a2.add_patch(Rectangle((-14, 0), 14-G/2, T, fc="#bbb", ec="k")); a2.add_patch(Rectangle((G/2, 0), 14, T, fc="#bbb", ec="k"))
a2.add_patch(Rectangle((-M.PWA, T), M.PWA-G/2-0.03, M.ZTOP-T, fc="#f2c48a", ec="k"))
pb = Rectangle((G/2+0.03, T), M.PWB-G/2-0.03, M.ZTOP-T, fc="#9ec9f0", ec="k"); a2.add_patch(pb)
a2.add_patch(MP(pocket_poly(), fc="white", ec="k", lw=0.8)); a2.add_patch(MP(tab_poly(), fc="#e8a040", ec="k", lw=1.2))
a2.set_xlim(-15, 16); a2.set_ylim(-3, 18.5); a2.set_aspect("equal"); a2.grid(alpha=0.2)
a2.set_title("SECTION A-A  (across the seam, through one pad)  -  front face at z=0, rear up   [mm]", fontsize=11, loc="left")
txt = [f"body thickness {T:g}", f"pad height above body {M.ZTOP-T:.2f}  (total {M.ZTOP:.2f})", f"tab: {M.E:g} long, {2*M.A0:.2f} thick at root -> {2*M.B0:.2f} at tip ({M.ANG:g} deg flanks)",
       f"clearance {M.C} per surface, seam gap {G} (0.1 per face)", f"floor {M.FLOOR}, cap {M.CAP}, end wall (lowest pocket) {M.STOP}", f"male pad {M.PWA:g} wide, female pad {M.PWB:g} wide, slide direction = vertical (Y), assemble from above"]
for i, t in enumerate(txt): a2.text(-14.5, 16.6-0.95*i, t, fontsize=8, va="top")
a2.text(-3.5, 1.2, "module A (male: pad + tab)", ha="center", fontsize=8); a2.text(7, 1.2, "module B (female: pad + pocket)", ha="center", fontsize=8)
# ---- tables
a3 = fig.add_axes([0.50, 0.06, 0.46, 0.38]); a3.axis("off")
lines = ["MODULES (print front face DOWN, rear pads up; PLA, 0.2 mm layers, supports for pads/pockets)"]
for m in V["modules"]:
    lines.append(f"  M{m['module']}: {m['size_xyz_mm'][0]:g} x {m['size_xyz_mm'][1]:g} x {m['size_xyz_mm'][2]:g} mm, {m['volume_cm3']} cm3 (~{m['grams_pla_est']} g), pads {m['pads']}, rear ties {m['rear_ties']}, watertight {m['watertight']}, shells {m['shells']}")
lines += ["", "JOINT PADS  (y range along the seam, colour)"]
for s, pads in V["pads"].items():
    lines.append(f"  seam x={float(s):g}: " + ", ".join(f"{p['y0']:.0f}-{p['y1']:.0f} ({p['colour']})" for p in pads))
lines += ["", "CLEARANCES (assembled)"] + [f"  {p['pair']}: interference {p['interference_mm3']} mm3, min gap {p['min_gap_mm']} mm" for p in V["pairs"]]
lines += ["", f"Front face: original {V['front_face']['area_original']} mm2, assembled {V['front_face']['area_assembled']} mm2 (hairline seam {V['front_face']['seam_hairline_mm']} mm at the {sum(len(v) for v in V['pads'].values())} crossings)",
          "Colours: black = slot 1, blue = slot 2 (2 filaments).  Scale 2.0149 x the approved 298 x 105 mm master.", "Not print-tested (printer not here)."]
a3.text(0, 1, "\n".join(lines), va="top", fontsize=9, family="monospace")
fig.text(0.04, 0.965, "BMW AUTOMOTIVE PAINTER - OPENWORK WALL ART  |  600 x 211 mm, 3 mm body, 3 interlocking modules  |  3D ZONE TECH", fontsize=15, weight="bold")
fig.savefig(mod / "technical_drawing.png", dpi=110); fig.savefig(mod / "technical_drawing.pdf")
print("ok")
