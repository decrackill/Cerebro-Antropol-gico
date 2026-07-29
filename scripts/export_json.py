"""
Exporta data/grafo.db a public/datos.json para que el frontend lo consuma
sin necesidad de un backend corriendo.

Uso:
    python scripts/export_json.py

Corre esto cada vez que edites la base de datos (por ejemplo después
de correr init_db.py de nuevo, o de insertar nodos a mano).
"""
import re
import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "grafo.db"
OUT_PATH = Path(__file__).parent.parent / "public" / "datos.json"

LIBROS = {
    "argonautas": "Los argonautas del Pacífico Occidental",
    "boas-f-1911-cuestiones-fundamentales-de-antropologia-cultural": "Cuestiones fundamentales de antropología cultural",
}

_RE_PDF = re.compile(r"([^/]+)\.pdf")


def _limpiar_fuente(fuente: str | None) -> tuple[str | None, str | None]:
    if not fuente:
        return None, None
    fuente = _RE_PDF.sub(lambda m: LIBROS.get(m.group(1), m.group(1)), fuente)
    libro = None
    for stem, titulo in LIBROS.items():
        if titulo in fuente:
            libro = titulo
            break
    if not libro:
        m = _RE_PDF.search(fuente)
        if m and m.group(1) in LIBROS:
            libro = LIBROS[m.group(1)]
    return fuente, libro


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    nodos = []
    for row in conn.execute("SELECT * FROM nodos"):
        nodo = dict(row)
        nodo["metadata"] = json.loads(nodo["metadatos"] or "{}")
        nodos.append(nodo)

    relaciones = []
    for row in conn.execute("SELECT * FROM relaciones"):
        r = dict(row)
        fuente_limpia, libro = _limpiar_fuente(r.get("fuente"))
        r["fuente"] = fuente_limpia
        r["libro"] = libro
        relaciones.append(r)

    conn.close()

    OUT_PATH.write_text(
        json.dumps({"nodos": nodos, "relaciones": relaciones}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Exportado a {OUT_PATH}")
    print(f"  {len(nodos)} nodos, {len(relaciones)} relaciones")


if __name__ == "__main__":
    main()
