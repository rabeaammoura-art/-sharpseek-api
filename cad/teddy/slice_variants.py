import sys,os
sys.path.insert(0,'/home/user/-sharpseek-api/cad')
import bambu_slice as bs
dens=os.environ.get('DENS'); pat=os.environ.get('PAT'); walls=os.environ.get('WALLS'); proc=os.environ.get('PROC','0.20mm Standard @BBL H2D')
_o=bs.flatten
def flatten(kind,name):
    d=_o(kind,name)
    if kind=='process':
        if dens: d['sparse_infill_density']=dens
        if pat: d['sparse_infill_pattern']=pat
        if walls: d['wall_loops']=walls
    return d
bs.flatten=flatten
sys.argv=['bambu_slice.py','--support','--process',proc,'--filament','Generic PLA @BBL H2D']+sys.argv[1:]
bs.main()
