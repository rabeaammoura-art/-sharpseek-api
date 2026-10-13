# Collapsible 3-compartment "Mercedes" serving tray

A round tray that lies almost flat with the handle down. Lift the handle and three
equal 120° compartments drop open as stepped, rigid bowls. Set it down and it nests flat
again. It is printed in one piece, collapsed, in PLA or PETG, with no supports and no
flexible parts. The handle is a second, separate print.

**Files:** everything is in `release/mercedes_tray/` and regenerates with `make mercedes`.

| File | What it is |
|---|---|
| `mercedes_tray.stl` | Tray: flange, dividers and 3 × 13 rings, collapsed, print-in-place (40 separate bodies) |
| `mercedes_tray_handle.stl` | Arc handle, laid flat |
| `mercedes_test_coupon.stl` | Ø120 test coupon: same walls, lips, gaps and ring height; 4 rings, no posts |
| `mercedes_tray.step`, `mercedes_tray_handle.step` | Same solids, for a quick non-parametric import |
| `mercedes_diagram.png`, `mercedes_3d.png` | Mechanism drawings, cut from the real model |
| `mercedes_verification.md` | Results of every automated check |
| `../../fusion/MercedesTray/` | Fusion 360 script that builds the parametric model |

## 1. Design summary

| | Value | Why |
|---|---|---|
| Tray diameter | **280 mm** | Fits the 300 × 320 safe single-nozzle area with 10 mm margin |
| Flange | 20 mm wide, 9 mm tall | Carries the hinge posts; stiff ring that everything hangs from |
| Divider ribs | 4 mm wide, 9 mm tall | Join the three compartments in the Mercedes Y |
| Compartment | 120° sector, R 120 mm, top opening 141 cm² | Three equal compartments |
| **Rings per compartment** | **13**, floor included, plus the fixed frame | Computed: (sector in-radius 55.7 − 5.2 − floor in-radius ≥ 12) / pitch 3.2 = 12.03 → 12 + floor |
| Wall | 1.2 mm | 3 lines of a 0.4 nozzle (0.4 mm line width) |
| Print-in-place gap | **0.40 mm**, horizontal, everywhere | 0.3 mm is reliable for short hinges. These walls run ~460 mm per ring with 39 rings side by side, so 0.4 leaves room for wobble and stringing. Elephant-foot compensation widens the first layer to ~0.67 mm. |
| Stop lip | 1.6 mm protrusion, 45° chamfer, 0.6 mm land | 1.2 mm radial engagement (lip − gap); 45° prints without support |
| Ring height | 7 mm | |
| Travel per step | 4.6 mm (= 7 − 2·0.6 − 1.6 + 0.4) | Chamfers meet face to face |
| **Collapsed height** | **19.0 mm** at the hinge posts; rings 7 mm, flange 9 mm | |
| **Extended depth** | **59.8 mm** (13 × 4.6); 68.8 mm overall | Wall slope 55°; about 0.37 L per compartment |
| Floor | inscribed circle Ø 24 mm, 1.2 mm thick | |
| Handle | Semicircle R 134, 10 × 6 mm band, Ø6 pins, 0.3 mm pin clearance | Rises 150 mm above the flange when upright |

### How it works

```
 COLLAPSED (as printed, 19 mm)          EXTENDED (handle lifted, 69 mm)
 frame r1 r2 r3 … r12 floor              frame ▄▄                     ▄▄ frame
 ███▙ ▐▌ ▐▌ ▐▌   ▐▌ ▐▌▁▁▁▁▁▁                   ▝▜▙ r1             r1 ▟▛▘
 all 13 rings side by side,                       ▝▜▙ r2       r2 ▟▛▘
 0.4 mm gap beside every wall                        ▝▜▙ …   … ▟▛▘
                                                        ▝▀▀floor▀▀▘
```

- Each ring has an **outward lip at its top** and an **inward lip at its bottom**, both
  chamfered at 45°.
- **Collapsed:** the lips sit at different heights with a 0.4 mm gap beside every wall,
  so each ring can slide vertically.
- **Lifting:** the frame rises. Each ring falls until its top lip lands on the bottom lip
  of the next larger ring. The 45° faces centre the rings and stop them.
- **Setting down:** the floors touch the table and gravity nests everything flat again.
- See `mercedes_diagram.png` for the top view, section A-A in both states, and a lip
  zoom drawn from the real model.

**Where the compartments meet (dividers and centre).** Every ring is an exact inward
offset S(d) of its own 120° sector:

> S(d) = points ≥ d from both radial edges and ≤ R − d from the centre

The three compartments never share a moving wall. Each one hangs inside its own opening in
the rigid frame, and the 4 mm divider ribs are part of that frame. Because all offsets
start from the same sector, walls stay exactly parallel. The clearance is 0.4 mm along the
straight edges and the arc, and larger at the apex and corners (0.4 / sin 60° and
0.4·√2). When the rings extend they step toward each sector's in-centre, away from the
dividers, so nothing collides at the centre either.

**Why the handle is a separate part.**
- A print-in-place handle would have to lie on the flange over a ~0.5 mm air gap. That is
  a 10 mm wide, 420 mm long unsupported bridge, which fuses or sags.
- The alternative is printing it beside the tray, but the tray already uses 280 of the
  300 mm.
- Printed flat on its own, the arch is laid along its strong direction. It snaps on by
  springing the two ends apart about 6 mm each, which is about 0.2 % strain in PLA. That
  is elastic, so it counts as assembly, not a flexible part.

**Load path.** Food → floor → lip → … → lip → frame → hinge pins → handle.
- Each ring wall carries the weight of everything below it. The lip contact is about
  460 mm long × 1.2 mm engaged.
- With 1 kg in one compartment, the stress across the wall's layer lines is about
  0.02 MPa. PLA layer adhesion is over 10 MPa.
- Static strength is not the limit. Shocks are: don't swing it or drop it.
- The tray hangs below the hinge axis, so it carries like a basket. An unevenly loaded
  tray will tilt a little about the hinge axis.

## 2. Print settings (Bambu Studio, H2D, 0.4 mm nozzle)

| Setting | Tray | Handle |
|---|---|---|
| Material | PLA (best for print-in-place) or PETG (see food note) | same |
| Orientation | As exported: collapsed, bottom on the plate | Flat, as exported |
| Supports | **Off** | Off |
| **Brim** | **No brim** (a brim would weld the ring bottoms together) | No brim |
| Layer height | 0.20 mm (0.16 mm for smoother lips) | 0.20 mm |
| Line width | 0.40 mm for all walls; wall loops 3 | default |
| **Elephant-foot compensation** | **0.15 mm** | 0.1 mm |
| Infill | 15 % gyroid (only the flange has infill) | 30 % |
| Avoid crossing walls | On (less stringing into the gaps) | |
| Bed | Textured PEI, 55 °C (PLA) / 70 °C (PETG) | |
| Estimate (PrusaSlicer, H2D-like profile) | ~7 h 50 min, 292 g | ~35 min, 18 g |

After printing:
- Hold the flange and push each floor up and down a few times to free the rings.
- If a ring's first layer is tacked to its neighbour, run a thin blade around that gap.

**Print `mercedes_test_coupon.stl` first** (~1 h 40 min, 55 g). If its rings come free
cleanly, the full tray will too. If they stick, raise `clear` to 0.45 and rebuild.

## 3. Food contact

- **Material.** Use a filament the maker sells as food-contact compliant (EU 10/2011 or
  FDA 21 CFR), uncoloured or with a food-safe pigment. Many natural PETG and some PLA
  grades qualify. Print it with a **stainless or hardened nozzle**, not brass, which can
  contain lead.
- **Bacteria.** FDM layer lines and the 0.4 mm gaps trap crumbs and bacteria. Use the
  tray for **dry snacks and wrapped sweets**, or line the compartments with paper cups.
- **Washing.** Hand wash in lukewarm water. PLA softens at about 55 °C, so no dishwasher.
- **Coatings.** Do **not** seal it with epoxy, which would glue the rings together.

## 4. Fusion 360 script

1. In Fusion, open *Utilities → Add-Ins → Scripts and Add-Ins*.
2. Click **+** next to My Scripts and pick the folder `fusion/MercedesTray`.
3. Click **Run** in a new design.

**What it builds.**
- Components **Tray** (frame plus 39 rings, collapsed) and **Handle** (folded down), as
  normal history features: sketches, extrude, loft and combine.
- Every key dimension becomes a **User Parameter** (mm).

**Which edits update live (Modify → Change Parameters):**
- Height parameters update the model directly: `ring_h`, `frame_h`, `lip_flat`, `lip`,
  `floor_t`, `handle_t`, `hinge_gap`. They drive the construction planes and extrude
  distances.
- Plan dimensions and the derived step count need a re-run: `tray_d`, `flange_w`,
  `divider_half`, `wall`, `clear`, `lip` (plan width) and N. Edit them in a design, then
  run the script in a new design with the same values. The script reads parameters that
  already exist. A Fusion timeline cannot add or remove ring bodies from a parameter, so
  N can't update live.
- Expect it to take several minutes: about 600 features are created.

## 5. Verification (from the generated files)

`make mercedes` runs everything below. The results are in `mercedes_verification.md`.

- **STL:**
  - The tray has 40 separate bodies, the handle has 1. All are watertight with
    consistent winding.
  - Both fit the H2D area: 280 × 280 × 19 mm and 278 × 142 × 6 mm.
- **Clearance (all body pairs, STL meshes, FCL):**
  - The STL minimum gap is 0.391 mm. The design value is 0.400, and faceting the
    concentric arcs costs 0.009 mm.
  - The exact B-rep gap is 0.4000 mm for every neighbour pair.
- **As sliced** (PrusaSlicer, H2D-like profile, external perimeters along the section
  line):
  - Lip layers: 0.39 to 0.41 mm.
  - First layer: 0.67 mm, because of elephant-foot compensation.
- **Motion:**
  - No collisions at 25, 50, 75 and 98 % extension.
  - At 100 % every lip pair touches with no penetration. The boolean noise is 0.2 µm.
  - Pulling 0.2 mm further collides, so the rings cannot separate.
  - The handle sweeps 0 to 180° in 5° steps with at least 0.30 mm to the frame (the pin
    clearance).
- **Fusion script = STL:**
  - `fusion/test_fusion_script.py` runs the real script against a stand-in for Fusion's
    `adsk` API.
  - All 41 bodies match the STL geometry, and the parameters are identical.
  - A deliberate 0.05 mm change in the script fails this test, so it is a real check.

**Not verified here (needs your hands):**
- Running the script in real Fusion 360. Fusion isn't available on Linux; the API calls
  follow the documented Fusion API but haven't executed in Fusion itself.
- A physical print.
- Behaviour under drops or swinging.
- PETG print-in-place at 0.4 mm. PETG strings more; test the coupon first.
