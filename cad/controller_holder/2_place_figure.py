# usage: python 2_place_figure.py <figure.stl> [scale=0.5] [cut_z=30]   (run inside work/)
# Cuts the junk under the feet, scales the figure to the holder figure's size, puts its feet on the base -> R05.ply
# and prints section tables (centre|size per height) of both figures to read the joints from.
import sys,trimesh,numpy as np
SC=float(sys.argv[2]) if len(sys.argv)>2 else 0.5; CUT=float(sys.argv[3]) if len(sys.argv)>3 else 30
K=trimesh.load('p_Knight.ply')
R=trimesh.load(sys.argv[1])
R=R.slice_plane([0,0,CUT],[0,0,1],cap=True); R.apply_translation([0,0,-CUT]); R.apply_scale(SC)
kf=K.vertices[K.vertices[:,2]<-70]; rf=R.vertices[R.vertices[:,2]<3]
R.apply_translation([kf[:,0].mean()-rf[:,0].mean(),kf[:,1].mean()-rf[:,1].mean(),-75.7-R.bounds[0][2]])
R.export('R05.ply')
def table(M,name,zs):
    print('==',name,M.bounds.round(1).tolist())
    for z in zs:
        s=M.section(plane_origin=[0,0,z],plane_normal=[0,0,1])
        if s is None: continue
        p,_=s.to_planar() if hasattr(s,'to_planar') else s.to_2D()
        out=[]
        for e in s.discrete:
            c=e.mean(0); ex=np.ptp(e,axis=0)
            if max(ex[0],ex[1])>4: out.append(f'({c[0]:.0f},{c[1]:.0f}|{ex[0]:.0f}x{ex[1]:.0f})')
        print(z,' '.join(out))
table(K,'KNIGHT',range(-70,70,10)); table(R,'RONALDO',range(-70,75,10))
