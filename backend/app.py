import os, json, datetime, subprocess, logging, time
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

GITHUB_REPO   = os.getenv("GITHUB_REPO", "usuario/encuesta-sucursales")
GITHUB_TOKEN  = os.getenv("GITHUB_TOKEN")
BRANCHES_FILE = os.getenv("BRANCHES_FILE", "data/branches.json")
RESP_FILE     = os.getenv("RESP_FILE", "data/responses.json")

def sh(args, cwd=".", check=True, capture=False):
    return subprocess.run(args, cwd=cwd, check=check,
                          capture_output=capture, text=True)

def ensure_repo():
    if not os.path.isdir(".git"):
        sh(["git", "init"])
        sh(["git", "checkout", "-b", "main"])
        sh(["git", "remote", "add", "origin", f"https://github.com/{GITHUB_REPO}.git"])
    # identidad (global ok)
    subprocess.run(["git", "config", "--global", "user.email", "bot@render.com"])
    subprocess.run(["git", "config", "--global", "user.name", "Render Bot"])
    # sync a último commit remoto
    sh(["git", "fetch", "origin"])
    sh(["git", "checkout", "main"])
    sh(["git", "reset", "--hard", "origin/main"])

def load_json_list(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []

def save_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def push_with_retry(filename, merge_fn, max_tries=5):
    """merge_fn(current_list) -> new_list  (idempotente)
       Reintenta si hay conflictos de avance (non-fast-forward)."""
    for i in range(max_tries):
        ensure_repo()
        abs_path = os.path.join(".", filename)
        current = load_json_list(abs_path)

        # construir nuevo contenido
        updated = merge_fn(current)
        save_json(abs_path, updated)

        sh(["git", "add", filename])
        sh(["git", "commit", "-m", f"update {filename}"])
        try:
            push_url = f"https://{GITHUB_TOKEN}@github.com/{GITHUB_REPO}.git"
            sh(["git", "push", push_url, "main"])
            return True
        except subprocess.CalledProcessError as e:
            # Pull --rebase y reintento (otro request se adelantó)
            app.logger.warning(f"Push failed (try {i+1}), retrying... {e}")
            # Volver a sincronizar con remoto y reintentar
            sh(["git", "fetch", "origin"])
            sh(["git", "rebase", "origin/main"], check=False)
            # Si el rebase falla, hacemos reset duro y reintentamos con nuevo merge
            sh(["git", "reset", "--hard", "origin/main"])
            time.sleep(0.2 * (i + 1))  # backoff corto
    return False

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/branches")
def get_branches():
    # Leer branches desde el repo local sincronizado
    try:
        ensure_repo()
        path = os.path.join(".", BRANCHES_FILE)
        return app.response_class(
            response=json.dumps(load_json_list(path)),
            status=200, mimetype="application/json"
        )
    except Exception:
        return app.response_class(response="[]", status=200, mimetype="application/json")

@app.post("/submit")
def submit():
    body = request.get_json(force=True)
    try:
        rating = int(body.get("rating", 0))
    except Exception:
        rating = 0
    branch_id = body.get("branch_id")
    device    = body.get("device", "")
    meta      = body.get("meta", {})

    if rating not in [1,2,3,4,5] or not branch_id:
        return jsonify({"error": "payload inválido"}), 400

    now = datetime.datetime.utcnow().isoformat() + "Z"
    rec = {
        "id": os.urandom(12).hex(),
        "ts": now,
        "branch_id": branch_id,
        "rating": rating,
        "device": device,
        "meta": meta
    }

    def merge_fn(current):
        # current es la lista leída DESPUÉS de sync con remoto
        current = current[:] if isinstance(current, list) else []
        current.append(rec)
        return current

    ok = push_with_retry(RESP_FILE, merge_fn)
    if not ok:
        return jsonify({"error": "no se pudo guardar (reintentos agotados)"}), 500
    return jsonify({"ok": True, "id": rec["id"]})
