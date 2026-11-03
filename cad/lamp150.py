"""Little-prince lamp at 150 mm: diffuser (own design, bear + text) and, from the owner's licensed 3MF, case + LED stand.

    .venv-cad/bin/python cad/lamp150.py --lamp-3mf path/to/littleprinceroundlamp.3mf --out DIR [--k 1.5]

Diffuser files (no third-party geometry) go to cad/print_files/lamp_150/. The case and the stand come from the
licensed file, so they are written to --out only (never commit them: the repo is public). Case and stand are scaled
in X/Y by k (height unchanged, which keeps print time reasonable); diffuser disc = 79 * k, relief 0.67 mm.
"""
import argparse
import json
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import trimesh
from shapely import affinity
from shapely.geometry import Point

from diffuser import build, R, DISC_H, RELIEF_H
from threemf import build_project_settings, write_bambu_3mf

HERE = Path(__file__).parent
WHITE, BLACK = "#F2F0EA", "#1B1B1B"


def lamp_mesh(z, name, oid):
    r = ET.fromstring(z.read(name))
    ns = r.tag.split("}")[0] + "}"
    for o in r.iter(ns + "object"):
        if o.get("id") == str(oid):
            v = np.array([[float(x.get(a)) for a in "xyz"] for x in o.iter(ns + "vertex")])
            f = np.array([[int(t.get(a)) for a in ("v1", "v2", "v3")] for t in o.iter(ns + "triangle")])
            return trimesh.Trimesh(v, f)
    raise KeyError(oid)


def settings(cols):
    tpl = (HERE / "config" / "bambu_project_4fil_pla.config").read_bytes()
    return build_project_settings(tpl, (cols + [cols[-1]] * 4)[:4], None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lamp-3mf", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--k", type=float, default=1.5)
    a = ap.parse_args()
    k = a.k
    pub = HERE / "print_files" / f"lamp_{int(round(79 * k * 100 / 79 / 1))}"  # lamp_150 for k=1.5
    pub.mkdir(parents=True, exist_ok=True)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    for lang in ("ar", "en"):
        g = affinity.scale(build(json.load(open(HERE / f"plaque/diffuser_{lang}.json"))), k, k, origin=(0, 0))
        disc = trimesh.creation.extrude_polygon(Point(0, 0).buffer(R * k, 128), DISC_H)
        rel = [trimesh.creation.extrude_polygon(p, RELIEF_H) for p in getattr(g, "geoms", [g]) if p.geom_type == "Polygon"]
        for r in rel:
            r.apply_translation([0, 0, DISC_H])
        relief = trimesh.util.concatenate(rel)
        write_bambu_3mf(pub / f"diffuser_{lang}.3mf", [("disc", disc, 1), ("relief", relief, 2)], center=(160, 160),
                        name=f"diffuser_{lang}", project_settings=settings([WHITE, BLACK]))
        print("wrote", pub / f"diffuser_{lang}.3mf", "disc dia %.0f mm" % (2 * R * k))
    z = zipfile.ZipFile(a.lamp_3mf)
    for name, mesh in (("case", lamp_mesh(z, "3D/Objects/object_4.model", 6)), ("stand", lamp_mesh(z, "3D/Objects/object_2.model", 1))):
        mesh.apply_scale((k, k, 1))
        c = mesh.bounds
        mesh.apply_translation([-(c[0][0] + c[1][0]) / 2, -(c[0][1] + c[1][1]) / 2, -c[0][2]])
        write_bambu_3mf(out / f"{name}_{int(k*100)}.3mf", [(name, mesh, 1)], center=(160, 160), name=name,
                        project_settings=settings([WHITE]))
        print("wrote", out / f"{name}_{int(k*100)}.3mf", np.round(mesh.bounds[1] - mesh.bounds[0], 1))


if __name__ == "__main__":
    main()
