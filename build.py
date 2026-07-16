import json,re,os
d=json.load(open('japan.min.json'))
for x in d: x['r']=re.sub(r'\s+(Ken|Do|Fu|To)$','',x['en']).strip()
data=json.dumps(d,separators=(',',':'),ensure_ascii=False)

html = r'''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>Keikenchi — Japan Lifetime Score</title>
<meta name="description" content="Отметь посещённые префектуры Японии и меряйся баллами с друзьями. Карта, баллы 0–5, счётчик визитов, ачивки, комнаты-лидерборды.">
<meta property="og:type" content="website">
<meta property="og:title" content="Keikenchi — Japan Lifetime Score">
<meta property="og:description" content="Отметь посещённые префектуры Японии и меряйся баллами с друзьями.">
<meta property="og:image" content="https://keikenchi-sca.pages.dev/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:url" content="https://keikenchi-sca.pages.dev/">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Keikenchi — Japan Lifetime Score">
<meta name="twitter:image" content="https://keikenchi-sca.pages.dev/og.png">
<style>
  :root{--bg:#f6efe1;--ink:#333;--line:#3a3a3a}
  *{box-sizing:border-box}
  html,body{margin:0;height:100%}
  body{background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Hiragino Sans","Noto Sans JP",sans-serif;-webkit-tap-highlight-color:transparent}
  .wrap{max-width:760px;margin:0 auto;padding:16px 12px 60px;text-align:center}
  h1{font-size:15px;letter-spacing:.06em;margin:6px 0 2px;font-weight:700}
  .score{display:inline-block;background:#fbe6a8;border-radius:12px;padding:12px 40px;font-size:30px;font-weight:800;min-width:180px}
  .count{font-size:12px;color:#8a7f6a;margin-top:4px}
  .layout{display:flex;gap:14px;align-items:flex-start;justify-content:center;margin-top:14px;flex-wrap:wrap}
  .legend{text-align:left;font-size:12px}
  .legend h3{font-size:13px;margin:0 0 8px}
  .lg{display:flex;align-items:center;gap:8px;padding:5px 8px;border-radius:8px;cursor:pointer;border:2px solid transparent;user-select:none}
  .lg.active{border-color:var(--line);background:#fff8}
  .dot{width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;border:2px solid var(--line);font-size:13px;flex:0 0 auto}
  .lg b{min-width:56px;display:inline-block}
  .lg span{color:#8a7f6a}
  .mapbox{position:relative;flex:1 1 320px;max-width:520px}
  svg{width:100%;height:auto;display:block;touch-action:none;background:transparent;border-radius:10px}
  path.pref{stroke:var(--line);stroke-width:.6;stroke-linejoin:round;cursor:pointer;transition:fill .12s}
  path.pref:hover{stroke-width:1.4}
  .zoombtns{position:absolute;right:8px;bottom:8px;display:flex;flex-direction:column;gap:6px}
  .zoombtns button{width:34px;height:34px;padding:0;font-size:18px;border-radius:8px;border:2px solid var(--line);background:#fff;cursor:pointer;font-weight:700;line-height:1}
  .bar{display:flex;gap:8px;justify-content:center;margin-top:16px;flex-wrap:wrap}
  .bar button{font:inherit;font-size:13px;padding:9px 16px;border-radius:10px;border:2px solid var(--line);background:#fff;cursor:pointer;font-weight:600}
  button:active{transform:translateY(1px)}
  #tip{position:fixed;pointer-events:none;background:#333;color:#fff;font-size:12px;padding:4px 8px;border-radius:6px;opacity:0;transition:opacity .1s;white-space:nowrap;z-index:9}
  .hint{font-size:12px;color:#8a7f6a;margin-top:8px}
  text.badge{font:700 11px -apple-system,sans-serif;fill:#222;paint-order:stroke;stroke:#fff;stroke-width:3px;text-anchor:middle;dominant-baseline:central;pointer-events:none}
  text.plabel{font:600 8px -apple-system,"Hiragino Sans",sans-serif;fill:#2a2a2a;paint-order:stroke;stroke:#fff;stroke-width:2.4px;text-anchor:middle;dominant-baseline:central;pointer-events:none}
  #plabels{display:none}
  #plabels.on{display:block}
  #pop .memo{margin-top:8px;width:190px;height:46px;font:inherit;font-size:12px;padding:5px 7px;border:2px solid #ddd;border-radius:8px;resize:none;display:block}
  .bar button.on{background:#fbe6a8}
  .cloud{display:flex;gap:8px;justify-content:center;align-items:center;margin-top:14px;flex-wrap:wrap}
  .cloud input,.rooms input{font:inherit;font-size:13px;padding:8px 10px;border:2px solid var(--line);border-radius:10px;width:150px}
  .cloud button,.rooms button{font:inherit;font-size:13px;padding:8px 14px;border-radius:10px;border:2px solid var(--line);background:#fff;cursor:pointer;font-weight:600}
  .cloud button#cloudsave{background:#cfe9ff}
  #cloudlink{font-size:12px;color:#8a7f6a}
  #cloudlink a{color:#2a6fb0}
  .rooms{display:flex;gap:8px;justify-content:center;align-items:center;margin-top:10px;flex-wrap:wrap}
  .mini{font-size:11px!important;padding:3px 8px!important;border-radius:7px!important}
  #board{max-width:420px;margin:16px auto 0;text-align:left}
  .btitle{font-size:13px;font-weight:700;margin-bottom:8px;display:flex;gap:8px;align-items:center;flex-wrap:wrap}
  .btitle code{background:#eee;padding:1px 6px;border-radius:5px}
  .brow{display:flex;align-items:center;gap:10px;padding:7px 10px;border:2px solid #eee;border-radius:10px;margin-bottom:5px;font-size:14px}
  .brow.me{border-color:var(--line);background:#fff8e0}
  .brow>b{width:20px;color:#8a7f6a}
  .brow .bn{flex:1;font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .brow a{font-size:12px;color:#2a6fb0}
  .brow .bs{font-weight:800;min-width:44px;text-align:right}
  #viewbanner{display:none;max-width:520px;margin:12px auto 0;padding:9px 12px;background:#fff3d6;border:2px solid var(--line);border-radius:10px;font-size:13px;text-align:center}
  #viewbanner.on{display:block}
  #ach{max-width:520px;margin:22px auto 0;text-align:left}
  #ach h3{font-size:13px;margin:0 0 10px}
  .achgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px}
  .achip{display:flex;gap:9px;align-items:center;padding:8px 10px;border:2px solid #eee;border-radius:10px;opacity:.45;filter:grayscale(1);transition:.2s}
  .achip.on{opacity:1;filter:none;border-color:var(--line);background:#fff}
  .achip .ae{font-size:22px;line-height:1}
  .achip b{display:block;font-size:12px}
  .achip small{color:#8a7f6a;font-size:11px}
  #toast{position:fixed;left:50%;bottom:26px;transform:translateX(-50%) translateY(24px);background:#333;color:#fff;padding:12px 20px;border-radius:12px;font-size:14px;font-weight:700;opacity:0;pointer-events:none;transition:.28s;z-index:50;box-shadow:0 8px 24px #0004}
  #toast.on{opacity:1;transform:translateX(-50%) translateY(0)}
  #acctbar{position:fixed;top:10px;right:12px;z-index:30;display:flex;gap:6px}
  #acctbar button{font:inherit;font-size:12px;font-weight:600;padding:6px 12px;border-radius:9px;border:2px solid var(--line);background:#fff;cursor:pointer}
  #acctbar .who{background:#fff8e0}
  #authmodal{position:fixed;inset:0;background:#0006;display:none;align-items:center;justify-content:center;z-index:60}
  #authmodal.on{display:flex}
  .authcard{background:#fff;border:2px solid var(--line);border-radius:16px;padding:22px;width:300px;text-align:center;position:relative}
  .authcard h3{margin:0 0 12px;font-size:17px}
  .authcard input{display:block;width:100%;font:inherit;font-size:14px;padding:10px 12px;border:2px solid var(--line);border-radius:10px;margin-bottom:10px}
  .authcard .go{width:100%;font:inherit;font-size:14px;font-weight:700;padding:11px;border-radius:10px;border:2px solid var(--line);background:#cfe9ff;cursor:pointer;margin-bottom:10px}
  .authcard .toggle{font-size:12px;color:#2a6fb0;cursor:pointer;background:none;border:none;display:block;margin:4px auto}
  .autherr{color:#c0392b;font-size:12px;min-height:16px;margin-bottom:6px}
  #history{max-width:520px;margin:20px auto 0;text-align:left}
  #history h3{font-size:13px;margin:0 0 10px}
  .hrow{display:flex;gap:10px;align-items:center;padding:8px 10px;border:2px solid #eee;border-radius:10px;margin-bottom:5px;font-size:13px}
  .hrow .hd{width:13px;height:13px;border-radius:50%;border:2px solid var(--line);flex:0 0 auto}
  .hrow .hn{font-weight:600}
  .hrow .hmemo{color:#555;font-size:11px;font-style:italic}
  .hrow .hmeta{color:#8a7f6a;font-size:11px;margin-left:auto;text-align:right;white-space:nowrap}
  #viewbanner button{font:inherit;font-size:12px;font-weight:700;margin-left:8px;padding:4px 10px;border-radius:8px;border:2px solid var(--line);background:#fff;cursor:pointer}
  #pop{position:fixed;z-index:20;background:#fff;border:2px solid var(--line);border-radius:12px;padding:9px 11px;box-shadow:0 8px 24px #0003;display:none}
  #pop .name{font-size:12px;font-weight:700;margin-bottom:7px;white-space:nowrap}
  #pop .stp{display:flex;align-items:center;gap:12px;justify-content:center}
  #pop .stp button{width:32px;height:32px;border-radius:8px;border:2px solid var(--line);background:#fff;font-size:18px;font-weight:700;cursor:pointer;line-height:1}
  #pop .n{font-size:19px;font-weight:800;min-width:26px;text-align:center}
  #pop .lbl{font-size:11px;color:#8a7f6a;margin-top:5px;text-align:center}
</style>
</head>
<body>
<div id="acctbar"></div>
<div class="wrap">
  <h1>ALL JAPAN KEIKENCHI</h1>
  <div class="score" id="total">0 pts</div>
  <div class="count" id="pct">0 / 47 префектур</div>

  <div class="layout">
    <div class="legend" id="legend"></div>
    <div class="mapbox">
      <svg id="map" xmlns="http://www.w3.org/2000/svg"><g id="vp"></g></svg>
      <div class="zoombtns">
        <button id="zin" title="Приблизить">+</button>
        <button id="zout" title="Отдалить">−</button>
        <button id="zfit" title="Сброс зума" style="font-size:13px">⤢</button>
      </div>
    </div>
  </div>

  <div class="hint">Уровень слева → клик красит балл. Правый клик / долгий тап — счётчик визитов (был неоднократно). Колесо/пинч — зум, тяни — двигать.</div>
  <div class="bar">
    <button id="labels">Названия</button>
    <button id="png">Скачать PNG</button>
    <button id="share">Поделиться ссылкой</button>
    <button id="reset">Сбросить</button>
  </div>

  <div id="viewbanner"></div>

  <div class="cloud">
    <input id="uname" maxlength="40" placeholder="твоё имя">
    <button id="cloudsave">☁ Сохранить в облако</button>
    <span id="cloudlink"></span>
  </div>
  <div class="rooms">
    <button id="roomnew">Создать комнату</button>
    <input id="roomid" maxlength="12" placeholder="код комнаты">
    <button id="roomjoin">Войти</button>
  </div>
  <div id="board"></div>
  <div id="history"></div>
  <div id="ach"></div>
</div>
<div id="toast"></div>
<div id="authmodal"><div class="authcard">
  <h3 id="authtitle">Вход</h3>
  <div class="autherr" id="autherr"></div>
  <input id="authuser" placeholder="ник" maxlength="20" autocomplete="username">
  <input id="authpass" type="password" placeholder="пароль" autocomplete="current-password">
  <button class="go" id="authgo">Войти</button>
  <button class="toggle" id="authtoggle">Нет аккаунта? Регистрация</button>
  <button class="toggle" id="authcancel">закрыть</button>
</div></div>
<div id="tip"></div>
<div id="pop">
  <div class="name"></div>
  <div class="stp"><button id="pmin">−</button><span class="n">0</span><button id="pplus">+</button></div>
  <div class="lbl">визитов</div>
  <textarea class="memo" placeholder="заметка: цель, отель, что видел…"></textarea>
</div>

<script>
const PREF = __DATA__;
const RAW = {0:'#ffffff',1:'#8fc7f0',2:'#7fd6a8',3:'#f5cf51',4:'#ee7f5f',5:'#f2a9cf'};
const LEG = [[5,'Resided','Жил там'],[4,'Stayed','Ночевал'],[3,'Visited','Гулял'],[2,'Landed','Заезжал'],[1,'Passed','Проездом'],[0,'Unexplored','Не был']];
let brush=4, state={}, cnt={}, memo={}, dates={};
const byId={};

// ---- projection (Okinawa lifted into a top-left inset so main islands fill the frame) ----
const W=520,H=560,PAD=8;
const OKI=47; // Okinawa prefecture id
const merc=(lo,la)=>[lo, Math.log(Math.tan(Math.PI/4+la*Math.PI/360))*180/Math.PI];
function bbox(feats){let a=1e9,b=1e9,c=-1e9,d=-1e9;for(const p of feats)for(const r of p.poly)for(const [lo,la] of r){const[x,y]=merc(lo,la);if(x<a)a=x;if(x>c)c=x;if(y<b)b=y;if(y>d)d=y;}return[a,b,c,d];}
const mainF=PREF.filter(p=>p.id!==OKI), okiF=PREF.filter(p=>p.id===OKI);
const [aX,aY,cX,dY]=bbox(mainF);
const sMain=Math.min((W-2*PAD)/(cX-aX),(H-2*PAD)/(dY-aY));
const offX=PAD+((W-2*PAD)-(cX-aX)*sMain)/2;               // center horizontally in leftover space
const projMain=(lo,la)=>{const[x,y]=merc(lo,la);return[offX+(x-aX)*sMain,PAD+(dY-y)*sMain];};
// Okinawa inset box (top-left)
const IB={x:6,y:150,w:120,h:128};
const [oX,oY,ocX,odY]=okiF.length?bbox(okiF):[0,0,1,1];
const sOki=Math.min(IB.w/((ocX-oX)||1),IB.h/((odY-oY)||1));
const projOki=(lo,la)=>{const[x,y]=merc(lo,la);return[IB.x+(x-oX)*sOki,IB.y+(odY-y)*sOki];};
const projFor=p=>(p.id===OKI?projOki:projMain);

// ---- render ----
const NS='http://www.w3.org/2000/svg';
const svg=document.getElementById('map'), vp=document.getElementById('vp');
svg.setAttribute('viewBox',`0 0 ${W} ${H}`);
const badges=document.createElementNS(NS,'g'); const badgeEl={};
function centroid(p){const pj=projFor(p);let sx=0,sy=0,n=0;for(const [lo,la] of p.poly[0]){const[x,y]=pj(lo,la);sx+=x;sy+=y;n++;}return[sx/n,sy/n];}
// Okinawa inset frame (dashed box + small label) — drawn under the paths
const frame=document.createElementNS(NS,'rect');frame.setAttribute('x',IB.x-2);frame.setAttribute('y',IB.y-14);frame.setAttribute('width',IB.w+4);frame.setAttribute('height',IB.h+18);frame.setAttribute('rx',8);frame.setAttribute('fill','none');frame.setAttribute('stroke','#c9bfa8');frame.setAttribute('stroke-width','1');frame.setAttribute('stroke-dasharray','4 3');vp.appendChild(frame);
const flab=document.createElementNS(NS,'text');flab.setAttribute('x',IB.x+2);flab.setAttribute('y',IB.y-4);flab.setAttribute('font-size','9');flab.setAttribute('fill','#8a7f6a');flab.setAttribute('font-weight','700');flab.textContent='沖縄 Okinawa';vp.appendChild(flab);
for(const p of PREF){
  byId[p.id]=p;
  const pj=projFor(p);
  let d='';
  for(const r of p.poly) d+='M'+r.map(([lo,la])=>{const[x,y]=pj(lo,la);return x.toFixed(1)+' '+y.toFixed(1);}).join('L')+'Z';
  const path=document.createElementNS(NS,'path');
  path.setAttribute('d',d); path.setAttribute('class','pref'); path.dataset.id=p.id;
  path.addEventListener('mousemove',e=>showTip(e,p));
  path.addEventListener('mouseleave',hideTip);
  path._pref=p;
  vp.appendChild(path);
  const [cx,cy]=centroid(p);
  const t=document.createElementNS(NS,'text'); t.setAttribute('class','badge'); t.setAttribute('x',cx.toFixed(1)); t.setAttribute('y',cy.toFixed(1));
  badges.appendChild(t); badgeEl[p.id]=t;
}
vp.appendChild(badges);
const labels=document.createElementNS(NS,'g'); labels.id='plabels'; vp.appendChild(labels);
const shortJa=j=>j.replace(/[県都府道]$/,'');
for(const p of PREF){const [cx,cy]=centroid(p);const t=document.createElementNS(NS,'text');t.setAttribute('class','plabel');t.setAttribute('x',cx.toFixed(1));t.setAttribute('y',(cy+9).toFixed(1));t.textContent=shortJa(p.ja);labels.appendChild(t);}
function updateBadge(id){const c=cnt[id]||0; badgeEl[id].textContent = c>=2 ? '×'+c : (memo[id]?'·':'');}
function updateAllBadges(){for(const p of PREF)updateBadge(p.id);}

// ---- legend ----
const legEl=document.getElementById('legend'); legEl.innerHTML='<h3>Score</h3>';
for(const [n,en,ru] of LEG){
  const div=document.createElement('div'); div.className='lg'; div.dataset.n=n;
  div.innerHTML=`<span class="dot" style="background:${RAW[n]}">${n}</span><b>${en}</b><span>${ru}</span>`;
  div.onclick=()=>{brush=n;syncLegend();};
  legEl.appendChild(div);
}
const syncLegend=()=>document.querySelectorAll('.lg').forEach(l=>l.classList.toggle('active',+l.dataset.n===brush));

// ---- score logic ----
function toggle(id){const c=state[id]||0;state[id]=(c===brush)?0:brush;if(!state[id])delete state[id];else if(!dates[id])dates[id]=Date.now();paint(id);recalc();save();}
function paint(id){const el=vp.querySelector(`path[data-id="${id}"]`);el.style.fill=RAW[state[id]||0];}
function paintAll(){for(const p of PREF)paint(p.id);}
function recalc(){let sum=0,cn=0;for(const k in state){sum+=state[k];if(state[k]>0)cn++;}let vis=0;for(const k in cnt)vis+=cnt[k];document.getElementById('total').textContent=sum+' pts';document.getElementById('pct').textContent=cn+' / 47 префектур'+(vis?` · ${vis} визитов`:'');if(typeof checkAch==='function')checkAch();if(typeof renderHistory==='function')renderHistory();}

// ---- tooltip ----
const tip=document.getElementById('tip');
function showTip(e,p){const m=memo[p.id]?' — '+memo[p.id].slice(0,40):'';tip.textContent=`${p.r} ${p.ja} · ${state[p.id]||0}${m}`;tip.style.left=(e.clientX+12)+'px';tip.style.top=(e.clientY+12)+'px';tip.style.opacity=1;}
function hideTip(){tip.style.opacity=0;}

// ---- visit-count popup ----
const pop=document.getElementById('pop'); let popId=null;
function openPop(id,cx,cy){popId=id;const p=byId[id];pop.querySelector('.name').textContent=p.r+' '+p.ja;pop.querySelector('.n').textContent=cnt[id]||0;pop.querySelector('.memo').value=memo[id]||'';pop.style.display='block';const w=pop.offsetWidth||210;pop.style.left=Math.max(6,Math.min(cx-w/2,innerWidth-w-6))+'px';pop.style.top=Math.min(cy+10,innerHeight-160)+'px';}
function closePop(){pop.style.display='none';popId=null;}
function bump(delta){if(popId==null)return;const v=Math.max(0,(cnt[popId]||0)+delta);if(v)cnt[popId]=v;else delete cnt[popId];pop.querySelector('.n').textContent=cnt[popId]||0;updateBadge(popId);recalc();save();}
pop.querySelector('.memo').addEventListener('input',e=>{if(popId==null)return;const v=e.target.value;if(v.trim())memo[popId]=v;else delete memo[popId];updateBadge(popId);save();});
document.getElementById('pplus').onclick=()=>bump(1);
document.getElementById('pmin').onclick=()=>bump(-1);
document.addEventListener('pointerdown',e=>{if(pop.style.display==='block'&&!pop.contains(e.target))closePop();},false);
svg.addEventListener('contextmenu',e=>{const pa=e.target.closest&&e.target.closest('path.pref');if(pa){e.preventDefault();openPop(pa._pref.id,e.clientX,e.clientY);}});

// ---- ZOOM / PAN ----
let k=1,tx=0,ty=0;
const K_MIN=1,K_MAX=14;
const apply=()=>vp.setAttribute('transform',`translate(${tx} ${ty}) scale(${k})`);
const toVB=(cx,cy)=>{const r=svg.getBoundingClientRect();return[(cx-r.left)/r.width*W,(cy-r.top)/r.height*H];};
function zoomAt(vx,vy,nk){
  nk=Math.max(K_MIN,Math.min(K_MAX,nk));
  const wx=(vx-tx)/k, wy=(vy-ty)/k;       // world point under cursor
  k=nk; tx=vx-wx*k; ty=vy-wy*k; clamp(); apply();
}
function clamp(){ // keep map within frame
  const min=W-W*k; if(tx>0)tx=0; if(tx<min)tx=min;
  const minY2=H-H*k; if(ty>0)ty=0; if(ty<minY2)ty=minY2;
  if(k<=1){tx=0;ty=0;}
}
// wheel
svg.addEventListener('wheel',e=>{e.preventDefault();const[vx,vy]=toVB(e.clientX,e.clientY);zoomAt(vx,vy,k*(e.deltaY<0?1.15:1/1.15));},{passive:false});
// pointer pan + pinch + click
const pts=new Map(); let moved=false,downT=0,pinchD=0,pinchMid=[0,0],downPath=null,lpTimer=null,lpFired=false;
svg.addEventListener('pointerdown',e=>{downPath=e.target.closest&&e.target.closest('path.pref');svg.setPointerCapture(e.pointerId);pts.set(e.pointerId,[e.clientX,e.clientY]);moved=false;lpFired=false;downT=Date.now();clearTimeout(lpTimer);if(pts.size===1&&downPath){const id=downPath._pref.id,cx=e.clientX,cy=e.clientY;lpTimer=setTimeout(()=>{if(!moved){lpFired=true;openPop(id,cx,cy);}},450);}if(pts.size===2){clearTimeout(lpTimer);const p=[...pts.values()];pinchD=Math.hypot(p[0][0]-p[1][0],p[0][1]-p[1][1]);pinchMid=toVB((p[0][0]+p[1][0])/2,(p[0][1]+p[1][1])/2);}});
svg.addEventListener('pointermove',e=>{
  if(!pts.has(e.pointerId))return;
  const prev=pts.get(e.pointerId); pts.set(e.pointerId,[e.clientX,e.clientY]);
  if(pts.size===2){
    const p=[...pts.values()]; const nd=Math.hypot(p[0][0]-p[1][0],p[0][1]-p[1][1]);
    if(pinchD>0){const[vx,vy]=pinchMid;zoomAt(vx,vy,k*nd/pinchD);} pinchD=nd; moved=true;
  }else if(pts.size===1){
    const r=svg.getBoundingClientRect();
    const dx=(e.clientX-prev[0])/r.width*W, dy=(e.clientY-prev[1])/r.height*H;
    if(Math.abs(e.clientX-prev[0])+Math.abs(e.clientY-prev[1])>2){moved=true;clearTimeout(lpTimer);}
    tx+=dx; ty+=dy; clamp(); apply();
  }
});
function up(e){
  clearTimeout(lpTimer);
  const quick=Date.now()-downT<400;
  pts.delete(e.pointerId); if(pts.size<2)pinchD=0;
  if(downPath && !moved && quick && !lpFired && pts.size===0) toggle(downPath._pref.id);
  downPath=null;
}
svg.addEventListener('pointerup',up);
svg.addEventListener('pointercancel',e=>{pts.delete(e.pointerId);if(pts.size<2)pinchD=0;});
// buttons
const center=()=>[W/2,H/2];
document.getElementById('zin').onclick=()=>zoomAt(...center(),k*1.4);
document.getElementById('zout').onclick=()=>zoomAt(...center(),k/1.4);
document.getElementById('zfit').onclick=()=>{k=1;tx=0;ty=0;apply();};

// ---- persistence + share ----
const encode=()=>{const sc=PREF.map(p=>state[p.id]||0).join('');return PREF.some(p=>cnt[p.id])? sc+'-'+PREF.map(p=>Math.min(35,cnt[p.id]||0).toString(36)).join('') : sc;};
function decode(str){state={};cnt={};const parts=str.split('-');const sc=parts[0],cc=parts[1];PREF.forEach((p,i)=>{const v=+sc[i]||0;if(v>0&&v<=5)state[p.id]=v;});if(cc)PREF.forEach((p,i)=>{const v=parseInt(cc[i]||'0',36)||0;if(v>0)cnt[p.id]=v;});}
function save(){if(viewMode)return;localStorage.setItem('keikenchi',encode());localStorage.setItem('keikenchi_memo',JSON.stringify(memo));if(!location.search)history.replaceState(null,'','#'+encode());schedulePush();if(typeof scheduleMe==='function')scheduleMe();}
function load(){try{memo=JSON.parse(localStorage.getItem('keikenchi_memo')||'{}')||{};}catch{memo={};}let src=location.hash.slice(1)||localStorage.getItem('keikenchi')||'';if(src&&/^[0-5]+(-[0-9a-z]+)?$/.test(src))decode(src);paintAll();updateAllBadges();recalc();}
async function boot(){
  renderAccountBar();
  const q=new URLSearchParams(location.search);
  if(q.get('room'))currentRoom=q.get('room');
  if(q.get('u')){ loadUserMap(q.get('u')); }
  else { const logged=await loadMe(); if(logged)renderAccountBar(); else load(); }
  if(currentRoom)renderBoard();
}
document.getElementById('reset').onclick=()=>{if(confirm('Сбросить всю карту?')){state={};cnt={};memo={};dates={};closePop();paintAll();updateAllBadges();recalc();save();}};
document.getElementById('share').onclick=async()=>{const url=location.origin+location.pathname+'#'+encode();try{await navigator.clipboard.writeText(url);alert('Ссылка скопирована!\n'+url);}catch{prompt('Скопируй ссылку:',url);}};

// labels toggle
const lblBtn=document.getElementById('labels');
lblBtn.onclick=()=>{const on=labels.classList.toggle('on');lblBtn.classList.toggle('on',on);};

// ---- export: clean card (map + score), as crisp PNG or vector SVG ----
const EXW=600,EXH=770;
function buildExportSVG(){
  const total=document.getElementById('total').textContent;
  const pct=document.getElementById('pct').textContent;
  const inner=vp.innerHTML; // paths+badges(+labels)+inset with inline fills
  const showL=labels.classList.contains('on');
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${EXW}" height="${EXH}" viewBox="0 0 ${EXW} ${EXH}">
<style>path{stroke:#3a3a3a;stroke-width:.5;stroke-linejoin:round;stroke-linecap:round}text.badge{font:700 11px -apple-system,sans-serif;fill:#222;paint-order:stroke;stroke:#fff;stroke-width:3px;text-anchor:middle;dominant-baseline:central}text.plabel{font:600 8px -apple-system,sans-serif;fill:#2a2a2a;paint-order:stroke;stroke:#fff;stroke-width:2.4px;text-anchor:middle;dominant-baseline:central;${showL?'':'display:none'}}#plabels{${showL?'':'display:none'}}</style>
<rect width="${EXW}" height="${EXH}" fill="#f6efe1"/>
<text x="300" y="40" text-anchor="middle" font-family="-apple-system,sans-serif" font-weight="700" font-size="16" letter-spacing="1.5" fill="#333">ALL JAPAN KEIKENCHI</text>
<rect x="200" y="58" width="200" height="52" rx="12" fill="#fbe6a8"/>
<text x="300" y="92" text-anchor="middle" font-family="-apple-system,sans-serif" font-weight="800" font-size="30" fill="#333">${total}</text>
<text x="300" y="128" text-anchor="middle" font-family="-apple-system,sans-serif" font-size="12" fill="#8a7f6a">${pct}</text>
<g transform="translate(40 150)">${inner}</g>
</svg>`;
}
function dl(href,name){const a=document.createElement('a');a.href=href;a.download=name;a.click();}

// PNG — very high resolution (~4800px wide) so it stays crisp when zoomed
const pngBtn=document.getElementById('png');
pngBtn.onclick=()=>{
  const svgStr=buildExportSVG();
  const url='data:image/svg+xml;base64,'+btoa(unescape(encodeURIComponent(svgStr)));
  const img=new Image();
  const old=pngBtn.textContent; pngBtn.textContent='рендер…'; pngBtn.disabled=true;
  const done=()=>{pngBtn.textContent=old;pngBtn.disabled=false;};
  img.onload=()=>{
    let S=8;                                   // ~4800x6160 px
    const MAXPX=32e6;                          // guard canvas area for cross-browser safety
    while(EXW*S*EXH*S>MAXPX && S>2) S--;
    const c=document.createElement('canvas'); c.width=EXW*S; c.height=EXH*S;
    const ctx=c.getContext('2d'); ctx.imageSmoothingEnabled=true; ctx.imageSmoothingQuality='high';
    ctx.setTransform(S,0,0,S,0,0); ctx.drawImage(img,0,0);
    c.toBlob(b=>{ if(b) dl(URL.createObjectURL(b),'keikenchi.png'); else alert('Не удалось отрендерить PNG (слишком большой холст).'); done(); },'image/png');
  };
  img.onerror=()=>{alert('Ошибка рендера PNG.');done();};
  img.src=url;
};


// ================= MVP-2: cloud save + rooms =================
const API='/api';
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let cloud=null; try{cloud=JSON.parse(localStorage.getItem('keikenchi_cloud')||'null');}catch{}
let currentRoom=null, viewMode=false, pushTimer=null;
const unameEl=document.getElementById('uname');
const boardEl=document.getElementById('board');
const bannerEl=document.getElementById('viewbanner');
if(cloud&&cloud.name)unameEl.value=cloud.name;

function myLink(){return location.origin+location.pathname+'?u='+(cloud&&cloud.id);}
function showCloudLink(){
  if(!cloud){document.getElementById('cloudlink').textContent='';return;}
  document.getElementById('cloudlink').innerHTML=`сохранено · <a href="${myLink()}" target="_blank">моя ссылка</a> <button class="mini" data-copy="${myLink()}">копир.</button>`;
}
async function saveCloud(){
  const name=(unameEl.value.trim()||'аноним'), data=encode();
  try{
    if(cloud&&cloud.id&&cloud.editKey){
      const res=await fetch(`${API}/map/${cloud.id}`,{method:'PUT',headers:{'content-type':'application/json','x-edit-key':cloud.editKey},body:JSON.stringify({name,data})});
      if(res.status===403||res.status===404)cloud=null; else {cloud.name=name;localStorage.setItem('keikenchi_cloud',JSON.stringify(cloud));showCloudLink();return true;}
    }
    const res=await fetch(`${API}/map`,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({name,data})});
    const j=await res.json();
    if(j.id){cloud={id:j.id,editKey:j.editKey,name};localStorage.setItem('keikenchi_cloud',JSON.stringify(cloud));showCloudLink();return true;}
    throw new Error(j.error||'fail');
  }catch(e){alert('Нет связи с сервером.\nОблако работает только на задеплоенном сайте (не через file://).');return false;}
}
function schedulePush(){ if(!cloud||viewMode)return; clearTimeout(pushTimer); pushTimer=setTimeout(()=>{saveCloud().then(()=>{if(currentRoom)renderBoard();});},1500); }
async function ensureCloud(){ if(cloud&&cloud.id)return true; return await saveCloud(); }

async function roomCreate(){
  if(!await ensureCloud())return;
  const name=prompt('Название комнаты?','Наша поездка'); if(name===null)return;
  try{ const r=await (await fetch(`${API}/room`,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({name})})).json();
    if(r.id) await roomJoin(r.id);
  }catch{alert('Не удалось создать комнату.');}
}
async function roomJoin(id){
  id=String(id||'').trim(); if(!id)return;
  if(!await ensureCloud())return;
  try{
    const res=await fetch(`${API}/room/${id}/join`,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({mapId:cloud.id})});
    const j=await res.json();
    if(j.error){alert('Комната не найдена: '+id);return;}
    currentRoom=id; history.replaceState(null,'',location.pathname+'?room='+id); renderBoard();
  }catch{alert('Не удалось войти в комнату.');}
}
async function renderBoard(){
  if(!currentRoom)return;
  try{
    const r=await (await fetch(`${API}/room/${currentRoom}`)).json();
    if(r.error){boardEl.innerHTML='';return;}
    const inv=location.origin+location.pathname+'?room='+r.id;
    const rows=(r.members||[]).map((mb,i)=>`<div class="brow ${cloud&&mb.id===cloud.id?'me':''}"><b>${i+1}</b><span class="bn">${esc(mb.name||'аноним')}</span><a href="?u=${mb.id}">карта</a><span class="bs">${mb.score}</span></div>`).join('')||'<div style="font-size:13px;color:#8a7f6a">пока пусто — пригласи друзей</div>';
    boardEl.innerHTML=`<div class="btitle">🏆 ${esc(r.name||'Комната')} · код <code>${r.id}</code> <button class="mini" data-copy="${inv}">пригласить</button></div>${rows}`;
  }catch{}
}
async function loadUserMap(id){
  try{
    const r=await (await fetch(`${API}/map/${id}`)).json();
    if(r.error){alert('Карта не найдена.');return;}
    decode(r.data); paintAll(); updateAllBadges(); recalc(); viewMode=true;
    bannerEl.className='on';
    bannerEl.innerHTML=`👀 карта пользователя <b>${esc(r.name||'аноним')}</b> · ${r.score} pts <button id="tomine">вести свою</button>`;
    document.getElementById('tomine').onclick=()=>{ viewMode=false; bannerEl.className=''; history.replaceState(null,'',location.pathname); load(); };
  }catch{alert('Нет связи с сервером.');}
}

// wire buttons
document.getElementById('cloudsave').onclick=()=>saveCloud();
document.getElementById('roomnew').onclick=roomCreate;
document.getElementById('roomjoin').onclick=()=>roomJoin(document.getElementById('roomid').value);
// copy-to-clipboard delegation
document.addEventListener('click',async e=>{const b=e.target.closest('[data-copy]');if(!b)return;try{await navigator.clipboard.writeText(b.dataset.copy);b.textContent='ок!';setTimeout(()=>{if(b.dataset.copy.includes('room'))b.textContent='пригласить';else b.textContent='копир.';},1200);}catch{prompt('Скопируй:',b.dataset.copy);}});

showCloudLink();


// ================= achievements =================
const range=(a,b)=>{const r=[];for(let i=a;i<=b;i++)r.push(i);return r;};
const ISLANDS={Хоккайдо:[1],Хонсю:range(2,35),Сикоку:[36,37,38,39],Кюсю:[40,41,42,43,44,45,46]};
const KANTO=[8,9,10,11,12,13,14], KANSAI=[24,25,26,27,28,29,30];
const marked=()=>Object.keys(state).length;
const sumScore=()=>{let s=0;for(const k in state)s+=state[k];return s;};
const hasScore=v=>Object.values(state).some(x=>x===v);
const allOf=ids=>ids.every(i=>state[i]);
const totVisits=()=>{let s=0;for(const k in cnt)s+=cnt[k];return s;};
const maxVisit=()=>{let m=0;for(const k in cnt)if(cnt[k]>m)m=cnt[k];return m;};
const islandsDone=()=>Object.values(ISLANDS).every(g=>g.some(i=>state[i]));
const ACH=[
  {id:'first',e:'👣',t:'Первый шаг',d:'отметить 1 префектуру',f:()=>marked()>=1},
  {id:'half',e:'🌓',t:'Полпути',d:'24 префектуры',f:()=>marked()>=24},
  {id:'all',e:'🗾',t:'Вся Япония',d:'все 47 отмечены',f:()=>marked()>=47},
  {id:'perfect',e:'💯',t:'Идеал',d:'все на 5 — 235 pts',f:()=>sumScore()>=235},
  {id:'resided',e:'🏠',t:'Осёдлый',d:'где-то жил (5)',f:()=>hasScore(5)},
  {id:'islander',e:'⛴️',t:'Островитянин',d:'4 главных острова',f:islandsDone},
  {id:'kanto',e:'🗼',t:'Канто-мастер',d:'весь регион Канто',f:()=>allOf(KANTO)},
  {id:'kansai',e:'🏯',t:'Кансай-мастер',d:'весь регион Кансай',f:()=>allOf(KANSAI)},
  {id:'nomad',e:'🎒',t:'Кочевник',d:'20+ визитов',f:()=>totVisits()>=20},
  {id:'regular',e:'🔁',t:'Завсегдатай',d:'×5 в одну префектуру',f:()=>maxVisit()>=5},
  {id:'tottori',e:'🥚',t:'???',d:'секретная',secret:true,rt:'Нашёл Тоттори',rd:'отметил самую забытую',f:()=>!!state[31]},
];
const achEl=document.getElementById('ach');
let achSeen=[]; try{achSeen=JSON.parse(localStorage.getItem('keikenchi_ach')||'[]')||[];}catch{}
function renderAch(unlocked){
  const n=unlocked.length;
  achEl.innerHTML=`<h3>🏆 Ачивки · ${n}/${ACH.length}</h3><div class="achgrid">`+
    ACH.map(a=>{const on=unlocked.includes(a.id);
      const title=(a.secret&&!on)?a.t:(a.secret?a.rt:a.t);
      const desc=(a.secret&&!on)?a.d:(a.secret?a.rd:a.d);
      return `<div class="achip ${on?'on':''}"><span class="ae">${a.secret&&!on?'🔒':a.e}</span><span><b>${title}</b><small>${desc}</small></span></div>`;
    }).join('')+'</div>';
}
let toastQ=[],toastBusy=false;
function toast(msg){toastQ.push(msg);if(!toastBusy)nextToast();}
function nextToast(){const el=document.getElementById('toast');if(!toastQ.length){toastBusy=false;return;}toastBusy=true;el.textContent=toastQ.shift();el.classList.add('on');setTimeout(()=>{el.classList.remove('on');setTimeout(nextToast,350);},2200);}
function checkAch(){
  const unlocked=ACH.filter(a=>{try{return a.f();}catch{return false;}}).map(a=>a.id);
  for(const id of unlocked) if(!achSeen.includes(id)){
    const a=ACH.find(x=>x.id===id);
    if(achSeen.length) toast(`🏆 Ачивка: ${a.secret?a.rt:a.t}`); // no toast on very first load
  }
  if(unlocked.some(id=>!achSeen.includes(id))){achSeen=[...new Set([...achSeen,...unlocked])];localStorage.setItem('keikenchi_ach',JSON.stringify(achSeen));}
  renderAch(unlocked);
}


// ================= accounts / LK =================
let account=null, pushMeTimer=null;
const api=(path,opts={})=>fetch('/api'+path,{headers:{'content-type':'application/json'},...opts});
function buildExtra(){return {memo,dates,ach:achSeen};}
async function loadMe(){
  try{
    const r=await api('/me'); if(r.status!==200)return false;
    const j=await r.json(); account={username:j.user.username};
    if(j.map){
      decode(j.map.data); cloud={id:j.map.id};
      let ex={}; try{ex=JSON.parse(j.map.extra||'{}')||{};}catch{}
      memo=ex.memo||{}; dates=ex.dates||{}; achSeen=ex.ach||[];
      localStorage.setItem('keikenchi',encode()); localStorage.setItem('keikenchi_memo',JSON.stringify(memo));
    }
    paintAll(); updateAllBadges(); recalc();
    return true;
  }catch{return false;}
}
async function pushMe(){
  if(!account||viewMode)return;
  try{const r=await api('/me',{method:'PUT',body:JSON.stringify({name:account.username,data:encode(),extra:buildExtra()})});
    const j=await r.json(); if(j.id)cloud={id:j.id};
    if(currentRoom)renderBoard();
  }catch{}
}
function scheduleMe(){ if(!account||viewMode)return; clearTimeout(pushMeTimer); pushMeTimer=setTimeout(pushMe,1200); }

// auth modal
let authMode='login';
const authModal=document.getElementById('authmodal');
const authUserEl=document.getElementById('authuser'), authPassEl=document.getElementById('authpass'), authErrEl=document.getElementById('autherr');
function syncAuthUI(){document.getElementById('authtitle').textContent=authMode==='login'?'Вход':'Регистрация';document.getElementById('authgo').textContent=authMode==='login'?'Войти':'Создать аккаунт';document.getElementById('authtoggle').textContent=authMode==='login'?'Нет аккаунта? Регистрация':'Уже есть аккаунт? Войти';}
function openAuth(mode){authMode=mode;authErrEl.textContent='';syncAuthUI();authModal.classList.add('on');authUserEl.focus();}
function closeAuth(){authModal.classList.remove('on');authErrEl.textContent='';}
document.getElementById('authtoggle').onclick=()=>{authMode=authMode==='login'?'register':'login';authErrEl.textContent='';syncAuthUI();};
document.getElementById('authcancel').onclick=closeAuth;
authModal.addEventListener('click',e=>{if(e.target===authModal)closeAuth();});
async function doAuth(){
  const u=authUserEl.value.trim(), p=authPassEl.value;
  if(u.length<3||p.length<6){authErrEl.textContent='ник ≥3, пароль ≥6';return;}
  authErrEl.textContent='…';
  try{
    const r=await api('/auth/'+authMode,{method:'POST',body:JSON.stringify({username:u,password:p})});
    const j=await r.json();
    if(!r.ok){authErrEl.textContent=({['username taken']:'ник занят',['wrong login or password']:'неверный ник или пароль'}[j.error])||j.error||'ошибка';return;}
    account={username:j.username}; closeAuth(); authPassEl.value='';
    if(authMode==='login'){ await loadMe(); } else { await pushMe(); }  // register keeps current progress
    renderAccountBar(); toast('👤 Привет, '+j.username+'!');
  }catch{authErrEl.textContent='нет связи с сервером';}
}
document.getElementById('authgo').onclick=doAuth;
authPassEl.addEventListener('keydown',e=>{if(e.key==='Enter')doAuth();});
async function doLogout(){try{await api('/auth/logout',{method:'POST'});}catch{} account=null; renderAccountBar(); toast('вышли из аккаунта'); }
function renderAccountBar(){
  const el=document.getElementById('acctbar');
  if(account){
    el.innerHTML=`<button class="who" id="lkbtn">👤 ${esc(account.username)}</button><button id="logoutbtn">Выйти</button>`;
    document.getElementById('logoutbtn').onclick=doLogout;
    document.getElementById('lkbtn').onclick=()=>document.getElementById('history').scrollIntoView({behavior:'smooth',block:'center'});
  }else{
    el.innerHTML=`<button id="loginbtn">Войти / Регистрация</button>`;
    document.getElementById('loginbtn').onclick=()=>openAuth('login');
  }
}

// history "где я был"
const HLAB={5:'Жил там',4:'Ночевал',3:'Гулял',2:'Заезжал',1:'Проездом'};
function fmtDate(ts){try{return new Date(ts).toLocaleDateString('ru-RU',{day:'numeric',month:'short',year:'numeric'});}catch{return '';}}
function renderHistory(){
  const el=document.getElementById('history'); if(!el)return;
  const ids=Object.keys(state).filter(k=>state[k]>0).map(Number).sort((a,b)=>(state[b]-state[a])||(a-b));
  if(!ids.length){el.innerHTML='';return;}
  const rows=ids.map(id=>{const p=byId[id];const sc=state[id];const c=cnt[id]||0;const mm=memo[id];const dt=dates[id];
    const meta=[c>1?('×'+c):'',dt?fmtDate(dt):''].filter(Boolean).join(' · ');
    return `<div class="hrow"><span class="hd" style="background:${RAW[sc]}"></span><span><span class="hn">${esc(p.r)} ${esc(p.ja)}</span> — ${HLAB[sc]}${mm?` <span class="hmemo">«${esc(mm)}»</span>`:''}</span><span class="hmeta">${meta}</span></div>`;
  }).join('');
  el.innerHTML=`<h3>📖 Где я был · ${ids.length}</h3>`+rows;
}

apply(); syncLegend(); boot();
</script>
</body>
</html>'''
open('public/index.html','w').write(html.replace('__DATA__',data))
print('index.html KB',round(os.path.getsize('public/index.html')/1024,1))
