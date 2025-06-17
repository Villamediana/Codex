#!/usr/bin/env python3
# gera_json_bncc_expand.py  –  versão sem duplicar Línguas

import json, re, pathlib

ARQUIVO_TXT  = "teste.txt"
ARQUIVO_JSON = "habilidades.json"

# prefixo do código → [Título bonitinho, lista coletiva de itens]
TITLES = {
    "CI": ["🌱 Ciências da Natureza", []],
    "MA": ["➗ Matemática",           []],
    "GE": ["🌍 Ciências Humanas",     []],
    "HI": ["🌍 Ciências Humanas",     []],   # História junto
    "LP": ["🗣️ Línguas Portuguesa e Inglesa", []],
    # LI será alias para LP logo abaixo
    "AR": ["🎨 Artes e Educação Física", []],
}

# Faz LI apontar para o MESMO objeto de LP (mesma lista de itens)
TITLES["LI"] = TITLES["LP"]

padrao_codigo = re.compile(r"\((EF\d{2}([A-Z]{2})\d{2})\)\s*(.*)")

with open(ARQUIVO_TXT, encoding="utf-8") as f:
    for linha in f:
        linha = linha.strip()
        if not linha:
            continue
        codigo_e_desc = linha.split("\t")[-1]          # 4º campo
        m = padrao_codigo.match(codigo_e_desc)
        if not m:
            continue
        codigo_completo, prefixo, descricao = m.groups()
        TITLES[prefixo][1].append(f"({codigo_completo}) {descricao}")

# Gera HTML expansível, evitando repetição de títulos
blocos_html, vistos = [], set()
for titulo, itens in (v for v in TITLES.values() if v[1]):
    if titulo in vistos:
        continue
    vistos.add(titulo)
    blocos_html.append("<details>")
    blocos_html.append(f"  <summary>{titulo}</summary>")
    blocos_html.append("  <ul>")
    blocos_html.extend(f"    <li>{item}</li>" for item in itens)
    blocos_html.append("  </ul>")
    blocos_html.append("</details>\n")

objeto_json = {
    "id":   1,
    "name": "Habilidades BNCC",
    "short": "Coleção completa de habilidades (6º ao 9º ano)",
    "description": "\n".join(blocos_html),
    "image": "images/habilidades_bncc.jpg"
}

path = pathlib.Path(ARQUIVO_JSON)
path.write_text(json.dumps(objeto_json, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"✅ JSON salvo em: {path.resolve()}")
