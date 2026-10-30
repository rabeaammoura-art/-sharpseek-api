"""Write a multi-colour Bambu Studio 3MF: one object made of several parts, each assigned a filament slot.

write_bambu_3mf(path, parts, center, name, project_settings)
  parts:            [(part_name, trimesh.Trimesh, filament_slot)]  (slots are 1-based)
  center:           (x, y) plate position of the object's origin
  project_settings: bytes of a Bambu `project_settings.config` (the CLI crashes without one)
"""
import uuid
import zipfile
from xml.sax.saxutils import quoteattr

NS = ('xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
      'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
      'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p"')

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
 <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
 <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
 <Default Extension="png" ContentType="image/png"/>
 <Default Extension="gcode" ContentType="text/x.gcode"/>
</Types>"""

RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>"""

MODEL_RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Target="/3D/Objects/object_1.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>"""


def _uuid():
    return str(uuid.uuid4())


def _mesh_xml(mesh):
    v = "\n".join(f'     <vertex x="{x:.5f}" y="{y:.5f}" z="{z:.5f}"/>' for x, y, z in mesh.vertices)
    t = "\n".join(f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in mesh.faces)
    return f"   <mesh>\n    <vertices>\n{v}\n    </vertices>\n    <triangles>\n{t}\n    </triangles>\n   </mesh>"


def write_bambu_3mf(path, parts, center, name, project_settings):
    n = len(parts)
    obj_id = n + 1
    cx, cy = center
    objects = "".join(f'  <object id="{i}" p:UUID="{_uuid()}" type="model">\n{_mesh_xml(m)}\n  </object>\n'
                      for i, (_, m, _) in enumerate(parts, start=1))
    object_model = (f'<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" {NS}>\n'
                    ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n <resources>\n'
                    f'{objects} </resources>\n <build/>\n</model>')
    comps = "".join(f'    <component p:path="/3D/Objects/object_1.model" objectid="{i}" p:UUID="{_uuid()}" '
                    f'transform="1 0 0 0 1 0 0 0 1 {cx:.3f} {cy:.3f} 0"/>\n' for i in range(1, n + 1))
    model = f"""<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" {NS}>
 <metadata name="Application">BambuStudio-02.08.02.61</metadata>
 <metadata name="BambuStudio:3mfVersion">1</metadata>
 <resources>
  <object id="{obj_id}" p:UUID="{_uuid()}" type="model">
   <components>
{comps}   </components>
  </object>
 </resources>
 <build p:UUID="{_uuid()}">
  <item objectid="{obj_id}" p:UUID="{_uuid()}" transform="1 0 0 0 1 0 0 0 1 0 0 0" printable="1"/>
 </build>
</model>"""
    part_cfg = "".join(
        f'    <part id="{i}" subtype="normal_part" uuid="{_uuid()}">\n'
        f'      <metadata key="name" value={quoteattr(pn)}/>\n'
        f'      <metadata key="extruder" value="{slot}"/>\n'
        f'      <metadata key="matrix" value="1 0 0 {cx:.3f} 0 1 0 {cy:.3f} 0 0 1 0 0 0 0 1"/>\n'
        f'      <mesh_stat face_count="{len(m.faces)}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>\n'
        f'    </part>\n'
        for i, (pn, m, slot) in enumerate(parts, start=1))
    settings = f"""<?xml version="1.0" encoding="UTF-8"?>
<config>
  <object id="{obj_id}">
    <metadata key="name" value={quoteattr(name)}/>
    <metadata key="extruder" value="{parts[0][2]}"/>
{part_cfg}  </object>
  <plate>
    <metadata key="plater_id" value="1"/>
    <metadata key="plater_name" value=""/>
    <metadata key="locked" value="false"/>
    <metadata key="filament_map_mode" value="Auto For Flush"/>
    <metadata key="filament_maps" value="{' '.join('1' for _ in range(max(s for _, _, s in parts)))}"/>
    <metadata key="filament_volume_maps" value="{' '.join('0' for _ in range(max(s for _, _, s in parts)))}"/>
  </plate>
  <assemble>
  </assemble>
</config>"""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", RELS)
        z.writestr("3D/_rels/3dmodel.model.rels", MODEL_RELS)
        z.writestr("3D/3dmodel.model", model)
        z.writestr("3D/Objects/object_1.model", object_model)
        z.writestr("Metadata/model_settings.config", settings)
        z.writestr("Metadata/project_settings.config", project_settings)
