# usage: python 5_preview.py   (run inside work/, reads t4.ply) -> final_preview2.png
import trimesh,numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
R=trimesh.load('t4.ply').simplify_quadric_decimation(face_count=90000)
B=trimesh.load('p_Base.ply').simplify_quadric_decimation(face_count=6000); C=trimesh.load('p_Ctrl.ply').simplify_quadric_decimation(face_count=5000)
fig=plt.figure(figsize=(21,10))
for k,(e,a,wc) in enumerate([(8,-125,True),(8,-125,False),(8,175,False),(8,-90,False)]):
    ax=fig.add_subplot(1,4,k+1,projection='3d')
    ax.plot_trisurf(*B.vertices.T[:2],B.faces,B.vertices[:,2],color='#7a7',linewidth=0)
    ax.plot_trisurf(*R.vertices.T[:2],R.faces,R.vertices[:,2],color='#cc3838',linewidth=0,shade=True)
    if wc: ax.plot_trisurf(*C.vertices.T[:2],C.faces,C.vertices[:,2],color='#9bd',alpha=.25,linewidth=0)
    ax.view_init(e,a);ax.set_xlim(-85,85);ax.set_ylim(-60,60);ax.set_zlim(-85,85)
    try: ax.set_box_aspect((170,120,170),zoom=1.9)
    except TypeError: ax.set_box_aspect((170,120,170))
    ax.set_axis_off()
plt.subplots_adjust(0,0,1,1,0,0);plt.savefig('final_preview2.png',dpi=62); print('ok')
