import numpy as np, matplotlib.colors as mc
from PIL import Image
from scipy import ndimage as ndi
im=Image.open('ref.png').convert('RGB'); a=np.array(im).astype(float)/255
hsv=mc.rgb_to_hsv(a); H,S,V=hsv[...,0]*360,hsv[...,1],hsv[...,2]
pinkh=(H>318)&(H<350)
lab=np.zeros(H.shape,int)            # 0 bg, 1 white, 2 light pink, 3 dark pink, 4 yellow
lab[(S<0.12)&(V>0.9)]=1
lab[pinkh&(S>=0.32)&(S<0.64)&(V>0.85)]=2
lab[pinkh&((S>=0.64)|(V<0.85))&(S>0.5)]=3
lab[(H>38)&(H<62)&(S>0.8)&(V>0.85)]=4
# plaque silhouette: pink frame ring -> fill
pink=(lab==2)|(lab==3)
pk=ndi.binary_closing(pink,iterations=3)
fill=ndi.binary_fill_holes(pk)
comp,n=ndi.label(fill); sizes=ndi.sum(fill,comp,range(1,n+1)); sil=comp==(1+int(np.argmax(sizes)))
ys,xs=np.nonzero(sil); print('sil bbox',xs.min(),xs.max(),ys.min(),ys.max())
lab2=np.where(sil,lab,0); lab2[sil&(lab2==0)]=1       # inside the plaque everything unknown is white base
np.save('lab.npy',lab2); np.save('sil.npy',sil)
cols=np.array([[230,230,230],[255,255,255],[250,120,180],[190,20,90],[250,210,0]],np.uint8)
Image.fromarray(cols[lab2]).save('lab.png')
