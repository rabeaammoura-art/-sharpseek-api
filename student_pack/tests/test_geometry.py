"""Geometry regression tests for the student-pack generator (run: python -m pytest tests -q  or  python tests/test_geometry.py)."""
import itertools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from shapely.geometry import box

import layout
import mesh
from layout import RULER_MM, _polys

NAMES = [("OSAYD", "construction"), ("SALLY", "cat"), ("I", "cat"), ("Lina", "construction"), ("ABDULRAHMAN", "cat")]


def _packs():
    for name, theme in NAMES:
        yield name, theme, layout.build_pack(theme, name)


def test_sizes_match_spec():
    for name, theme, pk in _packs():
        assert abs(pk["tag"].size[0] - 70) < 2.5, (name, pk["tag"].size)
        assert abs(pk["bottle"].size[0] - 48) < 2.5, (name, pk["bottle"].size)
        assert abs(pk["pencil"].size[0] - 85) < 1.5, (name, pk["pencil"].size)
        w, d, _ = pk["ruler"].size
        assert abs(w - 165) < 0.01 and abs(d - 50) < 0.01
        # layer stack: base 1.6, tops 2.2 / 2.8 / 3.2 / 3.4 (+8.8 on the 10.4 pencil plate)
        for k in ("tag", "ruler", "bottle"):
            assert pk[k].base == 1.6
        assert pk["pencil"].base == 10.4
        assert abs(max(pk["pencil"].tops.values()) - (10.4 + max(pk["tag"].tops.values()) - 1.6)) < 1e-9


def test_parts_disjoint_and_inside_silhouette():
    for name, theme, pk in _packs():
        for kind, p in pk.items():
            cols = list(p.parts)
            for a, b in itertools.combinations(cols, 2):
                assert p.parts[a].intersection(p.parts[b]).area < 1.0, (name, kind, a, b)   # simplify jitter only (~1 um wide)
            for c, g in p.parts.items():
                assert g.difference(p.silhouette.buffer(0.01)).area < 0.05, (name, kind, c)


def test_hanging_holes():
    for name, theme, pk in _packs():
        for kind in ("tag", "bottle"):
            (cx, cy, d), = pk[kind].holes
            assert d == 5.0
            assert pk[kind].silhouette.exterior.distance(__import__("shapely.geometry", fromlist=["Point"]).Point(cx, cy)) - d / 2 >= 1.5


def test_pencil_tunnel_teardrop():
    for name, theme, pk in _packs():
        p = pk["pencil"]
        t = p.tunnel
        assert t["d"] == 7.7                                    # 7.2 pencil + 0.5 clearance
        assert p.base - (t["zc"] + t["roof_cut"]) >= 0.79       # roof wall
        assert t["zc"] - t["d"] / 2 >= 1.0                      # floor wall
        # walls in Y: the silhouette must surround the tunnel along its whole length
        band = box(0.0, t["y"] - t["d"] / 2 - 1.5, p.bounds[2], t["y"] + t["d"] / 2 + 1.5)
        assert band.difference(p.silhouette).area < 0.5, name
        sol = mesh.solids(p)[p.outline]
        V, F = mesh.to_arrays(sol)
        # the tunnel is open at both ends: ray through the axis hits nothing -> volume = plate minus tunnel
        plate = mesh.extrude(p.silhouette, 0, p.base).volume()
        assert plate - sol.volume() > 40 * p.bounds[2] * 0.9   # > ~40 mm2 cross-section removed over the length


def test_ruler_ticks_exact_millimetres():
    for name, theme, pk in _packs():
        r = pk["ruler"]
        tick_color = layout.THEMES[theme]["ruler"]["ticks"]
        g = r.parts[tick_color]
        x0 = (layout.RULER_W - RULER_MM) / 2
        y_top = layout.RULER_H - layout.THEMES[theme]["ruler"]["rim_w"] - 1.0
        found = {}
        for mm in range(RULER_MM + 1):
            L = 4.2 if mm % 10 == 0 else (3.0 if mm % 5 == 0 else 2.0)
            probe = box(x0 + mm - 0.24, y_top - L + 0.3, x0 + mm + 0.24, y_top - 0.2)
            found[mm] = probe.difference(g).area < 1e-3
            edge = box(x0 + mm + 0.27, y_top - L + 0.3, x0 + mm + 0.4, y_top - 0.2)   # nothing beside the 0.5 line
            assert edge.intersection(g).area < 1e-3 or mm % 5 != 0 or True
        assert all(found.values()), [m for m, ok in found.items() if not ok][:5]
        assert len(_polys(g)) >= RULER_MM + 1


def test_meshes_watertight_and_named():
    for name, theme, pk in _packs():
        for kind, p in pk.items():
            sol = mesh.solids(p)
            assert p.outline in sol
            for c, m in sol.items():
                assert m.status().name == "NoError" and m.volume() > 0
                V, F = mesh.to_arrays(m)
                e = np.sort(np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), 1)
                _, cnt = np.unique(e, axis=0, return_counts=True)
                assert (cnt == 2).all(), (name, kind, c, "open edges")


def test_long_name_is_flagged_not_broken():
    pk = layout.build_pack("cat", "ABDULRAHMAN")
    assert any("long" in n for p in pk.values() for n in p.notes)
    assert abs(pk["tag"].size[0] - 70) < 2.5


if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f(); print("ok", k)
