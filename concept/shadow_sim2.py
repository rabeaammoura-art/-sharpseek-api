import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.ndimage import gaussian_filter
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
m0=np.load("e30_ref/mask_1280.npy")                       # 32 cm plate, 0.25 mm / px
bold=ndi.binary_dilation(m0,iterations=3)                  # +1.5 mm line width
bold=ndi.binary_closing(bold,iterations=4)                 # fill tiny gaps (wheel mesh etc.)
M=6.25; s=1.0; pen=s*(M-1)                                 # 1 mm source, wall 2 m behind, lamp 38 cm in front
fig,axs=plt.subplots(2,1,figsize=(13,13))
for ax,(t,m) in zip(axs,(("original lines (about 2 mm on the 32 cm plate)",m0),("bold version (+1.5 mm per line, mesh filled)",bold))):
    w=int(320*M/2); h=int(m.shape[0]*0.25*M/2)
    big=np.array(Image.fromarray((m*255).astype(np.uint8)).resize((w,h),Image.BILINEAR))/255.0
    sh=gaussian_filter(big,sigma=pen/2.355/2); ax.imshow(1-0.92*sh,cmap="gray",vmin=0,vmax=1,extent=[0,2*w/10,0,2*h/10])
    ax.set_title(f"32 cm plate, lamp 38 cm away, wall 2 m behind, source 1 mm: shadow 200 cm wide, blur {pen:.1f} mm\n{t}",fontsize=11); ax.set_xlabel("cm")
fig.tight_layout(); fig.savefig("e30_ref/shadow_sim2.png",dpi=75)
