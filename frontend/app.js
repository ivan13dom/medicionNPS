const API = window.__CONFIG__.API_BASE;
const $ = sel => document.querySelector(sel);
const THANKS_MS = 1600;

// ---- Branch handling
async function loadBranches(){
  const sel = $('#branch');
  sel.innerHTML = '<option value="">Cargando...</option>';
  try{
    const r = await fetch(`${API}/branches`);
    const data = await r.json();
    sel.innerHTML = '<option value="">Seleccioná tu sucursal</option>';
    data.forEach(b=>{
      const opt = document.createElement('option');
      opt.value = b.id;          // { id, name }
      opt.textContent = b.name;  
      sel.appendChild(opt);
    });
    // restaurar si está bloqueada
    const locked = localStorage.getItem('branch.locked') === '1';
    const saved = localStorage.getItem('branch.id');
    if(saved){ sel.value = saved; }
    setLocked(locked);
  }catch(e){
    sel.innerHTML = '<option>Error al cargar sucursales</option>';
  }
}

function setLocked(locked){
  const sel = $('#branch');
  const btn = $('#lockBranch');
  sel.disabled = locked;
  btn.textContent = locked ? 'Desbloquear' : 'Bloquear';
  $('#branchHint').textContent = locked ? '(bloqueada para este equipo)' : '(selección solo para el personal)';
}

$('#lockBranch').addEventListener('click', ()=>{
  const sel = $('#branch');
  const cur = sel.value;
  if(!cur){ alert('Elegí una sucursal antes de bloquear.'); return; }
  const locked = !(localStorage.getItem('branch.locked') === '1');
  localStorage.setItem('branch.locked', locked ? '1' : '0');
  localStorage.setItem('branch.id', cur);
  setLocked(locked);
});

// ---- Queue offline
function queueResponse(payload){
  const q = JSON.parse(localStorage.getItem('queue')||'[]');
  q.push(payload);
  localStorage.setItem('queue', JSON.stringify(q));
}

async function flushQueue(){
  let q = JSON.parse(localStorage.getItem('queue')||'[]');
  if(!q.length) return;
  const remain = [];
  for(const p of q){
    try{ await sendPayload(p); }
    catch{ remain.push(p); }
  }
  localStorage.setItem('queue', JSON.stringify(remain));
}
setInterval(flushQueue, 15000);

// ---- Submit
async function sendPayload(payload){
  const r = await fetch(`${API}/submit`, {
    method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)
  });
  if(!r.ok) throw new Error('Network');
}

function deviceInfo(){
  return navigator.userAgent.slice(0,160);
}

function show(id){ $(id).classList.remove('hidden'); }
function hide(id){ $(id).classList.add('hidden'); }

function setupFaces(){
  document.querySelectorAll('.face').forEach(btn=>{
    btn.addEventListener('click', async ()=>{
      const rating = Number(btn.dataset.rating);
      const branch = $('#branch').value || localStorage.getItem('branch.id');
      if(!branch){ alert('Seleccioná la sucursal (personal).'); return; }

      // animación
      btn.classList.add('spin');
      setTimeout(()=>btn.classList.remove('spin'), 600);

      const payload = {
        rating,
        branch_id: branch,
        device: deviceInfo(),
        meta: { screen: { w: window.innerWidth, h: window.innerHeight } }
      };

      try{
        await sendPayload(payload);
        show('#thanks'); setTimeout(()=>hide('#thanks'), THANKS_MS);
      }catch(e){
        queueResponse(payload);
        show('#error'); setTimeout(()=>hide('#error'), 1800);
      }
    })
  });
}

window.addEventListener('DOMContentLoaded', ()=>{
  loadBranches();
  setupFaces();
  flushQueue();
});
