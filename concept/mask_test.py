import numpy as np
src=open('pieces_e30.py').read().split("m=np.array(im)>0")[0].replace("from build123d import BuildSketch, BuildPart, Polygon, extrude, export_stl, Plane","")
exec(src)
from scipy import ndimage as ndi
m0=np.array(im)>0
def disk(r): y,x=np.ogrid[-r:r+1,-r:r+1]; return x*x+y*y<=r*r
for r in (20,35,50):
    mm=ndi.binary_closing(np.pad(m0,60),structure=disk(r))[60:-60,60:-60]
    mm=ndi.binary_fill_holes(mm)
    print(r,"area m2: %.3f"%(mm.sum()/1e6))
    Image.fromarray((~mm*255).astype('uint8')).save(f"mask_r{r}.png")
