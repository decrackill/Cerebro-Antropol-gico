"""Tests de base de datos."""
import sqlite3


def test_conectar_db(tmp_db):
    from pipeline.core.db import conectar_db
    conn = sqlite3.connect(tmp_db)
    conn.execute("PRAGMA foreign_keys = ON")
    assert conn is not None
    conn.close()


def test_foreign_keys_habilitadas(db_conn):
    result = db_conn.execute("PRAGMA foreign_keys").fetchone()
    assert result[0] == 1


def test_tabla_nodos_existe(db_conn):
    tables = db_conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='nodos'"
    ).fetchone()
    assert tables is not None


def test_tabla_relaciones_existe(db_conn):
    tables = db_conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='relaciones'"
    ).fetchone()
    assert tables is not None


def test_columnas_nodos(db_conn):
    cols = [row[1] for row in db_conn.execute("PRAGMA table_info(nodos)")]
    assert 'id' in cols
    assert 'tipo' in cols
    assert 'nombre' in cols
    assert 'descripcion' in cols
    assert 'metadatos' in cols


def test_columnas_relaciones(db_conn):
    cols = [row[1] for row in db_conn.execute("PRAGMA table_info(relaciones)")]
    assert 'id' in cols
    assert 'origen_id' in cols
    assert 'destino_id' in cols
    assert 'tipo' in cols
    assert 'peso' in cols
    assert 'fuente' in cols
    assert 'cita_textual' in cols


def test_insert_select_nodo(db_conn):
    db_conn.execute(
        "INSERT INTO nodos (tipo, nombre, descripcion) VALUES (?, ?, ?)",
        ("concepto", "Test Insert", "Descripción")
    )
    db_conn.commit()
    row = db_conn.execute("SELECT * FROM nodos WHERE nombre = 'Test Insert'").fetchone()
    assert row is not None
    assert row[1] == "concepto"


def test_insert_relacion(db_conn):
    # Obtener IDs de nodos existentes
    nodos = db_conn.execute("SELECT id FROM nodos LIMIT 2").fetchall()
    assert len(nodos) >= 2

    db_conn.execute(
        "INSERT INTO relaciones (origen_id, destino_id, tipo, peso, fuente, cita_textual) VALUES (?, ?, ?, 1.0, ?, ?)",
        (nodos[0][0], nodos[1][0], "estudia_a", "fuente_test", "cita de prueba")
    )
    db_conn.commit()
    row = db_conn.execute("SELECT * FROM relaciones WHERE fuente = 'fuente_test'").fetchone()
    assert row is not None
    assert row[6] == "cita de prueba"  # cita_textual


def test_fusionar_nodos(db_conn):
    from pipeline.core.db import fusionar_nodos

    # Crear dos nodos
    db_conn.execute("INSERT INTO nodos (tipo, nombre) VALUES (?, ?)", ("autor", "Nodo A"))
    db_conn.execute("INSERT INTO nodos (tipo, nombre) VALUES (?, ?)", ("autor", "Nodo B"))
    db_conn.commit()

    id_a = db_conn.execute("SELECT id FROM nodos WHERE nombre = 'Nodo A'").fetchone()[0]
    id_b = db_conn.execute("SELECT id FROM nodos WHERE nombre = 'Nodo B'").fetchone()[0]

    # Crear relación desde B
    nodo_origen = db_conn.execute("SELECT id FROM nodos WHERE nombre = 'Obra Test'").fetchone()[0]
    db_conn.execute(
        "INSERT INTO relaciones (origen_id, destino_id, tipo) VALUES (?, ?, ?)",
        (nodo_origen, id_b, "estudia_a")
    )
    db_conn.commit()

    # Fusionar B → A
    fusionar_nodos(db_conn, id_a, id_b)

    # Verificar que B ya no existe
    assert db_conn.execute("SELECT id FROM nodos WHERE id = ?", (id_b,)).fetchone() is None

    # Verificar que la relación ahora apunta a A
    rel = db_conn.execute("SELECT destino_id FROM relaciones WHERE origen_id = ?", (nodo_origen,)).fetchone()
    assert rel[0] == id_a


def test_eliminar_nodo_cascada(db_conn):
    from pipeline.core.db import eliminar_nodo_cascada

    # Crear nodo con relación
    db_conn.execute("INSERT INTO nodos (tipo, nombre) VALUES (?, ?)", ("obra", "Para Eliminar"))
    db_conn.commit()
    id_nodo = db_conn.execute("SELECT id FROM nodos WHERE nombre = 'Para Eliminar'").fetchone()[0]

    nodo_origen = db_conn.execute("SELECT id FROM nodos LIMIT 1").fetchone()[0]
    db_conn.execute(
        "INSERT INTO relaciones (origen_id, destino_id, tipo) VALUES (?, ?, ?)",
        (nodo_origen, id_nodo, "estudia_a")
    )
    db_conn.commit()

    # Eliminar
    eliminar_nodo_cascada(db_conn, id_nodo)

    # Verificar
    assert db_conn.execute("SELECT id FROM nodos WHERE id = ?", (id_nodo,)).fetchone() is None
    assert db_conn.execute("SELECT id FROM relaciones WHERE destino_id = ?", (id_nodo,)).fetchone() is None
