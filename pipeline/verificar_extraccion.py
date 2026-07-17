"""
Verifica que un libro procesado con extractor.py haya sido efectivamente
cubierto por completo: cruza el log de extracción (chunks y fallos) contra
las relaciones/fuentes realmente guardadas en la DB.

Uso: python verificar_extraccion.py argonautas
     (usa el mismo "stem" del pdf, sin extensión ni ruta)
"""
import json
import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR.parent / "data" / "grafo.db"


def main():
    if len(sys.argv) < 2:
        print("Uso: python verificar_extraccion.py <nombre_stem_del_pdf>")
        logs = list(BASE_DIR.glob("extraccion_log_*.json"))
        if logs:
            print("\nLogs disponibles:")
            for l in logs:
                print(f"  {l.stem.replace('extraccion_log_', '')}")
        return

    stem = sys.argv[1]
    log_path = BASE_DIR / f"extraccion_log_{stem}.json"
    if not log_path.exists():
        print(f"✗ No existe {log_path.name}. ¿Corriste extractor.py con logging activado sobre este libro?")
        return

    log = json.loads(log_path.read_text(encoding="utf-8"))
    print("═" * 60)
    print(f"VERIFICACIÓN DE EXTRACCIÓN: {log['pdf']}")
    print("═" * 60)
    print(f"  Páginas totales del PDF: {log['total_paginas']}")
    print(f"  Chunks generados: {log['total_chunks']}")
    print(f"  Chunks con error (JSON inválido): {len(log['chunks_con_error'])}")

    if log["chunks_con_error"]:
        print("\n  ⚠ CHUNKS QUE FALLARON (nunca extrajeron nada):")
        for f in log["chunks_con_error"]:
            rango = next(
                (r for r in log["rangos_de_pagina_por_chunk"] if r["chunk"] == f["chunk_index"]),
                None,
            )
            paginas = f"p.{rango['pagina_inicio']}-{rango['pagina_fin']}" if rango else "?"
            print(f"    - Chunk {f['chunk_index']} ({paginas}): {f['razon']}")
        print("\n  ◈ Estas páginas NUNCA se analizaron correctamente. Debes re-extraerlas")
        print("    manualmente si te importa cubrirlas.")
    else:
        print("  ✓ Ningún chunk falló al momento de la extracción con Gemini")

    conn = sqlite3.connect(DB_PATH)
    filas = conn.execute(
        "SELECT fuente FROM relaciones WHERE fuente LIKE ?", (f"{log['pdf']}%",)
    ).fetchall()
    conn.close()

    fuentes_en_db = {f[0] for f in filas}
    chunks_sin_ninguna_relacion_en_db = []
    for r in log["rangos_de_pagina_por_chunk"]:
        fuente_esperada = f"{log['pdf']}, p.{r['pagina_inicio']}-{r['pagina_fin']}"
        if fuente_esperada not in fuentes_en_db:
            chunks_sin_ninguna_relacion_en_db.append(r)

    print(f"\n  Relaciones en DB provenientes de este libro: {len(fuentes_en_db)} fuentes únicas")
    if chunks_sin_ninguna_relacion_en_db:
        print(f"\n  ⚠ Chunks que SÍ se extrajeron bien pero terminaron con 0 relaciones aprobadas en la DB:")
        for r in chunks_sin_ninguna_relacion_en_db:
            print(f"    - Chunk {r['chunk']} (p.{r['pagina_inicio']}-{r['pagina_fin']})")
        print("\n  Esto puede ser normal (esa sección no tenía nada citable) o significar que")
        print("  esas relaciones se rechazaron en revisar.py o se perdieron por un bug ya corregido.")
    else:
        print("  ✓ Cada chunk generado tiene al menos una relación finalmente aprobada en la DB")


if __name__ == "__main__":
    main()
