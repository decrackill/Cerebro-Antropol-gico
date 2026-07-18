"""
Refuerza el esquema de la DB con validaciones a nivel de base de datos,
para que los bugs de scripts (presentes o futuros) no puedan corromper
los datos aunque el código tenga un error.

Uso: python reforzar_esquema.py (una sola vez, es seguro correrlo varias veces)
"""
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR.parent / "data" / "grafo.db"


def main():
    conn = sqlite3.connect(DB_PATH)

    conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_relacion_unica
        ON relaciones (origen_id, destino_id, tipo)
    """)

    conn.execute("CREATE INDEX IF NOT EXISTS idx_relaciones_origen ON relaciones (origen_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_relaciones_destino ON relaciones (destino_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_nodos_tipo ON nodos (tipo)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_nodos_nombre ON nodos (nombre)")

    conn.commit()
    conn.close()
    print("✓ Esquema reforzado: índice único anti-duplicados + índices de rendimiento.")


if __name__ == "__main__":
    main()
