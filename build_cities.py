#!/usr/bin/env python3
"""Generate public/cities.html — city-level (市区町村) tracker.
Overview = Japan prefectures shaded by completion; click a prefecture to drill
into its municipalities (lazy-loaded from public/geo/<id>.json) and score them.
Reuses the prefecture outline data (japan.min.json)."""
import json, re, os

pref = json.load(open('japan.min.json'))
for x in pref: x['r'] = re.sub(r'\s+(Ken|Do|Fu|To)$', '', x['en']).strip()
PREF = json.dumps(pref, separators=(',', ':'), ensure_ascii=False)

idx = json.load(open('public/geo/index.json')) if os.path.exists('public/geo/index.json') else {}
IDX = json.dumps(idx, separators=(',', ':'), ensure_ascii=False)

HTML = r'''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>Keikenchi — Уровень по городам</title>
<meta name="description" content="Отмечай посещённые города и районы Японии на детальной карте муниципалитетов.">
<style>
  :root{--bg:#f6efe1;--ink:#333;--line:#3a3a3a}
  *{box-sizing:border-box}
  html,body{margin:0;height:100%}
  body{background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Hiragino Sans","Noto Sans JP",sans-serif;-webkit-tap-highlight-color:transparent}
  .wrap{max-width:760px;margin:0 auto;padding:16px 12px 60px;text-align:center}
  h1{font-size:15px;letter-spacing:.06em;margin:6px 0 2px;font-weight:700}
  .crumb{font-size:13px;color:#8a7f6a;margin:6px 0}
  .crumb a{color:#2a6fb0;cursor:pointer;text-decoration:none}
  .score{display:inline-block;background:#fbe6a8;border-radius:12px;padding:10px 30px;font-size:22px;font-weight:800;min-width:150px}
  .count{font-size:12px;color:#8a7f6a;margin-top:4px}
  .topbar{position:fixed;top:10px;left:12px;right:12px;display:flex;justify-content:space-between;z-index:30}
  .topbar a,.topbar button{font:inherit;font-size:12px;font-weight:600;padding:6px 12px;border-radius:9px;border:2px solid var(--line);background:#fff;cursor:pointer;text-decoration:none;color:var(--ink)}
  .layout{display:flex;gap:14px;align-items:flex-start;justify-content:center;margin-top:12px;flex-wrap:wrap}
  .legend{text-align:left;font-size:12px}
  .legend h3{font-size:13px;margin:0 0 8px}
  .lg{display:flex;align-items:center;gap:8px;padding:5px 8px;border-radius:8px;cursor:pointer;border:2px solid transparent;user-select:none}
  .lg.active{border-color:var(--line);background:#fff8}
  .dot{width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;border:2px solid var(--line);font-size:13px;flex:0 0 auto}
  .lg b{min-width:56px;display:inline-block}
  .lg span{color:#8a7f6a}
  .mapbox{position:relative;flex:1 1 320px;max-width:560px}
  svg{width:100%;height:auto;display:block;touch-action:none;border-radius:10px}
  path.reg{stroke:var(--line);stroke-linejoin:round;cursor:pointer;transition:fill .12s}
  path.reg:hover{stroke-width:1.6}
  .zoombtns{position:absolute;right:8px;bottom:8px;display:flex;flex-direction:column;gap:6px}
  .zoombtns button{width:34px;height:34px;padding:0;font-size:18px;border-radius:8px;border:2px solid var(--line);background:#fff;cursor:pointer;font-weight:700;line-height:1}
  .hint{font-size:12px;color:#8a7f6a;margin-top:10px}
  #tip{position:fixed;pointer-events:none;background:#333;color:#fff;font-size:12px;padding:4px 8px;border-radius:6px;opacity:0;transition:opacity .1s;white-space:nowrap;z-index:9}
  #toast{position:fixed;left:50%;bottom:26px;transform:translateX(-50%) translateY(24px);background:#333;color:#fff;padding:12px 20px;border-radius:12px;font-size:14px;font-weight:700;opacity:0;pointer-events:none;transition:.28s;z-index:50}
  #toast.on{opacity:1;transform:translateX(-50%) translateY(0)}
  .spin{opacity:.5;font-size:13px;padding:20px}
</style>
</head>
<body>
<div class="topbar"><a href="/">← карта префектур</a><span id="acct"></span></div>
<div class="wrap">
  <h1>KEIKENCHI · УРОВЕНЬ ПО ГОРОДАМ</h1>
  <div class="crumb" id="crumb">🗾 Япония</div>
  <div class="score" id="score">0 / 0</div>
  <div class="count" id="cnt"></div>
  <div class="layout">
    <div class="legend" id="legend"></div>
    <div class="mapbox">
      <svg id="map" xmlns="http://www.w3.org/2000/svg"><g id="vp"></g></svg>
      <div class="zoombtns">
        <button id="zin">+</button><button id="zout">−</button><button id="zfit">⤢</button>
      </div>
    </div>
  </div>
  <div class="hint" id="hint">Клик по префектуре — открыть её города. Префектуры подсвечены по доле отмеченных городов.</div>
</div>
<div id="tip"></div><div id="toast"></div>
<script>
const PREF=__PREF__, IDX=__IDX__;
const RAW={0:'#ffffff',1:'#8fc7f0',2:'#7fd6a8',3:'#f5cf51',4:'#ee7f5f',5:'#f2a9cf'};
const LEG=[[5,'Resided','Жил там'],[4,'Stayed','Ночевал'],[3,'Visited','Гулял'],[2,'Landed','Заезжал'],[1,'Passed','Проездом'],[0,'Unexplored','Не был']];
let brush=4, cities={}, account=null, view='over', curPref=null, curCities=[], pushT=null;
try{cities=JSON.parse(localStorage.getItem('keikenchi_cities')||'{}')||{};}catch{}

const W=560,H=580,PAD=10;
const merc=(lo,la)=>[lo,Math.log(Math.tan(Math.PI/4+la*Math.PI/360))*180/Math.PI];
const NS='http://www.w3.org/2000/svg';
const svg=document.getElementById('map'),vp=document.getElementById('vp');
svg.setAttribute('viewBox',`0 0 ${W} ${H}`);
const tip=document.getElementById('tip');
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

// ---- robust fit: bbox from the main cluster (median ± 3·IQR of centroids), far islands excluded ----
function centroidOf(it){let sx=0,sy=0,n=0;for(const [lo,la] of it.poly[0]){const[x,y]=merc(lo,la);sx+=x;sy+=y;n++;}return[sx/n,sy/n];}
function projector(items){
  const cen=items.map(centroidOf);
  const q=(arr,p)=>{const a=[...arr].sort((x,y)=>x-y);return a[Math.floor((a.length-1)*p)];};
  const xs=cen.map(c=>c[0]),ys=cen.map(c=>c[1]);
  const mx=q(xs,.5),my=q(ys,.5);
  const iqrx=Math.max(q(xs,.75)-q(xs,.25),1e-4),iqry=Math.max(q(ys,.75)-q(ys,.25),1e-4);
  let a=1e9,b=1e9,c=-1e9,d=-1e9,used=0;
  items.forEach((it,i)=>{
    if(Math.abs(cen[i][0]-mx)>3*iqrx || Math.abs(cen[i][1]-my)>3*iqry) return;
    used++;for(const r of it.poly)for(const [lo,la] of r){const[x,y]=merc(lo,la);if(x<a)a=x;if(x>c)c=x;if(y<b)b=y;if(y>d)d=y;}
  });
  if(!used){for(const it of items)for(const r of it.poly)for(const [lo,la] of r){const[x,y]=merc(lo,la);if(x<a)a=x;if(x>c)c=x;if(y<b)b=y;if(y>d)d=y;}}
  const s=Math.min((W-2*PAD)/(c-a||1),(H-2*PAD)/(d-b||1));
  const ox=PAD+((W-2*PAD)-(c-a)*s)/2, oy=PAD+((H-2*PAD)-(d-b)*s)/2;
  return (lo,la)=>{const[x,y]=merc(lo,la);return[ox+(x-a)*s,oy+(d-y)*s];};
}
function pathD(poly,proj){let s='';for(const r of poly)s+='M'+r.map(([lo,la])=>{const[x,y]=proj(lo,la);return x.toFixed(1)+' '+y.toFixed(1);}).join('L')+'Z';return s;}

// ---- completion tint for a prefecture ----
function lerpHex(h1,h2,t){const a=parseInt(h1.slice(1),16),b=parseInt(h2.slice(1),16);const r=x=>x>>16&255,g=x=>x>>8&255,bl=x=>x&255;const m=(p,q)=>Math.round(p+(q-p)*t);return `rgb(${m(r(a),r(b))},${m(g(a),g(b))},${m(bl(a),bl(b))})`;}
function prefRatio(id){const info=IDX[id];if(!info||!info.n)return null;let done=0;/* count cities of this pref marked */for(const code in cities){if(code.slice(0,2)===String(id).padStart(2,'0'))done++;}return done/info.n;}

// ================= OVERVIEW =================
function renderOverview(){
  view='over';curPref=null;
  document.getElementById('crumb').innerHTML='🗾 Япония';
  document.getElementById('hint').textContent='Клик по префектуре — открыть её города. Подсветка = доля отмеченных городов.';
  vp.innerHTML='';k=1;tx=0;ty=0;apply();
  const proj=projector(PREF);
  let totDone=0,totAll=0;
  for(const p of PREF){
    const path=document.createElementNS(NS,'path');
    path.setAttribute('d',pathD(p.poly,proj));path.setAttribute('class','reg');path.setAttribute('stroke-width','.6');
    const info=IDX[p.id];const r=prefRatio(p.id);
    path.style.fill = (r==null)?'#eee' : (r===0?'#ffffff':lerpHex('#ffe7d8','#ee7f5f',Math.min(1,r)));
    if(info){totAll+=info.n;}
    for(const code in cities){if(code.slice(0,2)===String(p.id).padStart(2,'0'))totDone++;}
    path.addEventListener('mousemove',e=>{const rr=prefRatio(p.id);const info=IDX[p.id];tip.textContent=info?`${p.r} — ${Math.round((rr||0)*info.n)}/${info.n} городов`:`${p.r} — нет данных`;tip.style.left=(e.clientX+12)+'px';tip.style.top=(e.clientY+12)+'px';tip.style.opacity=1;});
    path.addEventListener('mouseleave',()=>tip.style.opacity=0);
    path.addEventListener('click',()=>{if(IDX[p.id])openPref(p.id);else toast('данные городов этой префектуры ещё не загружены');});
    vp.appendChild(path);
  }
  document.getElementById('score').textContent=totDone+' / '+totAll;
  document.getElementById('cnt').textContent='городов отмечено по всей Японии';
  renderLegend(false);
}

// ================= PREFECTURE DETAIL =================
async function openPref(id){
  view='detail';curPref=id;tip.style.opacity=0;
  document.getElementById('crumb').innerHTML='<a id="back">🗾 Япония</a> › '+(PREF.find(p=>p.id===id)||{}).r;
  document.getElementById('back').onclick=renderOverview;
  document.getElementById('hint').textContent='Клик по городу — отметить уровнем слева. Колесо/пинч — зум, тяни — двигать.';
  vp.innerHTML='<text x="'+(W/2)+'" y="'+(H/2)+'" text-anchor="middle" class="spin">загрузка городов…</text>';
  let geo;
  try{geo=await (await fetch('/geo/'+id+'.json')).json();}catch{vp.innerHTML='';toast('не удалось загрузить города');return;}
  curCities=geo.cities;
  vp.innerHTML='';k=1;tx=0;ty=0;apply();
  const proj=projector(geo.cities);
  for(const c of geo.cities){
    const path=document.createElementNS(NS,'path');
    path.setAttribute('d',pathD(c.poly,proj));path.setAttribute('class','reg');path.setAttribute('stroke-width','.5');
    path.style.fill=RAW[cities[c.code]||0];path.dataset.code=c.code;path._c=c;
    path.addEventListener('mousemove',e=>{tip.textContent=`${c.name} · ${cities[c.code]||0}`;tip.style.left=(e.clientX+12)+'px';tip.style.top=(e.clientY+12)+'px';tip.style.opacity=1;});
    path.addEventListener('mouseleave',()=>tip.style.opacity=0);
    vp.appendChild(path);
  }
  renderLegend(true);
  updatePrefStats();
}
function updatePrefStats(){
  if(view!=='detail')return;
  let done=0,sum=0;for(const c of curCities){const v=cities[c.code]||0;if(v>0)done++;sum+=v;}
  document.getElementById('score').textContent=done+' / '+curCities.length;
  document.getElementById('cnt').textContent='городов · '+sum+' pts в этой префектуре';
}
function paintCity(code){const el=vp.querySelector(`path[data-code="${code}"]`);if(el)el.style.fill=RAW[cities[code]||0];}
function setCity(code){const cur=cities[code]||0;cities[code]=(cur===brush)?0:brush;if(!cities[code])delete cities[code];paintCity(code);updatePrefStats();saveCities();}

// ---- legend ----
function renderLegend(on){
  const el=document.getElementById('legend');el.innerHTML='<h3>Score</h3>';
  for(const [n,en,ru] of LEG){const div=document.createElement('div');div.className='lg';div.dataset.n=n;
    div.innerHTML=`<span class="dot" style="background:${RAW[n]}">${n}</span><b>${en}</b><span>${ru}</span>`;
    div.onclick=()=>{brush=n;document.querySelectorAll('.lg').forEach(l=>l.classList.toggle('active',+l.dataset.n===brush));};
    el.appendChild(div);}
  document.querySelectorAll('.lg').forEach(l=>l.classList.toggle('active',+l.dataset.n===brush));
  el.style.visibility=on?'visible':'hidden';
}

// ---- persistence + account ----
function saveCities(){localStorage.setItem('keikenchi_cities',JSON.stringify(cities));if(account)scheduleMe();if(view==='over')renderOverview();}
function scheduleMe(){clearTimeout(pushT);pushT=setTimeout(async()=>{try{await fetch('/api/me',{method:'PUT',headers:{'content-type':'application/json'},body:JSON.stringify({extra:{cities}})});}catch{}} ,1200);}
async function loadAccount(){
  try{const r=await fetch('/api/me');if(r.status!==200)return;const j=await r.json();account={username:j.user.username};
    document.getElementById('acct').textContent='👤 '+j.user.username;
    let ex={};try{ex=JSON.parse(j.map&&j.map.extra||'{}')||{};}catch{}
    if(ex.cities){cities={...ex.cities,...cities};localStorage.setItem('keikenchi_cities',JSON.stringify(cities));}
  }catch{}
}

// ---- toast ----
let tq=[],tb=false;
function toast(m){tq.push(m);if(!tb)nt();}
function nt(){const el=document.getElementById('toast');if(!tq.length){tb=false;return;}tb=true;el.textContent=tq.shift();el.classList.add('on');setTimeout(()=>{el.classList.remove('on');setTimeout(nt,300);},2000);}

// ================= ZOOM / PAN (shared) =================
let k=1,tx=0,ty=0;const K_MIN=1,K_MAX=40;
const apply=()=>vp.setAttribute('transform',`translate(${tx} ${ty}) scale(${k})`);
const toVB=(cx,cy)=>{const r=svg.getBoundingClientRect();return[(cx-r.left)/r.width*W,(cy-r.top)/r.height*H];};
function zoomAt(vx,vy,nk){nk=Math.max(K_MIN,Math.min(K_MAX,nk));const wx=(vx-tx)/k,wy=(vy-ty)/k;k=nk;tx=vx-wx*k;ty=vy-wy*k;clamp();apply();}
function clamp(){const mnx=W-W*k;if(tx>0)tx=0;if(tx<mnx)tx=mnx;const mny=H-H*k;if(ty>0)ty=0;if(ty<mny)ty=mny;if(k<=1){tx=0;ty=0;}}
svg.addEventListener('wheel',e=>{e.preventDefault();const[vx,vy]=toVB(e.clientX,e.clientY);zoomAt(vx,vy,k*(e.deltaY<0?1.15:1/1.15));},{passive:false});
const pts=new Map();let moved=false,downT=0,pinchD=0,pinchMid=[0,0],downEl=null;
svg.addEventListener('pointerdown',e=>{downEl=e.target.closest&&e.target.closest('path.reg');svg.setPointerCapture(e.pointerId);pts.set(e.pointerId,[e.clientX,e.clientY]);moved=false;downT=Date.now();if(pts.size===2){const p=[...pts.values()];pinchD=Math.hypot(p[0][0]-p[1][0],p[0][1]-p[1][1]);pinchMid=toVB((p[0][0]+p[1][0])/2,(p[0][1]+p[1][1])/2);}});
svg.addEventListener('pointermove',e=>{if(!pts.has(e.pointerId))return;const prev=pts.get(e.pointerId);pts.set(e.pointerId,[e.clientX,e.clientY]);
  if(pts.size===2){const p=[...pts.values()];const nd=Math.hypot(p[0][0]-p[1][0],p[0][1]-p[1][1]);if(pinchD>0){const[vx,vy]=pinchMid;zoomAt(vx,vy,k*nd/pinchD);}pinchD=nd;moved=true;}
  else if(pts.size===1){const r=svg.getBoundingClientRect();const dx=(e.clientX-prev[0])/r.width*W,dy=(e.clientY-prev[1])/r.height*H;if(Math.abs(e.clientX-prev[0])+Math.abs(e.clientY-prev[1])>2)moved=true;tx+=dx;ty+=dy;clamp();apply();}});
function up(e){const quick=Date.now()-downT<400;pts.delete(e.pointerId);if(pts.size<2)pinchD=0;
  if(downEl&&!moved&&quick&&pts.size===0){const code=downEl.dataset.code;if(view==='detail'&&code)setCity(code);}
  downEl=null;}
svg.addEventListener('pointerup',up);
svg.addEventListener('pointercancel',e=>{pts.delete(e.pointerId);if(pts.size<2)pinchD=0;});
document.getElementById('zin').onclick=()=>zoomAt(W/2,H/2,k*1.4);
document.getElementById('zout').onclick=()=>zoomAt(W/2,H/2,k/1.4);
document.getElementById('zfit').onclick=()=>{k=1;tx=0;ty=0;apply();};

// ---- boot ----
(async()=>{ await loadAccount(); renderOverview(); })();
</script>
</body>
</html>'''

HTML = HTML.replace('__PREF__', PREF).replace('__IDX__', IDX)
open('public/cities.html', 'w').write(HTML)
print('public/cities.html', round(os.path.getsize('public/cities.html')/1024, 1), 'KB | prefectures with city data:', len(idx))
