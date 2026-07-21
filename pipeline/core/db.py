"""Operaciones de base de datos para el pipeline.

Todas las funciones de CRUD, fusión y consulta de la DB.
"""
import json
import sqlite3

from .config import DB_PATH, TIPOS_VALIDOS_RELACION, TIPOS_VALIDOS_NODO


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

# ═══════════════════════════════════════════════════════════════════════════
# VALIDACIÓN CENTRALIZADA DE RELACIONES (Manifiesto v1.1)
# ═══════════════════════════════════════════════════════════════════════════

# Mapa de compatibilidad: tipo_relacion -> (origenes_validos, destinos_validos)
COMPATIBILIDAD_RELACIONES = {
    "autor_de":              ({"autor"}, {"obra"}),
    "influenciado_por":      ({"autor", "obra", "escuela", "corriente", "concepto"},
                              {"autor", "obra", "escuela", "corriente", "concepto"}),
    "critica_a":             ({"autor", "obra", "escuela", "corriente"},
                              {"autor", "obra", "escuela", "corriente", "concepto"}),
    "desarrolla_concepto":   ({"autor", "obra", "escuela", "corriente"}, {"concepto"}),
    "redefine_a":            ({"autor", "obra", "concepto"}, {"concepto"}),
    "precursor_de":          ({"autor", "obra", "escuela", "corriente", "concepto"},
                              {"autor", "obra", "escuela", "corriente", "concepto"}),
    "pertenece_a":           ({"autor", "concepto", "escuela"}, {"escuela", "corriente"}),
    "estudia_a":             ({"autor", "obra"}, {"poblacion", "cultura"}),
    "contemporaneo_de":      ({"autor"}, {"autor"}),
    "parte_del_debate":      ({"autor", "obra", "concepto", "poblacion", "escuela", "corriente"},
                              {"debate"}),
    "es_mentor_de":          ({"autor"}, {"autor"}),
    "colabora_con":          ({"autor"}, {"autor"}),
}


def _validar_tipo_relacion(tipo: str) -> tuple[bool, str | None]:
    """Verifica que el tipo de relación sea canónico (Nivel A)."""
    if tipo not in TIPOS_VALIDOS_RELACION:
        return False, f"Tipo '{tipo}' no es canónico. Válidos: {sorted(TIPOS_VALIDOS_RELACION)}"
    return True, None


def _validar_no_reflexividad(origen_id: int, destino_id: int) -> tuple[bool, str | None]:
    """Verifica que un nodo no se conecte a sí mismo."""
    if origen_id == destino_id:
        return False, "Un nodo no puede conectarse a sí mismo (no reflexividad)"
    return True, None


def _validar_firewall_poblacion(conn: sqlite3.Connection, origen_id: int, destino_id: int,
                                 tipo: str) -> tuple[bool, str | None]:
    """
    Firewall epistemológico (Manifiesto §5.3):
    - poblacion SOLO puede ser destino de 'estudia_a'
    - poblacion SOLO puede ser origen de 'parte_del_debate'
    """
    tipos_nodo = dict(conn.execute("SELECT id, tipo FROM nodos").fetchall())
    tipo_origen = tipos_nodo.get(origen_id)
    tipo_destino = tipos_nodo.get(destino_id)

    if tipo_origen is None or tipo_destino is None:
        return True, None

    if tipo_origen == "poblacion" and tipo != "parte_del_debate":
        return False, (f"Firewall: 'poblacion' como origen solo permite 'parte_del_debate', "
                       f"no '{tipo}'")

    if tipo_destino == "poblacion" and tipo != "estudia_a":
        return False, (f"Firewall: 'poblacion' como destino solo permite 'estudia_a', "
                       f"no '{tipo}'")

    return True, None


def _validar_compatibilidad_nodos(conn: sqlite3.Connection, origen_id: int, destino_id: int,
                                   tipo: str) -> tuple[bool, str | None]:
    """Verifica que los tipos de nodo sean compatibles con el tipo de relación."""
    if tipo not in COMPATIBILIDAD_RELACIONES:
        return True, None

    tipos_nodo = dict(conn.execute("SELECT id, tipo FROM nodos").fetchall())
    tipo_origen = tipos_nodo.get(origen_id)
    tipo_destino = tipos_nodo.get(destino_id)

    if tipo_origen is None or tipo_destino is None:
        return True, None

    origenes_ok, destinos_ok = COMPATIBILIDAD_RELACIONES[tipo]
    errores = []
    if tipo_origen not in origenes_ok:
        errores.append(f"Origen tipo '{tipo_origen}' no compatible con '{tipo}' (esperaba: {sorted(origenes_ok)})")
    if tipo_destino not in destinos_ok:
        errores.append(f"Destino tipo '{tipo_destino}' no compatible con '{tipo}' (esperaba: {sorted(destinos_ok)})")

    if errores:
        return False, "; ".join(errores)
    return True, None


def _validar_evidencia(fuente: str | None, cita_textual: str | None) -> tuple[bool, str | None]:
    """Verifica que la relación tenga evidencia documental (Manifiesto §6.2)."""
    if not fuente and not cita_textual:
        return False, "Relación sin evidencia: se requiere al menos 'fuente' o 'cita_textual'"
    return True, None


def validar_relacion(conn: sqlite3.Connection, origen_id: int, destino_id: int,
                     tipo: str, fuente: str | None = None,
                     cita_textual: str | None = None) -> tuple[bool, str | None]:
    """
    Punto de entrada único para validación ontológica de relaciones.

    Ejecuta todas las validaciones definidas en el Manifiesto v1.1:
    1. Tipo de relación canónico
    2. No reflexividad
    3. Firewall epistemológico (poblacion)
    4. Compatibilidad origen/destino
    5. Evidencia documental

    Retorna:
        (True, None) si la relación es válida
        (False, "error(s)") si no pasa alguna validación
    """
    validadores = [
        ("tipo_relacion", lambda: _validar_tipo_relacion(tipo)),
        ("reflexividad", lambda: _validar_no_reflexividad(origen_id, destino_id)),
        ("firewall", lambda: _validar_firewall_poblacion(conn, origen_id, destino_id, tipo)),
        ("compatibilidad", lambda: _validar_compatibilidad_nodos(conn, origen_id, destino_id, tipo)),
        ("evidencia", lambda: _validar_evidencia(fuente, cita_textual)),
    ]

    errores = []
    for nombre, validator in validadores:
        ok, error = validator()
        if not ok:
            errores.append(f"[{nombre}] {error}")

    if errores:
        return False, " | ".join(errores)
    return True, None
