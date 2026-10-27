"""Slice with Bambu Studio using the official H2D profiles, with the settings meant for this model:
5 wall loops (the 2.0 mm shell), 0% sparse infill (the lattice is part of the model), tree supports on."""
import sys
sys.path.insert(0, 'cad')
import bambu_slice as bs
_orig = bs.flatten
def flatten(kind, name):
    d = _orig(kind, name)
    if kind == 'process':
        d.update(wall_loops='5', sparse_infill_density='0%')
    return d
bs.flatten = flatten
sys.argv = ['bambu_slice.py', '--support', '--filament', 'Generic PLA @BBL H2D'] + sys.argv[1:]
bs.main()
