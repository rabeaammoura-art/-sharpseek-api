"""Editable CAD (STEP, B-rep) of the joint features of each module, as exact parametric solids:
rear pads, tabs, pads-minus-pockets and rear tie bars, in assembled art coordinates (front face z=0).
The traced body is a ~85 MB polyline extrusion and takes minutes per module, so it is OFF by default (--with-body).
usage: python step_export.py <stl_dir_master> <out_dir> [--with-body]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); import modular as M
from build123d import Wire, Face, extrude, Compound, Box, Pos, export_step, Vector, Align, Location

def face_of(pg):
    ring = lambda c: Wire.make_polygon([Vector(x, y, 0) for x, y in list(c.coords)[:-1]])
    return Face(ring(pg.exterior), [ring(h) for h in pg.interiors])

def solid_of(geom, z0, z1):
    out = []
    for pg in (geom.geoms if hasattr(geom, "geoms") else [geom]):
        if pg.area > 0.05: out.append(Pos(0, 0, z0) * extrude(face_of(pg), z1 - z0))
    return out

def prism_xz(poly, ya, yb):
    f = Face(Wire.make_polygon([Vector(x, 0, z) for x, z in poly]))
    return Pos(0, ya, 0) * extrude(f, yb - ya, dir=Vector(0, 1, 0))

def pad_block(x0, x1, y0, y1):
    return Box(x1 - x0, y1 - y0, M.ZTOP - M.T + 0.02, align=(Align.MIN,) * 3).moved(Location((x0, y0, M.T - 0.02)))

if __name__ == "__main__":
    FULL = "--with-body" in sys.argv
    BK, BU, k = M.load_master(sys.argv[1]); out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
    mods, info = M.build(BK, BU, None)
    for m in mods:
        parts = solid_of(m["foot"], 0, M.T) if FULL else []
        for bar, col in m["ties"]: parts += solid_of(bar, M.T - 0.02, M.T + 2.2)
        for kind, s, y0, y1, c, j in m["pads"]:
            lowest = (j == 0)
            if kind == "male":
                pb = pad_block(s - M.G/2 - M.PWA, s - M.G/2 - 0.03, y0, y1)
                xr, xt = s - M.G/2 - 0.5, s + M.G/2 + M.E
                tab = prism_xz([(xr, M.ZC - M.half(s, xr)), (xt, M.ZC - M.half(s, xt)), (xt, M.ZC + M.half(s, xt)), (xr, M.ZC + M.half(s, xr))], y0 + (M.STOP if lowest else 0) + M.BIN, y1)
                parts += [pb, tab]
            else:
                pb = pad_block(s + M.G/2 + 0.03, s + M.G/2 + M.PWB, y0, y1)
                xm, xt = s + M.G/2 - 0.5, s + M.G/2 + M.E + 0.3
                pocket = prism_xz([(xm, M.ZC - M.half(s, xm) - M.C), (xt, M.ZC - M.half(s, xt) - M.C), (xt, M.ZC + M.half(s, xt) + M.C), (xm, M.ZC + M.half(s, xm) + M.C)], (y0 + M.STOP) if lowest else (y0 - 1), y1 + 1)
                parts.append(pb - pocket)
        export_step(Compound(parts), str(out / f"module{m['i']}_joints{'_with_body' if FULL else ''}.step")); print("module", m["i"], "ok", flush=True)
