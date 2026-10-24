"""Colour/relief zones, defined in mm on the 94 cm plate (x right, y DOWN), scaled to any size."""
import math, numpy as np
from PIL import Image, ImageDraw
def ell(cx,cy,rx,ry,n=72): return [(cx+rx*math.cos(2*math.pi*i/n),cy+ry*math.sin(2*math.pi*i/n)) for i in range(n)]
ZONES={                                   # name: (colour, [polygons])
 "wheels":    ("silver",[ell(556,360,78,106), ell(882,270,46,82)]),
 "headlights":("white", [[(250,216),(382,236),(390,284),(262,277)], [(20,192),(90,200),(92,248),(24,242)]]),
 "kidneys":   ("grey",  [[(116,203),(192,203),(192,277),(116,277)]]),
}
def zone_masks(shape,px_per_mm,len_cm):
    """masks (bool) for each zone on a raster with `px_per_mm` px per real mm of a plate `len_cm` long (row 0 = top)."""
    H,W=shape; s=len_cm*10/940.0*px_per_mm; out={}
    for name,(col,polys) in ZONES.items():
        im=Image.new('L',(W,H),0); d=ImageDraw.Draw(im)
        for p in polys: d.polygon([(x*s,y*s) for x,y in p],fill=255)
        out[name]=np.array(im)>0
    return out
