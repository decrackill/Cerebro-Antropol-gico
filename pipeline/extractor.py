"""
Lee un PDF completo, lo divide en fragmentos con rastreo de páginas,
y extrae entidades/relaciones con Gemini, acumulando candidatos.

Uso: python extractor.py ../libros/argonautas.pdf
Opcional: python extractor.py ../libros/argonautas.pdf --max-chunks 5
"""
import sys
import json
import sqlite3
import os
import time
import argparse
from pathlib import Path
from google import genai
from dotenv import load_dotenv
import fitz  # PyMuPDF

from prompts import build_prompt_extraccion_grafo

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")
DB_PATH = BASE_DIR.parent / "data" / "grafo.db"

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = "gemini-2.5-flash"

CARACTERES_POR_CHUNK = 40000
PAUSA_ENTRE_LLAMADAS = 4


def cargar_nodos_existentes():
    conn = sqlite3.connect(DB_PATH)
    filas = conn.execute("SELECT id, tipo, nombre FROM nodos").fetchall()
    conn.close()
    return [{"id": f[0], "tipo": f[1], "nombre": f[2]} for f in filas]


def extraer_paginas_pdf(ruta):
    doc = fitz.open(ruta)
    paginas = [(i + 1, pagina.get_text()) for i, pagina in enumerate(doc)]
    doc.close()
    return paginas


def dividir_en_chunks(paginas, tamano=CARACTERES_POR_CHUNK):
    chunks = []
    texto_actual = ""
    pagina_inicio = None

    for num_pagina, texto_pagina in paginas:
        if pagina_inicio is None:
            pagina_inicio = num_pagina

        if len(texto_actual) + len(texto_pagina) > tamano and texto_actual:
            chunks.append({
                "texto": texto_actual,
                "pagina_inicio": pagina_inicio,
                "pagina_fin": num_pagina - 1,
            })
            texto_actual = texto_pagina
            pagina_inicio = num_pagina
        else:
            texto_actual += "\n\n" + texto_pagina

    if texto_actual.strip():
        chunks.append({
            "texto": texto_actual,
            "pagina_inicio": pagina_inicio,
            "pagina_fin": paginas[-1][0],
        })

    return chunks


TIPOS_ALIAS = {"libro": "obra", "libros": "obra", "texto": "obra"}


def normalizar_tipos(resultado):
    for n in resultado.get("nodos_nuevos", []):
        if n["tipo"] in TIPOS_ALIAS:
            n["tipo"] = TIPOS_ALIAS[n["tipo"]]
    return resultado


def procesar_chunk(texto_chunk, nodos_existentes, nodos_nuevos_acumulados):
    catalogo_completo = nodos_existentes + [
        {"id": n["id"], "tipo": n["tipo"], "nombre": n["nombre"]}
        for n in nodos_nuevos_acumulados
    ]
    prompt_sistema = build_prompt_extraccion_grafo(catalogo_completo)

    respuesta = client.models.generate_content(
        model=MODEL,
        contents=texto_chunk,
        config={"system_instruction": prompt_sistema},
    )

    texto_json = respuesta.text.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(texto_json)
    except json.JSONDecodeError:
        print("  ⚠ Chunk devolvió JSON inválido, se omite. Respuesta:")
        print("   ", texto_json[:200])
        return {"nodos_nuevos": [], "relaciones_nuevas": []}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf")
    parser.add_argument("--max-chunks", type=int, default=None, help="Limita cuántos chunks procesar (para pruebas)")
    args = parser.parse_args()

    print(f"◈ Leyendo {args.pdf}...")
    paginas = extraer_paginas_pdf(args.pdf)
    print(f"  {len(paginas)} páginas extraídas")

    chunks = dividir_en_chunks(paginas)
    if args.max_chunks:
        chunks = chunks[: args.max_chunks]
    print(f"  Dividido en {len(chunks)} fragmentos")

    nodos_existentes = cargar_nodos_existentes()
    print(f"  {len(nodos_existentes)} nodos existentes cargados como contexto\n")

    nodos_acumulados = []
    relaciones_acumuladas = []
    nombre_pdf = Path(args.pdf).name

    for i, chunk in enumerate(chunks, 1):
        print(f"◈ Procesando fragmento {i}/{len(chunks)} (páginas {chunk['pagina_inicio']}-{chunk['pagina_fin']})...")
        resultado = procesar_chunk(chunk["texto"], nodos_existentes, nodos_acumulados)
        resultado = normalizar_tipos(resultado)

        nuevos = resultado.get("nodos_nuevos", [])
        nuevas_rels = resultado.get("relaciones_nuevas", [])

        fuente_str = f"{nombre_pdf}, p.{chunk['pagina_inicio']}-{chunk['pagina_fin']}"
        for r in nuevas_rels:
            r["fuente"] = fuente_str

        nodos_acumulados.extend(nuevos)
        relaciones_acumuladas.extend(nuevas_rels)

        print(f"  +{len(nuevos)} nodos, +{len(nuevas_rels)} relaciones (acumulado: {len(nodos_acumulados)}, {len(relaciones_acumuladas)})")

        if i < len(chunks):
            time.sleep(PAUSA_ENTRE_LLAMADAS)

    out_path = BASE_DIR / "candidatos_pendientes.json"
    out_path.write_text(
        json.dumps(
            {"nodos_nuevos": nodos_acumulados, "relaciones_nuevas": relaciones_acumuladas},
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )

    print(f"\n✓ Total: {len(nodos_acumulados)} nodos y {len(relaciones_acumuladas)} relaciones propuestas")
    print(f"  Guardado en {out_path}")
    print(f"  Siguiente paso: python revisar.py")


if __name__ == "__main__":
    main()
