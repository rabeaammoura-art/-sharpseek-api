---
name: 3d-picture-to-cad
description: How to turn a reference picture (or the owner's design idea) into a printable CAD model without redoing it five times. Use whenever the owner gives a picture/drawing/design to reproduce or combine (workshop key holder, plaques, signs, logos) and the result must look like the picture.
---

# Picture -> CAD without wasting the owner's time

Lessons from the wrench key-holder job (the first by-eye build and the auto-traced workshop both got rejected). Follow this order.

1. **Measure first, never guess the image size.** Read the real pixel size of the file (I once assumed 2000 px, it was 2345 px and everything drifted). Work in the picture's own coordinates and convert with one scale factor.
2. **Use the right tool per kind of shape.**
   - Big silhouettes (outline of the whole object): trace from colour masks, smooth them (gaussian), draw the result over the picture and look.
   - Small details (text, gears, cans, spanners, cabinet, discs, lifts): draw them **clean and parametric** (shapely/build123d) at positions measured on a 5x zoomed crop. Do NOT auto-trace them: tracing copies the image noise (wavy edges, broken thin parts). Text = real font, never traced letters.
   - Symmetric things (car, lifts): draw one half and mirror it geometrically.
3. **Flat 2D preview BEFORE any 3D.** Draw the whole thing flat in the final colours, also overlaid on the reference (S=1 check), and show it to the owner. Only after his OK extrude to 3D. A 3D render is a poor place to judge shapes.
4. **Ask for marks, not essays.** The owner answers best by circling problems on the picture and saying what is good/bad per element. Record his good/bad list per element in the work log, and keep what he approved untouched.
5. **One change per round, look at the zoomed result.** After every fix render a close-up crop of the changed area. Never say "better" without looking.
6. **Printing limits from the start.** Min feature about 0.7 mm printed (0.6 absolute); engraved lines at least 0.6 mm; check the real size after the final scale (1 picture unit may be 0.15 mm). Colour count: use what the owner decided (here 3). Print orientation: plate on the bed, no supports, no loose pieces, no glue, no screws if a printed solution is as strong.
7. **Keep versions.** Never break an approved version: new version = new script/folder that imports the old one. Ask before starting the next big step; the owner said "do nothing without my permission".
8. **Third-party designs and pictures.** The owner may adapt parts (he has the designers' OK) but the repo is public: keep third-party meshes, profiles and traces of pictures of unknown origin OUT of git (local scratch, path passed as an argument); commit only my own code. Copy the idea/proportions, build the geometry again from clean parametric shapes.
9. **Verify numerically too.** Bounds (Z must start at 0 = wall), watertight, valid solids, interference check, final size vs bed. A bug like "hook 12 mm behind the wall" is visible only in the numbers.
10. **Report honestly in short Jordanian Arabic:** what is done, what is not (not sliced / not print-tested), what is open, then ONE clear next step.
