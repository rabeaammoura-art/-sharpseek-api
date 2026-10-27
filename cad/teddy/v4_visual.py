import sys; sys.path.insert(0,'.')
import trimesh,numpy as np,view3d
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
S='/tmp/claude-0/-home-user--sharpseek-api/c69ab67c-81c4-5df2-a89e-e3b545ae3b81/scratchpad/v4/'
T=trimesh.load('out/teddy_rear_heart_LED_v4.stl'); L=trimesh.load('out/heart_front_lithophane_v4.stl')
tc=(0.85,0.62,0.4); lc=(0.97,0.95,0.92)
view3d.view([T,L],[tc,lc],S+'f.png' if False else 'v4_front.png',0,8,center=(861.4,838.8,100),size=(190,220))
view3d.view([T,L],[tc,lc],'v4_3q.png',-35,15,center=(861.4,838.8,100),size=(210,220))
view3d.view([T],[tc],'v4_bottom.png',0,-80,center=(861.4,847,10),size=(150,150),res=0.3)
view3d.view([L],[lc],'v4_litho_back.png',180,-25,center=(861.4,770,56),size=(100,90),res=0.2)
import shutil
for n in ['v4_front.png','v4_3q.png','v4_bottom.png','v4_litho_back.png']: shutil.copy('/tmp/claude-0/-home-user--sharpseek-api/c69ab67c-81c4-5df2-a89e-e3b545ae3b81/scratchpad/'+n,S+n)
fig,ax=plt.subplots(1,3,figsize=(30,11))
def sec(a,m,o,n,i,j,c,lw=.7):
    s=m.section(plane_origin=o,plane_normal=n)
    if s is None: return
    for e in s.discrete: a.plot(e[:,i],e[:,j],c,lw=lw)
sec(ax[0],T,[861.43,0,0],[1,0,0],1,2,'k'); sec(ax[0],L,[861.43,0,0],[1,0,0],1,2,'tab:red',1.2)
ax[0].set_aspect('equal');ax[0].set_title('x=861.4 (front on the left): hollow body, pillars + diamond beams, litho (red)')
sec(ax[1],T,[0,0,56],[0,0,1],0,1,'k'); sec(ax[1],L,[0,0,56],[0,0,1],0,1,'tab:red',1.2)
ax[1].set_aspect('equal');ax[1].set_title('z=56 (x right, y down): walls, pillars, flange + litho C-lip');ax[1].invert_yaxis()
sec(ax[2],T,[0,0,52],[0,0,1],0,1,'k'); sec(ax[2],L,[0,0,52],[0,0,1],0,1,'tab:red',1.2)
ax[2].set_xlim(812,850);ax[2].set_ylim(792,758);ax[2].set_aspect('equal');ax[2].grid(alpha=.3);ax[2].set_title('z=52 left flank: snap tab (barb behind the flange)')
plt.tight_layout();plt.savefig(S+'v4_sections.png',dpi=45)
