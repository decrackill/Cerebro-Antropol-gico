"""
MODO MANUAL — para cuando se acaban los tokens de la API.
Genera, chunk por chunk, un archivo de texto con el prompt completo listo
para pegar en un chat web (ChatGPT, Claude, Gemini, etc.), y después toma
la respuesta JSON que pegues de vuelta y la integra al mismo
candidatos_pendientes.json que usa todo el resto del pipeline. Usa el mismo
checkpoint que extractor.py, así que podés alternar API y modo manual sin
duplicar ni perder progreso.

Uso:
  python modo_manual.py ../libros/archivo.pdf generar
    -> genera prompt_manual_chunk_N.txt con el siguiente fragmento pendiente

  python modo_manual.py ../libros/archivo.pdf pegar
    -> te pide que pegues la respuesta JSON del chat, la valida e integra
"""
import sys
import json
from pathlib import Path

from .extractor import (
    extraer_paginas_pdf, dividir_en_chunks, cargar_checkpoint, guardar_checkpoint,
    chunk_ya_procesado, cargar_nodos_existentes, normalizar_tipos,
)
from .prompts import build_prompt_extraccion_grafo
from ..core.config import CACHE_DIR

CHUNK_ACTUAL_PATH = CACHE_DIR / "modo_manual_chunk_actual.json"


def generar(ruta_pdf):
    nombre_pdf = Path(ruta_pdf).name
    paginas = extraer_paginas_pdf(ruta_pdf)
    chunks = dividir_en_chunks(paginas)
    checkpoint = cargar_checkpoint(nombre_pdf)

    pendientes = [i for i in range(len(chunks)) if not chunk_ya_procesado(checkpoint, i + 1)]
    if not pendientes:
        print(f"✓ Todos los {len(chunks)} chunks ya están procesados (vía API o manual).")
        return

    idx = pendientes[0]
    i = idx + 1
    chunk = chunks[idx]

    nodos_existentes = cargar_nodos_existentes()
    prompt_sistema = build_prompt_extraccion_grafo(nodos_existentes)

    contenido = f"""{prompt_sistema}

═══════════════════════════════════════════════════════════
TEXTO A ANALIZAR (fragmento {i}/{len(chunks)}, páginas {chunk['pagina_inicio']}-{chunk['pagina_fin']}):
═══════════════════════════════════════════════════════════

{chunk['texto']}
"""

    salida = BASE_DIR / f"prompt_manual_chunk_{i}.txt"
    salida.write_text(contenido, encoding="utf-8")

    CHUNK_ACTUAL_PATH.write_text(json.dumps({
        "pdf": nombre_pdf,
        "chunk_index": i,
        "pagina_inicio": chunk["pagina_inicio"],
        "pagina_fin": chunk["pagina_fin"],
        "total_chunks": len(chunks),
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"✓ Generado: {salida.name}")
    print(f"  Fragmento {i}/{len(chunks)} (páginas {chunk['pagina_inicio']}-{chunk['pagina_fin']})")
    print(f"  Progreso del libro: {len(checkpoint.get('chunks_procesados', []))}/{len(chunks)} chunks ya hechos")
    print(f"\n◈ Siguiente paso:")
    print(f"  1. Abrí {salida.name} y copiá TODO el contenido")
    print(f"  2. Pegalo en un chat de ChatGPT/Claude/Gemini (uno nuevo, sin contexto previo)")
    print(f"  3. Copiá la respuesta JSON completa que te dé")
    print(f"  4. Corré: python modo_manual.py {ruta_pdf} pegar")


def pegar(ruta_pdf):
    if not CHUNK_ACTUAL_PATH.exists():
        print("✗ No hay ningún chunk esperando respuesta. Corré primero 'generar'.")
        return

    info = json.loads(CHUNK_ACTUAL_PATH.read_text(encoding="utf-8"))
    nombre_pdf = info["pdf"]

    print(f"Pegá la respuesta JSON del chat para el fragmento {info['chunk_index']}/{info['total_chunks']}")
    print("(pegá todo, y en una línea nueva sola escribí FIN para terminar)")
    print()

    lineas = []
    while True:
        try:
            linea = input()
        except EOFError:
            break
        if linea.strip() == "FIN":
            break
        lineas.append(linea)

    texto_json = "\n".join(lineas).strip()
    texto_json = texto_json.replace("```json", "").replace("```", "").strip()

    try:
        resultado = json.loads(texto_json)
    except json.JSONDecodeError as e:
        print(f"\n✗ El texto pegado no es JSON válido: {e}")
        print("  No se guardó nada. Revisá que copiaste la respuesta completa del chat")
        print("  (a veces el chat agrega texto antes/después del JSON — borralo y volvé a intentar).")
        return

    resultado = normalizar_tipos(resultado)
    nuevos = resultado.get("nodos_nuevos", [])
    nuevas_rels = resultado.get("relaciones_nuevas", [])

    fuente_str = f"{nombre_pdf}, p.{info['pagina_inicio']}-{info['pagina_fin']}"
    for r in nuevas_rels:
        r["fuente"] = fuente_str

    out_path = BASE_DIR / "candidatos_pendientes.json"
    if out_path.exists():
        previo = json.loads(out_path.read_text(encoding="utf-8"))
        nuevos = previo.get("nodos_nuevos", []) + nuevos
        nuevas_rels = previo.get("relaciones_nuevas", []) + nuevas_rels

    out_path.write_text(json.dumps(
        {"nodos_nuevos": nuevos, "relaciones_nuevas": nuevas_rels},
        ensure_ascii=False, indent=2,
    ), encoding="utf-8")

    checkpoint = cargar_checkpoint(nombre_pdf)
    checkpoint.setdefault("chunks_procesados", []).append(info["chunk_index"])
    checkpoint["total_chunks"] = info["total_chunks"]
    guardar_checkpoint(nombre_pdf, checkpoint)

    CHUNK_ACTUAL_PATH.unlink()
    (BASE_DIR / f"prompt_manual_chunk_{info['chunk_index']}.txt").unlink(missing_ok=True)

    print(f"\n✓ Integrado: +{len(resultado.get('nodos_nuevos', []))} nodos, +{len(resultado.get('relaciones_nuevas', []))} relaciones")
    print(f"  Checkpoint actualizado: chunk {info['chunk_index']}/{info['total_chunks']} marcado como hecho")
    print(f"\n◈ Para continuar con el siguiente fragmento:")
    print(f"  python modo_manual.py {ruta_pdf} generar")


def main():
    if len(sys.argv) < 3 or sys.argv[2] not in ("generar", "pegar"):
        print("Uso:")
        print("  python modo_manual.py ../libros/archivo.pdf generar")
        print("  python modo_manual.py ../libros/archivo.pdf pegar")
        return

    ruta_pdf, accion = sys.argv[1], sys.argv[2]
    if accion == "generar":
        generar(ruta_pdf)
    else:
        pegar(ruta_pdf)


if __name__ == "__main__":
    main()
