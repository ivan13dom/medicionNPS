const API = window.__CONFIG__.API_BASE;
const $ = s => document.querySelector(s);
const overlay = $('#alert'); const alertText = $('#alertText');

function showAlert(msg){ alertText.textContent = msg; overlay.classList.add('show'); setTimeout(()=>overlay.classList.remove('show'), 1200); }

async function loadBranches(){
  const sel = $('#branch');
  sel.innerHTML = '<option value="">Cargando...</option>';
  try{
    const r = await fetch(`${API}/branches`);
    const data = await r.json();
    sel.innerHTML = '<option value="">Seleccioná tu sucursal</option>';
    data.forEach(b=>{
      const opt = document.createElement('option');
      opt.value = b.id; opt.textContent = b.name; sel.appendChild(opt);
    });
    const saved = localStorage.getItem('branch.id');
    if(saved) sel.value = saved;
  }catch(e){
    sel.innerHTML = '<option>Error al cargar sucursales</option>';
  }
}

$('#save').addEventListener('click', ()=>{
  const val = $('#branch').value;
  if(!val){ showAlert('Elegí una sucursal'); return; }
  localStorage.setItem('branch.id', val);
  showAlert('Sucursal guardada');
});

$('#clear').addEventListener('click', ()=>{
  localStorage.removeItem('branch.id');
  $('#branch').value = '';
  showAlert('Configuración borrada');
});

window.addEventListener('DOMContentLoaded', loadBranches);
