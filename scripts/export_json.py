"""
Exporta data/grafo.db a src/datos.json para que el frontend lo consuma
sin necesidad de un backend corriendo.

Uso:
    python scripts/export_json.py

Corre esto cada vez que edites la base de datos (por ejemplo después
de correr init_db.py de nuevo, o de insertar nodos a mano).
"""
import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "grafo.db"
OUT_PATH = Path(__file__).parent.parent / "src" / "datos.json"


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
        relaciones.append(dict(row))

    conn.close()

    OUT_PATH.write_text(
        json.dumps({"nodos": nodos, "relaciones": relaciones}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Exportado a {OUT_PATH}")
    print(f"  {len(nodos)} nodos, {len(relaciones)} relaciones")


if __name__ == "__main__":
    main()
