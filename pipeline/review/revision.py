"""Herramientas de revisión de candidatos (Fase 2).

Funciones para revisar manual y automática mente los candidatos extraídos.
"""
import json
from collections import defaultdict
from difflib import get_close_matches

from ..core.config import (
    CANDIDATOS_PATH, REVISION_ESTADO_PATH,
    TIPOS_VALIDOS_NODO, PATRON_AUTOR_SUPERFICIAL,
    CUTOFF_FUZZY_REVISION,
)
from ..core.db import conectar_db, relacion_ya_existe
from ..core.utils import (
    normalizar_tipo_relacion, pedir_opcion, barra_progreso,
    clave_relacion, similitud,
)


def _cargar_estado_revision():
    if REVISION_ESTADO_PATH.exists():
        return json.loads(REVISION_ESTADO_PATH.read_text(encoding="utf-8"))
    return {"nodos_revisados": {}, "relaciones_revisadas": []}


def _guardar_estado_revision(estado):
    REVISION_ESTADO_PATH.write_text(
        json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def herramienta_revisar():
    """
    Revisión manual de candidatos_pendientes.json, uno por uno: para cada
    nodo nuevo pregunta aprobar/rechazar/editar (incluyendo tipo e id), con
    detección de posibles duplicados y descarte automático de 'autores
    superficiales' (menciones de nota al pie sin aporte teórico). Para cada
    relación, resuelve el id real (numérico existente o snake_case nuevo) y
    evita insertar relaciones ya existentes. Checkpoint retomable en
    revision_estado.json: si cancelás a mitad de camino, la próxima corrida
    sigue exactamente donde quedaste.
    """
    if not CANDIDATOS_PATH.exists():
        print("✗ No hay candidatos_pendientes.json. Corre extractor.py primero.")
        return

    candidatos = json.loads(CANDIDATOS_PATH.read_text(encoding="utf-8"))
    estado = _cargar_estado_revision()
    conn = conectar_db()

    filas = conn.execute("SELECT id, nombre, tipo FROM nodos").fetchall()
    catalogo = {nombre: id_ for id_, nombre, tipo in filas}
    catalogo_por_tipo = defaultdict(dict)
    for id_, nombre, tipo in filas:
        catalogo_por_tipo[tipo][nombre] = id_
    mapa_gemini_a_real = {
        id_gemini: info["id_real"]
        for id_gemini, info in estado["nodos_revisados"].items()
        if info["decision"] in ("insertado", "reutilizado")
    }

    nodos_nuevos = candidatos.get("nodos_nuevos", [])
    pendientes_nodos = [n for n in nodos_nuevos if n["id"] not in estado["nodos_revisados"]]
    ya_hechos_nodos = len(nodos_nuevos) - len(pendientes_nodos)

    print("═" * 60)
    print("NODOS NUEVOS")
    print(f"  {barra_progreso(ya_hechos_nodos, len(nodos_nuevos))}")
    print("═" * 60)

    for n in pendientes_nodos:
        id_gemini = n["id"]
        print(f"\n[{n['confianza'].upper()}] {n['tipo']} — {n['nombre']} (id: {id_gemini})")
        print(f"  {n.get('descripcion', n.get('resumen', ''))}")
        print(f"  Progreso: {barra_progreso(ya_hechos_nodos, len(nodos_nuevos))}")
        if n.get("justificacion_concepto") and n["tipo"] == "concepto":
            print(f"  Justificación: {n['justificacion_concepto']}")

        if PATRON_AUTOR_SUPERFICIAL.search(n.get("descripcion", n.get("resumen", ""))) and n["tipo"] == "autor":
            print(f"  ⚠ Autor superficial — descartado automáticamente.")
            estado["nodos_revisados"][id_gemini] = {"decision": "descartado_auto", "id_real": None}
            _guardar_estado_revision(estado)
            ya_hechos_nodos += 1
            continue

        nombres_mismo_tipo = list(catalogo_por_tipo.get(n["tipo"], {}).keys())
        similares = get_close_matches(n["nombre"], nombres_mismo_tipo, n=3, cutoff=CUTOFF_FUZZY_REVISION)
        decision_tomada = False

        if similares:
            print(f"  ⚠ POSIBLE DUPLICADO de: {', '.join(similares)}")
            resp = pedir_opcion(
                "  ¿Es el mismo nodo? (s = usar existente / n = distinto / omitir): ",
                validas={"s", "n", "omitir"}, alias={"si": "s", "sí": "s", "o": "omitir"},
            )
            if resp == "s":
                id_real = catalogo_por_tipo[n["tipo"]][similares[0]]
                mapa_gemini_a_real[id_gemini] = id_real
                estado["nodos_revisados"][id_gemini] = {"decision": "reutilizado", "id_real": id_real}
                _guardar_estado_revision(estado)
                print("  ✓ Reutilizado")
                decision_tomada = True
            elif resp == "omitir":
                estado["nodos_revisados"][id_gemini] = {"decision": "omitido", "id_real": None}
                _guardar_estado_revision(estado)
                print("  ✗ Omitido")
                decision_tomada = True

        if not decision_tomada:
            resp = pedir_opcion(
                "  ¿Aprobar como nodo nuevo? (s/n/editar): ",
                validas={"s", "n", "editar"}, alias={"si": "s", "sí": "s", "e": "editar"},
            )
            if resp == "s":
                tipo_final = n["tipo"].strip().lower()
                if tipo_final not in TIPOS_VALIDOS_NODO:
                    print(f"  ⚠ Tipo no reconocido: '{n['tipo']}'")
                    entrada = input(f"  Corregí el tipo ({'/'.join(sorted(TIPOS_VALIDOS_NODO))}): ").strip().lower()
                    tipo_final = entrada if entrada in TIPOS_VALIDOS_NODO else tipo_final
                metadatos = {"id_gemini": id_gemini}
                if n.get("justificacion_concepto"):
                    metadatos["justificacion_concepto"] = n["justificacion_concepto"]
                if n.get("confianza"):
                    metadatos["confianza"] = n["confianza"]
                try:
                    cur = conn.execute(
                        "INSERT INTO nodos (tipo, nombre, descripcion, metadatos) VALUES (?, ?, ?, ?)",
                        (tipo_final, n["nombre"], n.get("descripcion", n.get("resumen", "")),
                         json.dumps(metadatos, ensure_ascii=False)),
                    )
                except Exception:
                    print(f"  ✗ Ya existe un nodo con el nombre '{n['nombre']}' (UNIQUE). Se omite.")
                    estado["nodos_revisados"][id_gemini] = {"decision": "omitido_duplicado_nombre", "id_real": None}
                    _guardar_estado_revision(estado)
                    ya_hechos_nodos += 1
                    continue
                id_real = cur.lastrowid
                conn.commit()
                mapa_gemini_a_real[id_gemini] = id_real
                catalogo[n["nombre"]] = id_real
                estado["nodos_revisados"][id_gemini] = {"decision": "insertado", "id_real": id_real}
                _guardar_estado_revision(estado)
                print(f"  ✓ Insertado (id={id_real})")
            elif resp == "editar":
                nuevo_nombre = input(f"  Nombre [{n['nombre']}]: ") or n["nombre"]
                nueva_desc = input(f"  Descripción [{n.get('descripcion', n.get('resumen', ''))}]: ") or n.get("descripcion", n.get("resumen", ""))
                entrada_tipo = input(f"  Tipo [{n['tipo']}] ({'/'.join(sorted(TIPOS_VALIDOS_NODO))}): ").strip().lower()
                nuevo_tipo = entrada_tipo if entrada_tipo in TIPOS_VALIDOS_NODO else n["tipo"]
                cur = conn.execute(
                    "INSERT INTO nodos (tipo, nombre, descripcion, metadatos) VALUES (?, ?, ?, ?)",
                    (nuevo_tipo, nuevo_nombre, nueva_desc, json.dumps({"id_gemini": id_gemini})),
                )
                id_real = cur.lastrowid
                conn.commit()
                mapa_gemini_a_real[id_gemini] = id_real
                catalogo[nuevo_nombre] = id_real
                estado["nodos_revisados"][id_gemini] = {"decision": "insertado", "id_real": id_real}
                _guardar_estado_revision(estado)
                print(f"  ✓ Insertado editado (id={id_real})")
            else:
                estado["nodos_revisados"][id_gemini] = {"decision": "descartado", "id_real": None}
                _guardar_estado_revision(estado)
                print("  ✗ Descartado")
        ya_hechos_nodos += 1

    print("\n" + "═" * 60)
    relaciones_nuevas = candidatos.get("relaciones_nuevas", [])
    ids_validos = {row[0] for row in conn.execute("SELECT id FROM nodos")}
    pendientes_rels = [r for r in relaciones_nuevas if clave_relacion(r) not in estado["relaciones_revisadas"]]
    ya_hechos_rels = len(relaciones_nuevas) - len(pendientes_rels)
    print("RELACIONES NUEVAS")
    print(f"  {barra_progreso(ya_hechos_rels, len(relaciones_nuevas))}")
    print("═" * 60)

    for r in pendientes_rels:
        clave = clave_relacion(r)
        origen = r["origen"]
        destino = r["destino"]
        if isinstance(origen, int) or (isinstance(origen, str) and origen.strip().isdigit()):
            origen = int(origen) if isinstance(origen, int) else int(origen.strip())
        else:
            origen = mapa_gemini_a_real.get(origen)
        if isinstance(destino, int) or (isinstance(destino, str) and destino.strip().isdigit()):
            destino = int(destino) if isinstance(destino, int) else int(destino.strip())
        else:
            destino = mapa_gemini_a_real.get(destino)

        if origen is None or destino is None or origen not in ids_validos or destino not in ids_validos:
            print(f"\n⚠ Relación omitida — nodo no mapeado: {r['origen']} → {r['destino']}")
            estado["relaciones_revisadas"].append(clave)
            _guardar_estado_revision(estado)
            ya_hechos_rels += 1
            continue

        if relacion_ya_existe(conn, origen, destino, normalizar_tipo_relacion(r["tipo"])):
            print(f"\n⚠ Relación YA EXISTE, se omite: {r['origen']} → {r['destino']} ({r['tipo']})")
            estado["relaciones_revisadas"].append(clave)
            _guardar_estado_revision(estado)
            ya_hechos_rels += 1
            continue

        print(f"\n[{r['confianza'].upper()}] {r['origen']} → {r['destino']} --{r['tipo']}-->")
        print(f'  Cita: "{r.get("cita_textual", "")}"')
        print(f"  Progreso: {barra_progreso(ya_hechos_rels, len(relaciones_nuevas))}")
        if r.get("fuente"):
            print(f"  Fuente: {r['fuente']}")
        resp = pedir_opcion("  ¿Aprobar? (s/n): ", validas={"s", "n"}, alias={"si": "s", "sí": "s"})
        if resp == "s":
            conn.execute(
                "INSERT INTO relaciones (origen_id, destino_id, tipo, peso, fuente, cita_textual) VALUES (?, ?, ?, 1.0, ?, ?)",
                (origen, destino, normalizar_tipo_relacion(r["tipo"]), r.get("fuente"), r.get("cita_textual")),
            )
            conn.commit()
            print("  ✓ Insertada")
        else:
            print("  ✗ Descartada")
        estado["relaciones_revisadas"].append(clave)
        _guardar_estado_revision(estado)
        ya_hechos_rels += 1

    conn.close()


def _resolver_referencia_conexion(ref, mapa_id, catalogo, nombres_por_id_gemini, umbral, ids_validos):
    """Resuelve una referencia de nodo para conectar_automatico: numérica
    directa (si existe), id_gemini de este mismo lote, o fuzzy match por nombre."""
    if isinstance(ref, int) or (isinstance(ref, str) and ref.strip().isdigit()):
        posible = int(ref)
        return posible if posible in ids_validos else None
    if ref in mapa_id:
        valor = mapa_id[ref]
        return valor if not isinstance(valor, str) else None
    nombre = nombres_por_id_gemini.get(ref)
    if nombre:
        sims = get_close_matches(nombre, list(catalogo.keys()), n=1, cutoff=umbral)
        if sims:
            return catalogo[sims[0]][0]
    return None


def herramienta_conectar_automatico(umbral=None, dry_run=False):
    """
    Resuelve TODAS las relaciones pendientes de candidatos_pendientes.json
    de una sola pasada, sin preguntar una por una: match directo por id
    numérico existente, o fuzzy match por nombre contra el catálogo actual
    de la DB. Los nodos nuevos sin match se insertan automáticamente.
    """
    from ..core.config import UMBRAL_FUZZY
    umbral = umbral if umbral is not None else UMBRAL_FUZZY
    if not CANDIDATOS_PATH.exists():
        print("✗ No hay candidatos_pendientes.json.")
        return

    candidatos = json.loads(CANDIDATOS_PATH.read_text(encoding="utf-8"))
    conn = conectar_db()
    filas = conn.execute("SELECT id, tipo, nombre FROM nodos").fetchall()
    catalogo = {nombre: (id_, tipo) for id_, tipo, nombre in filas}
    ids_validos = {id_ for id_, _, _ in filas}
    nombres_por_id_gemini = {n["id"]: n["nombre"] for n in candidatos.get("nodos_nuevos", [])}

    print("═" * 60)
    print(f"CONEXIÓN AUTOMÁTICA (umbral: {umbral}){' — DRY RUN' if dry_run else ''}")
    print("═" * 60)

    log_nodos = []
    mapa_id = {}
    for n in candidatos.get("nodos_nuevos", []):
        if n["nombre"] in catalogo:
            mapa_id[n["id"]] = catalogo[n["nombre"]][0]
        elif dry_run:
            mapa_id[n["id"]] = f"DRY:{n['nombre']}"
            log_nodos.append(n["nombre"])
        else:
            cur = conn.execute(
                "INSERT INTO nodos (tipo, nombre, descripcion, metadatos) VALUES (?, ?, ?, ?)",
                (n["tipo"], n["nombre"], n.get("descripcion", n.get("resumen", "")),
                 json.dumps({"id_gemini": n["id"], "insertado_por": "conexion_automatica"})),
            )
            id_real = cur.lastrowid
            conn.commit()
            mapa_id[n["id"]] = id_real
            catalogo[n["nombre"]] = (id_real, n["tipo"])
            ids_validos.add(id_real)
            log_nodos.append(n["nombre"])

    print(f"\nNodos insertados: {len(log_nodos)}")

    insertadas = 0
    ya_existian = 0
    no_resolubles = 0
    for r in candidatos.get("relaciones_nuevas", []):
        origen = _resolver_referencia_conexion(r["origen"], mapa_id, catalogo, nombres_por_id_gemini, umbral, ids_validos)
        destino = _resolver_referencia_conexion(r["destino"], mapa_id, catalogo, nombres_por_id_gemini, umbral, ids_validos)

        if origen is None or destino is None:
            no_resolubles += 1
            continue

        if dry_run:
            insertadas += 1
            continue

        if relacion_ya_existe(conn, origen, destino, normalizar_tipo_relacion(r["tipo"])):
            ya_existian += 1
            continue

        conn.execute(
            "INSERT INTO relaciones (origen_id, destino_id, tipo, peso, fuente, cita_textual) VALUES (?, ?, ?, 1.0, ?, ?)",
            (origen, destino, normalizar_tipo_relacion(r["tipo"]), r.get("fuente"), r.get("cita_textual")),
        )
        conn.commit()
        insertadas += 1

    conn.close()
    etiqueta = "Simuladas como insertables" if dry_run else "Insertadas"
    print(f"\n{etiqueta}: {insertadas} | Ya existían: {ya_existian} | No resolubles: {no_resolubles}")


def herramienta_conectar_automatico_menu():
    """Wrapper interactivo: pregunta el umbral de similitud y si simular o aplicar de verdad."""
    umbral_str = input("  Umbral de similitud fuzzy [0.80]: ").strip()
    umbral = float(umbral_str) if umbral_str else 0.80
    resp = pedir_opcion(
        "  ¿Simular o aplicar de verdad? (simular/aplicar): ",
        validas={"simular", "aplicar"}, alias={"s": "simular", "a": "aplicar"},
    )
    herramienta_conectar_automatico(umbral=umbral, dry_run=(resp == "simular"))


# ═══════════════════════════════════════════════════════════════════════════
# REVISIÓN TOTAL DE NODOS
# ═══════════════════════════════════════════════════════════════════════════

import csv
from ..core.config import (
    REVISION_TOTAL_ESTADO_PATH, REVISION_TOTAL_LOG_PATH,
    CRITERIOS_POR_TIPO, TIPOS_VALIDOS_NODO,
)
from ..core.db import cargar_grados, eliminar_nodo_cascada


def _cargar_estado_revision_total():
    if REVISION_TOTAL_ESTADO_PATH.exists():
        return json.loads(REVISION_TOTAL_ESTADO_PATH.read_text(encoding="utf-8"))
    return {"nodos_procesados": []}


def _guardar_estado_revision_total(estado):
    REVISION_TOTAL_ESTADO_PATH.write_text(
        json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _registrar_log_revision_total(id_, tipo, nombre, decision, detalle=""):
    with open(REVISION_TOTAL_LOG_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([id_, tipo, nombre, decision, detalle])


def herramienta_revision_total(tamano_lote=None):
    """
    Revisión completa de TODOS los nodos de la DB, agrupados por tipo,
    con criterios específicos por tipo. Decisiones: mantener/reclasificar/
    fusionar/eliminar/saltar. Resumable via checkpoint. Log en CSV.
    """
    conn = conectar_db()
    estado = _cargar_estado_revision_total()
    procesados = set(estado.get("nodos_procesados", []))

    filas = conn.execute("SELECT id, tipo, nombre, descripcion FROM nodos ORDER BY tipo, id").fetchall()
    pendientes = [(id_, tipo, nombre, desc) for id_, tipo, nombre, desc in filas if id_ not in procesados]

    if tamano_lote:
        pendientes = pendientes[:tamano_lote]

    print("═" * 60)
    print(f"REVISIÓN TOTAL — {len(pendientes)} nodos pendientes")
    print("═" * 60)

    grados = cargar_grados(conn)
    for id_, tipo, nombre, desc in pendientes:
        g = grados.get(id_, 0)
        criterio = CRITERIOS_POR_TIPO.get(tipo, "")
        print(f"\n[{tipo}] {nombre} (id={id_}, {g} relaciones)")
        if desc:
            print(f"  {desc[:120]}")
        if criterio:
            print(f"  Criterio: {criterio}")

        resp = pedir_opcion(
            "  Acción: (m)antener / (r)eclasificar / (f)usionar / (e)liminar / (s)altar: ",
            validas={"m", "r", "f", "e", "s"},
        )

        if resp == "m":
            _registrar_log_revision_total(id_, tipo, nombre, "mantenido")
            print("  ✓ Mantenido")
        elif resp == "r":
            nuevo_tipo = input(f"  Nuevo tipo ({'/'.join(sorted(TIPOS_VALIDOS_NODO))}): ").strip().lower()
            if nuevo_tipo in TIPOS_VALIDOS_NODO:
                conn.execute("UPDATE nodos SET tipo = ? WHERE id = ?", (nuevo_tipo, id_))
                conn.commit()
                _registrar_log_revision_total(id_, tipo, nombre, "reclasificado", nuevo_tipo)
                print(f"  ✓ Reclasificado a {nuevo_tipo}")
        elif resp == "f":
            objetivo = input("  Fusionar con (id o nombre): ").strip()
            if objetivo.isdigit():
                id_objetivo = int(objetivo)
            else:
                match = conn.execute("SELECT id FROM nodos WHERE nombre = ?", (objetivo,)).fetchone()
                id_objetivo = match[0] if match else None
            if id_objetivo:
                fusionar_nodos(conn, id_objetivo, id_)
                _registrar_log_revision_total(id_, tipo, nombre, "fusionado", str(id_objetivo))
                print(f"  ✓ Fusionado con id={id_objetivo}")
            else:
                print("  ⚠ Objetivo no encontrado")
        elif resp == "e":
            eliminar_nodo_cascada(conn, id_)
            _registrar_log_revision_total(id_, tipo, nombre, "eliminado")
            print("  ✓ Eliminado")
        else:
            _registrar_log_revision_total(id_, tipo, nombre, "saltado")
            print("  ⏭ Saltado")

        estado["nodos_procesados"].append(id_)
        _guardar_estado_revision_total(estado)

    conn.close()


def herramienta_revision_total_menu():
    lote_str = input("  Tamaño de lote (Enter = todos): ").strip()
    tamano = int(lote_str) if lote_str.isdigit() else None
    herramienta_revision_total(tamano_lote=tamano)
