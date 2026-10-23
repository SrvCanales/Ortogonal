"""
Proyección ortogonal sobre un plano — visualizador interactivo.

Ejecutar:
    pip install streamlit
    streamlit run app_proyeccion_ortogonal.py

Todo el display 3D y los cálculos corren en el navegador (three.js dentro de un
único componente HTML). Así, arrastrar un vector o editar una coordenada NO
dispara un "rerun" de Streamlit: la respuesta es inmediata y sin reinicios.
Requiere conexión a internet para cargar three.js desde cdnjs.
"""

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Proyección ortogonal", layout="wide")

st.markdown(
    """
    <style>
      #MainMenu, footer, header {visibility: hidden;}
      .stApp {background: #0d0f16;}
      .block-container {padding-top: 1.4rem; padding-bottom: 1rem; max-width: 1200px;}
      h1 {color: #eeeae2; font-weight: 600; font-size: 1.5rem !important; padding: 0 0 .1rem 0;}
      .sub {color: #8c92a4; font-size: .92rem; margin-bottom: .8rem;}
      iframe {border: none; border-radius: 14px;}
    </style>
    <h1>Proyección ortogonal sobre un plano</h1>
    <div class="sub">Mueve <b>a</b>, <b>b</b> y <b>v</b> con el mouse o con las coordenadas.
    Activa la base ortonormal y la proyección con los botones.</div>
    """,
    unsafe_allow_html=True,
)

HTML = r'''
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root{
    --bg:#12141c; --bg-deep:#0d0f16; --panel:#181b26; --panel-line:#272b3a;
    --text:#eeeae2; --muted:#8c92a4;
    --sol:#e8b94e; --p1:#e0674f; --p2:#3fa796; --p3:#8b7fd6; --p4:#d45a94;
  }
  *{box-sizing:border-box}
  html,body{margin:0;height:100%;background:var(--bg-deep);color:var(--text);
    font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;}
  #app{display:flex;gap:12px;height:100%;}
  #stage{position:relative;flex:1;min-width:0;background:var(--bg);
    border:1px solid var(--panel-line);border-radius:14px;overflow:hidden;}
  #stage canvas{display:block;width:100%;height:100%;touch-action:none;}
  #hint{position:absolute;left:14px;bottom:10px;font-size:12px;color:var(--muted);pointer-events:none;}
  #fail{position:absolute;inset:0;display:none;align-items:center;justify-content:center;
    color:var(--muted);font-size:14px;text-align:center;padding:24px;}

  #panel{width:304px;flex:none;background:var(--panel);border:1px solid var(--panel-line);
    border-radius:14px;padding:16px;display:flex;flex-direction:column;gap:16px;overflow:auto;}
  .sec{font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:var(--muted);margin-bottom:8px;}
  .vec{margin-bottom:10px;}
  .vname{display:flex;align-items:center;gap:8px;font-size:14px;margin-bottom:5px;}
  .vname i{width:10px;height:10px;border-radius:50%;display:inline-block;}
  .vname b{font-family:Georgia,serif;font-style:italic;font-weight:600;font-size:16px;}
  .vname span{color:var(--muted);font-size:12px;}
  .coords{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;}
  .coords label{display:flex;align-items:center;gap:5px;background:var(--bg);
    border:1px solid var(--panel-line);border-radius:8px;padding:0 8px;}
  .coords label:focus-within{border-color:var(--muted);}
  .coords label span{color:var(--muted);font-size:12px;font-family:Georgia,serif;font-style:italic;}
  .coords input{width:100%;min-width:0;background:transparent;border:none;outline:none;
    color:var(--text);font-size:14px;padding:8px 0;font-variant-numeric:tabular-nums;}

  .btns{display:flex;flex-direction:column;gap:8px;}
  .tog{background:transparent;color:var(--text);border:1px solid var(--panel-line);border-radius:10px;
    padding:11px 12px;font-size:14px;cursor:pointer;text-align:left;
    display:flex;align-items:center;justify-content:space-between;transition:background .12s,border-color .12s;}
  .tog:hover{border-color:var(--muted);}
  .tog::after{content:"";width:9px;height:9px;border-radius:50%;border:1.5px solid var(--muted);}
  .tog[aria-pressed="true"]{background:rgba(238,234,226,.08);border-color:var(--text);}
  .tog[aria-pressed="true"]::after{background:var(--text);border-color:var(--text);}

  #out{font-size:13px;line-height:1.65;color:var(--text);font-variant-numeric:tabular-nums;}
  #out .m{color:var(--muted);}
  #out .warn{color:var(--p1);}
  #out .row{margin-bottom:8px;}
  #out i.k{font-family:Georgia,serif;}

  @media (max-width:760px){
    #app{flex-direction:column;height:auto;min-height:100%;}
    #stage{flex:none;height:56vh;min-height:340px;}
    #panel{width:auto;overflow:visible;}
  }
</style>
</head>
<body>
<div id="app">
  <div id="stage">
    <div id="fail">No se pudo cargar three.js (¿sin conexión a internet?).</div>
    <div id="hint">Arrastra las puntas · gira arrastrando el fondo · Shift: mover en z</div>
  </div>
  <div id="panel">
    <div>
      <div class="sec">Plano</div>
      <div id="vecPlane"></div>
    </div>
    <div>
      <div class="sec">Vector</div>
      <div id="vecV"></div>
    </div>
    <div class="btns">
      <button class="tog" id="btnBasis" aria-pressed="false">Base ortonormal del plano</button>
      <button class="tog" id="btnProj"  aria-pressed="false">Proyección ortogonal de v</button>
    </div>
    <div id="out"></div>
  </div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
(function(){
if (typeof THREE === 'undefined'){ document.getElementById('fail').style.display='flex'; return; }

/* ───────── Estado ───────── */
const LIM = 5;                                   // rango de cada coordenada
const clamp = x => Math.max(-LIM, Math.min(LIM, x));
const S = {
  a: new THREE.Vector3(2, 0, 0),
  b: new THREE.Vector3(0, 2, 1),
  v: new THREE.Vector3(1.2, 1, 2.6)
};
let showBasis = false, showProj = false;
const e1 = new THREE.Vector3(), e2 = new THREE.Vector3(), proj = new THREE.Vector3();
const ZERO = new THREE.Vector3();

/* ───────── Escena ───────── */
const stage = document.getElementById('stage');
const renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.setClearColor(0x12141c, 1);
stage.insertBefore(renderer.domElement, stage.firstChild);
const cv = renderer.domElement;

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 100);
camera.up.set(0, 0, 1);
const cam = {az: 0.95, el: 0.42, r: 17};
function placeCamera(){
  const ce = Math.cos(cam.el);
  camera.position.set(cam.r*ce*Math.cos(cam.az), cam.r*ce*Math.sin(cam.az), cam.r*Math.sin(cam.el));
  camera.lookAt(0, 0, 0.4);
}
placeCamera();

let dirty = true;
(function loop(){ requestAnimationFrame(loop); if(dirty){ dirty = false; renderer.render(scene, camera); } })();

new ResizeObserver(() => {
  const w = stage.clientWidth, h = stage.clientHeight;
  if (!w || !h) return;
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  dirty = true;
}).observe(stage);

/* Rejilla y ejes (estáticos) */
const grid = new THREE.GridHelper(10, 10, 0x272b3a, 0x1d202c);
grid.rotateX(Math.PI/2);
scene.add(grid);
const ax = new THREE.BufferGeometry().setFromPoints([
  new THREE.Vector3(-5.5,0,0), new THREE.Vector3(5.5,0,0),
  new THREE.Vector3(0,-5.5,0), new THREE.Vector3(0,5.5,0),
  new THREE.Vector3(0,0,-5.5), new THREE.Vector3(0,0,5.5)]);
scene.add(new THREE.LineSegments(ax, new THREE.LineBasicMaterial({color:0x3b4055})));

function makeLabel(text, color, size, wide){
  const c = document.createElement('canvas'); c.width = wide ? 256 : 128; c.height = 128;
  const g = c.getContext('2d');
  g.font = 'italic 600 64px Georgia, serif'; g.fillStyle = color;
  g.textAlign = 'center'; g.textBaseline = 'middle';
  g.fillText(text, c.width/2, 68);
  const s = new THREE.Sprite(new THREE.SpriteMaterial({map:new THREE.CanvasTexture(c), transparent:true, depthTest:false}));
  s.scale.set(wide ? size*2 : size, size, 1);
  s.renderOrder = 10;
  scene.add(s);
  return s;
}
[['x',[6,0,0]],['y',[0,6,0]],['z',[0,0,6]]].forEach(([t,p]) => {
  const l = makeLabel(t, '#8c92a4', 0.6); l.position.set(...p);
});

/* Plano (parche cuadrado en la base ortonormal, se actualiza sin recrear geometría) */
const PS = 4.6;
const pg = new THREE.BufferGeometry();
pg.setAttribute('position', new THREE.BufferAttribute(new Float32Array(12), 3));
pg.setIndex([0,1,2, 0,2,3]);
const planeMesh = new THREE.Mesh(pg, new THREE.MeshBasicMaterial({
  color:0x8c92a4, transparent:true, opacity:0.17, side:THREE.DoubleSide, depthWrite:false}));
planeMesh.frustumCulled = false;
scene.add(planeMesh);
const eg = new THREE.BufferGeometry();
eg.setAttribute('position', new THREE.BufferAttribute(new Float32Array(12), 3));
const planeEdge = new THREE.LineLoop(eg, new THREE.LineBasicMaterial({color:0x8c92a4, transparent:true, opacity:0.55}));
planeEdge.frustumCulled = false;
scene.add(planeEdge);

/* Flechas */
const UP = new THREE.Vector3(0,1,0);
function makeArrow(color, r){
  const g = new THREE.Group();
  const mat = new THREE.MeshBasicMaterial({color});
  const shaft = new THREE.Mesh(new THREE.CylinderGeometry(r, r, 1, 14), mat);
  const head  = new THREE.Mesh(new THREE.ConeGeometry(r*3.2, 1, 18), mat);
  g.add(shaft, head); g.userData = {shaft, head};
  scene.add(g);
  return g;
}
const _d = new THREE.Vector3(), _q = new THREE.Quaternion();
function setArrow(g, from, to){
  _d.copy(to).sub(from);
  const L = _d.length();
  if (L < 1e-4){ g.visible = false; return; }
  g.visible = true;
  _d.divideScalar(L);
  const hl = Math.min(0.36, L*0.45), sl = L - hl;
  _q.setFromUnitVectors(UP, _d);
  const {shaft, head} = g.userData;
  shaft.quaternion.copy(_q); head.quaternion.copy(_q);
  shaft.scale.set(1, sl, 1); shaft.position.copy(from).addScaledVector(_d, sl/2);
  head.scale.set(1, hl, 1);  head.position.copy(from).addScaledVector(_d, sl + hl/2);
}

const COL = {a:0xe0674f, b:0x3fa796, v:0xe8b94e, e1:0x8b7fd6, e2:0xd45a94, proj:0xf2eee6};
const arrow = {
  a: makeArrow(COL.a, 0.035), b: makeArrow(COL.b, 0.035), v: makeArrow(COL.v, 0.04),
  e1: makeArrow(COL.e1, 0.07), e2: makeArrow(COL.e2, 0.07), proj: makeArrow(COL.proj, 0.06)
};
const lbl = {
  a: makeLabel('a', '#e0674f', 0.62), b: makeLabel('b', '#3fa796', 0.62), v: makeLabel('v', '#e8b94e', 0.62),
  e1: makeLabel('e₁', '#8b7fd6', 0.62), e2: makeLabel('e₂', '#d45a94', 0.62),
  proj: makeLabel('proy', '#f2eee6', 0.5, true)
};

/* Segmento punteado v → proyección y marca de ángulo recto */
const dg = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3(0,0,1)]);
const dashed = new THREE.Line(dg, new THREE.LineDashedMaterial({color:0xeeeae2, dashSize:0.16, gapSize:0.12, transparent:true, opacity:0.75}));
dashed.frustumCulled = false; scene.add(dashed);
const rg = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3(), new THREE.Vector3()]);
const rightAngle = new THREE.Line(rg, new THREE.LineBasicMaterial({color:0xeeeae2, transparent:true, opacity:0.8}));
rightAngle.frustumCulled = false; scene.add(rightAngle);

/* Manijas (puntas arrastrables) + zonas de captura invisibles más grandes */
const handles = {}, hits = [];
['a','b','v'].forEach(k => {
  const m = new THREE.Mesh(new THREE.SphereGeometry(0.11, 18, 14), new THREE.MeshBasicMaterial({color:COL[k]}));
  scene.add(m); handles[k] = m;
  const h = new THREE.Mesh(new THREE.SphereGeometry(0.5, 10, 8),
    new THREE.MeshBasicMaterial({transparent:true, opacity:0, depthWrite:false}));
  h.userData.key = k; scene.add(h); hits.push(h); handles[k+'_hit'] = h;
});

/* ───────── Panel de coordenadas ───────── */
const ROWS = [['a','a','var(--p1)','director 1','vecPlane'],
              ['b','b','var(--p2)','director 2','vecPlane'],
              ['v','v','var(--sol)','a proyectar','vecV']];
ROWS.forEach(([k,name,col,desc,host]) => {
  const d = document.createElement('div'); d.className = 'vec';
  d.innerHTML = `<div class="vname"><i style="background:${col}"></i><b>${name}</b><span>${desc}</span></div>
    <div class="coords">` + ['x','y','z'].map((c,i) =>
      `<label><span>${c}</span><input type="number" step="0.1" inputmode="decimal" data-k="${k}" data-i="${i}"></label>`).join('') + `</div>`;
  document.getElementById(host).appendChild(d);
});
const inputs = [...document.querySelectorAll('.coords input')];
const f = x => (Math.abs(x) < 0.005 ? 0 : x).toFixed(2);
const f3 = x => (Math.abs(x) < 0.0005 ? 0 : x).toFixed(3);
const fv = (u, g=f) => `(${g(u.x)}, ${g(u.y)}, ${g(u.z)})`;
function syncInputs(){
  inputs.forEach(inp => {
    if (inp === document.activeElement) return;
    inp.value = f(S[inp.dataset.k].getComponent(+inp.dataset.i));
  });
}
inputs.forEach(inp => inp.addEventListener('input', () => {
  const x = parseFloat(inp.value);
  if (!isFinite(x)) return;
  S[inp.dataset.k].setComponent(+inp.dataset.i, clamp(x));
  update();
}));
document.getElementById('panel').addEventListener('focusout', syncInputs);

const btnB = document.getElementById('btnBasis'), btnP = document.getElementById('btnProj');
btnB.onclick = () => { showBasis = !showBasis; btnB.setAttribute('aria-pressed', showBasis); update(); };
btnP.onclick = () => { showProj  = !showProj;  btnP.setAttribute('aria-pressed', showProj);  update(); };

/* ───────── Actualización (cálculo + escena + panel) ───────── */
const out = document.getElementById('out');
let lastHTML = '';
const _t = new THREE.Vector3(), _u = new THREE.Vector3();

function labelAt(s, tip, dir){
  s.position.copy(tip);
  if (dir && dir.lengthSq() > 1e-8) s.position.addScaledVector(dir.clone().normalize(), 0.5);
  s.position.z += 0.12;
}

function update(){
  const {a, b, v} = S;

  // Base ortonormal por Gram–Schmidt
  let ok = false;
  const la = a.length();
  if (la > 1e-3){
    e1.copy(a).divideScalar(la);
    e2.copy(b).addScaledVector(e1, -b.dot(e1));
    const l2 = e2.length();
    if (l2 > 1e-2){ e2.divideScalar(l2); ok = true; }
  }

  // Proyección ortogonal sobre el plano
  const c1 = ok ? v.dot(e1) : 0, c2 = ok ? v.dot(e2) : 0;
  proj.set(0,0,0);
  if (ok) proj.addScaledVector(e1, c1).addScaledVector(e2, c2);
  const resid = _t.copy(v).sub(proj);          // v − proy
  const rl = resid.length();

  // Vectores del usuario
  setArrow(arrow.a, ZERO, a); setArrow(arrow.b, ZERO, b); setArrow(arrow.v, ZERO, v);
  ['a','b','v'].forEach(k => { handles[k].position.copy(S[k]); handles[k+'_hit'].position.copy(S[k]); });
  labelAt(lbl.a, a, a); labelAt(lbl.b, b, b); labelAt(lbl.v, v, v);

  // Plano
  planeMesh.visible = planeEdge.visible = ok;
  if (ok){
    const sg = [[-1,-1],[1,-1],[1,1],[-1,1]];
    sg.forEach(([i,j], k) => {
      _u.copy(e1).multiplyScalar(i*PS).addScaledVector(e2, j*PS);
      pg.attributes.position.setXYZ(k, _u.x, _u.y, _u.z);
      eg.attributes.position.setXYZ(k, _u.x, _u.y, _u.z);
    });
    pg.attributes.position.needsUpdate = true; eg.attributes.position.needsUpdate = true;
  }

  // Base ortonormal visible
  const sb = ok && showBasis;
  arrow.e1.visible = arrow.e2.visible = lbl.e1.visible = lbl.e2.visible = sb;
  if (sb){
    setArrow(arrow.e1, ZERO, e1); setArrow(arrow.e2, ZERO, e2);
    labelAt(lbl.e1, e1, e1); labelAt(lbl.e2, e2, e2);
  }

  // Proyección visible
  const sp = ok && showProj;
  const hasProj = sp && proj.length() > 1e-3;
  const hasRes  = sp && rl > 1e-3;
  arrow.proj.visible = lbl.proj.visible = hasProj;
  if (hasProj){ setArrow(arrow.proj, ZERO, proj); labelAt(lbl.proj, proj, proj); }
  dashed.visible = hasRes;
  if (hasRes){
    dg.attributes.position.setXYZ(0, v.x, v.y, v.z);
    dg.attributes.position.setXYZ(1, proj.x, proj.y, proj.z);
    dg.attributes.position.needsUpdate = true;
    dashed.computeLineDistances();
  }
  rightAngle.visible = hasRes && hasProj;
  if (rightAngle.visible){
    const s = Math.min(0.28, rl*0.4, proj.length()*0.4);
    const d1 = resid.clone().divideScalar(rl).multiplyScalar(s);          // hacia v
    const d2 = proj.clone().normalize().multiplyScalar(-s);               // hacia el origen
    const p0 = proj.clone().add(d1), p1 = proj.clone().add(d1).add(d2), p2 = proj.clone().add(d2);
    [p0,p1,p2].forEach((p,i) => rg.attributes.position.setXYZ(i, p.x, p.y, p.z));
    rg.attributes.position.needsUpdate = true;
  }

  // Panel de resultados
  let h = '';
  if (!ok){
    h = `<div class="warn">a y b son paralelos (o nulos): no definen un plano.</div>`;
  } else {
    if (showBasis){
      h += `<div class="row"><span class="m">base ortonormal</span><br>
        <i class="k">e₁</i> = ${fv(e1,f3)}<br><i class="k">e₂</i> = ${fv(e2,f3)}<br>
        <span class="m">|e₁| = |e₂| = 1 &nbsp;·&nbsp; e₁·e₂ = ${f3(e1.dot(e2))}</span></div>`;
    }
    if (showProj){
      h += `<div class="row"><span class="m">proyección</span><br>
        <i class="k">proy</i> = (v·e₁)e₁ + (v·e₂)e₂<br>
        <span class="m">v·e₁ = ${f3(c1)} &nbsp; v·e₂ = ${f3(c2)}</span><br>
        <i class="k">proy</i> = ${fv(proj,f3)}<br>
        <span class="m">|v − proy| = ${f3(rl)} &nbsp;(⟂ al plano)</span></div>`;
    }
  }
  if (h !== lastHTML){ out.innerHTML = h; lastHTML = h; }

  syncInputs();
  dirty = true;
}

/* ───────── Interacción: arrastrar puntas / orbitar / pellizcar ───────── */
const rc = new THREE.Raycaster(), ndc = new THREE.Vector2(), dragPlane = new THREE.Plane();
const ptrs = new Map();
let drag = null, orbit = false, pinch0 = 0, r0 = 0;

function setRay(e){
  const r = cv.getBoundingClientRect();
  ndc.set(((e.clientX - r.left)/r.width)*2 - 1, -((e.clientY - r.top)/r.height)*2 + 1);
  rc.setFromCamera(ndc, camera);
}
function pick(e){
  setRay(e);
  const hit = rc.intersectObjects(hits, false)[0];
  return hit ? hit.object.userData.key : null;
}
function startDrag(key, e){
  const t = S[key];
  const n = new THREE.Vector3(); camera.getWorldDirection(n);
  let vertical = e.shiftKey;
  if (vertical){ n.z = 0; if (n.lengthSq() < 1e-4) vertical = false; else n.normalize(); }
  dragPlane.setFromNormalAndCoplanarPoint(n, t);
  const p = new THREE.Vector3();
  if (!rc.ray.intersectPlane(dragPlane, p)) p.copy(t);
  drag = {key, vertical, off: t.clone().sub(p)};
  cv.style.cursor = 'grabbing';
}
function moveDrag(e){
  setRay(e);
  const p = new THREE.Vector3();
  if (!rc.ray.intersectPlane(dragPlane, p)) return;
  const t = S[drag.key];
  if (drag.vertical) t.z = clamp(p.z + drag.off.z);
  else { t.copy(p).add(drag.off); t.set(clamp(t.x), clamp(t.y), clamp(t.z)); }
  update();
}

cv.addEventListener('pointerdown', e => {
  cv.setPointerCapture(e.pointerId);
  ptrs.set(e.pointerId, {x:e.clientX, y:e.clientY});
  if (ptrs.size === 2){
    drag = null; orbit = false;
    const [p, q] = [...ptrs.values()];
    pinch0 = Math.hypot(p.x - q.x, p.y - q.y); r0 = cam.r;
    return;
  }
  const k = pick(e);
  if (k) startDrag(k, e); else { orbit = true; cv.style.cursor = 'grabbing'; }
});
cv.addEventListener('pointermove', e => {
  if (!ptrs.has(e.pointerId)){                      // hover (solo mouse)
    cv.style.cursor = pick(e) ? 'grab' : 'default';
    return;
  }
  const prev = ptrs.get(e.pointerId);
  const dx = e.clientX - prev.x, dy = e.clientY - prev.y;
  ptrs.set(e.pointerId, {x:e.clientX, y:e.clientY});
  if (ptrs.size === 2){
    const [p, q] = [...ptrs.values()];
    const d = Math.hypot(p.x - q.x, p.y - q.y);
    if (pinch0 > 0){ cam.r = Math.max(7, Math.min(32, r0 * pinch0 / d)); placeCamera(); dirty = true; }
  } else if (drag){
    moveDrag(e);
  } else if (orbit){
    cam.az -= dx * 0.008;
    cam.el = Math.max(-1.4, Math.min(1.4, cam.el + dy * 0.008));
    placeCamera(); dirty = true;
  }
});
function endPtr(e){
  ptrs.delete(e.pointerId);
  if (ptrs.size < 2) pinch0 = 0;
  if (ptrs.size === 0 || drag === null){ orbit = ptrs.size === 1 ? false : orbit; }
  if (ptrs.size === 0){ drag = null; orbit = false; cv.style.cursor = 'default'; }
  else { drag = null; orbit = false; }
}
cv.addEventListener('pointerup', endPtr);
cv.addEventListener('pointercancel', endPtr);
cv.addEventListener('wheel', e => {
  e.preventDefault();
  cam.r = Math.max(7, Math.min(32, cam.r * Math.exp(e.deltaY * 0.001)));
  placeCamera(); dirty = true;
}, {passive:false});

update();
})();
</script>
</body>
</html>
'''

components.html(HTML, height=780, scrolling=True)
