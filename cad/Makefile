PY := ../.venv-cad/bin/python
PROFILE ?= config/bambu_h2d_asa_0.2mm.ini
PART ?= test_bracket

.PHONY: all build slice preview clean
all: build slice preview

build:            ## CAD -> out/$(PART).step (Fusion 360) + .stl + .3mf (Bambu Studio)
	$(PY) build.py $(PART)

slice: build      ## STL -> G-code with PrusaSlicer
	prusa-slicer --export-gcode --load $(PROFILE) --center 162,160 -o out/$(PART).gcode out/$(PART).stl
	@grep -E '^; (filament used \[g\]|estimated printing time \(normal)' out/$(PART).gcode

preview: build    ## PNG preview of the STL
	$(PY) preview.py out/$(PART).stl

clean:
	rm -rf out/*
