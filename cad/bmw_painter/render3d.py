"""Lit renders (three.js in headless Chromium) of the BMW painter wall art.
usage: python render3d.py <stl_dir_with_black_and_blue> <out_dir> <three_js_dir>   (three.min.js r128 + STLLoader.js)"""
import base64, json, sys, subprocess
from pathlib import Path
stl, out, js = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]); out.mkdir(parents=True, exist_ok=True)
items = [{"c": c, "b": base64.b64encode((stl / f"bmw_painter__{n}.stl").read_bytes()).decode()} for n, c in (("black", "#1c1c20"), ("blue", "#1d3fd0"))]
html = f"""<html><body style="margin:0"><script>{(js/'three.min.js').read_text()}</script><script>{(js/'STLLoader.js').read_text()}</script><script>
const items={json.dumps(items)};const W=2400,H=1050;
const r=new THREE.WebGLRenderer({{antialias:true,preserveDrawingBuffer:true}});r.setSize(W,H);r.shadowMap.enabled=true;r.shadowMap.type=THREE.PCFSoftShadowMap;document.body.appendChild(r.domElement);
const sc=new THREE.Scene();sc.background=new THREE.Color(0xe9e6df);
const g=new THREE.Group();function b2a(b){{const s=atob(b),a=new Uint8Array(s.length);for(let i=0;i<s.length;i++)a[i]=s.charCodeAt(i);return a.buffer}}
const L=new THREE.STLLoader();
for(const it of items){{const geo=L.parse(b2a(it.b));geo.computeVertexNormals();const m=new THREE.Mesh(geo,new THREE.MeshStandardMaterial({{color:it.c,roughness:0.6}}));m.castShadow=true;m.receiveShadow=true;g.add(m);}}
sc.add(g);const box=new THREE.Box3().setFromObject(g),c=box.getCenter(new THREE.Vector3());g.position.sub(c);
const wall=new THREE.Mesh(new THREE.PlaneGeometry(3000,2000),new THREE.MeshStandardMaterial({{color:0xf1eee8,roughness:1}}));wall.position.z=-(box.max.z-box.min.z)/2-5;wall.receiveShadow=true;sc.add(wall);
sc.add(new THREE.HemisphereLight(0xffffff,0x9a9a9a,0.8));
const d=new THREE.DirectionalLight(0xffffff,0.85);d.position.set(-300,400,500);d.castShadow=true;d.shadow.mapSize.set(4096,4096);
Object.assign(d.shadow.camera,{{left:-400,right:400,top:250,bottom:-250,near:10,far:2000}});d.shadow.radius=3;d.shadow.bias=-0.0004;sc.add(d);
const cam=new THREE.PerspectiveCamera(24,W/H,10,6000);const v=location.hash.slice(1)||'front';
const P={{front:[0,0,520],iso_l:[-260,-110,430],iso_r:[260,-110,430],rear:[0,0,-520],side:[520,0,40],close:[190,-20,230]}}[v];
const T={{close:[75,-10,0]}}[v]||[0,0,0];
if(v==='rear'){{wall.visible=false;sc.background=new THREE.Color(0xe9e6df);}}
cam.position.set(...P);cam.lookAt(...T);cam.up.set(0,1,0);r.render(sc,cam);window.done=true;
</script></body></html>"""
(out / "r.html").write_text(html)
(out / "r.js").write_text("""const {chromium}=require('playwright');(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
for(const v of ['front','iso_l','iso_r','rear','side','close']){const pg=await b.newPage({viewport:{width:2400,height:1050}});
await pg.goto('file://'+process.argv[2]+'#'+v);await pg.reload();await pg.waitForFunction('window.done===true',null,{timeout:120000});
await pg.locator('canvas').screenshot({path:process.argv[3]+'/render_'+v+'.png'});console.log(v);}await b.close();})();""")
subprocess.run(["node", str(out / "r.js"), str(out / "r.html"), str(out)], check=True, env={**__import__("os").environ, "NODE_PATH": subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()})
(out / "r.html").unlink(); (out / "r.js").unlink()
