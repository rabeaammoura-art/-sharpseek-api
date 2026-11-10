# usage: python 6_assemble.py [figure.ply=t4.ply] [out=holder_final.stl]   (run inside work/)
# Final part = (figure + base) - controller dummy, dropped to z=0. Base is raised 1.5 mm so the feet sink into it.
import sys,trimesh,numpy as np
F=sys.argv[1] if len(sys.argv)>1 else 't4.ply'; OUT=sys.argv[2] if len(sys.argv)>2 else 'holder_final.stl'
R=trimesh.load(F); B=trimesh.load('p_Base.ply'); C=trimesh.load('p_Ctrl.ply')
B.apply_translation([0,0,1.5])
U=R.union(B,engine='manifold'); print('union pieces',len(U.split(only_watertight=False)),'vol cm3',round(U.volume/1000,1))
M=U.difference(C,engine='manifold')
parts=M.split(only_watertight=False); print('after seat cut: pieces',len(parts),[round(p.volume,1) for p in parts][:6],'removed cm3',round((U.volume-M.volume)/1000,2))
M=max(parts,key=lambda p:p.volume)
dz=-M.bounds[0][2]; M.apply_translation([0,0,dz]); C.apply_translation([0,0,dz])
print('final watertight',M.is_watertight,'ext',M.extents.round(1),'vol cm3',round(M.volume/1000,1),'faces',len(M.faces))
M.export(OUT); C.export('controller_dummy_z0.ply')
# balance: controller centre of mass vs the seat (fists) in y
print('controller COM',C.center_mass.round(1),'| part COM',M.center_mass.round(1),'| base y',M.bounds[0][1].round(0),M.bounds[1][1].round(0))
