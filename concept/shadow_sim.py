import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
m=np.load("e30_ref/mask_700.npy").astype(float)            # 1 px = 1 mm, plate 70 cm
cases=[("A: lamp 1.5 m from plate, wall 1.0 m behind, LED 3 mm",1500,1000,3),
       ("B: lamp 0.8 m, wall 2.0 m, LED 3 mm",800,2000,3),
       ("C: lamp 0.8 m, wall 2.0 m, LED 1 mm (pinhole)",800,2000,1)]
fig,axs=plt.subplots(3,1,figsize=(13,15)); MMPX=2.0
for ax,(t,L,d,s) in zip(axs,cases):
    M=(L+d)/L; pen=s*d/L                                 # magnification, penumbra on the wall (mm)
    w=int(m.shape[1]*M/MMPX); h=int(m.shape[0]*M/MMPX)
    big=np.array(Image.fromarray((m*255).astype(np.uint8)).resize((w,h),Image.BILINEAR))/255.0
    sh=gaussian_filter(big,sigma=pen/2.355/MMPX)
    img=1-0.92*sh                                        # lit wall = 1, shadow = dark
    ax.imshow(img,cmap="gray",vmin=0,vmax=1,extent=[0,w*MMPX/10,0,h*MMPX/10])
    ax.set_title(f"{t}\nshadow {m.shape[1]*M/10:.0f} cm wide (x{M:.2f}), line width on wall {4*M:.1f} mm, blur {pen:.1f} mm  -> blur/line = {pen/(4*M):.2f}",fontsize=11)
    ax.set_xlabel("cm")
fig.tight_layout(); fig.savefig("e30_ref/shadow_sim.png",dpi=80)
