"""v4 build: hollow teddy with internal pillars/beams, removable lithophane joint, wide cable path.

usage: python build_v4.py <dir with original STLs> <photo.jpg> <out dir>
(the original STLs are the v1 files `*teddy_rear*.stl` and `*front_lith*.stl`; nothing is written next to them)
"""
import glob
import sys
import time

import numpy as np
import trimesh
import manifold3d as m3d
from shapely.geometry import LineString, Polygon

import base_mods
import hollow
import joint
import relief_swap
import teddy_edit as te
from heart import X0

SRC = sys.argv[1] if len(sys.argv) > 1 else '/root/.claude/uploads/c69ab67c-81c4-5df2-a89e-e3b545ae3b81/'
PHOTO = sys.argv[2] if len(sys.argv) > 2 else SRC + '5330ae15-image.jpg'
OUT = sys.argv[3] if len(sys.argv) > 3 else 'out/'
t0 = time.time()
log = lambda *a: print('[%4.0fs]' % (time.time() - t0), *a, flush=True)


def simplify(m, tol):
    mf = m3d.Manifold(m3d.Mesh(vert_properties=np.asarray(m.vertices, dtype=np.float32),
                               tri_verts=np.asarray(m.faces, dtype=np.uint32)))
    mm = mf.simplify(tol).to_mesh()
    return trimesh.Trimesh(np.asarray(mm.vert_properties)[:, :3].astype(float), np.asarray(mm.tri_verts), process=True)


def snap32(m):
    """Round to float32 (what an STL stores) and make sure the result is still a clean closed volume."""
    v = np.asarray(m.vertices, dtype=np.float32).astype(np.float64)
    r = trimesh.Trimesh(v, m.faces, process=True)
    r.update_faces(r.nondegenerate_faces())
    r.remove_unreferenced_vertices()
    return r


def save_and_verify(m, path):
    m = snap32(m)
    m.export(path)
    chk = trimesh.load(path)
    ok = chk.is_watertight and chk.is_winding_consistent and chk.is_volume
    log('saved', path, 'faces', len(chk.faces), 'watertight/volume OK' if ok else 'NOT A CLEAN VOLUME', 'volume %.0f mm3' % chk.volume)
    if not ok:
        raise SystemExit('export check failed: ' + path)
    return chk


T0 = trimesh.load(glob.glob(SRC + '*teddy_rear*')[0])
L0 = trimesh.load(glob.glob(SRC + '*front_lith*')[0])
H0, Pn = joint.pocket_polys(T0)

# ---------------------------------------------------------------- teddy
sec = L0.section(plane_origin=[0, 778.3, 0], plane_normal=[0, 1, 0])
Hout = Polygon(max(sec.discrete, key=lambda l: np.ptp(l[:, 0]))[:, [0, 2]]).buffer(0)
T = simplify(te.ring_fillet(T0, Hout), 0.01)                                # smooth fillet around the ring
log('fillet', len(T.faces))
for cx in (829.6, 893.2):                                                      # micro-slits at the lower flanks
    box = trimesh.creation.box(bounds=[[cx - 2.6, 774.0, 36.0], [cx + 2.6, 782.2, 42.6]])
    hull = te.boolean('intersection', [T, box]).convex_hull
    hull = te.boolean('difference', [hull, joint.prism_xz(Pn.buffer(0.1), 773.0, 784.0)])
    T = te.boolean('union', [T, hull])
T = simplify(T, 0.01)
T = te.boolean('union', [T, joint.flange_solid(H0)])                          # fixed flange (labyrinth)
cyl, zc = joint.notch_cutter(Pn)
T = te.boolean('difference', [T, cyl])                                         # finger notch at the cleft
T = base_mods.back_and_cable(T)                                                # sealed back, wide cable path
T = simplify(te.carve_details(T, max_edge=0.5), 0.003)                         # smile + paw pads
log('teddy before hollowing', len(T.faces), T.is_watertight)

occ, xs, ys, zs = hollow.occupancy(T, T.bounds[0] - 1.0, T.bounds[1] + 1.0)
f = hollow.cavity_field(occ, xs, ys, zs)
parts = hollow.cavity_mesh(f, xs, ys, zs)
log('cavity components', len(parts), [round(p.volume) for p in parts])
cav = simplify(parts[0], 0.1)
T = te.boolean('difference', [T, cav])
vent = trimesh.creation.cylinder(radius=1.0, height=8.0, sections=24,
                                 transform=trimesh.transformations.translation_matrix([X0, 880.0, 6.0]))
T = te.boolean('difference', [T, vent])
T = save_and_verify(T, OUT + 'teddy_rear_heart_LED_v4.stl')

# ---------------------------------------------------------------- lithophane
L3, tr, _ = relief_swap.swap_relief(L0, PHOTO)
dome = te.boolean('intersection', [L3, trimesh.creation.box(bounds=[[800, 740, 0], [920, joint.LIP_FRONT_Y - 0.005, 110]])])
tongue, bridge, skirt, _, _ = joint.litho_joint_parts(H0, Pn)
Lj = te.boolean('union', [dome,
                          joint.prism_xz(tongue, joint.LIP_FRONT_Y - 0.2, joint.BR_Y1),
                          joint.prism_xz(bridge, joint.BR_Y0, joint.BR_Y1),
                          joint.prism_xz(skirt, joint.BR_Y0, joint.SK_Y1)])
mid = LineString(Polygon(H0.buffer(-(joint.FL_LEN + joint.SK_GAP + joint.SK_T / 2)).exterior).exterior.coords)
cuts, adds = joint.snap_tabs(mid, (X0, 52.0))
Lj = te.boolean('union', [te.boolean('difference', [Lj] + cuts)] + adds)
Lj = save_and_verify(Lj, OUT + 'heart_front_lithophane_v4.stl')
log('done')
