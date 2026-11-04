"""Renders of the 3-module wall art (three.js in headless Chromium, no shadows).
usage: python render_modules.py <mod_dir (output of modular.py)> <three_js_dir>"""
import base64, json, sys, subprocess, os
from pathlib import Path
mod, js = Path(sys.argv[1]), Path(sys.argv[2]); out = mod / "renders"; out.mkdir(exist_ok=True)
val = json.loads((mod / "validation.json").read_text())
X0 = {m["module"]: m["global_x0"] for m in val["modules"]}
CX, CY, CZ = 300.0, 105.5, 7.0
COL = {"black": "#1c1c20", "blue": "#1d3fd0"}
def items(offsets):
    it = []
    for i in (1, 2, 3):
        for n in ("black", "blue"):
            f = mod / "stl" / f"module{i}__{n}.stl"
            if f.exists():
                o = offsets.get(i, (0, 0, 0))
                it.append({"c": COL[n], "b": base64.b64encode(f.read_bytes()).decode(), "o": [X0[i]-CX+o[0], -CY+o[1], -CZ+o[2]]})
    return it
# modules in model x order: M3 (painter) is at low x after mirroring; art-left (M1) at high x
EXP = {1: (60, 0, 0), 2: (0, 0, 0), 3: (-60, 0, 0)}
EXP_Y = {1: (60, 55, 0), 2: (0, 0, 0), 3: (-60, 0, 0)}
S1X = 600 - 196 - CX; S2X = 600 - 452 - CX
views = {
 "front":           (items({}),     dict(pos=[0, 0, -760], tgt=[0, 0, 0], fov=24)),
 "rear":            (items({}),     dict(pos=[0, 0, 760], tgt=[0, 0, 0], fov=24)),
 "exploded_front":  (items(EXP),    dict(pos=[-330, 160, -820], tgt=[0, 0, 0], fov=26)),
 "exploded_rear":   (items(EXP_Y),  dict(pos=[330, 200, 860], tgt=[0, 10, 0], fov=26)),
 "joint_seam1_rear":(items({}),     dict(pos=[S1X-70, 40, 150], tgt=[S1X, 0, 0], fov=32)),
 "joint_seam2_rear":(items({}),     dict(pos=[S2X+60, 20, 130], tgt=[S2X, 15, 0], fov=32)),
 "joint_exploded":  (items({1: (28, 0, 0), 2: (0, 0, 0)}), dict(pos=[S1X+10, 90, 170], tgt=[S1X, 0, 0], fov=32)),
}
(out / "views.json").write_text(json.dumps({k: v[1] for k, v in views.items()}))
for name, (it, cam) in views.items():
    html = f"""<html><body style="margin:0"><script>{(js/'three.min.js').read_text()}</script><script>{(js/'STLLoader.js').read_text()}</script><script>
const items={json.dumps(it)},cam0={json.dumps(cam)};const W=2400,H=1050;
const r=new THREE.WebGLRenderer({{antialias:true,preserveDrawingBuffer:true}});r.setSize(W,H);document.body.appendChild(r.domElement);
const sc=new THREE.Scene();sc.background=new THREE.Color(0xf0eee8);const L=new THREE.STLLoader();
function b2a(b){{const s=atob(b),a=new Uint8Array(s.length);for(let i=0;i<s.length;i++)a[i]=s.charCodeAt(i);return a.buffer}}
for(const it of items){{const geo=L.parse(b2a(it.b));geo.computeVertexNormals();const m=new THREE.Mesh(geo,new THREE.MeshStandardMaterial({{color:it.c,roughness:0.55,side:THREE.DoubleSide}}));m.position.set(...it.o);sc.add(m);}}
sc.add(new THREE.HemisphereLight(0xffffff,0x8a8a90,0.85));
const d=new THREE.DirectionalLight(0xffffff,0.9);d.position.set(-300,400,-500);sc.add(d);const d2=new THREE.DirectionalLight(0xffffff,0.7);d2.position.set(300,300,500);sc.add(d2);
const cam=new THREE.PerspectiveCamera(cam0.fov,W/H,1,6000);cam.position.set(...cam0.pos);cam.up.set(0,1,0);cam.lookAt(...cam0.tgt);r.render(sc,cam);window.done=true;
</script></body></html>"""
    (out / f"{name}.html").write_text(html)
(out / "r.js").write_text("""const {chromium}=require('playwright');(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
const names=JSON.parse(require('fs').readFileSync(process.argv[2]+'/views.json'));
for(const v of Object.keys(names)){const pg=await b.newPage({viewport:{width:2400,height:1050}});
await pg.goto('file://'+process.argv[2]+'/'+v+'.html');await pg.waitForFunction('window.done===true',null,{timeout:120000});
await pg.locator('canvas').screenshot({path:process.argv[2]+'/render_'+v+'.png'});console.log(v);await pg.close();}await b.close();})();""")
env = {**os.environ, "NODE_PATH": subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()}
subprocess.run(["node", str(out / "r.js"), str(out)], check=True, env=env)
for f in list(out.glob("*.html")) + [out / "r.js"]: f.unlink()
