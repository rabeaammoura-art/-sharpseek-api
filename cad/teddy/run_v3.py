"""v3: original heart geometry and mounting kept; new photo relief, smile, paw pads, cable channel moved to the base."""
import sys,glob
sys.path.insert(0,'.')
import trimesh
import teddy_edit as te, relief_swap
U=sys.argv[1] if len(sys.argv)>1 else '/root/.claude/uploads/c69ab67c-81c4-5df2-a89e-e3b545ae3b81/'
PHOTO=sys.argv[2] if len(sys.argv)>2 else U+'5330ae15-image.jpg'
OUT=sys.argv[3] if len(sys.argv)>3 else 'out/'
T=trimesh.load(glob.glob(U+'*teddy_rear*')[0]); L=trimesh.load(glob.glob(U+'*front_lith*')[0])
b=te.seal_back_and_bottom_channel(T)
c=te.carve_details(b)
print('teddy',len(c.faces),c.is_watertight)
c.export(OUT+'teddy_rear_heart_LED_v3.stl')
n,tr,_=relief_swap.swap_relief(L,PHOTO)
print('litho',len(n.faces),n.is_watertight,tr)
n.export(OUT+'heart_front_lithophane_v3.stl')
inter=trimesh.boolean.intersection([c,n],engine='manifold')
print('interference',inter.volume if len(inter.faces) else 0)
