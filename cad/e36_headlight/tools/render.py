"""Blender (bpy) renderer. usage: python render.py scene.json
scene: {"out":..., "res":[w,h], "samples":N, "objects":[{"path":..., "mat":"asacf|black|alu|lens|chrome|emit_red|emit_white|yellow|plastic", "color":[r,g,b], "strength":x}],
        "camera":{"loc":[x,y,z],"target":[x,y,z],"ortho":scale|null,"lens":mm}, "world":0.3, "dark":bool}"""
import bpy, json, sys, math, mathutils
sc=json.load(open(sys.argv[-1]))
bpy.ops.wm.read_factory_settings(use_empty=True)
S=bpy.context.scene; S.render.engine='CYCLES'; S.cycles.device='CPU'; S.cycles.samples=sc.get("samples",64)
S.cycles.use_denoising=True
try: S.cycles.denoiser='OPENIMAGEDENOISE'
except Exception: pass
S.render.resolution_x,S.render.resolution_y=sc.get("res",[1600,1000]); S.render.film_transparent=False
S.view_settings.view_transform='AgX' if 'AgX' in [i.identifier for i in S.view_settings.bl_rna.properties['view_transform'].enum_items] else 'Filmic'
S.unit_settings.scale_length=0.001
def mat(kind,color=None,strength=1.0):
    m=bpy.data.materials.new(kind); m.use_nodes=True; nt=m.node_tree; b=nt.nodes["Principled BSDF"]
    I=lambda k,v: b.inputs[k].__setattr__('default_value',v)
    if kind=="asacf":
        I("Base Color",(0.028,0.028,0.03,1)); I("Roughness",0.62)
        n=nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value=900; r=nt.nodes.new("ShaderNodeMapRange")
        r.inputs[3].default_value=0.5; r.inputs[4].default_value=0.75; nt.links.new(n.outputs[0],r.inputs[0]); nt.links.new(r.outputs[0],b.inputs["Roughness"])
    elif kind=="black": I("Base Color",(0.01,0.01,0.01,1)); I("Roughness",0.45)
    elif kind=="plastic": I("Base Color",(*(color or (0.05,0.05,0.05)),1)); I("Roughness",0.4)
    elif kind=="alu": I("Base Color",(0.6,0.6,0.62,1)); I("Metallic",1); I("Roughness",0.35)
    elif kind=="chrome": I("Base Color",(0.9,0.9,0.92,1)); I("Metallic",1); I("Roughness",0.08)
    elif kind=="lens":
        I("Base Color",(1,1,1,1)); I("Roughness",0.0); I("IOR",1.5)
        I("Transmission Weight",1.0)
    elif kind.startswith("emit"):
        c=color or ((1,0.02,0.01) if kind=="emit_red" else (0.85,0.9,1.0))
        I("Base Color",(*c,1)); I("Emission Color",(*c,1)); I("Emission Strength",strength)
    elif kind=="yellow": I("Base Color",(0.8,0.5,0.05,1)); I("Roughness",0.5)
    elif kind=="glass_amber": I("Base Color",(1,0.55,0.1,1)); I("Transmission Weight",0.9); I("Roughness",0.05)
    elif kind=="paint": I("Base Color",(*(color or (0.02,0.05,0.2)),1)); I("Metallic",0.6); I("Roughness",0.25); I("Coat Weight",1.0)
    return m
lo=mathutils.Vector((1e9,)*3); hi=-lo
for o in sc["objects"]:
    bpy.ops.wm.stl_import(filepath=o["path"]); ob=bpy.context.selected_objects[0]
    ob.data.materials.clear(); ob.data.materials.append(mat(o.get("mat","asacf"),o.get("color"),o.get("strength",1.0)))
    if o.get("smooth",True):
        for p in ob.data.polygons: p.use_smooth=True
        try:
            mod=ob.modifiers.new("ws","WEIGHTED_NORMAL") if False else None
            bpy.ops.object.shade_auto_smooth(angle=math.radians(o.get("smooth_angle",35)))
        except Exception as e: print("autosmooth",e)
    for v in ob.bound_box:
        w=ob.matrix_world@mathutils.Vector(v); lo=mathutils.Vector(map(min,lo,w)); hi=mathutils.Vector(map(max,hi,w))
# world
W=bpy.data.worlds.new("w"); S.world=W; W.use_nodes=True; bg=W.node_tree.nodes["Background"]
bg.inputs[0].default_value=(*sc.get("bg",(0.5,0.52,0.55)),1); bg.inputs[1].default_value=sc.get("world",0.35)
# lights (studio)
c=(lo+hi)/2; span=(hi-lo).length
def area(loc,energy,size,color=(1,1,1)):
    L=bpy.data.lights.new("a","AREA"); L.energy=energy; L.size=size; L.color=color; ob=bpy.data.objects.new("a",L); S.collection.objects.link(ob)
    ob.location=loc; d=c-mathutils.Vector(loc); ob.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
k=sc.get("light",1.0)
for loc,e in [((c.x-0.8*span,c.y-1.2*span,c.z+1.0*span),3.0e6),((c.x+1.2*span,c.y-0.6*span,c.z+0.4*span),1.5e6),((c.x,c.y+1.0*span,c.z+1.5*span),1.5e6)]:
    area(loc,e*k,span*0.8)
# floor
if sc.get("floor",True):
    bpy.ops.mesh.primitive_plane_add(size=span*20,location=(c.x,c.y,lo.z-sc.get("floor_gap",0.5)))
    fl=bpy.context.object; fl.data.materials.append(mat("plastic",(0.18,0.18,0.19)))
cam=bpy.data.cameras.new("c"); co=bpy.data.objects.new("c",cam); S.collection.objects.link(co); S.camera=co
C=sc["camera"]; tgt=mathutils.Vector(C.get("target",tuple(c))); co.location=C["loc"]
co.rotation_euler=(tgt-mathutils.Vector(C["loc"])).to_track_quat('-Z','Y').to_euler()
cam.clip_end=1e6; cam.clip_start=1
if C.get("ortho"): cam.type='ORTHO'; cam.ortho_scale=C["ortho"]
else: cam.lens=C.get("lens",50)
S.render.filepath=sc["out"]; bpy.ops.render.render(write_still=True); print("wrote",sc["out"])
