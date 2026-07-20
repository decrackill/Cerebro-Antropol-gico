"""Herramientas de limpieza y deduplicación (Fase 4).

Funciones para limpiar nodos ruido y fusionar duplicados.
"""
import json
import logging
from collections import defaultdict

from ..core.config import (
    BASE_DIR, LIMPIEZA_ESTADO_PATH,
    UMBRAL_SIMILITUD, UMBRAL_LIMPIEZA_AUTO,
    PATRONES_RUIDO, EXCLUSIONES_FUSION_NOMBRES_NOMBRES,
)
from ..core.db import (
    conectar_db, fusionar_nodos, eliminar_nodo_cascada,
    cargar_grados,
)
from ..core.utils import (
    normalizar, similitud, pedir_opcion, es_exclusion_fusion,
    detectar_duplicados, es_nodo_ruido, es_nodo_ruido_aislado,
    normalizar_tipo_relacion,
)

logger = logging.getLogger("cerebro.limpieza")


def _cargar_estado_limpieza():
    if LIMPIEZA_ESTADO_PATH.exists():
        return json.loads(LIMPIEZA_ESTADO_PATH.read_text(encoding="utf-8"))
    return {"nodos_procesados": []}


def _guardar_estado_limpieza(estado):
    LIMPIEZA_ESTADO_PATH.write_text(
        json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def herramienta_limpieza_automatica(aplicar=False):
    """
    Fusión segura de duplicados + eliminación de ruido biomédico, sin
    preguntar. Fusión un par solo cuando el nombre corto está literalmente
    CONTENIDO en el nombre largo (mismo tipo) y el corto tiene 0 relaciones.
    Elimina nodos con 0 relaciones que coinciden con vocabulario médico/biológico.
    """
    conn = conectar_db()
    filas = conn.execute("SELECT id, tipo, nombre, descripcion FROM nodos ORDER BY tipo, id").fetchall()
    grados = cargar_grados(conn)

    por_tipo = defaultdict(list)
    for id_, tipo, nombre, desc in filas:
        por_tipo[tipo].append((id_, nombre))

    fusiones = []
    ya_usados = set()
    for tipo, items in por_tipo.items():
        for id_a, nombre_a in items:
            if id_a in ya_usados:
                continue
            norm_a = normalizar(nombre_a)
            for id_b, nombre_b in items:
                if id_b == id_a or id_b in ya_usados:
                    continue
                norm_b = normalizar(nombre_b)
                if norm_a == norm_b:
                    continue
                if norm_a in norm_b or norm_b in norm_a:
                    if es_exclusion_fusion(nombre_a, nombre_b):
                        continue
                    g_a = grados.get(id_a, 0)
                    g_b = grados.get(id_b, 0)
                    if g_a == 0 and g_b > 0:
                        fusiones.append((id_b, id_a, nombre_b, nombre_a, "nombre_contenido"))
                    elif g_b == 0 and g_a > 0:
                        fusiones.append((id_a, id_b, nombre_a, nombre_b, "nombre_contenido"))
                    break

    eliminaciones = []
    for id_, tipo, nombre, desc in filas:
        if grados.get(id_, 0) == 0 and es_nodo_ruido(nombre, desc, grados.get(id_, 0)):
            eliminaciones.append((id_, tipo, nombre))

    print("═" * 60)
    print(f"LIMPIEZA AUTOMÁTICA{' — DRY RUN' if not aplicar else ''}")
    print("═" * 60)
    print(f"\nFusiones seguras: {len(fusiones)}")
    for id_mantener, id_borrar, n_mantener, n_borrar, razon in fusiones:
        print(f"  '{n_borrar}' → '{n_mantener}' ({razon})")
    print(f"\nEliminaciones de ruido: {len(eliminaciones)}")
    for id_, tipo, nombre in eliminaciones:
        print(f"  [{tipo}] {nombre}")

    if aplicar:
        for id_mantener, id_borrar, _, _, _ in fusiones:
            fusionar_nodos(conn, id_mantener, id_borrar)
        for id_, _, _ in eliminaciones:
            eliminar_nodo_cascada(conn, id_)
        print(f"\n✓ Aplicado: {len(fusiones)} fusiones, {len(eliminaciones)} eliminaciones")
    else:
        print("\n  (simulación — no se modificó la DB)")

    conn.close()


def herramienta_limpieza_automatica_menu():
    resp = pedir_opcion(
        "  ¿Simular o aplicar? (simular/aplicar): ",
        validas={"simular", "aplicar"}, alias={"s": "simular", "a": "aplicar"},
    )
    herramienta_limpieza_automatica(aplicar=(resp == "aplicar"))


def herramienta_fusionar_duplicados():
    """Fusión manual uno por uno de pares sospechosos."""
    conn = conectar_db()
    filas = conn.execute("SELECT id, tipo, nombre FROM nodos ORDER BY tipo, id").fetchall()
    grados = cargar_grados(conn)
    por_tipo = defaultdict(list)
    for id_, tipo, nombre in filas:
        por_tipo[tipo].append((id_, nombre))

    duplicados = detectar_duplicados(por_tipo)
    if not duplicados:
        print("✓ No se encontraron duplicados sospechosos.")
        conn.close()
        return

    print(f"Encontrados {len(duplicados)} pares sospechosos.\n")
    for id_a, nombre_a, id_b, nombre_b, tipo, score in duplicados:
        g_a = grados.get(id_a, 0)
        g_b = grados.get(id_b, 0)
        print(f"[{tipo}] '{nombre_a}' ({g_a} rels) ↔ '{nombre_b}' ({g_b} rels) — similitud: {score:.2f}")
        resp = pedir_opcion(
            "  ¿Fusionar? (a = mantener 'a' / b = mantener 'b' / n = no): ",
            validas={"a", "b", "n"}, alias={"si": "a", "sí": "a"},
        )
        if resp == "a":
            fusionar_nodos(conn, id_a, id_b)
            print(f"  ✓ Fusionado: '{nombre_b}' → '{nombre_a}'")
        elif resp == "b":
            fusionar_nodos(conn, id_b, id_a)
            print(f"  ✓ Fusionado: '{nombre_a}' → '{nombre_b}'")
        else:
            print("  ✗ Omitido")

    conn.close()


def herramienta_fusionar_auto():
    """Fusión automática: si un nodo del par tiene 0 relaciones, se fusiona sin preguntar."""
    conn = conectar_db()
    filas = conn.execute("SELECT id, tipo, nombre FROM nodos ORDER BY tipo, id").fetchall()
    grados = cargar_grados(conn)
    por_tipo = defaultdict(list)
    for id_, tipo, nombre in filas:
        por_tipo[tipo].append((id_, nombre))

    duplicados = detectar_duplicados(por_tipo, umbral=UMBRAL_LIMPIEZA_AUTO)
    fusionadas = 0
    for id_a, nombre_a, id_b, nombre_b, tipo, score in duplicados:
        g_a = grados.get(id_a, 0)
        g_b = grados.get(id_b, 0)
        if g_a == 0 and g_b > 0:
            fusionar_nodos(conn, id_b, id_a)
            fusionadas += 1
        elif g_b == 0 and g_a > 0:
            fusionar_nodos(conn, id_a, id_b)
            fusionadas += 1

    print(f"Fusionadas: {fusionadas}")
    conn.close()


def herramienta_limpieza_asistida():
    """Limpieza asistida: presenta nodos sospechosos uno por uno."""
    conn = conectar_db()
    filas = conn.execute("""
        SELECT n.id, n.tipo, n.nombre, n.descripcion
        FROM nodos n
        LEFT JOIN (SELECT origen_id AS id_nodo FROM relaciones
                   UNION ALL SELECT destino_id AS id_nodo FROM relaciones) r
          ON n.id = r.id_nodo
        WHERE r.id_nodo IS NULL
        ORDER BY n.tipo, n.nombre
    """).fetchall()

    if not filas:
        print("✓ No hay nodos aislados.")
        conn.close()
        return

    estado = _cargar_estado_limpieza()
    procesados = set(estado.get("nodos_procesados", []))
    pendientes = [(id_, tipo, nombre, desc) for id_, tipo, nombre, desc in filas if id_ not in procesados]

    print(f"Nodos aislados: {len(pendientes)} pendientes\n")
    for id_, tipo, nombre, desc in pendientes:
        print(f"[{tipo}] {nombre}")
        if desc:
            print(f"  {desc[:100]}...")
        resp = pedir_opcion(
            "  Acción: (m)antener / (r)eclasificar / (e)liminar / (s)altar: ",
            validas={"m", "r", "e", "s"},
        )
        if resp == "e":
            eliminar_nodo_cascada(conn, id_)
            print(f"  ✓ Eliminado")
        elif resp == "r":
            nuevo_tipo = input(f"  Nuevo tipo ({'/'.join(sorted(TIPOS_VALIDOS_NODO))}): ").strip().lower()
            if nuevo_tipo in TIPOS_VALIDOS_NODO:
                conn.execute("UPDATE nodos SET tipo = ? WHERE id = ?", (nuevo_tipo, id_))
                conn.commit()
                print(f"  ✓ Reclasificado a {nuevo_tipo}")
        else:
            print(f"  {'✓ Mantenido' if resp == 'm' else '⏭ Saltado'}")

        estado["nodos_procesados"].append(id_)
        _guardar_estado_limpieza(estado)

    conn.close()


def herramienta_limpiar_auto():
    """Eliminación agresiva automática de nodos ruido."""
    conn = conectar_db()
    filas = conn.execute("""
        SELECT n.id, n.tipo, n.nombre, n.descripcion
        FROM nodos n
        LEFT JOIN (SELECT origen_id AS id_nodo FROM relaciones
                   UNION ALL SELECT destino_id AS id_nodo FROM relaciones) r
          ON n.id = r.id_nodo
        WHERE r.id_nodo IS NULL
        ORDER BY n.tipo, n.nombre
    """).fetchall()

    eliminados = 0
    for id_, tipo, nombre, desc in filas:
        if es_nodo_ruido_aislado(nombre, desc, 0):
            eliminar_nodo_cascada(conn, id_)
            eliminados += 1

    print(f"Eliminados: {eliminados}")
    conn.close()


# ═══════════════════════════════════════════════════════════════════════════
# RECUPERACIÓN DE RELACIONES
# ═══════════════════════════════════════════════════════════════════════════

from ..core.config import RECUPERACION_ESTADO_PATH
from ..core.db import construir_mapa_resolucion, relacion_ya_existe


def herramienta_recuperar_relaciones():
    """
    Reprocesa relaciones de TODOS los archivos candidatos_procesados_*.json
    (y candidatos_pendientes.json si existe) que aún no se hayan podido
    insertar, usando construir_mapa_resolucion — que entiende ids numéricos
    actuales, ids snake_case originales de Gemini, Y cualquier id absorbido
    en fusiones posteriores. Esto rescata relaciones que antes quedaban 'no
    resolubles' para siempre porque el nodo que citaban fue fusionado con
    otro después de la extracción original. Checkpoint propio
    (recuperacion_estado.json) para no reprocesar lo ya resuelto.
    """
    archivos = sorted(BASE_DIR.glob("candidatos_procesados_*.json"))
    pendiente = BASE_DIR / "candidatos_pendientes.json"
    if pendiente.exists():
        archivos.append(pendiente)
    if not archivos:
        print("✗ No hay archivos de candidatos.")
        return

    conn = conectar_db()
    mapa = construir_mapa_resolucion(conn)

    estado = set()
    if RECUPERACION_ESTADO_PATH.exists():
        estado = set(json.loads(RECUPERACION_ESTADO_PATH.read_text(encoding="utf-8")))

    insertadas = 0
    ya_existian = 0
    no_resolubles = 0
    for archivo in archivos:
        datos = json.loads(archivo.read_text(encoding="utf-8"))
        for r in datos.get("relaciones_nuevas", []):
            clave = f"{r['origen']}->{r['destino']}::{r['tipo']}::{r.get('cita_textual', '')[:60]}"
            if clave in estado:
                continue

            origen = mapa.get(str(r["origen"]).strip())
            destino = mapa.get(str(r["destino"]).strip())

            if origen is None or destino is None:
                no_resolubles += 1
                estado.add(clave)
                continue

            if relacion_ya_existe(conn, origen, destino, normalizar_tipo_relacion(r["tipo"])):
                ya_existian += 1
            else:
                conn.execute(
                    "INSERT INTO relaciones (origen_id, destino_id, tipo, peso, fuente, cita_textual) VALUES (?, ?, ?, 1.0, ?, ?)",
                    (origen, destino, normalizar_tipo_relacion(r["tipo"]), r.get("fuente"), r.get("cita_textual")),
                )
                conn.commit()
                insertadas += 1

            estado.add(clave)
            RECUPERACION_ESTADO_PATH.write_text(
                json.dumps(sorted(estado), ensure_ascii=False, indent=2), encoding="utf-8"
            )

    conn.close()
    print(f"Recuperadas: {insertadas} | Ya existían: {ya_existian} | No resolubles: {no_resolubles}")
