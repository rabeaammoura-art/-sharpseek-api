import sys, json
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from skimage import measure
from shapely.geometry import Polygon
im=np.asarray(Image.open(sys.argv[1]).convert("RGB")).astype(float)
lum=im.mean(axis=2); mx=im.max(axis=2)
H,W=lum.shape; yy,xx=np.mgrid[0:H,0:W]
R,G,B=im[...,0],im[...,1],im[...,2]
bg=(R>135)&(R-B>45)
dark=(~bg)&(yy<728)&(xx>60)&(xx<1500)
dark=ndi.binary_opening(dark,iterations=2)
dark=ndi.binary_closing(dark,iterations=4); dark=ndi.binary_fill_holes(dark)
lab,n=ndi.label(dark); sizes=ndi.sum(dark,lab,range(1,n+1)); m=lab==(1+int(np.argmax(sizes)))
sm=ndi.gaussian_filter(m.astype(float),2.5)
c=max(measure.find_contours(sm,0.5),key=len)
p=Polygon([(x,y) for y,x in c]).buffer(0).simplify(0.8)
print(p.bounds,p.area)
json.dump({"sil":[list(q) for q in p.exterior.coords]},open(sys.argv[2],"w"))
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig=plt.figure(figsize=(15.36,10.24),dpi=100); ax=fig.add_axes([0,0,1,1]); ax.imshow(im.astype(np.uint8)); 
x,y=p.exterior.xy; ax.plot(x,y,'c',lw=2); ax.axis('off'); fig.savefig(sys.argv[3])
