# Fusion check of the mechanics (2026-11-18)

`verify_kickstand.ts` = an independent B-rep model of the removable kickstand pocket, module, leg, pin and the M2 plaque fixing (200 mm box),
run in Autodesk Fusion (cloud, `MCP.ExecuteTypeScript`) with its interference and minimum-distance tools. `kickstand_check_200.step` = the model it builds
(bodies: pocket block, module, leg open 24 deg, pin, post, plaque pocket, nut, screw; the folded leg is hidden). Editable parameters are the constants K at the top.

Result (mm3): module sliding in 0 / 0.07 (the detent bump touching the lip), leg 0-24 degrees 0 against module and pocket, 26 degrees 4.22 (stop, first
contact at 24.0 degrees), pin 0 (gap to the barrel hole 0.2), M2 nut / screw / post 0 (nut to pocket 0.15, screw to post hole 0.2).
Finding that changed the design: the flange touched the lip with 0 clearance and only 0.2 mm slack behind it; the chamber ceiling is now MOD_T + 0.4 (CH_TOP in `kickstand.py`).
Fusion checks the geometry, NOT the printer: real clearances still need a printed coupon.
