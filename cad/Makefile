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
