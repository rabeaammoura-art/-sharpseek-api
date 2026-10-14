"""Modify the ORIGINAL left housing mesh -> out/housing_L_mod.stl, and mirror -> out/housing_R_mod.stl.

Operations (all boolean, original outer geometry / mounting tabs / turn-signal interface untouched):
 1. remove the old inboard intake scoop + hose flange (box cut inside the bezel rim, top/bottom plates kept)
 2. restore the original front surface across the scoop as a 3 mm skin (quadratic fit, 0.3 mm RMS to the
    untouched face) -> one continuous printed fascia, no seam
 3. inboard Ø93 aperture with a cylindrical return collar (same look as the outboard opening)
 4. stiffening ribs behind the new skin
 5. mounting bosses for the aiming brackets (heat-set inserts) and top-access adjuster screw holes
 6. drain holes in the bottom plate
"""
import sys
from pathlib import Path
import numpy as np
import trimesh
import manifold3d as mf

sys.path.insert(0, str(Path(__file__).parent))
import params as P
import geom as G

OUT = G.OUT


def to_mf(tm: trimesh.Trimesh) -> mf.Manifold:
    m = mf.Manifold(mf.Mesh(vert_properties=np.asarray(tm.vertices, np.float32),
                            tri_verts=np.asarray(tm.faces, np.uint32)))
    assert m.status() == mf.Error.NoError, m.status()
    return m


def to_tm(m: mf.Manifold) -> trimesh.Trimesh:
    o = m.to_mesh()
    t = trimesh.Trimesh(np.asarray(o.vert_properties)[:, :3], np.asarray(o.tri_verts), process=True)
    parts = [b for b in t.split(only_watertight=False) if len(b.faces) > 50]   # drop zero-volume slivers
    return trimesh.util.concatenate(parts) if len(parts) > 1 else parts[0]


def box(x0, x1, y0, y1, z0, z1):
    return mf.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def cyl_y(cx, cz, r, y0, y1, n=128):
    """Cylinder along +Y from y0 to y1."""
    c = mf.Manifold.cylinder(y1 - y0, r, r, n)            # along +Z from 0
    return c.rotate([-90, 0, 0]).translate([cx, y0, cz])   # rotate Z->Y


def cyl_z(cx, cy, r, z0, z1, n=48):
    return mf.Manifold.cylinder(z1 - z0, r, r, n).translate([cx, cy, z0])


def surface_slab(x0, x1, z0, z1, off0, off1, step=2.0):
    """Solid between Y = F(x,z)+off0 and Y = F(x,z)+off1 over a rectangle (watertight grid mesh)."""
    xs = np.arange(x0, x1 + 1e-6, step); zs = np.arange(z0, z1 + 1e-6, step)
    if xs[-1] < x1: xs = np.append(xs, x1)
    if zs[-1] < z1: zs = np.append(zs, z1)
    X, Z = np.meshgrid(xs, zs, indexing="ij")
    nx, nz = X.shape
    front = np.stack([X, G.F(X, Z) + off0, Z], -1).reshape(-1, 3)
    back = np.stack([X, G.F(X, Z) + off1, Z], -1).reshape(-1, 3)
    V = np.vstack([front, back]); nb = len(front)
    idx = lambda i, j: i * nz + j
    F = []
    for i in range(nx - 1):
        for j in range(nz - 1):
            a, b, c, d = idx(i, j), idx(i + 1, j), idx(i + 1, j + 1), idx(i, j + 1)
            F += [[a, b, c], [a, c, d]]                         # front (normal -Y)
            F += [[a + nb, c + nb, b + nb], [a + nb, d + nb, c + nb]]
    def side(seq):
        out = []
        for p, q in zip(seq[:-1], seq[1:]):
            out += [[p, q + nb, q], [p, p + nb, q + nb]]
        return out
    ring = ([idx(i, 0) for i in range(nx)] + [idx(nx - 1, j) for j in range(1, nz)]
            + [idx(i, nz - 1) for i in range(nx - 2, -1, -1)] + [idx(0, j) for j in range(nz - 2, -1, -1)])
    F += side(ring)
    t = trimesh.Trimesh(V, np.array(F), process=True)
    if t.volume < 0: t.invert()
    trimesh.repair.fix_normals(t)
    return to_mf(t)


def build_left():
    orig = trimesh.load(OUT / "housing_L_repaired.stl")
    H = to_mf(orig)
    hull = to_mf(orig.convex_hull)
    cx, cz = P.PROJ_C
    fr = G.projector_frame()
    ap = G.aim_points()
    log = {}

    # 1. remove scoop: everything inside the bezel between the plates, behind the restored face skin.
    cut = (box(P.CUT_X[0], P.CUT_X[1], -200, 100, P.CUT_Z_LOW, P.TOP_PLATE_UNDERSIDE_FRONT - 0.3)
           )  # single height: the top-plate front step runs diagonally, a second box would hole it
    H = H - cut

    # 2. new skin on the restored surface, trimmed by the original convex hull (keeps rounded rim)
    # shave the ±0.4 mm fit residual off the old face inside the rim so new + old read as ONE surface
    H = H - (surface_slab(P.FASCIA_X[0], P.FASCIA_X[1], P.FASCIA_Z[0], P.FASCIA_Z[1], -6.0, 0.6))  # overlap, no coincident faces
    clip = hull + box(P.CUT_X[0], P.CUT_X[1], -300, 300, P.FASCIA_Z[0] + 5, P.FASCIA_Z[1] - 5)
    skin = surface_slab(P.FASCIA_X[0], P.FASCIA_X[1], P.FASCIA_Z[0], P.FASCIA_Z[1], 0.0, P.FASCIA_T) ^ clip
    # ribs behind the skin: horizontal rib above/below the aperture + vertical ribs either side
    ribs = mf.Manifold()
    rib_body = surface_slab(P.FASCIA_X[0], P.FASCIA_X[1], P.FASCIA_Z[0], P.FASCIA_Z[1],
                            P.FASCIA_T - 0.5, P.FASCIA_T + P.FASCIA_RIB_DEPTH)
    for x in (cx - 62.0, cx + 62.0, 4.0):
        ribs += rib_body ^ box(x - P.FASCIA_RIB_T / 2, x + P.FASCIA_RIB_T / 2, -300, 300, P.FASCIA_Z[0], P.FASCIA_Z[1])
    H = H + skin + ribs

    # 3. aperture + return collar (ID = aperture, extends to just behind the lens front plane)
    r_ap = P.PROJ_APERTURE_D / 2
    y_collar_end = fr["y_front"] + 8.0
    collar = cyl_y(cx, cz, r_ap + P.PROJ_COLLAR_T, fr["aperture_y"][0] - 8.0, y_collar_end)
    collar = collar - surface_slab(P.FASCIA_X[0], P.FASCIA_X[1], P.FASCIA_Z[0], P.FASCIA_Z[1], -60.0, 0.0)
    collar = collar ^ hull
    H = H + collar
    H = H - cyl_y(cx, cz, r_ap, -250, y_collar_end + 1)
    # the collar must not stick out of the original envelope
    log["collar_outside_hull_mm3"] = (collar - hull).volume()

    # 5. pads + through holes for the bracket screws, top-access adjuster holes, spring bosses
    bosses = mf.Manifold(); holes = mf.Manifold()
    for name, (x, y, side) in G.mounts().items():
        if side == "bot":       # M5 from below: pad up to the common bracket datum, counterbore in the underside
            bosses += cyl_z(x, y, 7.0, 128.0, G.BOSS_TOP_Z_BOTTOM)
            holes += cyl_z(x, y, P.CLEAR["M5"] / 2, 110.0, G.BOSS_TOP_Z_BOTTOM + 1)
            holes += cyl_z(x, y, 5.0, 110.0, 125.3 + 3.0)
        else:                   # M5 from above through the top plate into the pillar insert
            bosses += cyl_z(x, y, 7.0, G.BOSS_BOT_Z_TOP, G.top_underside_z(x, y) + 2.0)
            bosses += cyl_z(x, y, 8.0, 245.0, G.SEAT_Z)                       # flat head pad
            holes += cyl_z(x, y, P.CLEAR["M5"] / 2, G.BOSS_BOT_Z_TOP - 1, 270)
    log["mounts"] = {k: (round(float(t[0]), 1), round(float(t[1]), 1), t[2]) for k, t in G.mounts().items()}
    for k, (x, y) in G.adjusters().items():
        holes += cyl_z(x, y, P.CLEAR["M5"] / 2 + 0.25, 200, 270)
        if G.ADJ_SEAT[k] == "housing":
            bosses += cyl_z(x, y, 8.5, 245.0, G.SEAT_Z)                     # Ø17 flat pad for washer + head
    log["adjuster_xy"] = {k: (round(float(x), 1), round(float(y), 1)) for k, (x, y) in G.adjusters().items()}
    # preload spring seats on the back of the skin, in line with A and B (cup Ø9.5 x 3 deep on a post)
    sp = P.PRELOAD_SPRING; yc_front = fr["y_mount"] - P.CARRIER_T
    for k in ("A", "B"):
        x, _, z = ap[k]
        y_seat = yc_front - sp["l_installed"]
        y_skin = float(G.F(x, z)) + P.FASCIA_T - 0.5
        bosses += cyl_y(x, z, 7.0, y_skin, y_seat)
        holes += cyl_y(x, z, sp["od"] / 2 + 0.75, y_seat - 3.0, y_seat + 1.0)
        log[f"spring_{k}_post_length_mm"] = round(y_seat - y_skin, 1)
    H = H + bosses - holes

    # 6. drain holes (Ø6) in the bottom plate at the front of the new cavity
    for x in (cx - 30, cx + 30, -20.0):
        H = H - cyl_z(x, G.F(x, 131.0) + 12.0, 3.0, 120, 140)

    log["volume_cm3"] = H.volume() / 1000
    return H, log


def main():
    H, log = build_left()
    L = to_tm(H)
    L.export(OUT / "housing_L_mod.stl")
    R = L.copy(); R.apply_transform(np.diag([-1, 1, 1, 1])); R.apply_translation([P.RH_SHIFT_X, 0, 0])
    R.export(OUT / "housing_R_mod.stl")
    for k, v in log.items():
        print(k, v)
    for n, t in (("L", L), ("R", R)):
        print(n, "watertight", t.is_watertight, "volume %.1f cm3" % (t.volume / 1000), "bounds", t.bounds.round(1).tolist())


if __name__ == "__main__":
    main()
