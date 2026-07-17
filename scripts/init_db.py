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
    id TEXT PRIMARY KEY,
    tipo TEXT NOT NULL CHECK(tipo IN (
        'autor', 'obra', 'concepto', 'escuela', 'cultura', 'debate'
    )),
    nombre TEXT NOT NULL,
    resumen TEXT,
    metadata TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS relaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    origen TEXT NOT NULL,
    destino TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK(tipo IN (
        'influenciado_por', 'critica_a', 'desarrolla_concepto',
        'pertenece_a', 'estudia_a', 'contemporaneo_de',
        'precursor_de', 'parte_del_debate', 'redefine_a'
    )),
    nota TEXT,
    FOREIGN KEY (origen) REFERENCES nodos(id),
    FOREIGN KEY (destino) REFERENCES nodos(id)
);

CREATE INDEX IF NOT EXISTS idx_rel_origen ON relaciones(origen);
CREATE INDEX IF NOT EXISTS idx_rel_destino ON relaciones(destino);
"""

NODOS = [
    ("malinowski", "autor", "Bronisław Malinowski",
     "Antropólogo polaco-británico, pionero del trabajo de campo prolongado y la observación participante.",
     {"nacimiento": 1884, "muerte": 1942, "afiliacion": "London School of Economics"}),
    ("mauss", "autor", "Marcel Mauss",
     "Sociólogo y antropólogo francés, sobrino de Durkheim, teórico del don y la reciprocidad.",
     {"nacimiento": 1872, "muerte": 1950}),
    ("argonautas", "obra", "Los argonautas del Pacífico Occidental",
     "Estudio etnográfico de 1922 sobre el intercambio ceremonial Kula en las islas Trobriand.",
     {"anio": 1922}),
    ("reciprocidad", "concepto", "Reciprocidad",
     "Principio de intercambio mutuo de bienes, favores o gestos entre individuos o grupos.",
     {}),
    ("funcionalismo", "escuela", "Funcionalismo",
     "Corriente que explica las instituciones sociales por las funciones que cumplen para la sociedad.",
     {"periodo": "1920s-1950s"}),
    ("trobriandeses", "cultura", "Trobriandeses",
     "Pueblo de las islas Trobriand, Papúa Nueva Guinea, célebres por el intercambio Kula.",
     {"region": "Melanesia"}),
]

RELACIONES = [
    ("malinowski", "argonautas", "influenciado_por", None),  # placeholder de ejemplo
    ("malinowski", "reciprocidad", "desarrolla_concepto", "A través del análisis del Kula"),
    ("malinowski", "funcionalismo", "pertenece_a", "Uno de sus fundadores"),
    ("malinowski", "trobriandeses", "estudia_a", "Trabajo de campo 1915-1918"),
    ("mauss", "reciprocidad", "desarrolla_concepto", "En 'Ensayo sobre el don' (1925)"),
    ("malinowski", "mauss", "contemporaneo_de", None),
]

# Corrección: la relación autor->obra debería ser un tipo propio.
# Por simplicidad en el MVP se resuelve con metadata en el nodo obra: {"autor": "malinowski"}


def main():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)

    for id_, tipo, nombre, resumen, meta in NODOS:
        conn.execute(
            "INSERT OR REPLACE INTO nodos (id, tipo, nombre, resumen, metadata) VALUES (?, ?, ?, ?, ?)",
            (id_, tipo, nombre, resumen, json.dumps(meta, ensure_ascii=False)),
        )

    conn.execute("DELETE FROM relaciones")  # evita duplicados al re-ejecutar
    for origen, destino, tipo, nota in RELACIONES:
        conn.execute(
            "INSERT INTO relaciones (origen, destino, tipo, nota) VALUES (?, ?, ?, ?)",
            (origen, destino, tipo, nota),
        )

    conn.commit()
    conn.close()
    print(f"Base de datos creada en {DB_PATH}")
    print(f"  {len(NODOS)} nodos, {len(RELACIONES)} relaciones")


if __name__ == "__main__":
    main()