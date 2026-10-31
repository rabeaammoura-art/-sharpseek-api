# Stand (ركاية) design notes — for Claude, not for the user

Living record of every stand idea for the newborn plaque, so we do not forget or re-propose rejected ideas.
Update it whenever an idea is built, tested, accepted or rejected. Code lives in `cad/newborn_plaque.py`.

## Hard facts and constraints (do not forget)

- **Printer has NOT arrived yet** (H2D). Nothing here is print-tested. Everything below is software-verified at best.
  Never ask the user to "print a test" until they say the printer is there; prepare coupons for later instead.
- The plaque is printed **front face up**: raised relief on top, **back face on the bed**. So the back can have
  **recesses/cavities** (printable) but **no protrusions** (would need supports under the whole plate).
  Printing the plaque tilted or on edge: measured 10x time (colour changes every layer) — rejected.
- Plaque thickness: base 2.4 mm, but **4.2 mm in the frame band** (base 2.4 + 1.8 raised frame). The frame band is
  12 mm wide, straight along the sides between y = -120 and +120 (corner radius 30).
- Frame band is the only place that is thick enough for a recess without adding material.
- User priorities: **print time > cost** (said many times), **no glue**, **no thicker base** (extra cost),
  does not like loose separate pieces, wants it **folding like photo-frame easels** if possible,
  wants it attached/never lost. Repo is public.
- Stand geometry used: plaque leans back 12 deg (`TILT`). CoM is at (size/2)*sin(tilt) behind the bottom edge
  (31 mm at 300). Any stand needs foot support well behind that.
- H2D: each nozzle covers 325x320 mm; a 300 mm plate + prime tower does not fit (slicer conflict) — separate issue.

## Options

| id | idea | pros | cons | status |
|---|---|---|---|---|
| `feet` (default) | two blocks with a tilted slot the bottom edge slides into | no glue, no extra thickness, simple, stable (margin 22 mm at 300) | 2 loose parts, ~70 g, 1h12 extra print at 300, user said "not suitable at all" (shape, separate, no fold, cost/time) | built; software-verified |
| `easel` | folding leg + bracket **glued** to the back (M3 bolt hinge) | folds flat like a photo frame, cheap (~13 g) | needs glue — user rejected glue | built; rejected by user |
| `clip` | C-shaped clip on one side edge of the frame + folding leg (M3 bolt) | 1 part, ~10 g, 25 min, folds flat | single leg off-centre (less tip resistance), grip by friction only (may slip), thin PETG jaws | built; shown to user, not decided |
| T-slot in plate back | dovetail recess in the back, bracket slides in | no glue | needs base ~4 mm thick (+~100 g at 300) | rejected (cost) |
| heat-set inserts in frame band | M2.5x3 brass inserts in 4.2 mm band, bracket screwed on | strong, removable, no glue | needs soldering iron + tips (Temu kit), only 3 mm inserts fit, 1.2 mm front skin may mark, labour per plaque | discussed; user said do the plaque only, stand later |
| `slots` (user idea) | two long pockets in the frame bands, each with a **print-in-place folding leg** | no glue, one piece, symmetric, ~0 extra cost/time (legs in base colour, no colour change), folds flat inside the pocket | PIP hinge pin ~2 mm between thin 1.4 mm walls (weakest point), 0.4 mm gaps may fuse, ceiling skin bridges ~9 mm over the leg, band walls thin (maybe widen frame 12 -> 14 mm), 24 deg open angle needed so the 240 mm leg fits | **not built**; numbers in the chat: pivot 240 mm up, leg 240x8x2.4, foot ~100 mm behind, margin ~69 mm |
| `rails` (user idea, newest) | two **long T/dovetail rails** recessed in the frame bands (one per side, open at the bottom end); a separate printed **bridge** spans the back from side to side with a T-tab at each end that slides into the rails; the leg is on the bridge | no glue, no thicker base (uses the existing 4.2 mm band), bridge+leg is one accessory printed in any orientation (hinge can be M3 bolt or print-in-place), **central leg = symmetric**, **height/angle adjustable** by sliding, removable, ships flat | 2 pieces (plaque + bridge), rail walls thin (cavity ~8 mm in a 12 mm band, opening ~5 mm), retention is friction only unless a detent is added, bar ~300 mm long (flexible), unknown tolerances | **BUILT** (`"stand": "rails"`, 280 mm and up): exact clearance 0.200 mm, zero interference (measured on cross-sections); bridge 14x294x3 mm standing on its edge 19 min 12 g + leg 25 min 18 g (PLA, single colour, reliable); the rails add 0 time to the plaque. Not print-tested (no printer). M3 bolt + nut for the hinge |

## Notes on `rails` (to design next)

- Rail cross-section (in the 4.2 mm band, back face on the bed): opening ~5 mm wide for z 0-1.0, cavity ~8 mm wide for
  z 1.0-2.8, ceiling skin 1.4 mm. Cavity ceiling bridges 8 mm (ok). Walls left in a 12 mm band: ~2 mm each side.
- At x = +-144 the straight band ends where the corner arc starts (y ~ -138): rails can open on the curved bottom edge.
- Bridge: bar ~ 280 x 10 x 3 mm across the back at the pivot height, T-tabs 7.6 x 1.6 on a 4.6 neck at both ends.
  Insertion: from the bottom, slide up the rails. Load path: leg force presses the bar into the plate; the upward
  component is taken by the friction/detent in the rails -> add a small detent bump or a stop at the top end of each rail.
- Leg on the bridge: centre hinge (M3 bolt, as in `easel`) or print-in-place, folds flat along the back (leg 230 mm,
  open angle 24-30 deg like `clip`). Overhang of the folded leg below the plate bottom is ~5 mm at 30 deg.
- Open questions: detent design, rail tolerance (0.3-0.4 mm?) — only the printer can answer. Keep tolerance a parameter.

## Estimation warning (important)

Multi-colour slices **without a prime tower are unreliable**: on a re-run the standard 300 mm plaque gave 21 million g
for one colour (meshes were fine). Earlier 300 mm multi-colour times/costs (4h47 etc.) must not be quoted as facts.
With the tower enabled (`--tower-x`) the 150/200 mm numbers look sane, but a 300 mm plate + tower conflicts on the H2D
bed. Single-colour parts (stands, boxes) are reliable.

## Decision log

- Feet first (no glue). User: "not suitable at all" (separate pieces, shape, not folding, cost/time).
- Folding glued easel -> rejected (glue). Thicker base for T-slot -> rejected (cost).
- Clip on the side -> shown, user asked about heat-set inserts instead (Temu kit: M2-M3 inserts + iron tips).
- User: do the plaque only, stand later; wants this notes file; then proposed `rails`.

## Next actions (when the user says go)

1. ~~Implement `stand: "rails"`~~ done (see table). Next: a detent/stop for the bridge if friction is not enough (after the first print).
2. Implement `stand: "slots"` only if `rails` fails.
3. Generate small test coupons (frame-band piece + tab) so the first print is cheap, **after the printer arrives**.
