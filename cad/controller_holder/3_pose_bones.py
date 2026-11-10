# usage: python 3_pose_bones.py -- out.ply LEAN HEAD_Y WRIST_X WRIST_Y WRIST_Z HIPS_DY   (needs `pip install bpy`, run inside work/)
# Builds a simple skeleton in R05.ply (joint coordinates below are for the Ronaldo figure: re-measure for another figure),
# leans the spine back, keeps the head up and puts the fists on the wrist target with 2-bone IK.
# Ronaldo result: python 3_pose_bones.py -- t4.ply 33 5 16 -30 15.1 8
import bpy,math,sys
from mathutils import Vector,Matrix
A=sys.argv[sys.argv.index('--')+1:]; OUT=A[0]; LEAN=float(A[1]); HY=float(A[2]); WX=float(A[3]); WY=float(A[4]); WZ=float(A[5]); DY=float(A[6])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.ply_import(filepath='R05.ply')
ob=bpy.context.selected_objects[0]; bpy.context.view_layer.objects.active=ob
ob.location.x-=6; bpy.ops.object.transform_apply(location=True)
m=ob.modifiers.new('d','DECIMATE'); m.ratio=0.3; bpy.ops.object.modifier_apply(modifier='d')
V=Vector
spec={'hips':(V((1,4,-22)),V((1,4,-10)),None),
 'spine1':(V((1,4,-10)),V((1,4,10)),'hips'),
 'spine2':(V((1,4,10)),V((1,4,32)),'spine1'),
 'head':(V((1,2,38)),V((1,-6,69)),'spine2')}
for s,n in ((-1,'L'),(1,'R')):
    spec['upper'+n]=(V((1+s*21,4,32)),V((1+s*17,-7,2)),'spine2')
    spec['fore'+n]=(V((1+s*17,-7,2)),V((1+s*9,-37,0)),'upper'+n)
    hx,kx,ax_,fx=(-14,-26,-33,-37) if s<0 else (12,25,30,32)
    spec['thigh'+n]=(V((hx,2,-18)),V((kx,2,-40)),'hips')
    spec['shin'+n]=(V((kx,2,-40)),V((ax_,11,-62)),'thigh'+n)
    spec['foot'+n]=(V((ax_,11,-62)),V((fx,4,-74)),'shin'+n)
bpy.ops.object.armature_add(enter_editmode=True,location=(0,0,0))
arm=bpy.context.object; eb=arm.data.edit_bones; eb.remove(eb[0])
for n,(h,t,p) in spec.items():
    b=eb.new(n); b.head=h; b.tail=t
for n,(h,t,p) in spec.items():
    if p: eb[n].parent=eb[p]
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); arm.select_set(True)
bpy.context.view_layer.objects.active=arm
bpy.ops.object.parent_set(type='ARMATURE_AUTO'); print('groups',len(ob.vertex_groups))
bpy.ops.object.mode_set(mode='POSE')
pbs=arm.pose.bones
def aim(name,direction):
    pb=pbs[name]; bpy.context.view_layer.update()
    head=pb.head.copy()
    rest=(pb.bone.tail_local-pb.bone.head_local).normalized()
    q=rest.rotation_difference(Vector(direction).normalized())
    pb.matrix=Matrix.Translation(head)@q.to_matrix().to_4x4()@pb.bone.matrix_local.to_3x3().to_4x4()
    bpy.context.view_layer.update()
r=math.radians
pbs['hips'].location=pbs['hips'].bone.matrix_local.to_3x3().inverted()@Vector((0,DY,0))
aim('spine1',(0,math.sin(r(LEAN*0.45)),math.cos(r(LEAN*0.45))))
aim('spine2',(0,math.sin(r(LEAN)),math.cos(r(LEAN))))
aim('head',(0,HY,31))
for s,n in ((-1,'L'),(1,'R')):
    bpy.context.view_layer.update()
    S=pbs['upper'+n].head.copy(); l1=pbs['upper'+n].bone.length; l2=pbs['fore'+n].bone.length
    W=Vector((1+s*WX,WY,WZ)); d=W-S; D=min(d.length,l1+l2-0.5); dn=d.normalized()
    a=(l1*l1-l2*l2+D*D)/(2*D); h=math.sqrt(max(l1*l1-a*a,0))
    pole=Vector((s*0.35,0.5,-1)); pole=(pole-dn*pole.dot(dn)).normalized()
    E=S+dn*a+pole*h
    aim('upper'+n,E-S); aim('fore'+n,(S+dn*D)-E)
bpy.context.view_layer.update()
for n in ('upperL','foreL','upperR','foreR','head'): print(n,[round(c,1) for c in pbs[n].head],[round(c,1) for c in pbs[n].tail])
bpy.ops.object.mode_set(mode='OBJECT'); bpy.context.view_layer.objects.active=ob
for mod in list(ob.modifiers):
    if mod.type=='ARMATURE': bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True)
bpy.ops.wm.ply_export(filepath=OUT,export_selected_objects=True,export_normals=False,export_colors='NONE')
print('done')
