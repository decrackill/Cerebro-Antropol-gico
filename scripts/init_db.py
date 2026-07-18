"""
Inicializa la base de datos del Cerebro Antropológico.
Crea las tablas 'nodos' y 'relaciones' y siembra un sub-grafo de ejemplo
alrededor de Malinowski para tener algo navegable desde el día 1.

Uso:
    python scripts/init_db.py
"""
import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "grafo.db"

SCHEMA = """
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
        'influenciado_por', 'critica_a', 'desarrolla_concepto',
        'pertenece_a', 'estudia_a', 'contemporaneo_de',
        'precursor_de', 'parte_del_debate', 'redefine_a'
    )),
    peso REAL DEFAULT 1.0,
    fuente TEXT,
    FOREIGN KEY (origen_id) REFERENCES nodos(id),
    FOREIGN KEY (destino_id) REFERENCES nodos(id)
);

CREATE INDEX IF NOT EXISTS idx_rel_origen ON relaciones(origen_id);
CREATE INDEX IF NOT EXISTS idx_rel_destino ON relaciones(destino_id);
"""

NODOS = [
    ("autor", "Bronisław Malinowski",
     "Antropólogo polaco-británico, pionero del trabajo de campo prolongado y la observación participante.",
     {"nacimiento": 1884, "muerte": 1942, "afiliacion": "London School of Economics"}),
    ("autor", "Marcel Mauss",
     "Sociólogo y antropólogo francés, sobrino de Durkheim, teórico del don y la reciprocidad.",
     {"nacimiento": 1872, "muerte": 1950}),
    ("obra", "Los argonautas del Pacífico Occidental",
     "Estudio etnográfico de 1922 sobre el intercambio ceremonial Kula en las islas Trobriand.",
     {"anio": 1922}),
    ("concepto", "Reciprocidad",
     "Principio de intercambio mutuo de bienes, favores o gestos entre individuos o grupos.",
     {}),
    ("escuela", "Funcionalismo",
     "Corriente que explica las instituciones sociales por las funciones que cumplen para la sociedad.",
     {"periodo": "1920s-1950s"}),
    ("cultura", "Trobriandeses",
     "Pueblo de las islas Trobriand, Papúa Nueva Guinea, célebres por el intercambio Kula.",
     {"region": "Melanesia"}),
]

RELACIONES_SEED = [
    # (nombre_origen, nombre_destino, tipo_relacion, nota)
    ("Bronisław Malinowski", "Los argonautas del Pacífico Occidental", "influenciado_por", None),
    ("Bronisław Malinowski", "Reciprocidad", "desarrolla_concepto", "A través del análisis del Kula"),
    ("Bronisław Malinowski", "Funcionalismo", "pertenece_a", "Uno de sus fundadores"),
    ("Bronisław Malinowski", "Trobriandeses", "estudia_a", "Trabajo de campo 1915-1918"),
    ("Marcel Mauss", "Reciprocidad", "desarrolla_concepto", "En 'Ensayo sobre el don' (1925)"),
    ("Bronisław Malinowski", "Marcel Mauss", "contemporaneo_de", None),
]


def main():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)

    for tipo, nombre, desc, meta in NODOS:
        conn.execute(
            "INSERT OR IGNORE INTO nodos (tipo, nombre, descripcion, metadatos) VALUES (?, ?, ?, ?)",
            (tipo, nombre, desc, json.dumps(meta, ensure_ascii=False)),
        )

    nombre_a_id = {row[1]: row[0] for row in conn.execute("SELECT id, nombre FROM nodos").fetchall()}

    for origen_nombre, destino_nombre, tipo, nota in RELACIONES_SEED:
        origen_id = nombre_a_id.get(origen_nombre)
        destino_id = nombre_a_id.get(destino_nombre)
        if origen_id and destino_id:
            conn.execute(
                "INSERT OR IGNORE INTO relaciones (origen_id, destino_id, tipo, fuente) VALUES (?, ?, ?, ?)",
                (origen_id, destino_id, tipo, nota),
            )

    conn.commit()
    conn.close()
    print(f"Base de datos creada en {DB_PATH}")
    print(f"  {len(NODOS)} nodos, {len(RELACIONES_SEED)} relaciones")


if __name__ == "__main__":
    main()