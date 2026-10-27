"""Stage 1: teddy joint features (fillet, slit fill, flange, notch) + new litho. Saves intermediates to the scratchpad."""
import sys,glob,time,pickle
sys.path.insert(0,'.')
import trimesh,numpy as np
import manifold3d as m3d
from shapely.geometry import Polygon,box as sbox
from shapely.ops import unary_union
import teddy_edit as te, relief_swap, joint
U='/root/.claude/uploads/c69ab67c-81c4-5df2-a89e-e3b545ae3b81/'
W='/tmp/claude-0/-home-user--sharpseek-api/c69ab67c-81c4-5df2-a89e-e3b545ae3b81/scratchpad/v4/'
PHOTO=U+'5330ae15-image.jpg'
T0=trimesh.load(glob.glob(U+'*teddy_rear*')[0]); L0=trimesh.load(glob.glob(U+'*front_lith*')[0])
def simplify(m,tol=0.01):
    mf=m3d.Manifold(m3d.Mesh(vert_properties=np.asarray(m.vertices,dtype=np.float32),tri_verts=np.asarray(m.faces,dtype=np.uint32)))
    mm=mf.simplify(tol).to_mesh()
    return trimesh.Trimesh(np.asarray(mm.vert_properties)[:,:3].astype(float),np.asarray(mm.tri_verts),process=True)
t=time.time()
H0,Pn=joint.pocket_polys(T0)
print('H0 bounds',np.round(H0.bounds,2),'area %.0f'%H0.area,'| P_notch bounds',np.round(Pn.bounds,2),'area %.0f'%Pn.area)
# 1) fillet around the ring
sec=L0.section(plane_origin=[0,778.3,0],plane_normal=[0,1,0]); loop=max(sec.discrete,key=lambda l:np.ptp(l[:,0])); Hout=Polygon(loop[:,[0,2]]).buffer(0)
T=te.ring_fillet(T0,Hout); T=simplify(T,0.01); print('fillet+simplify',len(T.faces),T.is_watertight,round(time.time()-t))
# 2) micro-slit fill: convex hull of the local solid in two small boxes (mirror pair)
for cx in (829.6,893.2):
    box=trimesh.creation.box(bounds=[[cx-2.6,774.0,36.0],[cx+2.6,782.2,42.6]])
    piece=te.boolean('intersection',[T,box]); hull=piece.convex_hull
    hull=te.boolean('difference',[hull,joint.prism_xz(Pn.buffer(0.1),773.0,784.0)])      # never fill the pocket itself
    T=te.boolean('union',[T,hull])
T=simplify(T,0.01); print('slits filled',len(T.faces),T.is_watertight,round(time.time()-t))
# 3) flange + notch
fl=joint.flange_solid(H0); T=te.boolean('union',[T,fl])
cyl,zc=joint.notch_cutter(Pn); T=te.boolean('difference',[T,cyl]); print('flange+notch z_c=%.1f'%zc,len(T.faces),T.is_watertight,round(time.time()-t))
T.export(W+'teddy_stage1.stl')
# 4) litho: relief swap, cut at the seat plane, new tongue + bridge + skirt + tabs
L3,tr,_=relief_swap.swap_relief(L0,PHOTO); print('relief swapped',tr)
dome=te.boolean('intersection',[L3,trimesh.creation.box(bounds=[[800,740,0],[920,joint.LIP_FRONT_Y-0.005,110]])])
print('dome cut',len(dome.faces),dome.is_watertight,np.round(dome.bounds,2).tolist())
tongue,bridge,skirt,sk_in,sk_out=joint.litho_joint_parts(H0,Pn)
parts=[dome,
       joint.prism_xz(tongue,joint.LIP_FRONT_Y-0.2,joint.BR_Y1),
       joint.prism_xz(bridge,joint.BR_Y0,joint.BR_Y1),
       joint.prism_xz(skirt,joint.BR_Y0,joint.SK_Y1)]
Lj=te.boolean('union',parts); print('litho joined',len(Lj.faces),Lj.is_watertight)
mid=Polygon(H0.buffer(-(joint.FL_LEN+joint.SK_GAP+joint.SK_T/2)).exterior)
from shapely.geometry import LineString
mid_line=LineString(mid.exterior.coords)
cuts,adds=joint.snap_tabs(mid_line,(861.43,52.0))
Lj=te.boolean('difference',[Lj]+cuts); Lj=te.boolean('union',[Lj]+adds)
print('litho with tabs',len(Lj.faces),Lj.is_watertight,'volume %.0f'%Lj.volume,np.round(Lj.bounds,1).tolist())
Lj.export(W+'litho_stage1.stl')
