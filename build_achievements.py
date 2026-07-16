#!/usr/bin/env python3
"""Generate public/achievements.html — standalone achievements page.
Recomputes from localStorage (keikenchi / keikenchi_plan) and, if logged in,
from the account (/api/me). No map geometry needed."""
import os

HTML = r'''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>Keikenchi — Ачивки</title>
<style>
  :root{--bg:#f6efe1;--ink:#333;--line:#3a3a3a}
  *{box-sizing:border-box}
  html,body{margin:0;height:100%}
  body{background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Hiragino Sans","Noto Sans JP",sans-serif}
  .topbar{position:fixed;top:10px;left:12px;right:12px;display:flex;justify-content:space-between;z-index:30}
  .topbar a,.topbar span{font:inherit;font-size:12px;font-weight:600;padding:6px 12px;border-radius:9px;border:2px solid var(--line);background:#fff;text-decoration:none;color:var(--ink)}
  .wrap{max-width:640px;margin:0 auto;padding:56px 14px 60px;text-align:center}
  h1{font-size:20px;margin:4px 0 2px}
  .prog{font-size:13px;color:#8a7f6a;margin-bottom:6px}
  .bar{height:10px;background:#e7e0cf;border-radius:6px;overflow:hidden;max-width:320px;margin:8px auto 20px}
  .bar>i{display:block;height:100%;background:#ee7f5f}
  .achgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px}
  .achip{display:flex;gap:11px;align-items:center;padding:12px;border:2px solid #eee;border-radius:12px;opacity:.45;filter:grayscale(1);transition:.2s;text-align:left}
  .achip.on{opacity:1;filter:none;border-color:var(--line);background:#fff}
  .achip .ae{font-size:28px;line-height:1}
  .achip b{display:block;font-size:14px}
  .achip small{color:#8a7f6a;font-size:12px}
</style>
</head>
<body>
<div class="topbar"><a href="/">← карта префектур</a><span id="acct"></span></div>
<div class="wrap">
  <h1>🏆 Ачивки</h1>
  <div class="prog" id="prog">0 / 0</div>
  <div class="bar"><i id="barfill" style="width:0%"></i></div>
  <div class="achgrid" id="grid"></div>
</div>
<script>
let state={},cnt={},plan={};
function decode(str){state={};cnt={};const parts=String(str).split('-');const sc=parts[0]||'',cc=parts[1];
  for(let i=0;i<sc.length;i++){const v=+sc[i]||0;if(v>0&&v<=5)state[i+1]=v;}
  if(cc)for(let i=0;i<cc.length;i++){const v=parseInt(cc[i]||'0',36)||0;if(v>0)cnt[i+1]=v;}}
try{decode(localStorage.getItem('keikenchi')||'');}catch{}
try{plan=JSON.parse(localStorage.getItem('keikenchi_plan')||'{}')||{};}catch{}

const range=(a,b)=>{const r=[];for(let i=a;i<=b;i++)r.push(i);return r;};
const ISLANDS={h:[1],hon:range(2,35),shi:[36,37,38,39],kyu:[40,41,42,43,44,45,46]};
const KANTO=[8,9,10,11,12,13,14],KANSAI=[24,25,26,27,28,29,30];
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
  {id:'planner',e:'📌',t:'Планировщик',d:'наметил след. поездку',f:()=>Object.keys(plan).length>=1},
  {id:'dreamer',e:'🗺️',t:'Мечтатель',d:'5 префектур в плане',f:()=>Object.keys(plan).length>=5},
  {id:'tottori',e:'🥚',t:'???',d:'секретная',secret:true,rt:'Нашёл Тоттори',rd:'отметил самую забытую',f:()=>!!state[31]},
];
function render(){
  const unlocked=ACH.filter(a=>{try{return a.f();}catch{return false;}}).map(a=>a.id);
  const n=unlocked.length;
  document.getElementById('prog').textContent=n+' / '+ACH.length+' открыто';
  document.getElementById('barfill').style.width=Math.round(n/ACH.length*100)+'%';
  document.getElementById('grid').innerHTML=ACH.map(a=>{const on=unlocked.includes(a.id);
    const title=(a.secret&&!on)?a.t:(a.secret?a.rt:a.t);
    const desc=(a.secret&&!on)?a.d:(a.secret?a.rd:a.d);
    return `<div class="achip ${on?'on':''}"><span class="ae">${a.secret&&!on?'🔒':a.e}</span><span><b>${title}</b><small>${desc}</small></span></div>`;
  }).join('');
}
async function loadAccount(){
  try{const r=await fetch('/api/me');if(r.status!==200)return;const j=await r.json();
    document.getElementById('acct').textContent='👤 '+j.user.username;
    if(j.map){decode(j.map.data);let ex={};try{ex=JSON.parse(j.map.extra||'{}')||{};}catch{}plan=ex.plan||plan;}
    render();
  }catch{}
}
render(); loadAccount();
</script>
</body>
</html>'''
open('public/achievements.html','w').write(HTML)
print('public/achievements.html', round(os.path.getsize('public/achievements.html')/1024,1),'KB')
