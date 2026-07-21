"""Fixtures compartidos para tests."""
import sqlite3
import tempfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent


@pytest.fixture
def project_root():
    """Retorna la raíz del proyecto."""
    return PROJECT_ROOT


@pytest.fixture
def tmp_db():
    """Crea una base de datos SQLite temporal con esquema y seed."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    # Crear esquema
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS nodos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL CHECK(tipo IN (
                'autor', 'obra', 'concepto', 'escuela', 'cultura',
                'debate', 'poblacion', 'corriente'
            )),
            nombre TEXT NOT NULL UNIQUE,
            descripcion TEXT,
            metadatos TEXT DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS relaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            origen_id INTEGER NOT NULL,
            destino_id INTEGER NOT NULL,
            tipo TEXT NOT NULL CHECK(tipo IN (
                'autor_de', 'influenciado_por', 'critica_a', 'desarrolla_concepto',
                'redefine_a', 'precursor_de', 'pertenece_a', 'estudia_a',
                'contemporaneo_de', 'parte_del_debate', 'es_mentor_de', 'colabora_con'
            )),
            peso REAL DEFAULT 1.0,
            fuente TEXT,
            cita_textual TEXT,
            FOREIGN KEY (origen_id) REFERENCES nodos(id),
            FOREIGN KEY (destino_id) REFERENCES nodos(id)
        );
    """)

    # Seed datos de prueba
    conn.execute("INSERT INTO nodos (tipo, nombre, descripcion) VALUES (?, ?, ?)",
                 ("autor", "Autor Test", "Descripción de prueba"))
    conn.execute("INSERT INTO nodos (tipo, nombre, descripcion) VALUES (?, ?, ?)",
                 ("obra", "Obra Test", "Obra de prueba"))
    conn.execute("INSERT INTO nodos (tipo, nombre, descripcion) VALUES (?, ?, ?)",
                 ("concepto", "Concepto Test", "Concepto de prueba"))
    conn.commit()
    conn.close()

    yield db_path

    # Limpiar
    db_path.unlink(missing_ok=True)


@pytest.fixture
def db_conn(tmp_db):
    """Retorna una conexión a la DB temporal."""
    conn = sqlite3.connect(tmp_db)
    conn.execute("PRAGMA foreign_keys = ON")
    yield conn
    conn.close()
