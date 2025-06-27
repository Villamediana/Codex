#!/usr/bin/env python3
# gera_json_bncc_expand_v4.py  –  somente linhas com disciplina, ano, unidade e habilidade
# agora tolera ausência de “EXPLICAÇÃO” sem quebrar

import csv, json, pathlib, re
from collections import defaultdict, OrderedDict

ARQUIVO_TXT  = "teste.txt"        # TSV separado por TAB
ARQUIVO_JSON = "habilidades.json"

CODIGO_RE = re.compile(r"\((EF\d{2}[A-Z]{2}\d{2})\)")

# disciplina → ano → unidade → [habilidade_dict]
hierarquia = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

with open(ARQUIVO_TXT, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f, delimiter="\t")
    for row in reader:
        disc    = (row.get("DISCIPLINA") or "").strip()
        ano     = (row.get("ANO") or "").strip()
        unidade = (row.get("UNIDADES TEMÁTICAS") or "").strip()
        hab_txt = (row.get("HABILIDADES") or "").strip()

        # só processa se esses quatro campos estiverem preenchidos
        if not (disc and ano and unidade and hab_txt):
            continue

        objeto     = (row.get("OBJETOS DE CONHECIMENTO") or "").strip()
        explicacao = (row.get("EXPLICAÇÃO") or "").strip()

        pilares = []
        if (row.get("PILAR DE DECOMPOSIÇÃO") or "").strip().upper() == "X":
            pilares.append("Decomposição")
        if (row.get("PILAR DE RECONHECIMENTO DE PADRÕES") or "").strip().upper() == "X":
            pilares.append("Reconhecimento de Padrões")
        if (row.get("PILAR DE ABSTRAÇÃO") or "").strip().upper() == "X":
            pilares.append("Abstração")
        if (row.get("PILAR DE ALGORITMOS") or "").strip().upper() == "X":
            pilares.append("Algoritmos")

        m = CODIGO_RE.search(hab_txt)
        codigo = m.group(1) if m else "--"
        desc   = hab_txt.split(")", 1)[-1].strip()

        habilidade = {
            "codigo":     codigo,
            "descricao":  desc,
            "objeto":     objeto,
            "pilares":    pilares,
            "explicacao": explicacao
        }
        hierarquia[disc][ano][unidade].append(habilidade)

# ─── Monta “data” filtrando níveis vazios ───────────────────────────────
disciplinas_list = []
for disc, anos in sorted(hierarquia.items()):
    anos_list = []
    for ano, unidades in sorted(anos.items()):
        unidades_list = []
        for unidade, habs in sorted(unidades.items()):
            if habs:
                unidades_list.append({
                    "unidade":     unidade,
                    "habilidades": habs
                })
        if unidades_list:
            anos_list.append({
                "ano":      ano,
                "unidades": unidades_list
            })
    if anos_list:
        disciplinas_list.append({
            "disciplina": disc,
            "anos":       anos_list
        })

# ─── Gera HTML aninhado (<details>) ───────────────────────────────────
def add_indent(lines, lvl):
    return [("  " * lvl) + l for l in lines]

def habilidade_para_html(h):
    pilares_txt = ", ".join(h["pilares"]) or "—"
    return (
        f"<details class='hab-det'>"
        f"<summary><span class='hab-code'>{h['codigo']}</span> {h['descricao']}</summary>"
        f"<p><strong>Pilares:</strong> {pilares_txt}</p>"
        f"<p><strong>Objeto de conhecimento:</strong> {h['objeto']}</p>"
        f"<p><strong>Explicação:</strong> {h['explicacao']}</p>"
        f"</details>"
    )

blocos_html = []
for disc in disciplinas_list:
    blocos_html.append(f"<details><summary><b>{disc['disciplina']}</b></summary>")
    for ano in disc["anos"]:
        blocos_html.extend(add_indent([f"<details><summary>{ano['ano']}</summary>"], 1))
        for uni in ano["unidades"]:
            blocos_html.extend(add_indent([f"<details><summary>{uni['unidade']}</summary>"], 2))
            blocos_html.extend(add_indent(["<ul style='list-style:none;padding-left:0;'>"], 3))
            blocos_html.extend(
                add_indent([f"<li>{habilidade_para_html(h)}</li>" for h in uni["habilidades"]], 4)
            )
            blocos_html.extend(add_indent(["</ul></details>"], 3))
        blocos_html.extend(add_indent(["</details>"], 1))
    blocos_html.append("</details>\n")

# ─── Salva JSON final ───────────────────────────────────────────────────
objeto_json = OrderedDict([
    ("id",     1),
    ("name",   "Habilidades BNCC"),
    ("short",  "Coleção completa de habilidades (6º ao 9º ano)"),
    ("image",  "images/habilidades_bncc.jpg"),
    ("data",   disciplinas_list),
    ("html",   "\n".join(blocos_html))
])

path = pathlib.Path(ARQUIVO_JSON)
path.write_text(json.dumps(objeto_json, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"✅ JSON salvo em: {path.resolve()}")
