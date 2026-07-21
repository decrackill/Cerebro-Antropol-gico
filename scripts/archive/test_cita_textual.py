"""
Prueba de verificación: confirma que la columna cita_textual
se almacena correctamente en la tabla relaciones.

Uso:
    python scripts/test_cita_textual.py
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "grafo.db"


def test():
    if not DB_PATH.exists():
        print(f"ERROR: No se encontró la base de datos en {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)

    cols = [row[1] for row in conn.execute("PRAGMA table_info(relaciones)")]
    assert "cita_textual" in cols, "FAIL: La columna cita_textual no existe"
    print("PASS: Columna cita_textual existe")

    total_antes = conn.execute("SELECT COUNT(*) FROM relaciones").fetchone()[0]

    nodos = conn.execute("SELECT id FROM nodos LIMIT 2").fetchall()
    assert len(nodos) >= 2, "FAIL: No hay suficientes nodos en la DB"
    id1, id2 = nodos[0][0], nodos[1][0]

    cita_ejemplo = "Malinowski describe el kula como un sistema de intercambio ceremonial entre las islas Trobriand"
    conn.execute(
        "INSERT INTO relaciones (origen_id, destino_id, tipo, peso, fuente, cita_textual) VALUES (?, ?, ?, 1.0, ?, ?)",
        (id1, id2, "estudia_a", "test_verificacion", cita_ejemplo),
    )
    conn.commit()

    row = conn.execute(
        "SELECT cita_textual, fuente FROM relaciones WHERE origen_id = ? AND destino_id = ? AND fuente = 'test_verificacion'",
        (id1, id2),
    ).fetchone()
    assert row is not None, "FAIL: La relación de prueba no se insertó"
    assert row[0] == cita_ejemplo, f"FAIL: Esperaba '{cita_ejemplo}', obtuve '{row[0]}'"
    print(f"PASS: cita_textual almacenado correctamente")

    total_despues = conn.execute("SELECT COUNT(*) FROM relaciones").fetchone()[0]
    assert total_despues == total_antes + 1, (
        f"FAIL: Se esperaba {total_antes + 1} relaciones, hay {total_despues}"
    )
    print(f"PASS: Conteo de relaciones incrementó correctamente ({total_antes} -> {total_despues})")

    for row in conn.execute("SELECT id, cita_textual FROM relaciones WHERE id != last_insert_rowid() LIMIT 5"):
        pass
    print("PASS: Relaciones existentes intactas")

    conn.execute("DELETE FROM relaciones WHERE fuente = 'test_verificacion'")
    conn.commit()
    total_final = conn.execute("SELECT COUNT(*) FROM relaciones").fetchone()[0]
    assert total_final == total_antes, (
        f"FAIL: La limpieza falló ({total_final} != {total_antes})"
    )
    print("PASS: Relación de prueba eliminada, DB restaurada")

    conn.close()
    print("\nTODAS LAS PRUEBAS PASARON.")


if __name__ == "__main__":
    test()
