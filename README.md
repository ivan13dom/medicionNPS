# Encuesta de Sucursales — Proyecto NUEVO

## Flujo (dos pantallas)
1) `frontend/setup.html`: selección de sucursal (solo personal). Guarda `branch.id` en `localStorage`.
2) `frontend/survey.html`: encuesta con íconos sobrios (SVG). Si no hay sucursal, redirige a `setup.html`.

## Configuración
- Editá `setup.html` y `survey.html` para poner tu backend:
  window.__CONFIG__.API_BASE = "https://TU-BACKEND.onrender.com"

## Backend (Render)
- En `backend/`: `app.py`, `requirements.txt`, `Procfile`.
- Variables de entorno:
  - GITHUB_REPO = usuario/encuesta-sucursales
  - GITHUB_TOKEN = <PAT con scope repo>
  - (opc) BRANCHES_FILE = data/branches.json
  - (opc) RESP_FILE     = data/responses.json

## Endpoints
- GET /health
- GET /branches
- POST /submit    # body: {branch_id, rating: 1..5, device?, meta?}
