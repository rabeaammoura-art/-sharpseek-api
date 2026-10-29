# Teddy-bear photo lamp: hand-off to a local session

Repo `rabeaammoura-art/-sharpseek-api`, branch `claude/teddy-v2` (no PR; the user never asked for one). Work lives in `cad/teddy/`,
outputs in `cad/teddy/out/manus_fix/`. Read `cad/teddy/README.md` too.

## Product
Commercial 3D-printed teddy bear (about 200 mm tall, Bambu Lab H2D, PLA+ or PETG, never ASA) with a heart-shaped removable lid on
the chest and an LED behind it. The lid can later carry a lithophane photo relief. The lid must be swappable.
No paint or marker on the product, no magnets (light leakage), no hollow lattice. Print budget about 15 h, current about 9 h 45 m / 280 g.

## Current state (v5)
- `out/manus_fix/teddy_body_chest_led_v5.stl` and `chest_heart_lid_v5.stl`, built by `fix_manus.py` from the ORIGINAL bear
  (`teddy_no_ams_200mm_scaled_master.stl`, 167 x 164 x 200 mm, front = -Y, back = +Y, base z = 0) and Manus' lid
  (`chest_heart_closed_dome_lid_v2.stl`, used only as the front dome surface).
- Run: `python cad/teddy/fix_manus.py <original bear> <manus lid v2> cad/teddy/out/manus_fix/` (Windows: `.venv-cad\Scripts\python`).
  Dependencies are in `cad/requirements.txt`.
- Geometry: geometric heart outline (two R22 lobes, tangent sides, tip fillet 6, cleft fillet 5), 85 mm wide, z 26.5..94, centre x 84.5;
  pocket floor y = 78, side clearance 0.3 mm; lid shell 2 mm with a 4 mm rounded edge; LED recess O33 x 7 deep at (84.6, 63.6);
  cable channel O12 at y = 87 down to the base, trench 12 x 5 mm to the rear edge; two pins O4.8 at (68,74) and (101,74) with bosses/bores.
- `rebuild_rim()` rebuilds a band around the pocket (removes feather edges, smooths the rim); `save()` repairs float32 seam edges.
- Checks done: watertight single volume, seated overlap 0, lid pulls out toward -Y with 0 overlap to 25 mm, back of torso unchanged,
  base flat (20,328 mm2, tip-over 44 deg), no material thinner than 1 mm next to the pocket.
- Bambu Studio numbers (PLA, 0.20 mm, tree supports, lightning 10 % + 3 walls): body 7h47m / 234 g, lid rim-on-bed 1h56m / 46 g.
  Slicing wrapper: `cad/teddy/slice_variants.py` (env DENS, PAT, WALLS, PROC) over `cad/bambu_slice.py` (needs Bambu Studio via flatpak, Linux only).

## v6 (done)
The user sent `heart_sketch_mm.dxf` (in `cad/teddy/input/`); `fix_manus.py ... input/heart_sketch_mm.dxf` builds `*_v6.stl` from it (see README). v6 is the current deliverable; v5 used my geometric heart.

## What the user did before
The user cut a clean heart pocket themselves in Fusion 360 (file `173488c4-teddy_no_ams_200mm_scaled_master.stl`). Findings: exported 10x too big
(1672 mm; Fusion unit mistake), mesh not closed (1242 components, 1272 non-manifold edges around the rim), blade-thin skin remnants at the lower rim,
no LED recess/channel/pins, pocket floor at about y = 65-70 instead of 78. The outline itself is smooth and the user prefers it.

## Next step (superseded by v6; remaining: user review, test print of the lid first)
Take the user's heart from Fusion and feed it to `fix_manus.py` as the outline `P` (replace `heart_outline()`), then rebuild body and lid.
Needed from Fusion, in millimetres: the heart sketch as DXF (1:1) and the heart as a body exported as STL (Unit: Millimeter), plus heart width/height and pocket depth.
If the Fusion script below is used: Utilities, Scripts and Add-Ins (Shift+S), new script, paste, Run. It exports every sketch as DXF and every body as STL,
and shows each body's size in mm (the bear must read 167 x 164 x 200).

```python
import adsk.core, adsk.fusion, os
def run(context):
    app = adsk.core.Application.get(); ui = app.userInterface
    design = adsk.fusion.Design.cast(app.activeProduct)
    dlg = ui.createFolderDialog(); dlg.title = 'Export folder'
    if dlg.showDialog() != adsk.core.DialogResults.DialogOK:
        return
    out = dlg.folder; root = design.rootComponent; lines = []
    for sk in root.sketches:
        sk.saveAsDXF(os.path.join(out, 'sketch_%s.dxf' % sk.name)); lines.append('sketch: ' + sk.name)
    em = design.exportManager
    for b in root.bRepBodies:
        o = em.createSTLExportOptions(b, os.path.join(out, 'body_%s.stl' % b.name))
        o.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        em.execute(o); bb = b.boundingBox
        lines.append('%s: %.1f x %.1f x %.1f mm' % (b.name, (bb.maxPoint.x-bb.minPoint.x)*10, (bb.maxPoint.y-bb.minPoint.y)*10, (bb.maxPoint.z-bb.minPoint.z)*10))
    ui.messageBox('\n'.join(lines))
```
(untested inside Fusion)

## Not verified yet
Lightning infill on the bear, light leakage around the 0.3 mm gap, pin retention, real LED module size (recess O33 x 7), support roughness on the pocket ceiling
(if the lid does not fit, raise `SIDE_CLEAR` to 0.4), and the commercial-use licence of the downloaded bear (no licence file came with it).

## Working notes
- Answer briefly, in Arabic; the user is direct and wants a commercial-grade look. Do not spend effort needlessly.
- Keep original input files unmodified. Never name a helper script `inspect.py`. Run Python on untrusted inputs with `-I`.
- Flat-shaded renders of the pebbled bear surface look rougher than the print will (about 0.3 mm texture); judge geometry by sections and numbers.
- The input files are NOT in the repo: the original bear STL and Manus' lid v2 (the user has both).
