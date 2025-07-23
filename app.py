from flask import Flask, render_template, abort, request, redirect, url_for, send_from_directory
import json
import os
from werkzeug.utils import secure_filename
from datetime import datetime

from script import start_pipeline  # seu módulo de pipeline/background

app = Flask(__name__)

# ─── Configuração de upload ────────────────────────────────────────────────
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "images")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ─── Carga inicial de projects.json ──────────────────────────────────────
JSON_PATH = os.path.join(BASE_DIR, "projects.json")
with open(JSON_PATH, encoding="utf-8") as f:
    projects = json.load(f)

# ─── ROTA PRINCIPAL ─────────────────────────────────────────────────────────
@app.route("/")
def index():
    start_pipeline()  # dispara em background, se ainda não rodando
    disciplines = sorted({p["discipline"] for p in projects})
    return render_template("index.html", projects=projects, disciplines=disciplines)

# ─── Detalhe de projeto ────────────────────────────────────────────────────
@app.route("/projects/<int:project_id>")
def project_detail(project_id):
    proj = next((p for p in projects if p["id"] == project_id), None)
    if not proj:
        abort(404)
    return render_template("projects.html", project=proj)

# ─── Exclui projeto ─────────────────────────────────────────────────────────
@app.route("/delete/<int:project_id>", methods=["POST"])
def delete_project(project_id):
    global projects
    projects = [p for p in projects if p["id"] != project_id]
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(projects, f, indent=2, ensure_ascii=False)
    return redirect(url_for("index"))

# ─── Cria projeto ──────────────────────────────────────────────────────────
@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        title       = request.form.get("title", "").strip()
        discipline  = request.form.get("discipline", "").strip()
        unit        = request.form.get("unit", "").strip()
        # captura múltiplas habilidades
        abilities   = request.form.getlist("abilities")
        content     = request.form.get("content", "").strip()

        # validação: todas as strings e pelo menos uma habilidade
        if not all([title, discipline, unit, content]) or not abilities:
            abort(400, "Campos obrigatórios faltando.")

        new_id = max((p["id"] for p in projects), default=0) + 1

        file = request.files.get("cover_image")
        if file and allowed_file(file.filename):
            fn = secure_filename(f"{new_id}_{datetime.now():%Y%m%d%H%M%S}_{file.filename}")
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], fn))
            img = f"images/{fn}"
        else:
            img = "images/placeholder.jpg"

        projects.append({
            "id": new_id,
            "name": title,
            "discipline": discipline,
            "unit": unit,
            # armazena a lista de códigos selecionados
            "abilities": abilities,
            "description": content,
            "image": img
        })
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(projects, f, indent=2, ensure_ascii=False)

        return redirect(url_for("project_detail", project_id=new_id))

    return render_template("create.html", edit_mode=False)


# ─── Edita projeto ─────────────────────────────────────────────────────────
@app.route("/edit/<int:project_id>", methods=["GET", "POST"])
def edit_project(project_id):
    proj = next((p for p in projects if p["id"] == project_id), None)
    if not proj:
        abort(404)

    if request.method == "POST":
        title       = request.form.get("title", "").strip()
        discipline  = request.form.get("discipline", "").strip()
        unit        = request.form.get("unit", "").strip()
        # captura múltiplas habilidades
        abilities   = request.form.getlist("abilities")
        content     = request.form.get("content", "").strip()

        if not all([title, discipline, unit, content]) or not abilities:
            abort(400, "Campos obrigatórios faltando.")

        file = request.files.get("cover_image")
        if file and allowed_file(file.filename):
            fn = secure_filename(f"{project_id}_{datetime.now():%Y%m%d%H%M%S}_{file.filename}")
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], fn))
            proj["image"] = f"images/{fn}"

        proj.update({
            "name": title,
            "discipline": discipline,
            "unit": unit,
            # substitui a lista de habilidades
            "abilities": abilities,
            "description": content
        })

        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(projects, f, indent=2, ensure_ascii=False)

        return redirect(url_for("project_detail", project_id=project_id))

    return render_template("create.html", project=proj, edit_mode=True)


# ─── Rotas de JSON/HTML de habilidades (lazy-load) ─────────────────────────
HAB_PATH = os.path.join(BASE_DIR, "habilidades.json")

@app.route("/habilidades.json")
def habilidades_json():
    start_pipeline()
    if not os.path.exists(HAB_PATH):
        return ("", 202)
    return send_from_directory(BASE_DIR, "habilidades.json", mimetype="application/json")

@app.route("/habilidades")
def habilidades_view():
    if not os.path.exists(HAB_PATH):
        return render_template("gerando_habilidades.html"), 202
    with open(HAB_PATH, encoding="utf-8") as f:
        hab = json.load(f)
    return render_template("habilidades.html", hab=hab)

# ─── Rotas de pilares e microbit (lazy-load) ───────────────────────────────
@app.route("/pilares")
def pilares_view():
    path = os.path.join(BASE_DIR, "pilares.json")
    with open(path, encoding="utf-8") as f:
        p = json.load(f)
    return render_template("pilares.html", pilar=p)

@app.route("/microbit")
def microbit_view():
    path = os.path.join(BASE_DIR, "microbit.json")
    with open(path, encoding="utf-8") as f:
        m = json.load(f)
    return render_template("microbit.html", micro=m)

if __name__ == "__main__":
    app.run(debug=True)
