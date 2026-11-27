"""Write a multi-colour Bambu Studio 3MF: one object made of several parts, each assigned a filament slot.

write_bambu_3mf(path, parts, center, name, project_settings)
  parts:            [(part_name, trimesh.Trimesh, filament_slot)]  (slots are 1-based)
  center:           (x, y) plate position of the object's origin
  project_settings: bytes of a Bambu `project_settings.config` (the CLI crashes without one)
"""
import json
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


def build_project_settings(template_bytes, colours, tower=None, nozzle=1):
    """Project settings for the 3MF: a 4-filament template (so Bambu Studio opens it with all colours), the slot colours,
    one nozzle for every colour, no skirt/brim (they leave the bed beside a big plate) and, if given, the prime tower
    tower = (x, y, width) in mm."""
    cfg = json.loads(template_bytes)
    cfg["filament_colour"] = [c.upper() for c in colours]
    cfg["filament_map_mode"] = "Manual"
    cfg["filament_map"] = [str(nozzle)] * len(colours)
    n = len(colours)
    fm = cfg.get("flush_volumes_matrix")
    if fm and len(fm) == n * n:       # H2D has two nozzles: Bambu Studio wants one flush matrix per nozzle (else "partial purging volume set to 0")
        cfg["flush_volumes_matrix"] = list(fm) * 2
    cfg["skirt_loops"], cfg["brim_type"] = "0", "no_brim"
    cfg["enable_prime_tower"] = "1" if tower else "0"
    if tower:
        cfg["wipe_tower_x"], cfg["wipe_tower_y"], cfg["prime_tower_width"] = [str(tower[0])], [str(tower[1])], str(tower[2])
        cfg["prime_tower_brim_width"] = "0"
    return json.dumps(cfg, indent=4)


def write_bambu_3mf(path, parts, center, name, project_settings):
    n_slots = max(max(s for _, _, s in parts), len(json.loads(project_settings).get("filament_colour", [])))
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
    <metadata key="filament_map_mode" value="Manual"/>
    <metadata key="filament_maps" value="{' '.join('1' for _ in range(n_slots))}"/>
    <metadata key="filament_volume_maps" value="{' '.join('0' for _ in range(n_slots))}"/>
  </plate>
  <assemble>
  </assemble>
</config>"""
    # all colours on the first (left) nozzle: the right nozzle cannot reach the first 25 mm of the bed, so a 300 mm plate
    # would be "unprintable" for it
    cfg = json.loads(project_settings)
    n_fil = max(max(s for _, _, s in parts), len(cfg.get("filament_colour", [])))      # every slot of the project, not just the ones used
    cfg["filament_map_mode"] = "Manual"
    cfg["filament_map"] = ["1"] * n_fil
    fm = cfg.get("flush_volumes_matrix")
    if fm and len(fm) == n_fil * n_fil:      # H2D: one flush matrix per nozzle, else Bambu Studio says "Purge volumes matrix do not match to the correct size!"
        cfg["flush_volumes_matrix"] = list(fm) * 2
    project_settings = json.dumps(cfg, indent=4)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", RELS)
        z.writestr("3D/_rels/3dmodel.model.rels", MODEL_RELS)
        z.writestr("3D/3dmodel.model", model)
        z.writestr("3D/Objects/object_1.model", object_model)
        z.writestr("Metadata/model_settings.config", settings)
        z.writestr("Metadata/project_settings.config", project_settings)


def write_bambu_3mf_multi(path, objects, project_settings):
    """Several separate objects on one plate (each can be deleted / moved on its own in Bambu Studio).
    objects: [(object_name, [(part_name, trimesh.Trimesh, filament_slot)], (x, y))]"""
    files, assemblies, items, cfg_objs, rels = {}, [], [], [], []
    nid = 1
    for k, (oname, parts, (cx, cy)) in enumerate(objects, start=1):
        fname = f"/3D/Objects/object_{k}.model"
        rels.append(f' <Relationship Target="{fname}" Id="rel-{k}" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>')
        ids = list(range(nid, nid + len(parts))); nid += len(parts)
        objs = "".join(f'  <object id="{i}" p:UUID="{_uuid()}" type="model">\n{_mesh_xml(m)}\n  </object>\n'
                       for i, (_, m, _) in zip(ids, parts))
        files[fname[1:]] = (f'<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" {NS}>\n'
                            ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n <resources>\n'
                            f'{objs} </resources>\n <build/>\n</model>')
        assemblies.append((oname, parts, ids, fname, cx, cy))
    aid = nid
    res, part_cfg_all = [], []
    for oname, parts, ids, fname, cx, cy in assemblies:
        comps = "".join(f'    <component p:path="{fname}" objectid="{i}" p:UUID="{_uuid()}" '
                        f'transform="1 0 0 0 1 0 0 0 1 {cx:.3f} {cy:.3f} 0"/>\n' for i in ids)
        res.append(f'  <object id="{aid}" p:UUID="{_uuid()}" type="model">\n   <components>\n{comps}   </components>\n  </object>\n')
        items.append(f'  <item objectid="{aid}" p:UUID="{_uuid()}" transform="1 0 0 0 1 0 0 0 1 0 0 0" printable="1"/>\n')
        pc = "".join(
            f'    <part id="{i}" subtype="normal_part" uuid="{_uuid()}">\n'
            f'      <metadata key="name" value={quoteattr(pn)}/>\n'
            f'      <metadata key="extruder" value="{slot}"/>\n'
            f'      <metadata key="matrix" value="1 0 0 {cx:.3f} 0 1 0 {cy:.3f} 0 0 1 0 0 0 0 1"/>\n'
            f'      <mesh_stat face_count="{len(m.faces)}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>\n'
            f'    </part>\n' for i, (pn, m, slot) in zip(ids, parts))
        cfg_objs.append(f'  <object id="{aid}">\n    <metadata key="name" value={quoteattr(oname)}/>\n'
                        f'    <metadata key="extruder" value="{parts[0][2]}"/>\n{pc}  </object>\n')
        aid += 1
    nslots = max(s for _, parts, _ in objects for _, _, s in parts)
    model = (f'<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" {NS}>\n'
             ' <metadata name="Application">BambuStudio-02.08.02.61</metadata>\n <metadata name="BambuStudio:3mfVersion">1</metadata>\n'
             f' <resources>\n{"".join(res)} </resources>\n <build p:UUID="{_uuid()}">\n{"".join(items)} </build>\n</model>')
    settings = (f'<?xml version="1.0" encoding="UTF-8"?>\n<config>\n{"".join(cfg_objs)}  <plate>\n'
                '    <metadata key="plater_id" value="1"/>\n    <metadata key="plater_name" value=""/>\n'
                '    <metadata key="locked" value="false"/>\n    <metadata key="filament_map_mode" value="Manual"/>\n'
                f'    <metadata key="filament_maps" value="{" ".join("1" for _ in range(nslots))}"/>\n'
                f'    <metadata key="filament_volume_maps" value="{" ".join("0" for _ in range(nslots))}"/>\n'
                '  </plate>\n  <assemble>\n  </assemble>\n</config>')
    model_rels = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
                  + "\n".join(rels) + "\n</Relationships>")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", RELS)
        z.writestr("3D/_rels/3dmodel.model.rels", model_rels)
        z.writestr("3D/3dmodel.model", model)
        for n, t in files.items():
            z.writestr(n, t)
        z.writestr("Metadata/model_settings.config", settings)
        z.writestr("Metadata/project_settings.config", project_settings)


def widen_filaments(cfg, n, single_template_bytes):
    """Grow a 4-filament project config (dict) to n filaments: every per-filament list (length 1 in the single-filament
    template) is extended by repeating its first value; flush matrices are rebuilt n x n per nozzle."""
    single = json.loads(single_template_bytes)
    for k, v in list(cfg.items()):
        if isinstance(v, list) and isinstance(single.get(k), list) and len(single[k]) == 1 and len(v) != n:
            cfg[k] = (v + [v[0]] * n)[:n]
    fm = cfg.get("flush_volumes_matrix", [])
    off = next((x for x in fm if x not in ("0", 0)), "280")
    one = [("0" if i == j else str(off)) for i in range(n) for j in range(n)]
    cfg["flush_volumes_matrix"] = one * 2
    fv = cfg.get("flush_volumes_vector", ["1", "1"])
    cfg["flush_volumes_vector"] = [fv[0], fv[1]] * n if len(fv) >= 2 else fv
    return cfg
