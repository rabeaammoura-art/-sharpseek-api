// Autodesk Fusion (cloud, MCP.ExecuteTypeScript) check of the printed kickstand + plaque fixing for the 200 mm box.
// Independent B-rep model (boxes / cylinders in mm, box frame: x across, y up, z inward from the outer back face), NOT the mesh code in cad/kickstand.py.
// Checks: module sliding into the dovetail pocket (6 positions), leg 0..26 degrees vs module / pocket block, pin, M2 nut / screw / post (plaque fixing).
// Result of 2026-11-18 (all in mm3): slide [0,0,0,0.07,0.07,0] (detent bump), leg 0..24 deg = 0, 26 deg = 4.22 vs module (stop at 24.0 deg), pin 0, nut / screw 0.
// Parameters K come from cad/kickstand.py layout(200) with the chamber ceiling 4.9 (MOD_T + 0.4). Run it with the 2.3 scratch format of invoke_fusion.
type Design = import("@adsk/fusion").adsk.fusion.Design;
const K:any = {ya:64, y0:47, yin:37, legLen:166.8, wb:10.186, wtop:13.186, ch:4.9, pad:6.9};
function run(){
  const app = adsk.core.Application.get();
  app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType);
  const design = app.activeProduct as Design;
  design.designType = adsk.fusion.DesignTypes.DirectDesignType;
  const root = design.rootComponent;
  const tbm = adsk.fusion.TemporaryBRepManager.get();
  const P = (x:number,y:number,z:number)=>adsk.core.Point3D.create(x/10,y/10,z/10);
  const V = (x:number,y:number,z:number)=>adsk.core.Vector3D.create(x,y,z);
  const obb = (c:number[],ld:number[],wd:number[],l:number,w:number,h:number)=>tbm.createBox(adsk.core.OrientedBoundingBox3D.create(P(c[0],c[1],c[2]),V(ld[0],ld[1],ld[2]),V(wd[0],wd[1],wd[2]),l/10,w/10,h/10));
  const ab = (x0:number,x1:number,y0:number,y1:number,z0:number,z1:number)=>obb([(x0+x1)/2,(y0+y1)/2,(z0+z1)/2],[1,0,0],[0,1,0],x1-x0,y1-y0,z1-z0);
  const cylx = (y:number,z:number,r:number,x0:number,x1:number)=>tbm.createCylinderOrCone(P(x0,y,z),r/10,P(x1,y,z),r/10);
  const cylz = (x:number,y:number,r:number,z0:number,z1:number)=>tbm.createCylinderOrCone(P(x,y,z0),r/10,P(x,y,z1),r/10);
  const uni = (a:any,b:any)=>{ tbm.booleanOperation(a,b,adsk.fusion.BooleanTypes.UnionBooleanType); return a; };
  const dif = (a:any,b:any)=>{ tbm.booleanOperation(a,b,adsk.fusion.BooleanTypes.DifferenceBooleanType); return a; };
  const its = (a:any,b:any)=>{ tbm.booleanOperation(a,b,adsk.fusion.BooleanTypes.IntersectionBooleanType); return a; };
  const hexz = (cx:number,cy:number,af:number,z0:number,z1:number)=>{ let h:any = null; for (const a of [0,60,120]) { const r=a*Math.PI/180; const s = obb([cx,cy,(z0+z1)/2],[Math.cos(r),Math.sin(r),0],[-Math.sin(r),Math.cos(r),0],100,af,z1-z0); h = h ? its(h,s) : s; } return h; };
  const add = (b:any,name:string,vis:boolean=true)=>{ const x = root.bRepBodies.add(b); x.name = name; x.isVisible = vis; return x; };
  const vol = (a:any,b:any)=>{ const col = adsk.core.ObjectCollection.create(); col.add(a); col.add(b); const r = design.analyzeInterference(design.createInterferenceInput(col)); let v=0; for (let i=0;i<r.count;i++) v += r.item(i).interferenceBody.volume*1000; return Math.round(v*100)/100; };
  const gap = (a:any,b:any)=>Math.round(app.measureManager.measureMinimumDistance(a,b).value*10*1000)/1000;
  const out:any = {};
  const ylo = K.yin-0.4, yhi = K.y0+28+0.4;
  const mkBlock = ()=>{ let b:any = ab(-40,40,ylo-8,yhi+8,0,K.pad); dif(b, ab(-12.4,12.4,ylo,yhi,-1,2.5)); dif(b, ab(-15.4,15.4,K.yin-0.4,K.yin+10.4,-1,2.5)); dif(b, ab(-15.4,15.4,K.yin+28-10-0.4,K.yin+28+0.4,-1,2.5)); dif(b, ab(-15.4,15.4,ylo,yhi,2.5,K.ch)); for (const s of [-1,1]) dif(b, cylz(s*12.4,K.y0+5,0.9,-1,2.5)); return b; };
  const mkModule = (y0:number)=>{ let m:any = ab(-15,15,y0,y0+10,2.5,4.5); uni(m, ab(-15,15,y0+18,y0+28,2.5,4.5)); uni(m, ab(-12,12,y0,y0+28,0,2.5)); for (const s of [-1,1]) uni(m, cylz(s*12.0,y0+5,0.45,0,2.5)); uni(m, ab(6.35,10.85,y0+2,y0+23.5,-K.wtop,0)); uni(m, ab(-10.85,-6.35,y0+2,y0+23.5,-K.wtop,0)); uni(m, ab(-10.85,10.85,y0+3,y0+9,-K.wtop,-K.wb)); dif(m, cylx(y0+17,-4.5,2.7,-12,12)); return m; };
  const mkLeg = (deg:number, ya:number)=>{ const t = deg*Math.PI/180, c=Math.cos(t), s=Math.sin(t); const dir=[0,-c,-s], bv=[0,s,-c], ax=[0,ya,-4.5], L=K.legLen-0.4; const at=(a:number,b:number)=>[ax[0]+a*dir[0]+b*bv[0], ax[1]+a*dir[1]+b*bv[1], ax[2]+a*dir[2]+b*bv[2]]; let g:any = obb(at(L/2,-2.5),dir,bv,L,4,12); uni(g, obb(at(L-5,-2.5),dir,bv,10,4,28)); uni(g, cylx(ya,-4.5,4.5,-6,6)); dif(g, cylx(ya,-4.5,2.7,-8,8)); return g; };
  const mkPin = (ya:number)=>{ let p:any = cylx(ya,-4.5,2.5,-12.85,13.85); uni(p, cylx(ya,-4.5,4.0,-12.85,-10.85)); return p; };
  const block = add(mkBlock(),'box_back_pocket_200');
  out.slide = []; for (let i=0;i<=5;i++){ const m = add(mkModule(K.yin+i*2),'tmp_module_'+i,false); out.slide.push(vol(block,m)); m.deleteMe(); }
  const mod = add(mkModule(K.y0),'module_locked');
  const legOpen = add(mkLeg(24,K.ya),'leg_open_24deg'); add(mkLeg(0,K.ya),'leg_folded',false);
  const pin = add(mkPin(K.ya),'pin');
  out.legs = {}; for (const d of [0,12,22,23.5,24,26]){ const g = add(mkLeg(d,K.ya),'tmp_leg_'+d,false); out.legs[d] = {vsBlock: vol(block,g), vsModule: vol(mod,g)}; g.deleteMe(); }
  out.pin = {vsModule: vol(mod,pin), vsLeg: vol(legOpen,pin), vsBlock: vol(block,pin)};
  out.locked_vs_block = vol(block,mod);
  out.gaps_mm = { pin_vs_leg_hole: gap(pin,legOpen), module_vs_block: gap(mod,block) };
  const fx = 96;   // M2 fixing of the 200 plaque: post D8 / hole 2.4, pocket af 4.3, nut af 4.0 x 1.6, screw D2 x 14
  let post:any = ab(fx-8,fx+8,-12,12,0,1.0); uni(post, cylz(fx,0,4.0,1.0,11.6)); dif(post, cylz(fx,0,1.2,-1,12));
  let plate:any = ab(fx-12,fx+12,-12,12,11.6,14.0); dif(plate, hexz(fx,0,4.3,11,14.5));
  const pP = add(post,'post_M2'), pL = add(plate,'plaque_base_pocket_M2'), pN = add(hexz(fx,0,4.0,11.6,13.2),'nut_M2'), pS = add(cylz(fx,0,1.0,-2,13.6),'screw_M2x14');
  out.fixM2_200 = {nut_vs_plate: vol(pL,pN), nut_vs_post: vol(pP,pN), screw_vs_post: vol(pP,pS), screw_vs_plate: vol(pL,pS), nut_to_plate_gap_mm: gap(pL,pN), screw_to_post_hole_gap_mm: gap(pP,pS)};
  return out;
}
adsk.result = JSON.stringify(run());
