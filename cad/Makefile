PY := ../.venv-cad/bin/python
PROFILE ?= config/printer_pla_0.2mm.ini
PART ?= test_bracket

.PHONY: all build slice preview clean
all: build slice preview

build:            ## CAD -> out/$(PART).step (Fusion 360) + out/$(PART).stl
	$(PY) build.py $(PART)

slice: build      ## STL -> G-code with PrusaSlicer
	prusa-slicer --export-gcode --load $(PROFILE) --center 110,110 -o out/$(PART).gcode out/$(PART).stl
	@grep -E '^; (filament used \[g\]|estimated printing time \(normal)' out/$(PART).gcode

preview: build    ## PNG preview of the STL
	$(PY) preview.py out/$(PART).stl

clean:
	rm -rf out/*

# ---- Mercedes tray -------------------------------------------------------
MERC_PROFILE := config/h2d_pla_0.2mm.ini
.PHONY: mercedes
mercedes:         ## build, slice (estimate), verify, render the Mercedes tray
	$(PY) build.py mercedes_tray mercedes_base mercedes_test_coupon
	for p in mercedes_tray mercedes_base mercedes_test_coupon; do \
	  prusa-slicer --export-gcode --load $(MERC_PROFILE) --center 162.5,160 -o out/$$p.gcode out/$$p.stl >/dev/null && \
	  grep -E '^; (filament used \[g\]|estimated printing time \(normal)' out/$$p.gcode; done
	$(PY) verify_mercedes.py
	cd parts && ../$(PY) -c "from _mercedes import P; from _decor import export_json; export_json(P, '../fusion/MercedesTray/decor.json')"
	$(PY) fusion/test_fusion_script.py
	$(PY) render_mercedes.py
	mkdir -p release/mercedes_tray && cp out/mercedes_tray.stl out/mercedes_base.stl \
	  out/mercedes_test_coupon.stl out/mercedes_tray.step out/mercedes_base.step \
	  out/mercedes_diagram.png out/mercedes_3d.png out/mercedes_verification.md release/mercedes_tray/

.PHONY: mercedes-animation
mercedes-animation:  ## render the open/close animation (mp4 + gif)
	xvfb-run -a $(PY) animate_mercedes.py
	mkdir -p release/mercedes_tray && cp out/mercedes_animation.mp4 out/mercedes_animation.gif release/mercedes_tray/
