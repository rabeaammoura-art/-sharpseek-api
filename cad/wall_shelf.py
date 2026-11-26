"""Wall/cabinet display shelf that also hides a row of screw heads.

Profile (side view, x = away from the cabinet, y = up) extruded along the length,
printed standing on its END (length = Z) so layers run along the load: no supports.
Usage: python cad/wall_shelf.py out_prefix [length depth]
"""
import sys
import numpy as np
import trimesh
from shapely.geometry import box, Point
from shapely.ops import unary_union
from shapely.geometry import Polygon

L = float(sys.argv[2]) if len(sys.argv) > 2 else 250.0   # length along the cabinet
D = float(sys.argv[3]) if len(sys.argv) > 3 else 120.0   # shelf depth
T = 3.0          # plate / shelf thickness
GAP = 4.0        # stand-off so the plate clears screw heads
BACK_H = 80.0    # back plate height (covers the screw band)
RAIL = 9.0       # stand-off rail height top/bottom
LIP = 10.0
GUS_H = 55.0     # gusset height below the shelf
GUS_T = 3.0
N_GUS = 5

# --- main profile (x,y), y=0 is the top face of the shelf's underside -> shelf y 0..T
parts = [
    box(0, 0, T, BACK_H),                 # back plate
    box(0, 0, D, T),                      # shelf
    box(D - 3, 0, D, LIP),                # front lip
    box(-GAP, 0, 0, RAIL + T),            # bottom stand-off rail
    box(-GAP, BACK_H - RAIL, 0, BACK_H),  # top stand-off rail
]
prof = unary_union(parts)
# fixing holes: through plate + rail (axis X), top rail and bottom rail
holes_y = [BACK_H - RAIL / 2, T + RAIL / 2]


def extrude(poly, z0, z1):
    m = trimesh.creation.extrude_polygon(poly, z1 - z0)
    m.apply_translation([0, 0, z0])
    return m


meshes = [extrude(prof, 0, L)]
# gussets: triangles below the shelf touching the cabinet face (x=-GAP)
tri = Polygon([(-GAP, -GUS_H), (-GAP, 0.01), (D * 0.85, 0.01)])
xs = np.linspace(GUS_T / 2 + 2, L - GUS_T / 2 - 2, N_GUS)
for z in xs:
    meshes.append(extrude(tri, z - GUS_T / 2, z + GUS_T / 2))
body = trimesh.util.concatenate(meshes)
body = trimesh.boolean.union(meshes, engine="manifold") if hasattr(trimesh, "boolean") else body

# screw holes (countersunk) from the front, along -X
fix_z = np.linspace(25, L - 25, 4)
cuts = []
for y in holes_y:
    for z in fix_z:
        cyl = trimesh.creation.cylinder(radius=2.3, height=20, sections=24)
        cyl.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
        cyl.apply_translation([0, y, z])
        cone = trimesh.creation.cone(radius=4.6, height=2.6, sections=24)
        cone.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [0, 1, 0]))
        cone.apply_translation([T + 0.01, y, z])
        cuts += [cyl, cone]
body = trimesh.boolean.difference([body] + cuts, engine="manifold")

# print orientation: length along Z already (standing on its end); drop to z=0, centre x/y
body.apply_translation(-body.bounds[0])
out = sys.argv[1]
body.export(out + ".stl")
print(out + ".stl", body.extents, "watertight", body.is_watertight, "vol cm3", body.volume / 1000)
