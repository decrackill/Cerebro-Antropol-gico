"""
Lee un PDF completo, lo divide en fragmentos con rastreo de páginas,
y extrae entidades/relaciones con Gemini u OpenRouter, acumulando candidatos.
Soporta múltiples API keys con rotación automática ante errores de cuota.
Guarda checkpoint para reanudar desde donde quedó.

Uso: python extractor.py ../libros/argonautas.pdf
Opcional: python extractor.py ../libros/argonautas.pdf --max-chunks 5
Para reiniciar desde cero: python extractor.py ../libros/argonautas.pdf --reset
"""
import sys
import json
import sqlite3
import os
import time
import argparse
from pathlib import Path
from google import genai
from openai import OpenAI
from dotenv import load_dotenv
import fitz  # PyMuPDF

from .prompts import build_prompt_extraccion_grafo

from ..core.config import DB_PATH, ENV_PATH, CACHE_DIR, STATE_DIR, LOGS_DIR

load_dotenv(ENV_PATH)

GEMINI_MODEL = "gemini-2.5-flash"
OPENROUTER_MODEL = "google/gemini-2.5-flash"

CARACTERES_POR_CHUNK = 40000
PAUSA_ENTRE_LLAMADAS = 4


class APIKeyRotator:
    """Maneja múltiples API keys (Gemini y OpenRouter) con rotación automática."""

    def __init__(self):
        self.keys = []
        self.clients = []
        self.key_types = []
        self.current_index = 0
        self._load_keys()

    def _load_keys(self):
        key_num = 1
        while True:
            env_name = f"GEMINI_API_KEY" if key_num == 1 else f"GEMINI_API_KEY_{key_num}"
            key = os.getenv(env_name)
            if not key:
                break
            self.keys.append(key)
            self.clients.append(genai.Client(api_key=key))
            self.key_types.append("gemini")
            key_num += 1

        or_num = 1
        while True:
            env_name = f"OPENROUTER_API_KEY" if or_num == 1 else f"OPENROUTER_API_KEY_{or_num}"
            key = os.getenv(env_name)
            if not key:
                break
            self.keys.append(key)
            self.clients.append(OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=key,
            ))
            self.key_types.append("openrouter")
            or_num += 1

        if not self.keys:
            raise ValueError("No se encontró GEMINI_API_KEY ni OPENROUTER_API_KEY en .env")

    def get_client(self):
        return self.clients[self.current_index]

    def get_key_type(self):
        return self.key_types[self.current_index]

    def rotate(self):
        """Rota a la siguiente key. Devuelve False si ya no quedan keys."""
        self.current_index += 1
        if self.current_index >= len(self.keys):
            self.current_index = 0
            return False
        return True

    def current_key_index(self):
        return self.current_index + 1

    def total_keys(self):
        return len(self.keys)


_api_rotator = None


def _get_api_rotator():
    global _api_rotator
    if _api_rotator is None:
        _api_rotator = APIKeyRotator()
    return _api_rotator


def cargar_nodos_existentes():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    filas = conn.execute("SELECT id, tipo, nombre FROM nodos").fetchall()
    conn.close()
    existentes = [{"id": f[0], "tipo": f[1], "nombre": f[2]} for f in filas]

    pendientes_path = CACHE_DIR / "candidatos_pendientes.json"
    if pendientes_path.exists():
        pendientes = json.loads(pendientes_path.read_text(encoding="utf-8"))
        for n in pendientes.get("nodos_nuevos", []):
            existentes.append({"id": n["id"], "tipo": n["tipo"], "nombre": n["nombre"]})

    return existentes


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


def get_checkpoint_path(nombre_pdf):
    return STATE_DIR / f"checkpoint_{Path(nombre_pdf).stem}.json"


def cargar_checkpoint(nombre_pdf):
    path = get_checkpoint_path(nombre_pdf)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"chunks_procesados": [], "total_chunks": 0}


def guardar_checkpoint(nombre_pdf, checkpoint):
    path = get_checkpoint_path(nombre_pdf)
    path.write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2), encoding="utf-8")


def chunk_ya_procesado(checkpoint, indice_chunk):
    return indice_chunk in checkpoint.get("chunks_procesados", [])


def procesar_chunk(texto_chunk, nodos_existentes, nodos_nuevos_acumulados, log_fallos, indice_chunk):
    catalogo_completo = nodos_existentes + [
        {"id": n["id"], "tipo": n["tipo"], "nombre": n["nombre"]}
        for n in nodos_nuevos_acumulados
    ]
    prompt_sistema = build_prompt_extraccion_grafo(catalogo_completo)

    intentos = 0
    max_intentos = _get_api_rotator().total_keys() + 1

    while intentos < max_intentos:
        try:
            client = _get_api_rotator().get_client()
            key_type = _get_api_rotator().get_key_type()

            if key_type == "openrouter":
                respuesta = client.chat.completions.create(
                    model=OPENROUTER_MODEL,
                    max_tokens=8000,
                    messages=[
                        {"role": "system", "content": prompt_sistema},
                        {"role": "user", "content": texto_chunk},
                    ],
                )
                texto_respuesta = respuesta.choices[0].message.content
            else:
                respuesta = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=texto_chunk,
                    config={"system_instruction": prompt_sistema},
                )
                texto_respuesta = respuesta.text
            break
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "rate_limit" in error_str.lower():
                intentos += 1
                if intentos < max_intentos:
                    print(f"  ⚠ Key {_get_api_rotator().current_key_index()} ({key_type}) sin cuota, rotando a siguiente...")
                    _get_api_rotator().rotate()
                    time.sleep(2)
                else:
                    print(f"  ⚠ Todas las keys agotadas en chunk {indice_chunk}")
                    log_fallos.append({
                        "chunk_index": indice_chunk,
                        "razon": "todas_las_keys_agotadas",
                        "respuesta_cruda": "",
                    })
                    return {"nodos_nuevos": [], "relaciones_nuevas": []}
            else:
                print(f"  ⚠ Error API en chunk {indice_chunk}: {e}")
                log_fallos.append({
                    "chunk_index": indice_chunk,
                    "razon": f"api_error: {str(e)[:100]}",
                    "respuesta_cruda": "",
                })
                return {"nodos_nuevos": [], "relaciones_nuevas": []}

    texto_json = texto_respuesta.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(texto_json)
    except json.JSONDecodeError:
        print("  ⚠ Chunk devolvió JSON inválido, se omite. Respuesta:")
        print("   ", texto_json[:200])
        log_fallos.append({
            "chunk_index": indice_chunk,
            "razon": "json_invalido",
            "respuesta_cruda": texto_json[:500],
        })
        return {"nodos_nuevos": [], "relaciones_nuevas": []}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf")
    parser.add_argument("--max-chunks", type=int, default=None, help="Limita cuántos chunks procesar (para pruebas)")
    parser.add_argument("--reset", action="store_true", help="Reinicia el checkpoint y procesa todos los chunks")
    args = parser.parse_args()

    nombre_pdf = Path(args.pdf).name

    if args.reset:
        checkpoint_path = get_checkpoint_path(nombre_pdf)
        if checkpoint_path.exists():
            checkpoint_path.unlink()
        print("✓ Checkpoint reiniciado\n")

    print(f"◈ Leyendo {args.pdf}...")
    paginas = extraer_paginas_pdf(args.pdf)
    print(f"  {len(paginas)} páginas extraídas")
    print(f"  {_get_api_rotator().total_keys()} API key(s) disponible(s) para rotación")
    for i in range(_get_api_rotator().total_keys()):
        tipo = _get_api_rotator().key_types[i]
        print(f"    - Key {i+1}: {tipo}")

    chunks = dividir_en_chunks(paginas)
    if args.max_chunks:
        chunks = chunks[: args.max_chunks]
    print(f"  Dividido en {len(chunks)} fragmentos")

    checkpoint = cargar_checkpoint(nombre_pdf)
    chunks_pendientes = [i for i in range(len(chunks)) if not chunk_ya_procesado(checkpoint, i + 1)]

    if not chunks_pendientes:
        print(f"\n✓ Todos los {len(chunks)} chunks ya fueron procesados. Nothing to do.")
        return

    print(f"  Checkpoint: {len(checkpoint.get('chunks_procesados', []))} chunk(s) ya procesado(s)")
    print(f"  Pendientes: {len(chunks_pendientes)} chunk(s)\n")

    nodos_existentes = cargar_nodos_existentes()
    print(f"  {len(nodos_existentes)} nodos existentes cargados como contexto\n")

    nodos_acumulados = []
    relaciones_acumuladas = []
    log_fallos = []

    try:
        for idx in chunks_pendientes:
            i = idx + 1
            chunk = chunks[idx]
            print(f"◈ Procesando fragmento {i}/{len(chunks)} (páginas {chunk['pagina_inicio']}-{chunk['pagina_fin']})...")
            resultado = procesar_chunk(chunk["texto"], nodos_existentes, nodos_acumulados, log_fallos, i)
            resultado = normalizar_tipos(resultado)

            nuevos = resultado.get("nodos_nuevos", [])
            nuevas_rels = resultado.get("relaciones_nuevas", [])

            if nuevos or nuevas_rels:
                fuente_str = f"{nombre_pdf}, p.{chunk['pagina_inicio']}-{chunk['pagina_fin']}"
                for r in nuevas_rels:
                    r["fuente"] = fuente_str

                nodos_acumulados.extend(nuevos)
                relaciones_acumuladas.extend(nuevas_rels)

                checkpoint.setdefault("chunks_procesados", []).append(i)
                checkpoint["total_chunks"] = len(chunks)
                guardar_checkpoint(nombre_pdf, checkpoint)

                print(f"  +{len(nuevos)} nodos, +{len(nuevas_rels)} relaciones ✓ checkpoint guardado")
            else:
                print(f"  Chunk {i}: sin resultados nuevos (omitido del checkpoint)")

            if idx != chunks_pendientes[-1]:
                time.sleep(PAUSA_ENTRE_LLAMADAS)
    except Exception as e:
        print(f"\n⚠ Error en fragmento {i}/{len(chunks)}: {e}")
        print(f"  Guardando resultados parciales ({len(nodos_acumulados)} nodos, {len(relaciones_acumuladas)} relaciones)...")

    out_path = CACHE_DIR / "candidatos_pendientes.json"

    if out_path.exists():
        previo = json.loads(out_path.read_text(encoding="utf-8"))
        nodos_acumulados = previo.get("nodos_nuevos", []) + nodos_acumulados
        relaciones_acumuladas = previo.get("relaciones_nuevas", []) + relaciones_acumuladas
        print(f"  (combinado con {len(previo.get('nodos_nuevos', []))} nodos pendientes de una sesión anterior)")

    out_path.write_text(
        json.dumps(
            {"nodos_nuevos": nodos_acumulados, "relaciones_nuevas": relaciones_acumuladas},
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )

    log_path = LOGS_DIR / f"extraccion_log_{Path(args.pdf).stem}.json"
    log_path.write_text(
        json.dumps({
            "pdf": nombre_pdf,
            "total_paginas": len(paginas),
            "total_chunks": len(chunks),
            "chunks_con_error": log_fallos,
            "rangos_de_pagina_por_chunk": [
                {"chunk": i, "pagina_inicio": c["pagina_inicio"], "pagina_fin": c["pagina_fin"]}
                for i, c in enumerate(chunks, 1)
            ],
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    procesados = len(checkpoint.get("chunks_procesados", []))
    print(f"\n✓ Total: {len(nodos_acumulados)} nodos y {len(relaciones_acumuladas)} relaciones propuestas")
    print(f"  Checkpoint: {procesados}/{len(chunks)} chunks procesados")
    print(f"  Guardado en {out_path}")
    if log_fallos:
        print(f"  ⚠ {len(log_fallos)} chunk(s) fallaron — ver {log_path.name}")
    print(f"  Siguiente paso: python cerebro.py")


if __name__ == "__main__":
    main()
