"""
Migración idempotente: agrega la columna cita_textual a la tabla relaciones.

- Crea backup automático (grafo.db.bak) antes de modificar
- Verifica integridad: conteo de nodos y relaciones sin cambios
- Seguro para ejecutar múltiples veces
"""
import sqlite3
import shutil
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "grafo.db"
BAK_PATH = DB_PATH.with_suffix(".db.bak")


def migrate():
    if not DB_PATH.exists():
        print(f"ERROR: No se encontró la base de datos en {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)

    cols = [row[1] for row in conn.execute("PRAGMA table_info(relaciones)")]
    if "cita_textual" in cols:
        print("OK: La columna cita_textual ya existe. Nada que hacer.")
        conn.close()
        return

    conn.close()
    shutil.copy2(DB_PATH, BAK_PATH)
    print(f"Backup creado: {BAK_PATH}")

    conn = sqlite3.connect(DB_PATH)
    nodos_antes = conn.execute("SELECT COUNT(*) FROM nodos").fetchone()[0]
    rels_antes = conn.execute("SELECT COUNT(*) FROM relaciones").fetchone()[0]

    conn.execute("ALTER TABLE relaciones ADD COLUMN cita_textual TEXT")
    conn.commit()

    nodos_despues = conn.execute("SELECT COUNT(*) FROM nodos").fetchone()[0]
    rels_despues = conn.execute("SELECT COUNT(*) FROM relaciones").fetchone()[0]

    assert nodos_antes == nodos_despues, (
        f"ERROR: nodos cambiaron ({nodos_antes} -> {nodos_despues})"
    )
    assert rels_antes == rels_despues, (
        f"ERROR: relaciones cambiaron ({rels_antes} -> {rels_despues})"
    )

    print(f"Columna cita_textual agregada exitosamente.")
    print(f"Verificación: {nodos_antes} nodos, {rels_antes} relaciones — sin cambios.")

    conn.close()


if __name__ == "__main__":
    migrate()
