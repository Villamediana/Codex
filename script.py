#!/usr/bin/env python3
# bncc_pipeline.py  –  módulo importável: pipoca script ou background

import os
import csv
import json
import re
import requests
import pandas as pd
import subprocess
import psutil

from io import BytesIO, StringIO
from collections import defaultdict, OrderedDict
from pathlib import Path

# ——— Configurações ——————————————————————————————————————————
SHEET_ID     = "1Ucm0ejpZvPp_D1iaCOskYsZwH67xl9xJJ6Of_7RsUu4"
EXPORT_URL   = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"
ARQUIVO_JSON = "habilidades.json"
CODIGO_RE    = re.compile(r"\((EF\d{2}[A-Z]{2}\d{2})\)")

# ——— 1) Pipeline principal ————————————————————————————————————
def main():
    # 1. baixa XLSX
    resp = requests.get(EXPORT_URL)
    resp.raise_for_status()
    xls = pd.ExcelFile(BytesIO(resp.content))

    # 2. concatena abas em TSV em memória
    tsv_buf = StringIO()
    first    = True
    for sheet in xls.sheet_names:
        df = xls.parse(sheet_name=sheet, dtype=str).fillna("")
        df.to_csv(tsv_buf, sep="\t", index=False, header=first)
        first = False
    tsv_buf.seek(0)

    # 3. lê o TSV e monta hierarquia
    hierarquia = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    reader     = csv.DictReader(tsv_buf, delimiter="\t")
    for row in reader:
        disc    = (row.get("DISCIPLINA") or "").strip()
        ano     = (row.get("ANO") or "").strip()
        uni     = (row.get("UNIDADES TEMÁTICAS") or "").strip()
        hab_txt = (row.get("HABILIDADES") or "").strip()
        if not (disc and ano and uni and hab_txt):
            continue

        objeto     = (row.get("OBJETOS DE CONHECIMENTO") or "").strip()
        explicacao = (row.get("EXPLICAÇÃO") or "").strip()

        pilares = []
        if row.get("PILAR DE DECOMPOSIÇÃO","").strip().upper()=="X":
            pilares.append("Decomposição")
        if row.get("PILAR DE RECONHECIMENTO DE PADRÕES","").strip().upper()=="X":
            pilares.append("Reconhecimento de Padrões")
        if row.get("PILAR DE ABSTRAÇÃO","").strip().upper()=="X":
            pilares.append("Abstração")
        if row.get("PILAR DE ALGORITMOS","").strip().upper()=="X":
            pilares.append("Algoritmos")

        m      = CODIGO_RE.search(hab_txt)
        codigo = m.group(1) if m else "--"
        desc   = hab_txt.split(")",1)[-1].strip()

        hab = {
            "codigo":    codigo,
            "descricao": desc,
            "objeto":    objeto,
            "pilares":   pilares,
            "explicacao": explicacao
        }
        hierarquia[disc][ano][uni].append(hab)

    # 4. transforma em lista ordenada
    disciplinas = []
    for disc, anos in sorted(hierarquia.items()):
        anos_list = []
        for ano, unis in sorted(anos.items()):
            uni_list = [{"unidade": u, "habilidades": hs} for u,hs in sorted(unis.items()) if hs]
            if uni_list:
                anos_list.append({"ano": ano, "unidades": uni_list})
        if anos_list:
            disciplinas.append({"disciplina": disc, "anos": anos_list})

    # 5. gera HTML
    def add_indent(lines, lvl):
        return [("  "*lvl)+l for l in lines]
    def hab_html(h):
        ptxt = ", ".join(h["pilares"]) or "—"
        return (
            f"<details class='hab-det'>"
            f"<summary><span class='hab-code'>{h['codigo']}</span> {h['descricao']}</summary>"
            f"<p><strong>Pilares:</strong> {ptxt}</p>"
            f"<p><strong>Objeto:</strong> {h['objeto']}</p>"
            f"<p><strong>Explicação:</strong> {h['explicacao']}</p>"
            f"</details>"
        )

    html_blocks = []
    for d in disciplinas:
        html_blocks.append(f"<details><summary><b>{d['disciplina']}</b></summary>")
        for a in d["anos"]:
            html_blocks.extend(add_indent([f"<details><summary>{a['ano']}</summary>"],1))
            for u in a["unidades"]:
                html_blocks.extend(add_indent([f"<details><summary>{u['unidade']}</summary>"],2))
                html_blocks.extend(add_indent(["<ul style='list-style:none;padding-left:0;'>"],3))
                html_blocks.extend(
                    add_indent([f"<li>{hab_html(h)}</li>" for h in u["habilidades"]], 4)
                )
                html_blocks.extend(add_indent(["</ul></details>"],3))
            html_blocks.extend(add_indent(["</details>"],1))
        html_blocks.append("</details>\n")

    # 6. escreve JSON
    out = OrderedDict([
        ("id",    1),
        ("name",  "Habilidades BNCC"),
        ("short", "Coleção completa de habilidades (6º ao 9º ano)"),
        ("image","images/habilidades_bncc.jpg"),
        ("data", disciplinas),
        ("html", "\n".join(html_blocks))
    ])
    Path(ARQUIVO_JSON).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ JSON salvo em: {Path(ARQUIVO_JSON).resolve()}")

# ——— 2) Helpers para background ————————————————————————————
MODULE_PATH = os.path.abspath(__file__)
MODULE_NAME = os.path.basename(MODULE_PATH)

def is_pipeline_running():
    for proc in psutil.process_iter(['cmdline']):
        cmd = proc.info['cmdline']
        if cmd and MODULE_NAME in cmd:
            return True
    return False

def start_pipeline():
    """
    Dispara em outro processo o próprio módulo,
    só se ainda não estiver rodando.
    """
    if not is_pipeline_running():
        subprocess.Popen(
            ['python', MODULE_PATH],
            cwd=os.path.dirname(MODULE_PATH),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

# permite rodar como script normal
if __name__ == "__main__":
    main()
