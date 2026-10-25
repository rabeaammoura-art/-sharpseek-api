"""Photo-style 3D renders of the real print geometry (the same solids that go into the 3MF) with three.js in headless Chromium.

    python website/render3d.py           # writes website/public/img/3d-*.png

Needs `npm install three` somewhere (THREE_DIR env var, default /tmp/claude-0/sp/r3d) and Playwright's Chromium.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "student_pack"))
import layout  # noqa: E402
import mesh  # noqa: E402
from themes import THEMES, resolve_theme  # noqa: E402

THREE = Path(os.environ.get("THREE_DIR", "/tmp/claude-0/sp/r3d"))
OUT = HERE / "public" / "img"
WORK = THREE / "scene"


def piece_meshes(theme, name, kind):
    p = layout.KINDS[kind](theme, name)
    sol = mesh.solids(p)
    out = []
    for c, m in sol.items():
        V, F = mesh.to_arrays(m)
        out.append({"color": THEMES[theme]["filament_rgb"][c], "pos": np.round(V[F].reshape(-1), 3).tolist(), "name": c})
    return p, out


def scene(theme, name, kinds, layout_xy, cam, size, out_png, bg=None):
    items = []
    for kind, (x, y, rot) in zip(kinds, layout_xy):
        p, ms = piece_meshes(theme, name, kind)
        w, d, _ = p.size
        items.append({"kind": kind, "w": w, "d": d, "x": x, "y": y, "rot": rot, "meshes": ms})
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK / "data.json").write_text(json.dumps({"items": items, "cam": cam, "size": size, "bg": bg}))
    html = """<!doctype html><meta charset=utf-8><body style="margin:0;background:transparent"><canvas id=c></canvas>
<script type=importmap>{"imports":{"three":"../node_modules/three/build/three.module.js"}}</script>
<script type=module>
import * as T from 'three';
const D = await (await fetch('data.json')).json();
const [W, H] = D.size, cv = document.getElementById('c');
const r = new T.WebGLRenderer({canvas: cv, antialias: true, alpha: true, preserveDrawingBuffer: true});
r.setSize(W, H, false); r.setPixelRatio(1); r.shadowMap.enabled = true; r.shadowMap.type = T.PCFSoftShadowMap; r.toneMapping = T.ACESFilmicToneMapping; r.toneMappingExposure = 1.05;
const s = new T.Scene(); if (D.bg) s.background = new T.Color(D.bg);
s.add(new T.HemisphereLight(0xffffff, 0x8899bb, 0.9));
const key = new T.DirectionalLight(0xffffff, 2.3); key.position.set(-90, -140, 220); key.castShadow = true; key.shadow.mapSize.set(2048, 2048);
Object.assign(key.shadow.camera, {left: -200, right: 200, top: 200, bottom: -200, near: 1, far: 700}); key.shadow.bias = -0.0004; s.add(key);
const rim = new T.DirectionalLight(0xbcd0ff, 0.8); rim.position.set(150, 120, 90); s.add(rim);
const g = new T.Group(); s.add(g);
for (const it of D.items) {
  const piece = new T.Group();
  for (const m of it.meshes) {
    const geo = new T.BufferGeometry(); geo.setAttribute('position', new T.Float32BufferAttribute(m.pos, 3)); geo.computeVertexNormals();
    const mat = new T.MeshPhysicalMaterial({color: m.color, roughness: 0.42, metalness: 0.0, clearcoat: 0.25, clearcoatRoughness: 0.5});
    const me = new T.Mesh(geo, mat); me.castShadow = true; me.receiveShadow = true; piece.add(me);
  }
  piece.position.set(it.x, it.y, 0); piece.rotation.z = it.rot * Math.PI / 180; g.add(piece);
}
if (!D.bg) { const gp = new T.Mesh(new T.PlaneGeometry(1200, 1200), new T.ShadowMaterial({opacity: 0.28})); gp.position.z = -0.05; gp.receiveShadow = true; s.add(gp); }
const c = D.cam, cam = new T.PerspectiveCamera(c.fov, W / H, 1, 2000); cam.up.set(0, 0, 1);
cam.position.set(...c.pos); cam.lookAt(...c.look); s.add(cam);
r.render(s, cam); window.__done = true;
</script>"""
    (WORK / "index.html").write_text(html)
    runner = f"""
const {{ chromium }} = require('playwright'); const http = require('http'); const fs = require('fs'); const path = require('path');
const root = {json.dumps(str(THREE))};
const srv = http.createServer((q, s) => {{ const f = path.join(root, decodeURIComponent(q.url.split('?')[0])); fs.readFile(f, (e, d) => {{ if (e) {{ s.writeHead(404); s.end(); }} else {{ s.writeHead(200, {{'content-type': f.endsWith('.js') || f.endsWith('.mjs') ? 'text/javascript' : f.endsWith('.json') ? 'application/json' : 'text/html'}}); s.end(d); }} }}); }}).listen(0, async () => {{
  const b = await chromium.launch({{ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] }});
  const p = await b.newPage({{ viewport: {{ width: {size[0]}, height: {size[1]} }} }});
  p.on('pageerror', e => console.log('ERR', e)); p.on('console', m => m.type() === 'error' && console.log('CONSOLE', m.text()));
  await p.goto('http://localhost:' + srv.address().port + '/scene/index.html'); await p.waitForFunction('window.__done', null, {{ timeout: 60000 }});
  await p.locator('#c').screenshot({{ path: {json.dumps(str(out_png))}, omitBackground: {str(bg is None).lower()} }});
  await b.close(); srv.close(); }});"""
    (WORK / "run.js").write_text(runner)
    r = subprocess.run(["node", str(WORK / "run.js")], capture_output=True, text=True, env={**os.environ, "NODE_PATH": subprocess.check_output(["npm", "root", "-g"], text=True).strip()})
    print(out_png.name, (r.stdout + r.stderr).strip()[:300])


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    cam = {"fov": 28, "pos": [20, -260, 235], "look": [20, 8, 0]}
    # pack hero scene: tag + bottle on top, pencil + ruler below
    scene("construction", "OMAR", ["tag", "bottle", "pencil", "ruler"], [(-62, 38, -4), (30, 38, 3), (-70, -32, 2), (22, -62, 0)], cam, (1600, 1100), OUT / "3d-pack-construction.png")
