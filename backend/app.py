import os, json, datetime, subprocess, logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

GITHUB_REPO   = os.getenv("GITHUB_REPO", "usuario/encuesta-sucursales")
GITHUB_TOKEN  = os.getenv("GITHUB_TOKEN")
BRANCHES_FILE = os.getenv("BRANCHES_FILE", "data/branches.json")
RESP_FILE     = os.getenv("RESP_FILE", "data/responses.json")

def _git(*args, cwd='.'):
    import subprocess
    return subprocess.run(list(args), cwd=cwd, check=True)

def commit_to_github(filename: str, content_as_obj):
    repo_path = "."
    if not os.path.isdir(os.path.join(repo_path, ".git")):
        _git("git", "init", cwd=repo_path)
        _git("git", "checkout", "-b", "main", cwd=repo_path)
        _git("git", "remote", "add", "origin", f"https://github.com/{GITHUB_REPO}.git", cwd=repo_path)

    subprocess.run(["git", "config", "--global", "user.email", "bot@render.com"], check=False)
    subprocess.run(["git", "config", "--global", "user.name", "Render Bot"], check=False)

    _git("git", "fetch", "origin", cwd=repo_path)
    _git("git", "checkout", "main", cwd=repo_path)
    _git("git", "reset", "--hard", "origin/main", cwd=repo_path)

    abs_path = os.path.join(repo_path, filename)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as f:
        json.dump(content_as_obj, f, ensure_ascii=False, indent=2)

    _git("git", "add", filename, cwd=repo_path)
    status = subprocess.run(["git", "status", "--porcelain"], cwd=repo_path, capture_output=True, text=True)
    if not status.stdout.strip():
        app.logger.info(f"Sin cambios en {filename}.")
        return

    _git("git", "commit", "-m", f"update {filename}", cwd=repo_path)
    push_url = f"https://{GITHUB_TOKEN}@github.com/{GITHUB_REPO}.git"
    _git("git", "push", push_url, "main", cwd=repo_path)

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/branches")
def get_branches():
    raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{BRANCHES_FILE}"
    r = requests.get(raw_url, timeout=10)
    if r.status_code == 200:
        try:
            return jsonify(r.json())
        except Exception:
            return jsonify([])
    return jsonify([])

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

    raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{RESP_FILE}"
    try:
        r = requests.get(raw_url, timeout=10)
        current = r.json() if r.status_code == 200 else []
        if not isinstance(current, list):
            current = []
    except Exception:
        current = []

    now = datetime.datetime.utcnow().isoformat() + "Z"
    rec = {
        "id": os.urandom(12).hex(),
        "ts": now,
        "branch_id": branch_id,
        "rating": rating,
        "device": device,
        "meta": meta
    }
    current.append(rec)
    commit_to_github(RESP_FILE, current)
    return jsonify({"ok": True, "id": rec["id"]})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
