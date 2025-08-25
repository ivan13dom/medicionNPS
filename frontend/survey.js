const API = window.__CONFIG__.API_BASE;
const $ = s => document.querySelector(s);
const THANKS_MS = 1600;

function deviceInfo(){ return navigator.userAgent.slice(0,160); }
function show(id){ $(id).classList.add('show'); }
function hide(id){ $(id).classList.remove('show'); }

function ensureBranch(){
  const b = localStorage.getItem('branch.id');
  if(!b){ window.location.href = 'setup.html'; return null; }
  $('#branchInfo').textContent = 'Sucursal actual: ' + b;
  return b;
}

async function sendPayload(p){
  const r = await fetch(`${API}/submit`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(p) });
  if(!r.ok) throw new Error('network');
}

function queueResponse(p){
  const q = JSON.parse(localStorage.getItem('queue')||'[]'); q.push(p);
  localStorage.setItem('queue', JSON.stringify(q));
}

async function flushQueue(){
  let q = JSON.parse(localStorage.getItem('queue')||'[]'); if(!q.length) return;
  const remain = [];
  for(const p of q){ try{ await sendPayload(p); } catch(e){ remain.push(p); } }
  localStorage.setItem('queue', JSON.stringify(remain));
}
setInterval(flushQueue, 15000);

function setup(){
  const branch = ensureBranch(); if(!branch) return;
  document.querySelectorAll('.face').forEach(btn=>{
    btn.addEventListener('click', async ()=>{
      const rating = Number(btn.dataset.rating);
      btn.classList.add('spin'); setTimeout(()=>btn.classList.remove('spin'), 600);
      const payload = { rating, branch_id: branch, device: deviceInfo(), meta:{ screen:{ w:innerWidth, h:innerHeight } } };
      try{
        await sendPayload(payload); show('#thanks'); setTimeout(()=>hide('#thanks'), THANKS_MS);
      }catch(e){
        queueResponse(payload); show('#error'); setTimeout(()=>hide('#error'), 1800);
      }
    });
  });
  flushQueue();
}

window.addEventListener('DOMContentLoaded', setup);
