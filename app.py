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


# ─── ROTA: Criar projeto (GET + POST) ──────────────────────────────────────
@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        selected = request.form.get("discipline", "").strip()
        new_disc = request.form.get("new_discipline", "").strip()
        discipline = new_disc if new_disc else selected
        content = request.form.get("content", "").strip()

        # Validações mínimas
        if not title or not discipline or not content:
            abort(400)

        # Calcular novo ID
        new_id = (max(p["id"] for p in projects) + 1) if projects else 1

        # Lidar com upload de imagem de capa
        file = request.files.get("cover_image")
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{new_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            image_path = f"images/{filename}"
        else:
            # caso nenhum arquivo, usar placeholder
            image_path = "images/placeholder.jpg"

        new_project = {
            "id": new_id,
            "name": title,
            "discipline": discipline,
            "description": content,
            "image": image_path
        }

        projects.append(new_project)
        # Reescreve o JSON completo
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(projects, f, indent=2, ensure_ascii=False)

        return redirect(url_for("project_detail", project_id=new_id))

    disciplinas = sorted({p["discipline"] for p in projects})
    return render_template("create.html", disciplines=disciplinas)

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


# ─── ROTA: Editar projeto (GET: preenche formulário; POST: salva alterações) ───────────────────────────────────────
@app.route("/edit/<int:project_id>", methods=["GET", "POST"])
def edit_project(project_id):
    proyecto = next((p for p in projects if p["id"] == project_id), None)
    if not proyecto:
        abort(404)

    if request.method == "POST":
        # Ler dados do form (igual create, mas atualiza o projeto existente)
        title = request.form.get("title", "").strip()
        selected = request.form.get("discipline", "").strip()
        new_disc = request.form.get("new_discipline", "").strip()
        discipline = new_disc if new_disc else selected
        content = request.form.get("content", "").strip()

        if not title or not discipline or not content:
            abort(400)

        # Lidar com upload de capa (se houver)
        file = request.files.get("cover_image")
        if file and allowed_file(file.filename):
            filename = secure_filename(
                f"{project_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
            )
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            proyecto["image"] = f"images/{filename}"
        # Se não enviar imagem, mantém a anterior

        # Atualiza campos
        proyecto["name"] = title
        proyecto["discipline"] = discipline
        proyecto["description"] = content

        # Reescreve JSON
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(projects, f, indent=2, ensure_ascii=False)

        return redirect(url_for("project_detail", project_id=project_id))

    # GET: exibe form preenchido
    disciplinas = sorted({p["discipline"] for p in projects})
    return render_template(
        "create.html",
        disciplines=disciplinas,
        project=proyecto,     # passa o projeto para pre preencher
        edit_mode=True        # sinaliza o template que é edição
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
