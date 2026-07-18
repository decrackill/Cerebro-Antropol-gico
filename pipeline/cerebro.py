"""
CEREBRO ANTROPOLÓGICO — Centro de Comandos Unificado
=====================================================
Todas las herramientas del pipeline en un solo archivo. Elegís el número
y se ejecuta. No necesitás recordar nombres de archivos.

Herramientas incluidas:
  1. Revisar candidatos pendientes (manual, uno por uno)
  2. Fusionar duplicados (requiere tu criterio)
  3. Fusionar duplicados automático (0 relaciones se fusionan solo)
  4. Limpieza asistida de nodos aislados/ruido
  5. Limpieza automática de ruido (sin preguntar)
  6. Limpieza automática segura (fusión + eliminación de ruido)
  7. Conexión automática de relaciones pendientes
  8. Recuperar relaciones perdidas
  9. Reforzar esquema de la DB
 10. Auditoría completa (diagnóstico, no cambia nada)
 11. Mantenimiento automático completo (post-libro)
 12. Exportar a datos.json para el navegador
 13. Limpiar archivos temporales procesados
  0. Salir

Uso: python cerebro.py
"""
import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path
from difflib import SequenceMatcher, get_close_matches
from collections import defaultdict, Counter

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR.parent / "data" / "grafo.db"
CANDIDATOS_PATH = BASE_DIR / "candidatos_pendientes.json"
REVISION_ESTADO_PATH = BASE_DIR / "revision_estado.json"
LIMPIEZA_ESTADO_PATH = BASE_DIR / "limpieza_estado.json"
RECUPERACION_ESTADO_PATH = BASE_DIR / "recuperacion_estado.json"

UMBRAL_SIMILITUD = 0.80
UMBRAL_FUZZY = 0.80

PATRONES_RUIDO = re.compile(
    r"(cr[aá]neo|cef[aá]lic|torus|osteo|esquelet|patolog[ií]a|anatom[ií]a|"
    r"medici[oó]n corporal|antropometr[ií]a|índice cef[aá]lico|"
    r"malformaci[oó]n|enfermedad|hueso|dentici[oó]n|estatura promedio|"
    r"pigmentaci[oó]n|coeficiente craneal|prognatismo|distribuci[oó]n de variables)",
    re.IGNORECASE,
)

PATRON_AUTOR_SUPERFICIAL = re.compile(
    r"(autor (mencionad|citad)o (como|en relaci)|citad[oa] en relaci[oó]n con la frecuencia)",
    re.IGNORECASE,
)

EXCLUSIONES_FUSION = {
    frozenset({236, 67}),
    frozenset({236, 233}),
    frozenset({243, 69}),
    frozenset({230, 317}),
}

TIPOS_VALIDOS_NODO = {"autor", "obra", "concepto", "escuela", "cultura", "debate", "poblacion", "corriente"}


# ─── Utilidades compartidas ────────────────────────────────────────────────

def similitud(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def normalizar(nombre):
    return re.sub(r"[^\wáéíóúñ ]", "", nombre.lower()).strip()

def pedir_opcion(mensaje, validas, alias=None):
    alias = alias or {}
    while True:
        resp = input(mensaje).strip().lower()
        if resp in alias:
            resp = alias[resp]
        if resp in validas:
            return resp
        print(f"  ⚠ No entendí '{resp}'. Opciones: {', '.join(sorted(validas))}")

def eliminar_nodo_cascada(conn, id_):
    conn.execute("DELETE FROM relaciones WHERE origen_id = ? OR destino_id = ?", (id_, id_))
    conn.execute("DELETE FROM nodos WHERE id = ?", (id_,))
    conn.commit()

def fusionar_nodos(conn, id_mantener, id_borrar):
    conn.execute("UPDATE relaciones SET origen_id = ? WHERE origen_id = ?", (id_mantener, id_borrar))
    conn.execute("UPDATE relaciones SET destino_id = ? WHERE destino_id = ?", (id_mantener, id_borrar))
    conn.execute("""
        DELETE FROM relaciones WHERE id NOT IN (
            SELECT MIN(id) FROM relaciones GROUP BY origen_id, destino_id, tipo
        )
    """)
    conn.execute("DELETE FROM nodos WHERE id = ?", (id_borrar,))
    conn.commit()

def relacion_ya_existe(conn, origen, destino, tipo):
    return conn.execute(
        "SELECT 1 FROM relaciones WHERE origen_id = ? AND destino_id = ? AND tipo = ?",
        (origen, destino, tipo),
    ).fetchone() is not None

def cargar_grados(conn):
    return dict(conn.execute("""
        SELECT id_nodo, COUNT(*) FROM (
            SELECT origen_id AS id_nodo FROM relaciones
            UNION ALL SELECT destino_id AS id_nodo FROM relaciones
        ) GROUP BY id_nodo
    """).fetchall())


# ═══════════════════════════════════════════════════════════════════════════
# 1. REVISAR CANDIDATOS (manual, uno por uno)
# ═══════════════════════════════════════════════════════════════════════════

def _barra_progreso(hechos, total, ancho=30):
    if total == 0:
        return "[sin candidatos]"
    prop = hechos / total
    llenos = int(ancho * prop)
    return f"[{'█' * llenos}{'░' * (ancho - llenos)}] {hechos}/{total} ({prop*100:.0f}%)"

def _cargar_estado_revision():
    if REVISION_ESTADO_PATH.exists():
        return json.loads(REVISION_ESTADO_PATH.read_text(encoding="utf-8"))
    return {"nodos_revisados": {}, "relaciones_revisadas": []}

def _guardar_estado_revision(estado):
    REVISION_ESTADO_PATH.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")

def _clave_relacion(r):
    return f"{r['origen']}->{r['destino']}::{r['tipo']}::{r.get('cita_textual', '')[:60]}"

def herramienta_revisar():
    """Revisión manual de candidatos pendientes (uno por uno, con checkpoint retomable)."""
    if not CANDIDATOS_PATH.exists():
        print("✗ No hay candidatos_pendientes.json. Corre extractor.py primero.")
        return

    candidatos = json.loads(CANDIDATOS_PATH.read_text(encoding="utf-8"))
    estado = _cargar_estado_revision()
    conn = sqlite3.connect(DB_PATH)

    filas = conn.execute("SELECT id, nombre FROM nodos").fetchall()
    catalogo = {nombre: id_ for id_, nombre in filas}
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
    print(f"  {_barra_progreso(ya_hechos_nodos, len(nodos_nuevos))}")
    print("═" * 60)

    for n in pendientes_nodos:
        id_gemini = n["id"]
        print(f"\n[{n['confianza'].upper()}] {n['tipo']} — {n['nombre']} (id: {id_gemini})")
        print(f"  {n.get('descripcion', n.get('resumen', ''))}")
        print(f"  Progreso: {_barra_progreso(ya_hechos_nodos, len(nodos_nuevos))}")
        if n.get("justificacion_concepto") and n["tipo"] == "concepto":
            print(f"  Justificación: {n['justificacion_concepto']}")

        if PATRON_AUTOR_SUPERFICIAL.search(n.get("descripcion", n.get("resumen", ""))) and n["tipo"] == "autor":
            print(f"  ⚠ Autor superficial — descartado automáticamente.")
            estado["nodos_revisados"][id_gemini] = {"decision": "descartado_auto", "id_real": None}
            _guardar_estado_revision(estado)
            ya_hechos_nodos += 1
            continue

        similares = get_close_matches(n["nombre"], list(catalogo.keys()), n=3, cutoff=0.75)
        decision_tomada = False

        if similares:
            print(f"  ⚠ POSIBLE DUPLICADO de: {', '.join(similares)}")
            resp = pedir_opcion(
                "  ¿Es el mismo nodo? (s = usar existente / n = distinto / omitir): ",
                validas={"s", "n", "omitir"}, alias={"si": "s", "sí": "s", "o": "omitir"},
            )
            if resp == "s":
                id_real = catalogo[similares[0]]
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
                cur = conn.execute(
                    "INSERT INTO nodos (tipo, nombre, descripcion, metadatos) VALUES (?, ?, ?, ?)",
                    (n["tipo"], n["nombre"], n.get("descripcion", n.get("resumen", "")), json.dumps({"id_gemini": id_gemini})),
                )
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
    pendientes_rels = [r for r in relaciones_nuevas if _clave_relacion(r) not in estado["relaciones_revisadas"]]
    ya_hechos_rels = len(relaciones_nuevas) - len(pendientes_rels)
    print("RELACIONES NUEVAS")
    print(f"  {_barra_progreso(ya_hechos_rels, len(relaciones_nuevas))}")
    print("═" * 60)

    for r in pendientes_rels:
        clave = _clave_relacion(r)
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

        if relacion_ya_existe(conn, origen, destino, r["tipo"]):
            print(f"\n⚠ Relación YA EXISTE, se omite: {r['origen']} → {r['destino']} ({r['tipo']})")
            estado["relaciones_revisadas"].append(clave)
            _guardar_estado_revision(estado)
            ya_hechos_rels += 1
            continue

        print(f"\n[{r['confianza'].upper()}] {r['origen']} → {r['destino']} --{r['tipo']}-->")
        print(f'  Cita: "{r.get("cita_textual", "")}"')
        print(f"  Progreso: {_barra_progreso(ya_hechos_rels, len(relaciones_nuevas))}")
        if r.get("fuente"):
            print(f"  Fuente: {r['fuente']}")
        resp = pedir_opcion("  ¿Aprobar? (s/n): ", validas={"s", "n"}, alias={"si": "s", "sí": "s"})
        if resp == "s":
            conn.execute(
                "INSERT INTO relaciones (origen_id, destino_id, tipo, peso, fuente) VALUES (?, ?, ?, 1.0, ?)",
                (origen, destino, r["tipo"], r.get("fuente")),
            )
            conn.commit()
            print("  ✓ Insertada")
        else:
            print("  ✗ Descartada")
        estado["relaciones_revisadas"].append(clave)
        _guardar_estado_revision(estado)
        ya_hechos_rels += 1

    conn.close()

    total_nodos = len(candidatos.get("nodos_nuevos", []))
    total_rels = len(candidatos.get("relaciones_nuevas", []))
    if len(estado["nodos_revisados"]) >= total_nodos and len(estado["relaciones_revisadas"]) >= total_rels:
        print("\n◈ Revisión completa. Archivando candidatos procesados...")
        archivo = BASE_DIR / f"candidatos_procesados_{__import__('datetime').datetime.now():%Y%m%d_%H%M%S}.json"
        CANDIDATOS_PATH.rename(archivo)
        REVISION_ESTADO_PATH.unlink(missing_ok=True)
        print(f"  Movido a {archivo.name}")
    print("\n◈ Corre exportar desde el menú.")


# ═══════════════════════════════════════════════════════════════════════════
# 2. FUSIONAR DUPLICADOS (manual, uno por uno)
# ═══════════════════════════════════════════════════════════════════════════

def herramienta_fusionar_duplicados():
    """Fusiona nodos duplicados uno por uno, con tu criterio para decidir cuál se queda."""
    conn = sqlite3.connect(DB_PATH)
    filas = conn.execute("SELECT id, tipo, nombre FROM nodos ORDER BY tipo, id").fetchall()
    grados = cargar_grados(conn)
    por_tipo = defaultdict(list)
    for id_, tipo, nombre in filas:
        por_tipo[tipo].append((id_, nombre))

    grupos = []
    vistos = set()
    for tipo, items in por_tipo.items():
        for i, (id_a, nombre_a) in enumerate(items):
            if id_a in vistos:
                continue
            for id_b, nombre_b in items[i + 1:]:
                if id_b in vistos:
                    continue
                if similitud(nombre_a, nombre_b) >= UMBRAL_SIMILITUD:
                    grupos.append({"a": (id_a, nombre_a, grados.get(id_a, 0)), "b": (id_b, nombre_b, grados.get(id_b, 0))})
                    vistos.add(id_b)

    print("═" * 60)
    print(f"FUSIÓN DE DUPLICADOS — {len(grupos)} grupo(s) sospechoso(s)")
    print("═" * 60)

    for i, g in enumerate(grupos, 1):
        id_a, nombre_a, grado_a = g["a"]
        id_b, nombre_b, grado_b = g["b"]
        print(f"\n[{i}/{len(grupos)}]")
        print(f"  A) id={id_a}  '{nombre_a}'  ({grado_a} relaciones)")
        print(f"  B) id={id_b}  '{nombre_b}'  ({grado_b} relaciones)")
        resp = input("  ¿Fusionar? (a/b/n): ").strip().lower()
        if resp == "a":
            fusionar_nodos(conn, id_a, id_b)
            print(f"  ✓ '{nombre_b}' → '{nombre_a}'")
        elif resp == "b":
            fusionar_nodos(conn, id_b, id_a)
            print(f"  ✓ '{nombre_a}' → '{nombre_b}'")
        else:
            print("  → Saltado")
    conn.close()


# ═══════════════════════════════════════════════════════════════════════════
# 3. FUSIONAR DUPLICADOS AUTOMÁTICO
# ═══════════════════════════════════════════════════════════════════════════

def herramienta_fusionar_auto():
    """Fusión automática: si un nodo tiene 0 relaciones y el otro tiene más, se fusiona solo."""
    conn = sqlite3.connect(DB_PATH)
    filas = conn.execute("SELECT id, tipo, nombre FROM nodos ORDER BY tipo, id").fetchall()
    grados = cargar_grados(conn)
    por_tipo = defaultdict(list)
    for id_, tipo, nombre in filas:
        por_tipo[tipo].append((id_, nombre))

    grupos = []
    vistos = set()
    for tipo, items in por_tipo.items():
        for i, (id_a, nombre_a) in enumerate(items):
            if id_a in vistos:
                continue
            for id_b, nombre_b in items[i + 1:]:
                if id_b in vistos:
                    continue
                if similitud(nombre_a, nombre_b) >= UMBRAL_SIMILITUD:
                    grupos.append({"a": (id_a, nombre_a, grados.get(id_a, 0)), "b": (id_b, nombre_b, grados.get(id_b, 0))})
                    vistos.add(id_b)

    print("═" * 60)
    print(f"FUSIÓN AUTOMÁTICA — {len(grupos)} grupo(s)")
    print("═" * 60)

    fusionados = 0
    saltados = 0
    for i, g in enumerate(grupos, 1):
        id_a, nombre_a, grado_a = g["a"]
        id_b, nombre_b, grado_b = g["b"]
        if grado_a == 0 and grado_b > 0:
            fusionar_nodos(conn, id_b, id_a)
            print(f"[{i}] ✓ '{nombre_a}' → '{nombre_b}'")
            fusionados += 1
        elif grado_b == 0 and grado_a > 0:
            fusionar_nodos(conn, id_a, id_b)
            print(f"[{i}] ✓ '{nombre_b}' → '{nombre_a}'")
            fusionados += 1
        else:
            print(f"[{i}] → Saltado: ambos con relaciones")
            saltados += 1
    conn.close()
    print(f"\nRESUMEN: {fusionados} fusionados | {saltados} saltados")


# ═══════════════════════════════════════════════════════════════════════════
# 4. LIMPIEZA ASISTIDA (manual, uno por uno)
# ═══════════════════════════════════════════════════════════════════════════

def _cargar_estado_limpieza():
    if LIMPIEZA_ESTADO_PATH.exists():
        return json.loads(LIMPIEZA_ESTADO_PATH.read_text(encoding="utf-8"))
    return {"revisados": {}}

def _guardar_estado_limpieza(estado):
    LIMPIEZA_ESTADO_PATH.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")

def herramienta_limpieza_asistida():
    """Detecta ruido médico/biológico y nodos aislados, te los presenta uno por uno para decidir."""
    conn = sqlite3.connect(DB_PATH)
    estado = _cargar_estado_limpieza()
    filas = conn.execute("SELECT id, tipo, nombre, descripcion FROM nodos ORDER BY id").fetchall()
    grados = cargar_grados(conn)

    candidatos = []
    for id_, tipo, nombre, desc in filas:
        desc = desc or ""
        razon = None
        if PATRONES_RUIDO.search(nombre) or PATRONES_RUIDO.search(desc):
            razon = "término médico/biológico detectado"
        elif grados.get(id_, 0) == 1 and len(desc) < 60:
            razon = "solo 1 relación y descripción muy corta"
        if razon:
            candidatos.append({"id": id_, "tipo": tipo, "nombre": nombre, "descripcion": desc, "razon": razon, "grado": grados.get(id_, 0)})

    pendientes = [c for c in candidatos if str(c["id"]) not in estado["revisados"]]
    print("═" * 60)
    print(f"LIMPIEZA ASISTIDA — {len(candidatos)} candidatos, {len(pendientes)} pendientes")
    print("═" * 60)

    if not pendientes:
        print("\n✓ No hay más candidatos pendientes.")
        conn.close()
        return

    for i, c in enumerate(pendientes, 1):
        print(f"\n[{i}/{len(pendientes)}] [{c['tipo']}] {c['nombre']} (id={c['id']}, grado={c['grado']})")
        print(f"  Descripción: {c['descripcion']}")
        print(f"  Razón: {c['razon']}")

        rels = conn.execute("""
            SELECT r.tipo, n2.nombre, 's' FROM relaciones r JOIN nodos n2 ON r.destino_id = n2.id WHERE r.origen_id = ?
            UNION ALL
            SELECT r.tipo, n1.nombre, 'e' FROM relaciones r JOIN nodos n1 ON r.origen_id = n1.id WHERE r.destino_id = ?
        """, (c["id"], c["id"])).fetchall()
        if rels:
            print("  Relaciones:")
            for tipo, otro, d in rels:
                print(f"    {'→' if d == 's' else '←'} {tipo} {'→' if d == 's' else '←'} {otro}")
        else:
            print("  (sin relaciones)")

        resp = pedir_opcion("  ¿Mantener / Reclasificar / Eliminar / Saltar? (m/r/e/s): ", validas={"m", "r", "e", "s"})
        if resp == "m":
            estado["revisados"][str(c["id"])] = {"decision": "mantenido"}
            print("  ✓ Mantenido")
        elif resp == "r":
            nuevo_tipo = pedir_opcion(f"  Nuevo tipo ({c['tipo']}) [{'/'.join(sorted(TIPOS_VALIDOS_NODO))}]: ", validas=TIPOS_VALIDOS_NODO)
            conn.execute("UPDATE nodos SET tipo = ? WHERE id = ?", (nuevo_tipo, c["id"]))
            conn.commit()
            estado["revisados"][str(c["id"])] = {"decision": "reclasificado", "nuevo_tipo": nuevo_tipo}
            print(f"  ✓ Reclasificado a '{nuevo_tipo}'")
        elif resp == "e":
            if pedir_opcion(f"  Confirmar eliminación de '{c['nombre']}' y sus {len(rels)} relación(es)? (s/n): ", validas={"s", "n"}) == "s":
                eliminar_nodo_cascada(conn, c["id"])
                estado["revisados"][str(c["id"])] = {"decision": "eliminado"}
                print("  ✓ Eliminado")
            else:
                print("  Cancelado")
                continue
        else:
            print("  → Saltado")
            continue
        _guardar_estado_limpieza(estado)

    conn.close()
    mantenidos = sum(1 for v in estado["revisados"].values() if v["decision"] == "mantenido")
    eliminados = sum(1 for v in estado["revisados"].values() if v["decision"] == "eliminado")
    print(f"\nRESUMEN: {mantenidos} mantenidos | {eliminados} eliminados")


# ═══════════════════════════════════════════════════════════════════════════
# 5. LIMPIEZA AUTOMÁTICA DE RUIDO (sin preguntar)
# ═══════════════════════════════════════════════════════════════════════════

def herramienta_limpiar_auto():
    """Elimina nodos con patrón médico/biológico + 1 relación y descripción corta, sin preguntar."""
    conn = sqlite3.connect(DB_PATH)
    filas = conn.execute("SELECT id, tipo, nombre, descripcion FROM nodos ORDER BY id").fetchall()
    grados = cargar_grados(conn)

    candidatos = []
    for id_, tipo, nombre, desc in filas:
        desc = desc or ""
        razon = None
        if PATRONES_RUIDO.search(nombre) or PATRONES_RUIDO.search(desc):
            razon = "término médico/biológico"
        elif grados.get(id_, 0) == 1 and len(desc) < 60:
            razon = "1 relación + desc corta"
        if razon:
            candidatos.append({"id": id_, "tipo": tipo, "nombre": nombre, "razon": razon, "grado": grados.get(id_, 0)})

    print("═" * 60)
    print(f"LIMPIEZA AUTOMÁTICA — {len(candidatos)} candidatos")
    print("═" * 60)
    for c in candidatos:
        print(f"  [{c['tipo']}] {c['nombre']} (id={c['id']}, grado={c['grado']}): {c['razon']}")
        eliminar_nodo_cascada(conn, c["id"])
    conn.close()
    print(f"\n✓ {len(candidatos)} nodos eliminados")


# ═══════════════════════════════════════════════════════════════════════════
# 6. LIMPIEZA AUTOMÁTICA SEGURA (fusión + eliminación de ruido)
# ═══════════════════════════════════════════════════════════════════════════

def herramienta_limpieza_automatica(aplicar=False):
    """Fusión segura de duplicados + eliminación de ruido biomédico. Sin preguntar."""
    conn = sqlite3.connect(DB_PATH)
    filas = conn.execute("SELECT id, tipo, nombre, descripcion FROM nodos ORDER BY tipo, id").fetchall()
    grados = cargar_grados(conn)

    # Fusiones: nombre corto CONTENIDO en nombre largo, mismo tipo, el corto con 0 relaciones
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
                if frozenset({id_a, id_b}) in EXCLUSIONES_FUSION:
                    continue
                if not (norm_a in norm_b or norm_b in norm_a):
                    continue
                if similitud(nombre_a, nombre_b) < 0.5:
                    continue
                ga, gb = grados.get(id_a, 0), grados.get(id_b, 0)
                if len(norm_a) < len(norm_b) and ga == 0:
                    fusiones.append({"mantener": (id_b, nombre_b), "eliminar": (id_a, nombre_a)})
                    ya_usados.add(id_a)
                elif len(norm_b) < len(norm_a) and gb == 0:
                    fusiones.append({"mantener": (id_a, nombre_a), "eliminar": (id_b, nombre_b)})
                    ya_usados.add(id_b)

    # Ruido: 0 relaciones + patrón biomédico
    ruido = []
    for id_, tipo, nombre, desc in filas:
        desc = desc or ""
        if grados.get(id_, 0) == 0 and (PATRONES_RUIDO.search(nombre) or PATRONES_RUIDO.search(desc)):
            ruido.append((id_, tipo, nombre))

    ids_resueltos = {f["eliminar"][0] for f in fusiones} | {r[0] for r in ruido}
    ambiguos = [(id_, tipo, nombre) for id_, tipo, nombre, _ in filas if grados.get(id_, 0) == 0 and id_ not in ids_resueltos]

    print("═" * 60)
    print(f"LIMPIEZA AUTOMÁTICA {'— APLICANDO' if aplicar else '— DRY RUN'}")
    print("═" * 60)

    print(f"\n◈ FUSIONES SEGURAS: {len(fusiones)}")
    for f in fusiones:
        print(f"    '{f['eliminar'][1]}' → '{f['mantener'][1]}'")
        if aplicar:
            fusionar_nodos(conn, f["mantener"][0], f["eliminar"][0])

    print(f"\n◈ ELIMINACIONES (ruido, 0 rel): {len(ruido)}")
    for id_, tipo, nombre in ruido:
        print(f"    [{tipo}] '{nombre}'")
        if aplicar:
            eliminar_nodo_cascada(conn, id_)

    if aplicar:
        conn.commit()

    print(f"\n◈ AMBIGUOS (necesitan tu criterio): {len(ambiguos)}")
    for tipo, items in defaultdict(list, {t: [(i, n) for i, t2, n in ambiguos if t2 == t] for t in set(t2 for _, t2, _ in ambiguos)}).items():
        print(f"\n  [{tipo}]")
        for id_, nombre in items:
            print(f"    id={id_:4d}  {nombre}")

    conn.close()
    if not aplicar:
        print("\nPara aplicar de verdad: corré la opción 6 de nuevo y elegí 'aplicar'.")


# ═══════════════════════════════════════════════════════════════════════════
# 7. CONEXIÓN AUTOMÁTICA DE RELACIONES
# ═══════════════════════════════════════════════════════════════════════════

def herramienta_conectar_automatico(umbral=None, dry_run=False):
    """Conecta relaciones pendientes: resuelve ids por fuzzy match e inserta nodos huérfanos."""
    umbral = umbral if umbral is not None else UMBRAL_FUZZY
    if not CANDIDATOS_PATH.exists():
        print("✗ No hay candidatos_pendientes.json.")
        return

    candidatos = json.loads(CANDIDATOS_PATH.read_text(encoding="utf-8"))
    conn = sqlite3.connect(DB_PATH)
    filas = conn.execute("SELECT id, tipo, nombre FROM nodos").fetchall()
    catalogo = {nombre: (id_, tipo) for id_, tipo, nombre in filas}

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
                (n["tipo"], n["nombre"], n.get("descripcion", n.get("resumen", "")), json.dumps({"id_gemini": n["id"], "insertado_por": "conexion_automatica"})),
            )
            id_real = cur.lastrowid
            conn.commit()
            mapa_id[n["id"]] = id_real
            catalogo[n["nombre"]] = (id_real, n["tipo"])
            log_nodos.append(n["nombre"])

    print(f"\nNodos insertados: {len(log_nodos)}")

    insertadas = 0
    no_resolubles = 0
    for r in candidatos.get("relaciones_nuevas", []):
        nombre_o = next((n["nombre"] for n in candidatos.get("nodos_nuevos", []) if n["id"] == r["origen"]), None)
        nombre_d = next((n["nombre"] for n in candidatos.get("nodos_nuevos", []) if n["id"] == r["destino"]), None)

        origen = mapa_id.get(r["origen"])
        if origen is None and nombre_o:
            sims = get_close_matches(nombre_o, list(catalogo.keys()), n=1, cutoff=umbral)
            if sims:
                origen = catalogo[sims[0]][0]

        destino = mapa_id.get(r["destino"])
        if destino is None and nombre_d:
            sims = get_close_matches(nombre_d, list(catalogo.keys()), n=1, cutoff=umbral)
            if sims:
                destino = catalogo[sims[0]][0]

        if origen is None or destino is None or isinstance(origen, str) or isinstance(destino, str):
            no_resolubles += 1
            continue

        if not dry_run and not relacion_ya_existe(conn, origen, destino, r["tipo"]):
            conn.execute(
                "INSERT INTO relaciones (origen_id, destino_id, tipo, peso, fuente) VALUES (?, ?, ?, 1.0, ?)",
                (origen, destino, r["tipo"], r.get("fuente")),
            )
            conn.commit()
        insertadas += 1

    conn.close()
    print(f"\nRelaciones insertadas: {insertadas} | No resolubles: {no_resolubles}")


# ═══════════════════════════════════════════════════════════════════════════
# 8. RECUPERAR RELACIONES PERDIDAS
# ═══════════════════════════════════════════════════════════════════════════

def herramienta_recuperar_relaciones():
    """Reprocesa relaciones omitidas por bugs pasados de resolución de ids."""
    archivos = sorted(BASE_DIR.glob("candidatos_procesados_*.json"))
    pendiente = BASE_DIR / "candidatos_pendientes.json"
    if pendiente.exists():
        archivos.append(pendiente)
    if not archivos:
        print("✗ No hay archivos de candidatos.")
        return

    conn = sqlite3.connect(DB_PATH)
    ids_validos = {row[0] for row in conn.execute("SELECT id FROM nodos")}

    mapa_snake = {}
    for id_real, meta in conn.execute("SELECT id, metadatos FROM nodos WHERE metadatos IS NOT NULL"):
        try:
            m = json.loads(meta)
            if "id_gemini" in m:
                mapa_snake[m["id_gemini"]] = id_real
        except (json.JSONDecodeError, TypeError):
            pass

    estado = set()
    if RECUPERACION_ESTADO_PATH.exists():
        estado = set(json.loads(RECUPERACION_ESTADO_PATH.read_text(encoding="utf-8")))

    insertadas = 0
    no_resolubles = 0
    for archivo in archivos:
        datos = json.loads(archivo.read_text(encoding="utf-8"))
        for r in datos.get("relaciones_nuevas", []):
            clave = f"{r['origen']}->{r['destino']}::{r['tipo']}::{r.get('cita_textual', '')[:60]}"
            if clave in estado:
                continue
            origen = r["origen"]
            destino = r["destino"]
            if isinstance(origen, int) or (isinstance(origen, str) and origen.strip().isdigit()):
                origen = int(origen) if isinstance(origen, int) else int(origen.strip())
                origen = origen if origen in ids_validos else None
            else:
                origen = mapa_snake.get(origen)
            if isinstance(destino, int) or (isinstance(destino, str) and destino.strip().isdigit()):
                destino = int(destino) if isinstance(destino, int) else int(destino.strip())
                destino = destino if destino in ids_validos else None
            else:
                destino = mapa_snake.get(destino)

            if origen is None or destino is None:
                no_resolubles += 1
                estado.add(clave)
                continue

            if not relacion_ya_existe(conn, origen, destino, r["tipo"]):
                conn.execute(
                    "INSERT INTO relaciones (origen_id, destino_id, tipo, peso, fuente) VALUES (?, ?, ?, 1.0, ?)",
                    (origen, destino, r["tipo"], r.get("fuente")),
                )
                conn.commit()
                insertadas += 1
            estado.add(clave)
            RECUPERACION_ESTADO_PATH.write_text(json.dumps(sorted(estado), ensure_ascii=False, indent=2), encoding="utf-8")

    conn.close()
    print(f"Recuperadas: {insertadas} | No resolubles: {no_resolubles}")


# ═══════════════════════════════════════════════════════════════════════════
# 9. REFORZAR ESQUEMA DE LA DB
# ═══════════════════════════════════════════════════════════════════════════

def herramienta_reforzar_esquema():
    """Blinda la DB con índice único anti-duplicados + índices de rendimiento."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_relacion_unica ON relaciones (origen_id, destino_id, tipo)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_relaciones_origen ON relaciones (origen_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_relaciones_destino ON relaciones (destino_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_nodos_tipo ON nodos (tipo)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_nodos_nombre ON nodos (nombre)")
    conn.commit()
    conn.close()
    print("✓ Esquema reforzado: índice único anti-duplicados + índices de rendimiento.")


# ═══════════════════════════════════════════════════════════════════════════
# 10. AUDITORÍA COMPLETA
# ═══════════════════════════════════════════════════════════════════════════

def herramienta_auditoria():
    """Diagnóstico completo del grafo: integridad, duplicados, aislados, cobertura, pérdida de relaciones."""
    conn = sqlite3.connect(DB_PATH)

    # Progreso pendiente
    print("═" * 60)
    print("PROGRESO DE REVISIÓN PENDIENTE")
    print("═" * 60)
    if not CANDIDATOS_PATH.exists():
        print("  No hay candidatos pendientes.")
    else:
        candidatos = json.loads(CANDIDATOS_PATH.read_text(encoding="utf-8"))
        estado = {"nodos_revisados": {}, "relaciones_revisadas": []}
        if REVISION_ESTADO_PATH.exists():
            estado = json.loads(REVISION_ESTADO_PATH.read_text(encoding="utf-8"))
        total_n = len(candidatos.get("nodos_nuevos", []))
        total_r = len(candidatos.get("relaciones_nuevas", []))
        print(f"  Nodos: {len(estado['nodos_revisados'])}/{total_n} | Relaciones: {len(estado['relaciones_revisadas'])}/{total_r}")

    # Estadísticas
    print("\n" + "═" * 60)
    print("ESTADÍSTICAS")
    print("═" * 60)
    filas = conn.execute("SELECT tipo, COUNT(*) FROM nodos GROUP BY tipo").fetchall()
    total = sum(c for _, c in filas)
    for tipo, c in sorted(filas):
        print(f"  {tipo:12s} {c}")
    print(f"  {'TOTAL':12s} {total}")
    total_rel = conn.execute("SELECT COUNT(*) FROM relaciones").fetchone()[0]
    print(f"\n  Relaciones: {total_rel}")
    print("\n  Top tipos de relación:")
    for tipo, c in conn.execute("SELECT tipo, COUNT(*) FROM relaciones GROUP BY tipo ORDER BY COUNT(*) DESC LIMIT 10").fetchall():
        print(f"    {tipo:30s} {c}")
    if total > 0:
        print(f"\n  Grado promedio: {(total_rel * 2) / total:.2f}")

    # Integridad referencial
    print("\n" + "═" * 60)
    print("INTEGRIDAD REFERENCIAL")
    print("═" * 60)
    ids_validos = {row[0] for row in conn.execute("SELECT id FROM nodos")}
    rotas = 0
    for rel_id, origen, destino, tipo in conn.execute("SELECT id, origen_id, destino_id, tipo FROM relaciones"):
        if origen not in ids_validos or destino not in ids_validos:
            rotas += 1
            print(f"  ⚠ Relación id={rel_id} ({tipo}) rota: {origen}→{destino}")
    if rotas == 0:
        print("  ✓ Todas las relaciones apuntan a nodos existentes")

    # Nodos aislados
    print("\n" + "═" * 60)
    print("NODOS AISLADOS")
    print("═" * 60)
    aislados = conn.execute("""
        SELECT id, tipo, nombre FROM nodos
        WHERE id NOT IN (SELECT origen_id FROM relaciones)
          AND id NOT IN (SELECT destino_id FROM relaciones)
        ORDER BY tipo, nombre
    """).fetchall()
    if aislados:
        print(f"  {len(aislados)} nodo(s) aislado(s)")
        por_tipo = defaultdict(list)
        for id_, tipo, nombre in aislados:
            por_tipo[tipo].append((id_, nombre))
        for tipo, items in por_tipo.items():
            print(f"\n  [{tipo}]")
            for id_, nombre in items:
                print(f"    id={id_:4d}  {nombre}")
    else:
        print("  ✓ Todo conectado")

    # Cobertura de libros
    print("\n" + "═" * 60)
    print("COBERTURA DE PÁGINAS POR LIBRO")
    print("═" * 60)
    por_libro = defaultdict(set)
    patron = re.compile(r"^(.*), p\.(\d+)-(\d+)$")
    for (fuente,) in conn.execute("SELECT fuente FROM relaciones WHERE fuente IS NOT NULL").fetchall():
        m = patron.match(fuente or "")
        if m:
            por_libro[m.group(1)].update(range(int(m.group(2)), int(m.group(3)) + 1))
    if not por_libro:
        print("  (sin fuentes registradas)")
    for libro, paginas in por_libro.items():
        pi, pf = min(paginas), max(paginas)
        faltantes = sorted(set(range(pi, pf + 1)) - paginas)
        print(f"\n  {libro}: {len(paginas)} páginas (rango {pi}-{pf})")
        if faltantes:
            print(f"    ⚠ Faltantes: {faltantes[:30]}")
        else:
            print("    ✓ Cubierto")

    # Duplicados
    print("\n" + "═" * 60)
    print("DUPLICADOS SOSPECHOSOS")
    print("═" * 60)
    filas = conn.execute("SELECT id, tipo, nombre FROM nodos ORDER BY tipo, id").fetchall()
    por_tipo = defaultdict(list)
    for id_, tipo, nombre in filas:
        por_tipo[tipo].append((id_, nombre))
    encontrados = 0
    for tipo, items in por_tipo.items():
        for i, (id_a, nombre_a) in enumerate(items):
            for id_b, nombre_b in items[i + 1:]:
                s = similitud(nombre_a, nombre_b)
                if s >= UMBRAL_SIMILITUD:
                    print(f"  ⚠ [{tipo}] '{nombre_a}' ↔ '{nombre_b}' ({s:.2f})")
                    encontrados += 1
    if encontrados == 0:
        print("  ✓ Sin duplicados obvios")

    conn.close()


# ═══════════════════════════════════════════════════════════════════════════
# 11. MANTENIMIENTO AUTOMÁTICO COMPLETO
# ═══════════════════════════════════════════════════════════════════════════

def herramienta_mantenimiento():
    """Combo completo post-libro: fusión + recuperación + export + auditoría."""
    print("\n◈ 1/4 — Fusionando duplicados obvios...")
    herramienta_limpieza_automatica(aplicar=True)

    print("\n◈ 2/4 — Recuperando relaciones...")
    herramienta_recuperar_relaciones()

    print("\n◈ 3/4 — Exportando...")
    subprocess.run([sys.executable, str(BASE_DIR.parent / "scripts" / "export_json.py")])

    print("\n◈ 4/4 — Auditoría...")
    herramienta_auditoria()


# ═══════════════════════════════════════════════════════════════════════════
# 12. EXPORTAR
# ═══════════════════════════════════════════════════════════════════════════

def herramienta_exportar():
    """Exporta la DB a datos.json para que el navegador muestre el grafo."""
    subprocess.run([sys.executable, str(BASE_DIR.parent / "scripts" / "export_json.py")])


# ═══════════════════════════════════════════════════════════════════════════
# 13. LIMPIAR ARCHIVOS TEMPORALES
# ═══════════════════════════════════════════════════════════════════════════

def herramienta_limpiar():
    """Borra archivos intermedios ya procesados (candidatos archivados, logs verificados)."""
    bloqueos = []
    if CANDIDATOS_PATH.exists():
        bloqueos.append("candidatos_pendientes.json sin archivar — corre revisar.py primero")
    if REVISION_ESTADO_PATH.exists():
        estado = json.loads(REVISION_ESTADO_PATH.read_text(encoding="utf-8"))
        if estado.get("nodos_revisados") or estado.get("relaciones_revisadas"):
            bloqueos.append("revision_estado.json con progreso a medias")

    if bloqueos:
        print("⚠ Hay cosas pendientes:")
        for b in bloqueos:
            print(f"  - {b}")
        resp = pedir_opcion(
            "  ¿Forzar limpieza de todos modos? (arriesgado) (s/n): ",
            validas={"s", "n"}, alias={"si": "s", "sí": "s"},
        )
        if resp != "s":
            print("Cancelado.")
            return
        print("  ⚠ Forzando pese a advertencias...")

    candidatos = list(BASE_DIR.glob("candidatos_procesados_*.json"))
    logs_ok = []
    for log_path in BASE_DIR.glob("extraccion_log_*.json"):
        log = json.loads(log_path.read_text(encoding="utf-8"))
        if not log.get("chunks_con_error"):
            logs_ok.append(log_path)

    if not candidatos and not logs_ok:
        print("✓ Pipeline ya está limpio.")
        return

    print(f"Se van a borrar {len(candidatos)} candidatos archivados + {len(logs_ok)} logs verificados:")
    for f in candidatos + logs_ok:
        print(f"  - {f.name}")
    if pedir_opcion("¿Confirmas? (s/n): ", validas={"s", "n"}, alias={"si": "s", "sí": "s"}) == "s":
        for f in candidatos + logs_ok:
            f.unlink()
        print(f"✓ {len(candidatos) + len(logs_ok)} archivos eliminados")
    else:
        print("Cancelado.")


# ═══════════════════════════════════════════════════════════════════════════
# WRAPPERS INTERACTIVOS (devuelven parámetros que antes iban por CLI)
# ═══════════════════════════════════════════════════════════════════════════

def herramienta_limpieza_automatica_menu():
    """Wrapper que pregunta si aplicar de verdad o solo simular."""
    resp = pedir_opcion(
        "  ¿Simular (dry-run, no cambia nada) o aplicar de verdad? (simular/aplicar): ",
        validas={"simular", "aplicar"}, alias={"s": "simular", "a": "aplicar"},
    )
    herramienta_limpieza_automatica(aplicar=(resp == "aplicar"))

def herramienta_conectar_automatico_menu():
    """Wrapper que pregunta umbral y simular/aplicar."""
    umbral_str = input("  Umbral de similitud fuzzy [0.80]: ").strip()
    umbral = float(umbral_str) if umbral_str else 0.80
    resp = pedir_opcion(
        "  ¿Simular o aplicar de verdad? (simular/aplicar): ",
        validas={"simular", "aplicar"}, alias={"s": "simular", "a": "aplicar"},
    )
    herramienta_conectar_automatico(umbral=umbral, dry_run=(resp == "simular"))


# ═══════════════════════════════════════════════════════════════════════════
# MENÚ PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════

OPCIONES = {
    "1":  ("Revisar candidatos pendientes (manual, uno por uno)", herramienta_revisar),
    "2":  ("Fusionar duplicados (requiere tu criterio)", herramienta_fusionar_duplicados),
    "3":  ("Fusionar duplicados automático (0 rel → se fusionan solos)", herramienta_fusionar_auto),
    "4":  ("Limpieza asistida de nodos aislados/ruido", herramienta_limpieza_asistida),
    "5":  ("Limpieza automática de ruido (sin preguntar)", herramienta_limpiar_auto),
    "6":  ("Limpieza automática segura (fusión + eliminación)", herramienta_limpieza_automatica_menu),
    "7":  ("Conexión automática de relaciones pendientes", herramienta_conectar_automatico_menu),
    "8":  ("Recuperar relaciones perdidas", herramienta_recuperar_relaciones),
    "9":  ("Reforzar esquema de la DB", herramienta_reforzar_esquema),
    "10": ("Auditoría completa (diagnóstico)", herramienta_auditoria),
    "11": ("Mantenimiento automático completo (post-libro)", herramienta_mantenimiento),
    "12": ("Exportar a datos.json", herramienta_exportar),
    "13": ("Limpiar archivos temporales", herramienta_limpiar),
    "0":  ("Salir", None),
}

EXTRAE = {
    "e1": "Extraer un libro nuevo (llama extractor.py)",
    "e2": "Modo manual — generar prompt para chat web / pegar respuesta",
    "e3": "Verificar cobertura de un libro (llama verificar_extraccion.py)",
}


def extraer():
    ruta = input("Ruta del PDF (ej: ../libros/nombre.pdf): ").strip()
    if not ruta:
        print("Cancelado.")
        return
    subprocess.run([sys.executable, str(BASE_DIR / "extractor.py"), ruta])

def modo_manual_menu():
    ruta = input("Ruta del PDF (ej: ../libros/nombre.pdf): ").strip()
    if not ruta:
        print("Cancelado.")
        return
    accion = pedir_opcion(
        "  ¿Generar prompt (para pegar en chat) o pegar respuesta del chat? (generar/pegar): ",
        validas={"generar", "pegar"}, alias={"g": "generar", "p": "pegar"},
    )
    subprocess.run([sys.executable, str(BASE_DIR / "modo_manual.py"), ruta, accion])

def verificar():
    stem = input("Nombre del PDF SIN extensión (ej: boas-f-1911...): ").strip()
    if not stem:
        print("Cancelado.")
        return
    subprocess.run([sys.executable, str(BASE_DIR / "verificar_extraccion.py"), stem])


def main():
    while True:
        print("\n" + "═" * 60)
        print("  CEREBRO ANTROPOLÓGICO — CENTRO DE COMANDOS UNIFICADO")
        print("═" * 60)
        print("  ── Extracción ──")
        for clave, descripcion in EXTRAE.items():
            print(f"  {clave}) {descripcion}")
        print("  ── Herramientas del grafo ──")
        for clave, (descripcion, _) in OPCIONES.items():
            print(f"  {clave:>2}) {descripcion}")

        eleccion = input("\n¿Qué querés hacer?: ").strip().lower()

        if eleccion == "e1":
            extraer()
        elif eleccion == "e2":
            modo_manual_menu()
        elif eleccion == "e3":
            verificar()
        elif eleccion in OPCIONES:
            descripcion, accion = OPCIONES[eleccion]
            if accion is None:
                print("Hasta luego.")
                break
            accion()
        else:
            print("⚠ Opción no válida.")


if __name__ == "__main__":
    main()
