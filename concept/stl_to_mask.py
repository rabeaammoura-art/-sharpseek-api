import numpy as np, sys
from PIL import Image, ImageDraw
p="/root/.claude/uploads/287d4316-4efc-5ff3-9835-c577044b3bfe/a4c32356-bmwe30.stl"
b=open(p,'rb').read(); n=int(np.frombuffer(b[80:84],'<u4')[0])
a=np.frombuffer(b[84:84+50*n],dtype=np.dtype([('n','<f4',3),('v','<f4',(3,3)),('a','<u2')]))
t=a['v'].astype(float); mn=t.reshape(-1,3).min(0); mx=t.reshape(-1,3).max(0)
LEN=float(sys.argv[1]) if len(sys.argv)>1 else 940.0       # final length, mm
sc=LEN/(mx[0]-mn[0]); W=int(round(LEN))+1; H=int(round((mx[1]-mn[1])*sc))+1
top=t[(t[:,:,2]>mx[2]-0.01).all(1)]                          # triangles lying on the top face
im=Image.new('L',(W,H),0); d=ImageDraw.Draw(im)
for tri in top: d.polygon([((x-mn[0])*sc,(mx[1]-y)*sc) for x,y,_ in tri],fill=255)
im.save("e30_ref/mask_%d.png"%LEN); np.save("e30_ref/mask_%d.npy"%LEN,np.array(im)>0)
print("scale xy x%.3f ; final %.0f x %.0f mm ; top tris %d of %d ; material area %.0f cm2 (%.0f%% of bbox)"%(sc,LEN,(mx[1]-mn[1])*sc,len(top),n,(np.array(im)>0).sum()/100,100*(np.array(im)>0).mean()))
