"""
Fusiona nodos duplicados: redirige todas las relaciones del nodo "duplicado"
hacia el nodo "canónico" que decidas mantener, y borra el duplicado. Usa el
mismo escaneo de similitud que auditoria.py, pero te deja decidir caso por
caso cuál de los dos es el que se queda.

Uso: python fusionar_duplicados.py
"""
import sqlite3
from pathlib import Path
from difflib import SequenceMatcher

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR.parent / "data" / "grafo.db"
UMBRAL = 0.80


def similitud(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def obtener_grupos_sospechosos(conn):
    filas = conn.execute("SELECT id, tipo, nombre FROM nodos ORDER BY tipo, id").fetchall()
    grados = dict(conn.execute("""
        SELECT id_nodo, COUNT(*) FROM (
            SELECT origen_id AS id_nodo FROM relaciones
            UNION ALL SELECT destino_id AS id_nodo FROM relaciones
        ) GROUP BY id_nodo
    """).fetchall())

    por_tipo = {}
    for id_, tipo, nombre in filas:
        por_tipo.setdefault(tipo, []).append((id_, nombre))

    grupos = []
    vistos = set()
    for tipo, items in por_tipo.items():
        for i, (id_a, nombre_a) in enumerate(items):
            if id_a in vistos:
                continue
            for id_b, nombre_b in items[i + 1:]:
                if id_b in vistos:
                    continue
                if similitud(nombre_a, nombre_b) >= UMBRAL:
                    grupos.append({
                        "a": (id_a, nombre_a, grados.get(id_a, 0)),
                        "b": (id_b, nombre_b, grados.get(id_b, 0)),
                    })
                    vistos.add(id_b)
    return grupos


def fusionar(conn, id_mantener, id_borrar):
    conn.execute("UPDATE relaciones SET origen_id = ? WHERE origen_id = ?", (id_mantener, id_borrar))
    conn.execute("UPDATE relaciones SET destino_id = ? WHERE destino_id = ?", (id_mantener, id_borrar))
    # elimina relaciones que hayan quedado duplicadas tras la redirección
    conn.execute("""
        DELETE FROM relaciones WHERE id NOT IN (
            SELECT MIN(id) FROM relaciones GROUP BY origen_id, destino_id, tipo
        )
    """)
    conn.execute("DELETE FROM nodos WHERE id = ?", (id_borrar,))
    conn.commit()


def main():
    conn = sqlite3.connect(DB_PATH)
    grupos = obtener_grupos_sospechosos(conn)

    print("═" * 60)
    print(f"FUSIÓN DE DUPLICADOS — {len(grupos)} grupo(s) sospechoso(s)")
    print("═" * 60)

    for i, g in enumerate(grupos, 1):
        id_a, nombre_a, grado_a = g["a"]
        id_b, nombre_b, grado_b = g["b"]
        print(f"\n[{i}/{len(grupos)}]")
        print(f"  A) id={id_a}  '{nombre_a}'  ({grado_a} relaciones)")
        print(f"  B) id={id_b}  '{nombre_b}'  ({grado_b} relaciones)")
        resp = input("  ¿Fusionar? (a = mantener A / b = mantener B / n = no son duplicados, saltar): ").strip().lower()

        if resp == "a":
            fusionar(conn, id_a, id_b)
            print(f"  ✓ Fusionado — se mantiene '{nombre_a}' (id={id_a}), '{nombre_b}' absorbido y eliminado")
        elif resp == "b":
            fusionar(conn, id_b, id_a)
            print(f"  ✓ Fusionado — se mantiene '{nombre_b}' (id={id_b}), '{nombre_a}' absorbido y eliminado")
        else:
            print("  → Saltado")

    conn.close()
    print("\n◈ Corre: cd .. && python scripts/export_json.py")


if __name__ == "__main__":
    main()
