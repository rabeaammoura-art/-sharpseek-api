"""Render product images of the Teddy-heart lithophane lamp from the mesh embedded in the earlier artifact
(https://claude.ai/artifact/1b1nYar4V76rGHqFutimzs).  Usage: python website/render_teddy.py <saved artifact html>"""
import base64
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
THREE = Path(os.environ.get("THREE_DIR", "/tmp/claude-0/sp/r3d"))
OUT = HERE / "public" / "img"
src = Path(sys.argv[1]).read_text(encoding="utf-8")
i = src.index("const DATA=") + len("const DATA=")
j = src.index("};", i) + 1
D = json.loads(src[i:j])


def decode(d):
    q = np.frombuffer(base64.b64decode(d["pos"]), dtype="<u2").reshape(-1, 3).astype(np.float64)
    V = np.array(d["min"]) + q / 65535 * np.array(d["ext"])
    F = np.frombuffer(base64.b64decode(d["idx"]), dtype="<u4").reshape(-1, 3)
    return np.round(V[F].reshape(-1), 2).tolist()      # un-indexed triangle soup: three.js computes flat-ish normals


def render(name, front_dz, cam, size, bg=None):
    WORK = THREE / "scene"; WORK.mkdir(parents=True, exist_ok=True)
    data = {"rb": decode(D["rb"]), "fb": decode(D["fb"]), "dz": front_dz, "cam": cam, "size": size, "bg": bg}
    (WORK / "teddy.json").write_text(json.dumps(data))
    (WORK / "teddy.html").write_text("""<!doctype html><meta charset=utf-8><body style="margin:0"><canvas id=c></canvas>
<script type=importmap>{"imports":{"three":"../node_modules/three/build/three.module.js"}}</script><script type=module>
import * as T from 'three';
const D = await (await fetch('teddy.json')).json(); const [W,H]=D.size;
const r = new T.WebGLRenderer({canvas:c,antialias:true,alpha:true,preserveDrawingBuffer:true}); r.setSize(W,H,false);
r.shadowMap.enabled=true; r.shadowMap.type=T.PCFSoftShadowMap; r.toneMapping=T.ACESFilmicToneMapping;
const s=new T.Scene(); if(D.bg) s.background=new T.Color(D.bg);
s.add(new T.HemisphereLight(0xffffff,0x9a8870,1.0));
const k=new T.DirectionalLight(0xffffff,2.2); k.position.set(160,240,420); k.castShadow=true; k.shadow.mapSize.set(2048,2048);
Object.assign(k.shadow.camera,{left:-260,right:260,top:260,bottom:-260,near:10,far:1400}); k.shadow.bias=-0.0006; s.add(k);
const f=new T.DirectionalLight(0xcfe0ff,0.7); f.position.set(-300,80,-300); s.add(f);
function mesh(pos,color,rough){const g=new T.BufferGeometry(); g.setAttribute('position',new T.Float32BufferAttribute(pos,3)); g.computeVertexNormals();
  const m=new T.Mesh(g,new T.MeshStandardMaterial({color,roughness:rough,metalness:0,side:T.DoubleSide})); m.castShadow=true; m.receiveShadow=true; return m;}
const rb=mesh(D.rb,0xd9b98f,.6), fb=mesh(D.fb,0xf4efe8,.55); fb.position.z=D.dz; s.add(rb,fb);
const gp=new T.Mesh(new T.PlaneGeometry(2000,2000),new T.ShadowMaterial({opacity:.25})); gp.rotation.x=-Math.PI/2; gp.position.y=-101; gp.receiveShadow=true; s.add(gp);
const c2=D.cam, cam=new T.PerspectiveCamera(c2.fov,W/H,10,4000); cam.position.set(...c2.pos); cam.lookAt(...c2.look); s.add(cam);
r.render(s,cam); window.__done=true;</script>""")
    runner = f"""
const {{ chromium }} = require('playwright'); const http=require('http'),fs=require('fs'),path=require('path'); const root={json.dumps(str(THREE))};
const srv=http.createServer((q,s)=>{{const f=path.join(root,decodeURIComponent(q.url.split('?')[0])); fs.readFile(f,(e,d)=>{{ if(e){{s.writeHead(404);s.end();}} else {{ s.writeHead(200,{{'content-type': f.endsWith('.js')||f.endsWith('.mjs')?'text/javascript':f.endsWith('.json')?'application/json':'text/html'}}); s.end(d);}} }});}}).listen(0,async()=>{{
 const b=await chromium.launch({{args:['--use-gl=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']}});
 const p=await b.newPage({{viewport:{{width:{size[0]},height:{size[1]}}}}}); p.on('pageerror',e=>console.log('ERR',e));
 await p.goto('http://localhost:'+srv.address().port+'/scene/teddy.html'); await p.waitForFunction('window.__done',null,{{timeout:90000}});
 await p.locator('#c').screenshot({{path:{json.dumps(str(OUT / name))},omitBackground:true}}); await b.close(); srv.close();}});"""
    (WORK / "run_teddy.js").write_text(runner)
    r = subprocess.run(["node", str(WORK / "run_teddy.js")], capture_output=True, text=True,
                       env={**os.environ, "NODE_PATH": subprocess.check_output(["npm", "root", "-g"], text=True).strip()})
    print(name, (r.stdout + r.stderr).strip()[:300])


OUT.mkdir(parents=True, exist_ok=True)
render("3d-teddy-assembled.png", 0, {"fov": 30, "pos": [260, 170, 560], "look": [0, -6, 20]}, (1200, 1200))
render("3d-teddy-exploded.png", 70, {"fov": 30, "pos": [330, 200, 520], "look": [0, -6, 36]}, (1400, 1100))
