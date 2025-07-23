from flask import (
    Flask, render_template, render_template_string, abort,
    request, redirect, url_for, send_from_directory, session
)
from werkzeug.utils import secure_filename
from datetime import datetime
import json, os

from script import start_pipeline  # seu módulo de pipeline/background

app = Flask(__name__)
app.secret_key = "4cpp0t12018**A"

# ─── Configurações ────────────────────────────────────────────────────────
ADMIN_PASSWORD      = "1f1sul*2o25"
ALLOWED_EXTENSIONS  = {"png", "jpg", "jpeg", "gif"}
BASE_DIR            = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER       = os.path.join(BASE_DIR, "static", "images")
JSON_PATH           = os.path.join(BASE_DIR, "projects.json")
HAB_PATH            = os.path.join(BASE_DIR, "habilidades.json")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ─── Helpers ──────────────────────────────────────────────────────────────
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def load_projects() -> list[dict]:
    """Carrega JSON garantindo chaves obrigatórias."""
    if not os.path.exists(JSON_PATH):
        return []
    with open(JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)

    dirty = False
    for p in data:
        if "aprov" not in p:
            p["aprov"] = False
            dirty = True
        if "prev_id" not in p:
            p["prev_id"] = None
            dirty = True
    if dirty:
        save_projects(data)
    return data


def save_projects(data: list[dict]) -> None:
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def approved_only(data: list[dict]) -> list[dict]:
    return [p for p in data if p.get("aprov")]


# carrega em memória na partida
all_projects = load_projects()


# ─── Rotas principais ─────────────────────────────────────────────────────
@app.route("/")
def index():
    projects    = approved_only(all_projects)
    disciplines = sorted({p["discipline"] for p in projects})
    return render_template("index.html", projects=projects, disciplines=disciplines)


@app.route("/projects/<int:project_id>")
def project_detail(project_id):
    proj = next((p for p in all_projects if p["id"] == project_id), None)
    if not proj:
        abort(404)
    return render_template("projects.html", project=proj)


@app.route("/delete/<int:project_id>", methods=["POST"])
def delete_project(project_id):
    global all_projects
    all_projects = [p for p in all_projects if p["id"] != project_id]
    save_projects(all_projects)
    return redirect(url_for("index"))


@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        title      = request.form.get("title", "").strip()
        discipline = request.form.get("discipline", "").strip()
        unit       = request.form.get("unit", "").strip()
        abilities  = request.form.getlist("abilities")
        content    = request.form.get("content", "").strip()

        if not all([title, discipline, unit, content]) or not abilities:
            abort(400, "Campos obrigatórios faltando.")

        new_id = max((p["id"] for p in all_projects), default=0) + 1

        file = request.files.get("cover_image")
        if file and allowed_file(file.filename):
            fn = secure_filename(f"{new_id}_{datetime.now():%Y%m%d%H%M%S}_{file.filename}")
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], fn))
            img = f"images/{fn}"
        else:
            img = "images/placeholder.jpg"

        new_proj = {
            "id":          new_id,
            "prev_id":     None,          # projeto original
            "name":        title,
            "discipline":  discipline,
            "unit":        unit,
            "abilities":   abilities,
            "description": content,
            "image":       img,
            "aprov":       False
        }
        all_projects.append(new_proj)
        save_projects(all_projects)

        return redirect(url_for("project_detail", project_id=new_id))

    return render_template("create.html", edit_mode=False)


@app.route("/edit/<int:project_id>", methods=["GET", "POST"])
def edit_project(project_id):
    orig = next((p for p in all_projects if p["id"] == project_id), None)
    if not orig:
        abort(404)

    if request.method == "POST":
        title      = request.form.get("title", "").strip()
        discipline = request.form.get("discipline", "").strip()
        unit       = request.form.get("unit", "").strip()
        abilities  = request.form.getlist("abilities")
        content    = request.form.get("content", "").strip()

        if not all([title, discipline, unit, content]) or not abilities:
            abort(400, "Campos obrigatórios faltando.")

        # cria nova versão pendente sem alterar a aprovada
        new_id = max((p["id"] for p in all_projects), default=0) + 1
        file   = request.files.get("cover_image")

        if file and allowed_file(file.filename):
            fn = secure_filename(f"{new_id}_{datetime.now():%Y%m%d%H%M%S}_{file.filename}")
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], fn))
            img = f"images/{fn}"
        else:
            img = orig["image"]

        new_proj = {
            "id":          new_id,
            "prev_id":     project_id,    # aponta para versão anterior
            "name":        title,
            "discipline":  discipline,
            "unit":        unit,
            "abilities":   abilities,
            "description": content,
            "image":       img,
            "aprov":       False          # precisa de aprovação
        }
        all_projects.append(new_proj)
        save_projects(all_projects)
        return redirect(url_for("project_detail", project_id=new_id))

    return render_template("create.html", project=orig, edit_mode=True)


# ─── Área administrativa ──────────────────────────────────────────────────
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="utf-8"><title>Login Admin</title></head>
<body style="font-family:sans-serif; text-align:center; margin-top:10vh;">
  <h2>Área Restrita</h2>
  <form method="post">
    <input type="password" name="password" placeholder="Senha de admin" autofocus required style="font-size:1.2rem;padding:.5rem;">
    <br><br>
    <button type="submit" style="font-size:1.1rem;padding:.5rem 1rem;">Entrar</button>
  </form>
  {% if error %}<p style="color:#c00;">{{ error }}</p>{% endif %}
</body>
</html>
"""


@app.route("/pending", methods=["GET", "POST"])
def pending_projects():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["is_admin"] = True
            return redirect(url_for("pending_projects"))
        return render_template_string(LOGIN_HTML, error="Senha incorreta.")

    if not session.get("is_admin"):
        return render_template_string(LOGIN_HTML, error=None)

    pendentes = [p for p in all_projects if not p.get("aprov")]
    return render_template("pending.html", projects=pendentes)


@app.route("/approve/<int:project_id>", methods=["POST"], endpoint="approve_project")
def approve_project(project_id):
    """Aprova nova versão e desativa antiga, se houver."""
    if not session.get("is_admin"):
        abort(401)

    proj = next((p for p in all_projects if p["id"] == project_id), None)
    if not proj:
        abort(404)

    # aprova novo
    proj["aprov"] = True

    # se for revisão, desativa versão anterior aprovada
    prev_id = proj.get("prev_id")
    if prev_id is not None:
        old = next((p for p in all_projects if p["id"] == prev_id), None)
        if old:
            old["aprov"] = False

    save_projects(all_projects)
    return "", 204

@app.route("/reject/<int:project_id>", methods=["POST"], endpoint="reject_project")
def reject_project(project_id):
    """Rejeita (remove) uma proposta de projeto pendente."""
    if not session.get("is_admin"):
        abort(401)

    global all_projects
    before = len(all_projects)
    all_projects = [p for p in all_projects if p["id"] != project_id]
    if len(all_projects) < before:
        save_projects(all_projects)
        return "", 204  # sucesso, sem conteúdo
    else:
        abort(404)


# ─── Dados auxiliares (lazy‑load) ─────────────────────────────────────────
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


# ─── Execução ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)
