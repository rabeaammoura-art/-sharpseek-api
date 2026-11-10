# Controller holder with a custom figure (PS5)

Idea (owner, 2026-11-09): take a proven controller holder (figure + base + controller dummy), replace its figure with
another figure (first one: a footballer for the owner's nephew) scaled to the same size, then move the new figure's
**bones** until it touches the controller at the same points as the original figure. The controller seat is not redesigned.

**No models in git.** The holder 3MF is someone else's design (owner asked the designer for permission to modify), the
figure is an AI-generated likeness. Everything in `work/` is git-ignored; keep the model files on your own machine.

## Steps (run inside `work/`)
1. `python ../1_extract_holder_parts.py holder.3mf` -> `p_Base.ply`, `p_Knight.ply`, `p_Ctrl.ply`
2. `python ../2_place_figure.py figure.stl 0.5 30` -> `R05.ply` + section tables (read shoulder / elbow / hip positions from them)
3. `python ../3_pose_bones.py -- t4.ply 33 5 16 -30 15.1 8` (Blender as a module: `pip install bpy`)
4. `python ../4_check_contact.py p_Knight.ply t4.ply` and compare with the original figure
5. `python ../5_preview.py`
6. `python ../6_assemble.py` -> `holder_final.stl` (figure + base - controller dummy), then `cad/print_test.py` on it

## What was learned
- The original figure faces the controller: it sits on the two **palms** (about 1.7 mm into the dummy, x -18..21) and
  leans on the **helmet** (1.1 mm gap); the chest is 7 mm away. The head is hidden from the front by design.
- Result for the first figure (height 143 mm): fists 1.5 mm in, x -20..20, head gap 0.9 mm, chest 9 mm away.
- A hand-made vertex blend to move the arms tore the mesh; Blender automatic weights (`ARMATURE_AUTO`) on a mesh
  decimated to ~130k faces gave a clean, watertight result.
- For another figure: generate it standing, one piece, feet apart, forearms forward; only the joint coordinates in
  step 3 and the six pose numbers change.

## Left
Slice with supports for time. Needs supports like the original holder (islands at the shorts hem, elbows, chin). Not print-tested.
