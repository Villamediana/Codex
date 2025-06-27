from flask import Flask, render_template, abort, request, redirect, url_for
import json
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)

# ─── Configuração de upload ────────────────────────────────────────────────
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "images")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed_file(filename):
    ext = filename.lower().rsplit(".", 1)[-1]
    return "." in filename and ext in ALLOWED_EXTENSIONS

# ─── Carga inicial de projects.json ──────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE_DIR, "projects.json")
with open(JSON_PATH, encoding="utf-8") as f:
    projects = json.load(f)


@app.route("/")
def index():
    # calcula as disciplinas únicas, ordenadas
    disciplines = sorted({ p["discipline"] for p in projects })
    return render_template("index.html",
                           projects=projects,
                           disciplines=disciplines)

@app.route("/projects/<int:project_id>")
def project_detail(project_id):
    proyecto = next((p for p in projects if p["id"] == project_id), None)
    if not proyecto:
        abort(404)
    return render_template("projects.html", project=proyecto)


from flask import send_from_directory

@app.route("/habilidades.json")
def habilidades_json():
    return send_from_directory(".", "habilidades.json")  # diretório do app


# ─── ROTA: Excluir projeto ───────────────────────────────────
@app.route("/delete/<int:project_id>", methods=["POST"])
def delete_project(project_id):
    global projects
    # Filtra, removendo o projeto com esse ID
    projects = [p for p in projects if p["id"] != project_id]
    # Reescreve o JSON
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(projects, f, indent=2, ensure_ascii=False)
    return redirect(url_for("index"))


# ─── ROTA: Criar projeto ────────────────────────────────────────────────
@app.route("/create", methods=["GET", "POST"])
def create():
    """
    POST recebe: title, discipline, unit, ability, content, cover_image.
    Retorna 400 se faltar algo essencial. Salva imagem na pasta static/images.
    """
    if request.method == "POST":
        title      = request.form.get("title", "").strip()
        discipline = request.form.get("discipline", "").strip()
        unit       = request.form.get("unit", "").strip()
        ability    = request.form.get("ability", "").strip()
        content    = request.form.get("content", "").strip()

        # validações mínimas
        if not all([title, discipline, unit, ability, content]):
            abort(400, "Campos obrigatórios faltando.")

        # novo id incremental
        new_id = max((p["id"] for p in projects), default=0) + 1

        # upload de imagem
        file = request.files.get("cover_image")
        if file and file.filename and allowed_file(file.filename):
            filename  = secure_filename(
                f"{new_id}_{datetime.now():%Y%m%d%H%M%S}_{file.filename}"
            )
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            image_url = f"images/{filename}"
        else:
            image_url = "images/placeholder.jpg"

        projects.append({
            "id":          new_id,
            "name":        title,
            "discipline":  discipline,
            "unit":        unit,
            "ability":     ability,
            "description": content,
            "image":       image_url
        })

        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(projects, f, indent=2, ensure_ascii=False)

        return redirect(url_for("project_detail", project_id=new_id))

    # GET – template faz todo o preenchimento via JS
    return render_template("create.html", edit_mode=False)


# ─── ROTA: Editar projeto ───────────────────────────────────────────────
@app.route("/edit/<int:project_id>", methods=["GET", "POST"])
def edit_project(project_id: int):
    projeto = next((p for p in projects if p["id"] == project_id), None)
    if not projeto:
        abort(404)

    if request.method == "POST":
        title      = request.form.get("title", "").strip()
        discipline = request.form.get("discipline", "").strip()
        unit       = request.form.get("unit", "").strip()
        ability    = request.form.get("ability", "").strip()
        content    = request.form.get("content", "").strip()

        if not all([title, discipline, unit, ability, content]):
            abort(400, "Campos obrigatórios faltando.")

        # upload de nova capa (opcional)
        file = request.files.get("cover_image")
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(
                f"{project_id}_{datetime.now():%Y%m%d%H%M%S}_{file.filename}"
            )
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            projeto["image"] = f"images/{filename}"

        # atualiza campos
        projeto.update({
            "name":        title,
            "discipline":  discipline,
            "unit":        unit,
            "ability":     ability,
            "description": content
        })

        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(projects, f, indent=2, ensure_ascii=False)

        return redirect(url_for("project_detail", project_id=project_id))

    # GET – devolve template em modo edição
    return render_template(
        "create.html",
        project=projeto,
        edit_mode=True
    )


# ─── Carga inicial de pilares.json ───────────────────────────────────────
PILARES_PATH = os.path.join(BASE_DIR, "pilares.json")
with open(PILARES_PATH, encoding="utf-8") as f:
    pilares = json.load(f)          # un único dict

@app.route("/pilares")
def pilares_view():
    return render_template("pilares.html", pilar=pilares)


# ─── Carga inicial de pilares.json ───────────────────────────────────────
MICROBIT_PATH = os.path.join(BASE_DIR, "microbit.json")
with open(MICROBIT_PATH, encoding="utf-8") as f:
    microbit = json.load(f)          # un único dict

@app.route("/microbit")
def microbit_view():
    return render_template("microbit.html", micro=microbit)


# ─── Carga inicial de pilares.json ───────────────────────────────────────
HABILIDADES = os.path.join(BASE_DIR, "habilidades.json")
with open(HABILIDADES, encoding="utf-8") as f:
    habilidades = json.load(f)          # un único dict

@app.route("/habilidades")
def habilidades_view():
    return render_template("habilidades.html", hab=habilidades)



if __name__ == "__main__":
    app.run(debug=True)
