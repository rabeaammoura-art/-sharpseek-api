# Collapsible 3-compartment "Mercedes" serving tray

This works like the classic carved-wood folding fruit basket, made rigid and printable.

- **Closed:** the tray lies 10 mm flat on its base.
- **Opening:** flip the handle up. Its two legs swing down onto the base and lift the
  frame, and three equal 120° compartments drop open as stepped bowls.
- **Locked open:** just past upright the handle drops into the base pockets and stays
  there. The floors rest on the base, so the food sits on the table.
- **Closing:** flip the handle back and everything nests flat again.

The tray, rings and handle are **one print, assembled as printed** (PLA or PETG, no
supports, no flexible parts). The base is a second print.

**Files:** everything is in `release/mercedes_tray/` and regenerates with `make mercedes`
(and `make mercedes-animation`).

| File | What it is |
|---|---|
| `mercedes_tray.stl` | Frame, 3 × 13 rings and handle with hinge pins, collapsed (41 separate bodies, one print) |
| `mercedes_base.stl` | Base plate with the two foot pockets |
| `mercedes_test_coupon.stl` | Ø141 test coupon: same rings, lips, gaps, hinge pin and handle ring; 4 rings |
| `mercedes_tray.step`, `mercedes_base.step` | Same solids, for a quick non-parametric import |
| `mercedes_diagram.png`, `mercedes_3d.png` | Drawings cut from the real model, including the lever action in side view |
| `mercedes_animation.mp4` / `.gif` | Opening and closing, rendered from the real model with the real kinematics |
| `mercedes_verification.md` | Results of every automated check |
| `../../fusion/MercedesTray/` | Fusion 360 script that builds the parametric model |

## 1. Design summary

| | Value | Why |
|---|---|---|
| Overall diameter | **Ø285 mm** tray, Ø290 base | Fits the 300 × 320 safe single-nozzle area |
| Frame | Flange Ø264, 12 mm wide; dividers 4 mm; 10 mm tall | Rigid Mercedes Y that every ring hangs from |
| Compartment | 120° sector, R 120 mm, top opening 141 cm² | Three equal compartments |
| **Rings per compartment** | **13**, floor included, plus the fixed frame | Computed: (sector in-radius 55.7 − 5.2 − floor in-radius ≥ 12) / pitch 3.2 = 12.03 → 12 + floor |
| Wall | 1.2 mm | 3 lines of a 0.4 nozzle |
| Print-in-place gap | **0.40 mm** between rings and at the hinge pin; 0.5 mm between the handle ring and the flange | 0.3 mm is fine for short hinges. Here 39 rings each run ~460 mm side by side, so 0.4 leaves room for wobble and stringing. Elephant-foot compensation opens the first layer to ~0.67 mm. |
| Stop lip | 1.6 mm, 45° chamfer, 0.6 mm land | 1.2 mm radial engagement; 45° prints without support |
| Ring height / travel | 7 mm / **4.6 mm per step** | Chamfers meet face to face |
| **Collapsed height** | **10 mm** (+ 6 mm base) | |
| **Open depth** | **59.8 mm** (13 × 4.6); frame top 69.8 mm above the base | Wall slope 55°, about 0.37 L per compartment |
| Handle | Outer ring 10 × 10 mm, spans 180° + 2 × 28.93° legs; arch top 207 mm above the base | |
| Leg angle | **28.93°** past each hinge | Solved so the frame lifts exactly 13 × 4.6 mm at the stop (59.75 mm): every ring is fully open and the floors rest on the base |
| Hinge | Ø4 pin, round on top with a 45° V underneath, in a Ø4.8 teardrop hole | Prints in place without support and turns freely |
| Base pockets | 4 mm deep; 45° entry ramps; vertical stop wall | Sized from the foot's real path between 80° and 100° |

### How it works

```
 CLOSED (10 mm)                            OPEN (handle at 100°, locked)
                                                         ║ handle
 handle ring  frame  r1 r2 … floor                       ║
 ▓▓▓  ███▙ ▐▌ ▐▌ ▐▌ ▐▌▁▁▁▁▁▁        frame ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
 ════════════ base ═══════════              ▝▜▙ r1          r1 ▟▛▘  ║ leg
                                               ▝▜▙ …     … ▟▛▘      ║
                                                  ▝▀floor▀▘         ║
                                          ══════════ base ══════════╚═ pocket
```

1. **Lever.** The handle is the outer ring, pinned to the flange at two opposite points.
   Each end continues 28.93° past its pin as a leg. Flipping the handle up swings both
   legs down onto the base. They act as levers and lift the frame. The side view in
   `mercedes_diagram.png` shows 0°, 50° and 100°.
2. **Rings.** As the frame rises, each ring hangs from the next larger one: its top lip
   lands on the bigger ring's bottom lip, and the 45° faces centre it. The floors stay on
   the base.
3. **Lock.** The lift peaks at about 60.8 mm (around 70–76°), then falls slightly while the feet drop into
   the base pockets. At **100°** the feet hit the vertical pocket wall.
   - From that point the tray's own weight presses the handle against the stop.
   - To close it, you have to push the handle back and raise the loaded frame about 1 mm.
   - The weight alone can't do that, so it stays open on the table.
4. **Closing.** Flip the handle back: the legs rise and everything nests flat.
5. **Carrying.** You can also carry it by the handle: the frame hangs from the hinge pins
   and the rings stay open by gravity.

**Where the compartments meet (dividers and centre).** Every ring is an exact inward
offset of its own 120° sector, so the three compartments never share a moving wall. The
4 mm dividers belong to the rigid frame.
- Walls stay parallel, with a 0.4 mm gap along the edges and arcs and more at the corners.
- When the rings extend they step toward each sector's in-centre, away from the dividers.

**Load path.** Food → floor → **base** (directly, because the floors rest on it). The
rings, lips and frame only carry their own weight plus the food resting on the ring steps.
Frame → hinge pins (Ø4) → legs → base. The stress at each pin is far below PLA's strength.

## 2. Print settings (Bambu Studio, H2D, 0.4 mm nozzle)

| Setting | Tray (one print) | Base |
|---|---|---|
| Material | PLA (most reliable for print-in-place) or PETG (see food note) | same or any |
| Orientation | As exported: collapsed, flat | Flat |
| Supports | **Off** | Off |
| **Brim** | **No brim** (it would weld the bottoms of the rings and the handle together) | Optional |
| Layer height | 0.20 mm | 0.20–0.28 mm |
| Line width / walls | 0.40 mm, 3 wall loops | 2 wall loops |
| **Elephant-foot compensation** | **0.15 mm** | default |
| Infill | 15 % (only the flange and handle have infill) | 8 %, 3 bottom / 4 top layers |
| Avoid crossing walls | On | |
| Estimate (PrusaSlicer, H2D-like profile) | ~8 h 35 min, 318 g | ~3 h 35 min, 156 g |

After printing the tray:
- Hold the flange and work each floor up and down, then swing the handle a few times.
- If a first layer is tacked, run a thin blade around that gap.

**Print `mercedes_test_coupon.stl` first** (~2 h 30 min, 80 g).
- It has the same rings, the same hinge pin and hole, and the same handle-ring gap. The
  ring gap is 0.6 there because of its tighter radius.
- If its rings and handle come free cleanly, the full tray will too.
- If they stick, raise `clear` (and `pin_clear`) to 0.45 and rebuild.

## 3. Food contact

- **Material.** Use a filament the maker sells as food-contact compliant (EU 10/2011 or
  FDA 21 CFR), printed with a **stainless or hardened nozzle**, not brass.
- **Bacteria.** Layer lines and the 0.4 mm gaps trap crumbs and bacteria. Use it for
  **dry snacks and wrapped sweets**, or line the compartments with paper cups.
- **Washing.** Hand wash in lukewarm water. PLA softens at about 55 °C, so no dishwasher.
- **Coatings.** Do **not** coat it with epoxy, which would glue the rings and hinge solid.

## 4. Fusion 360 script

1. In Fusion, open *Utilities → Add-Ins → Scripts and Add-Ins*.
2. Click **+** next to My Scripts and pick the folder `fusion/MercedesTray`.
3. Click **Run** in a new design.

**What it builds.**
- Component **Tray (one print, in place)**: frame, handle and 39 rings, collapsed.
- Component **Base**.
- Both are normal history features: sketches, extrude, loft and combine. Every key
  dimension becomes a **User Parameter**.

**Which edits update live (Modify → Change Parameters):**
- Height parameters update the model directly: `ring_h`, `frame_h`, `lip_flat`, `lip`,
  `floor_t`, `base_t`, `pocket_d`.
- Plan dimensions, the handle and pocket values, and the ring count N need a re-run in a
  new design. The script reads parameters that already exist. A Fusion timeline cannot
  add or remove ring bodies from a parameter, so N can't update live.
- If you change the leg angle or the ring dimensions, re-solve the pocket with
  `solve_pocket()` in `parts/_mercedes.py`. `verify_mercedes.py` checks that they match.

## 5. Verification (from the generated files)

`make mercedes` runs everything below. The results are in `mercedes_verification.md`
(every check passes).

- **STL:**
  - The tray has 41 separate bodies and the base has 1. All are watertight with
    consistent winding.
  - Both fit the H2D area: 285 × 285 × 10 mm and 290 × 290 × 6 mm.
- **Print-in-place clearance (all body pairs, STL meshes):**
  - STL minimum 0.391 mm. The design value is 0.400, and faceting the arcs costs 0.009.
  - The exact B-rep gap is 0.4000 mm for every ring pair and for the handle pin in its
    hole.
  - After slicing, external perimeters are 0.39–0.41 mm apart at the lips and 0.67 mm on
    the first layer.
- **Rings:**
  - No collisions at 25, 50, 75 and 98 % extension.
  - At 100 % every lip pair touches with no penetration.
  - Pulling 0.2 mm further collides, so the rings cannot separate.
- **Hinge:** the handle sweeps 0→100° relative to the frame with at least 0.40 mm
  clearance throughout.
- **Opening on the base:**
  - At poses 0, 20, 45, 70, 76, 78, 80, 85, 90, 95 and 100°, the frame lift comes from
    the actual leg geometry resting on the base surface.
  - The legs never touch a ring (≥ 9.4 mm).
  - Nothing sinks into the base.
  - At the stop the rings are fully open (last lip gap 0.05 mm) and the floors sit on the
    base.
- **Lock:**
  - The lift peaks before the stop.
  - Turning 2° past the stop drives the leg into the pocket wall.
  - The pocket in the model equals the foot's swept footprint.
- **Fusion script = STL:**
  - `fusion/test_fusion_script.py` runs the real script against a stand-in for Fusion's
    `adsk` API.
  - All 42 bodies match the geometry used for the STLs, and the parameters are identical.
  - Deliberately changing the pin by 2 % or the pocket by 0.1 mm fails the test, so it is
    a real check.

**Not verified here (needs your hands):**
- Running the script in real Fusion 360. Fusion isn't available on Linux.
- A physical print, especially the horizontal in-place hinge pin, which the coupon tests.
- Friction and the real feel of the lock.
- Drops.
- PETG at 0.4 mm gaps.
