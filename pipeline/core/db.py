"""Operaciones de base de datos para el pipeline.

Todas las funciones de CRUD, fusión y consulta de la DB.
"""
import json
import sqlite3

from .config import DB_PATH


def conectar_db() -> sqlite3.Connection:
    """Abre una conexión a la DB con foreign keys habilitados."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def eliminar_nodo_cascada(conn: sqlite3.Connection, id_: int) -> None:
    """Borra un nodo y todas sus relaciones (entrantes y salientes)."""
    conn.execute("DELETE FROM relaciones WHERE origen_id = ? OR destino_id = ?", (id_, id_))
    conn.execute("DELETE FROM nodos WHERE id = ?", (id_,))
    conn.commit()


def fusionar_nodos(conn: sqlite3.Connection, id_mantener: int, id_borrar: int) -> None:
    """
    Fusiona dos nodos: redirige todas las relaciones de id_borrar hacia
    id_mantener, PRESERVA en los metadatos de id_mantener un registro de
    todos los ids (numéricos previos y snake_case de Gemini) que alguna vez
    identificaron al nodo eliminado — bajo la clave 'ids_previos' — para que
    relaciones históricas archivadas que aún los referencien sigan siendo
    recuperables después de la fusión (ver construir_mapa_resolucion). Si
    alguno de los dos ids ya no existe (por ejemplo, fusionado antes en esta
    misma corrida), no hace nada y avisa en vez de fallar.
    """
    if id_mantener == id_borrar:
        return
    fila_m = conn.execute("SELECT metadatos FROM nodos WHERE id = ?", (id_mantener,)).fetchone()
    fila_b = conn.execute("SELECT metadatos FROM nodos WHERE id = ?", (id_borrar,)).fetchone()
    if fila_m is None or fila_b is None:
        print(f"  ⚠ Fusión omitida: id={id_mantener} o id={id_borrar} ya no existe "
              f"(probablemente fusionado antes en esta misma corrida).")
        return

    meta_m = json.loads(fila_m[0]) if fila_m[0] else {}
    meta_b = json.loads(fila_b[0]) if fila_b[0] else {}

    ids_previos = set(meta_m.get("ids_previos", []))
    ids_previos.add(str(id_borrar))
    if "id_gemini" in meta_b:
        ids_previos.add(meta_b["id_gemini"])
    ids_previos.update(meta_b.get("ids_previos", []))
    meta_m["ids_previos"] = sorted(ids_previos)
    conn.execute("UPDATE nodos SET metadatos = ? WHERE id = ?",
                 (json.dumps(meta_m, ensure_ascii=False), id_mantener))

    conn.execute("UPDATE relaciones SET origen_id = ? WHERE origen_id = ?", (id_mantener, id_borrar))
    conn.execute("UPDATE relaciones SET destino_id = ? WHERE destino_id = ?", (id_mantener, id_borrar))

    dupes = conn.execute("""
        SELECT MIN(id) as keep_id, origen_id, destino_id, tipo
        FROM relaciones GROUP BY origen_id, destino_id, tipo HAVING COUNT(*) > 1
    """).fetchall()
    for keep_id, o, d, t in dupes:
        best = conn.execute("""
            SELECT id, cita_textual FROM relaciones
            WHERE origen_id = ? AND destino_id = ? AND tipo = ?
            ORDER BY CASE WHEN cita_textual IS NOT NULL AND cita_textual != '' THEN 0 ELSE 1 END, id
            LIMIT 1
        """, (o, d, t)).fetchone()
        if best and best[1]:
            conn.execute("UPDATE relaciones SET cita_textual = ? WHERE id = ?", (best[1], keep_id))
        conn.execute("""
            DELETE FROM relaciones WHERE origen_id = ? AND destino_id = ? AND tipo = ? AND id != ?
        """, (o, d, t, keep_id))

    conn.execute("DELETE FROM nodos WHERE id = ?", (id_borrar,))
    conn.commit()


def relacion_ya_existe(conn: sqlite3.Connection, origen: int, destino: int, tipo: str) -> bool:
    """True si ya existe una relación exacta con ese origen/destino/tipo."""
    return conn.execute(
        "SELECT 1 FROM relaciones WHERE origen_id = ? AND destino_id = ? AND tipo = ?",
        (origen, destino, tipo),
    ).fetchone() is not None


def cargar_grados(conn: sqlite3.Connection) -> dict[int, int]:
    """Devuelve {id_nodo: número de relaciones}, para detectar nodos aislados."""
    return dict(conn.execute("""
        SELECT id_nodo, COUNT(*) FROM (
            SELECT origen_id AS id_nodo FROM relaciones
            UNION ALL SELECT destino_id AS id_nodo FROM relaciones
        ) GROUP BY id_nodo
    """).fetchall())


def construir_mapa_resolucion(conn: sqlite3.Connection) -> dict[str, int]:
    """
    Devuelve un dict que mapea CUALQUIER id que un nodo haya tenido alguna
    vez — su id numérico actual, su id_gemini original, o cualquier id
    absorbido en fusiones pasadas (ids_previos) — hacia su id_real actual
    en la DB. Es la pieza clave que permite recuperar relaciones históricas
    aunque el nodo que citaban haya sido fusionado con otro después.
    """
    mapa = {}
    for id_real, meta in conn.execute("SELECT id, metadatos FROM nodos"):
        mapa[str(id_real)] = id_real
        if meta:
            try:
                m = json.loads(meta)
                if "id_gemini" in m:
                    mapa[m["id_gemini"]] = id_real
                for viejo in m.get("ids_previos", []):
                    mapa[viejo] = id_real
            except (json.JSONDecodeError, TypeError):
                pass
    return mapa


def relaciones_de(conn: sqlite3.Connection, id_: int) -> list[dict]:
    """Devuelve todas las relaciones (entrantes + salientes) de un nodo."""
    filas = conn.execute("""
        SELECT r.id, r.tipo, r.fuente, r.cita_textual,
               CASE WHEN r.origen_id = ? THEN n2.nombre ELSE n1.nombre END AS otro_nombre,
               CASE WHEN r.origen_id = ? THEN r.destino_id ELSE r.origen_id END AS otro_id,
               CASE WHEN r.origen_id = ? THEN 'saliente' ELSE 'entrante' END AS direccion
        FROM relaciones r
        JOIN nodos n1 ON r.origen_id = n1.id
        JOIN nodos n2 ON r.destino_id = n2.id
        WHERE r.origen_id = ? OR r.destino_id = ?
    """, (id_, id_, id_, id_, id_)).fetchall()
    return [
        {"id": r[0], "tipo": r[1], "fuente": r[2], "cita_textual": r[3],
         "otro_nombre": r[4], "otro_id": r[5], "direccion": r[6]}
        for r in filas
    ]
