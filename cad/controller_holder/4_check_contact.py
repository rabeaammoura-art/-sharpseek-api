# usage: python 4_check_contact.py p_Knight.ply t4.ply   (run inside work/)
# Penetration (+) / gap (-) of each figure against the controller dummy, by height band (hands / chest / head).
import trimesh,numpy as np,sys
C=trimesh.load('p_Ctrl.ply').simplify_quadric_decimation(face_count=6000)
for F,n in [(a,a) for a in sys.argv[1:]]:
    M=trimesh.load(F)
    pts,_=trimesh.sample.sample_surface(M,12000,seed=2)
    pts=pts[pts[:,2]>5]
    d=trimesh.proximity.signed_distance(C,pts)
    for lo,hi,lab in ((5,32,'hands'),(32,46,'chest/neck'),(46,72,'head')):
        s=(pts[:,2]>=lo)&(pts[:,2]<hi); dd=d[s]
        print(n,lab,'penetration max mm',dd.max().round(1),'| near(<1.5mm) pts',int((np.abs(dd)<1.5).sum()),'| x of near',pts[s][np.abs(dd)<1.5][:,0].round(0).min() if (np.abs(dd)<1.5).any() else '-',pts[s][np.abs(dd)<1.5][:,0].round(0).max() if (np.abs(dd)<1.5).any() else '-')
