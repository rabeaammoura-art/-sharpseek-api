"""Lit render (three.js in headless Chromium, soft shadows) of the wrench key holder STLs.
Usage: python cad/wrench_render3d.py <out_dir> <tag> <three_js_dir>   (needs playwright + three.min.js, STLLoader.js)"""
import base64, json, sys
from pathlib import Path
import subprocess

out, variant, js = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
COL = {"black": "#26262a", "orange": "#ff7a00", "white": "#ececee", "red": "#d01818", "grey": "#8a8a94"}
PAL = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}      # optional palette override: {"black": "#hex", "white": "#hex", "orange": "#hex", "metal": ["white", "orange"]}
COL.update({k: v for k, v in PAL.items() if k in COL}); METAL = PAL.get("metal", [])
items = []
for f in sorted((out / "stl").glob("*.stl")):
    n, c = f.stem.split("__")
    if n.startswith("brake_") and n != f"brake_{variant}":
        continue
    items.append({"c": COL[c], "m": c, "met": c in METAL, "b": base64.b64encode(f.read_bytes()).decode()})
html = f"""<html><body style="margin:0;background:#d9d9dc"><script>{(js/'three.min.js').read_text()}</script>
<script>{(js/'STLLoader.js').read_text()}</script><script>
const items={json.dumps(items)};
const W=2400,H=900;const r=new THREE.WebGLRenderer({{antialias:true,preserveDrawingBuffer:true}});r.setSize(W,H);r.shadowMap.enabled=true;
r.shadowMap.type=THREE.PCFSoftShadowMap;document.body.appendChild(r.domElement);
const sc=new THREE.Scene();sc.background=new THREE.Color(0xd9d9dc);
const g=new THREE.Group();
function b2a(b){{const s=atob(b),a=new Uint8Array(s.length);for(let i=0;i<s.length;i++)a[i]=s.charCodeAt(i);return a.buffer}}
const L=new THREE.STLLoader();
for(const it of items){{let geo=L.parse(b2a(it.b));geo.computeVertexNormals();
 const m=new THREE.Mesh(geo,new THREE.MeshStandardMaterial({{color:it.c,roughness:it.met?0.45:(it.m=='white'?0.55:0.7),metalness:it.met?0.25:0.0}}));
 m.castShadow=true;m.receiveShadow=true;g.add(m);}}
sc.add(g);
const box=new THREE.Box3().setFromObject(g),c=box.getCenter(new THREE.Vector3());g.position.sub(c);
const wall=new THREE.Mesh(new THREE.PlaneGeometry(2000,1000),new THREE.MeshStandardMaterial({{color:0xe4e4e6,roughness:1}}));
wall.position.z=-(box.max.z-box.min.z)/2-0.01-(c.z-box.min.z)+ (c.z-box.min.z)-0.01;wall.position.z=box.min.z-c.z-0.02;wall.receiveShadow=false;sc.add(wall);
sc.add(new THREE.HemisphereLight(0xffffff,0x888890,0.75));
const d=new THREE.DirectionalLight(0xffffff,0.9);d.position.set(-250,350,400);d.castShadow=true;d.shadow.mapSize.set(4096,4096);
Object.assign(d.shadow.camera,{{left:-400,right:400,top:200,bottom:-200,near:10,far:1500}});d.shadow.radius=4;d.shadow.bias=-0.0004;sc.add(d);
const cam=new THREE.PerspectiveCamera(22,W/H,10,5000);
const v=location.hash.slice(1)||'front';
const P={{front:[0,10,780],iso:[-330,-170,820],side:[820,-30,120],low:[260,-330,560],close:[330,10,520]}}[v];
const T={{front:[0,0,0],iso:[0,0,0],close:[150,10,0],side:[0,-10,0],low:[0,-10,0]}}[v];
const sk=(box.max.x-box.min.x)/610;cam.position.set(P[0]*sk,P[1]*sk,P[2]*sk);cam.lookAt(T[0]*sk,T[1]*sk,T[2]*sk);r.render(sc,cam);window.done=true;
</script></body></html>"""
(out / "r.html").write_text(html)
runner = out / "r.js"
runner.write_text("""const {chromium}=require('playwright');(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
for(const v of ['front','iso','close','side','low']){const pg=await b.newPage({viewport:{width:2400,height:900}});
await pg.goto('file://'+process.argv[2]+'#'+v);await pg.reload();await pg.waitForFunction('window.done===true',null,{timeout:120000});
await pg.locator('canvas').screenshot({path:process.argv[3]+'_render_'+v+'.png'});console.log(v);}await b.close();})();""")
subprocess.run(["node", str(runner), str(out / "r.html"), str(out / "views" / variant)], check=True)
(out / "r.html").unlink(); runner.unlink()
