"""
CEREBRO ANTROPOLÓGICO — Centro de Comandos Unificado
=====================================================
Todas las herramientas del pipeline en un solo archivo, ordenadas según el
flujo real de uso después de extraer un libro. Escribí 'flujo' en el menú
para ver el orden paso a paso, o '?N' (ej: '?5') para ver qué hace y qué
parámetros acepta una herramienta puntual sin ejecutarla.

Uso: python cerebro.py
"""
import inspect
import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path
from difflib import SequenceMatcher, get_close_matches
from collections import defaultdict

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

# Pares de ids que el algoritmo de similitud detecta como "posibles duplicados"
# pero que ya confirmaste manualmente que son entidades distintas. Se excluyen
# de TODAS las herramientas de fusión (manual, automática y segura).
EXCLUSIONES_FUSION_NOMBRES_NOMBRES = {
    frozenset({"América", "Norteamérica"}),
    frozenset({"América", "América Central"}),
    frozenset({"Australianos", "Aborígenes australianos"}),
    frozenset({"Japoneses", "Japoneses de Hawái"}),
}


def _es_exclusion_fusion(nombre_a, nombre_b):
    return frozenset({nombre_a, nombre_b}) in EXCLUSIONES_FUSION_NOMBRES_NOMBRES

TIPOS_VALIDOS_NODO = {"autor", "obra", "concepto", "escuela", "cultura", "debate", "poblacion", "corriente"}

TIPOS_VALIDOS_RELACION = {
    "influenciado_por", "critica_a", "desarrolla_concepto", "pertenece_a",
    "estudia_a", "contemporaneo_de", "precursor_de", "parte_del_debate", "redefine_a",
}

TIPOS_ALIAS_RELACION = {
    "influyó_en": "influenciado_por",
    "influye_en": "influenciado_por",
    "influencio_a": "influenciado_por",
    "autor_de": "pertenece_a",
    "es_autor_de": "pertenece_a",
    "estudio": "estudia_a",
    "escribe_estudio_preliminar_para": "estudia_a",
    "describe_a": "estudia_a",
    "ejemplifica_con": "desarrolla_concepto",
    "ejemplo_de": "desarrolla_concepto",
    "ejemplo_en": "desarrolla_concepto",
    "ejemplificado_por": "desarrolla_concepto",
    "practica_concepto": "desarrolla_concepto",
    "promueve_concepto": "desarrolla_concepto",
    "incorpora_concepto": "desarrolla_concepto",
    "discute_concepto": "desarrolla_concepto",
    "estudia_concepto": "desarrolla_concepto",
    "sostiene_teoria": "desarrolla_concepto",
    "defiende": "desarrolla_concepto",
    "defiende_superioridad_de": "critica_a",
    "refuta": "critica_a",
    "lucha_contra": "critica_a",
    "opuesto_a": "critica_a",
    "contrasta_con": "critica_a",
    "malinterpreta_a": "critica_a",
    "limita": "critica_a",
    "limita_expansion_a": "critica_a",
    "subestima_concepto": "critica_a",
    "manipula_concepto": "critica_a",
    "colabora_con": "contemporaneo_de",
    "colaboro_con": "contemporaneo_de",
    "es_mentor_de": "precursor_de",
    "mentor_de": "precursor_de",
    "es_discípulo_de": "influenciado_por",
    "clasifica_como_activo": "desarrolla_concepto",
    "clasifica_como_pasivo": "desarrolla_concepto",
    "presenta_rasgo": "desarrolla_concepto",
    "representado_por": "desarrolla_concepto",
    "relacionado_con": "contemporaneo_de",
    "contribuye_a": "desarrolla_concepto",
    "trata_de": "desarrolla_concepto",
    "es_fuente_sobre": "estudia_a",
    "cita_a": "estudia_a",
    "localizado_en": "pertenece_a",
    "ubica_en": "pertenece_a",
    "incluye_a": "pertenece_a",
    "realiza_trabajo_de_campo_en": "estudia_a",
    "migra_a": "pertenece_a",
    "prologa_obra": "pertenece_a",
    "otorga_primacia_a": "desarrolla_concepto",
    "venera_concepto": "desarrolla_concepto",
    "usa_enfoque": "desarrolla_concepto",
    "traduce_obra": "pertenece_a",
    "publicado_como_traduccion": "pertenece_a",
    "publica": "pertenece_a",
    "origen_de": "precursor_de",
    "facilito_por": "influenciado_por",
    "expandida_en": "pertenece_a",
    "evalua_contribucion_de": "estudia_a",
    "dirige_publicacion": "pertenece_a",
    "difundido_en": "pertenece_a",
    "descubierta_por": "desarrolla_concepto",
    "dedica_obra_a": "pertenece_a",
    "considera_indispensable": "desarrolla_concepto",
    "condiciona": "influenciado_por",
    "atribuye_origen_a": "precursor_de",
    "aplicado_a": "desarrolla_concepto",
    "es_respuesta_a": "critica_a",
    "es_tipo_de": "pertenece_a",
}


def normalizar_tipo_relacion(tipo: str) -> str:
    """Normaliza un tipo de relación: minúsculas, sin espacios extra,
    resuelto contra TIPOS_ALIAS_RELACION."""
    t = tipo.strip().lower().replace(" ", "_")
    if t in TIPOS_VALIDOS_RELACION:
        return t
    if t in TIPOS_ALIAS_RELACION:
        return TIPOS_ALIAS_RELACION[t]
    return t


def _conectar_db():
    conn = _conectar_db()
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ═══════════════════════════════════════════════════════════════════════════
# UTILIDADES COMPARTIDAS
# ═══════════════════════════════════════════════════════════════════════════

def similitud(a, b):
    """Similitud de texto entre 0 y 1 (SequenceMatcher), usada para detectar duplicados."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def normalizar(nombre):
    """Quita acentos-safe, puntuación y mayúsculas para comparar nombres de forma laxa."""
    return re.sub(r"[^\wáéíóúñ ]", "", nombre.lower()).strip()

def pedir_opcion(mensaje, validas, alias=None):
    """Pide una respuesta hasta que sea válida; nunca deja pasar algo ambiguo sin avisar."""
    alias = alias or {}
    while True:
        resp = input(mensaje).strip().lower()
        if resp in alias:
            resp = alias[resp]
        if resp in validas:
            return resp
        print(f"  ⚠ No entendí '{resp}'. Opciones: {', '.join(sorted(validas))}")

def eliminar_nodo_cascada(conn, id_):
    """Borra un nodo y todas sus relaciones (entrantes y salientes)."""
    conn.execute("DELETE FROM relaciones WHERE origen_id = ? OR destino_id = ?", (id_, id_))
    conn.execute("DELETE FROM nodos WHERE id = ?", (id_,))
    conn.commit()

def fusionar_nodos(conn, id_mantener, id_borrar):
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
    conn.execute("UPDATE nodos SET metadatos = ? WHERE id = ?", (json.dumps(meta_m, ensure_ascii=False), id_mantener))

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
    """True si ya existe una relación exacta con ese origen/destino/tipo."""
    return conn.execute(
        "SELECT 1 FROM relaciones WHERE origen_id = ? AND destino_id = ? AND tipo = ?",
        (origen, destino, tipo),
    ).fetchone() is not None

def cargar_grados(conn):
    """Devuelve {id_nodo: número de relaciones}, para detectar nodos aislados."""
    return dict(conn.execute("""
        SELECT id_nodo, COUNT(*) FROM (
            SELECT origen_id AS id_nodo FROM relaciones
            UNION ALL SELECT destino_id AS id_nodo FROM relaciones
        ) GROUP BY id_nodo
    """).fetchall())

def construir_mapa_resolucion(conn):
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


# ═══════════════════════════════════════════════════════════════════════════
# FASE 2 · REVISIÓN — 1. Revisar candidatos pendientes (manual)
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
    conn = _conectar_db()

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

        nombres_mismo_tipo = list(catalogo_por_tipo.get(n["tipo"], {}).keys())
        similares = get_close_matches(n["nombre"], nombres_mismo_tipo, n=3, cutoff=0.75)
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
                        (tipo_final, n["nombre"], n.get("descripcion", n.get("resumen", "")), json.dumps(metadatos, ensure_ascii=False)),
                    )
                except sqlite3.IntegrityError:
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

        if relacion_ya_existe(conn, origen, destino, normalizar_tipo_relacion(r["tipo"])):
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
                (origen, destino, normalizar_tipo_relacion(r["tipo"]), r.get("fuente")),
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
    print("\n◈ Siguiente paso sugerido: opción 3 (recuperar relaciones) y luego 4 (auditoría).")


# ═══════════════════════════════════════════════════════════════════════════
# FASE 2 · REVISIÓN — 2. Conectar automático de relaciones
# ═══════════════════════════════════════════════════════════════════════════

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
    Pensado para lotes grandes (300+ relaciones) donde revisar.py se
    sentiría interminable; lo que no logra resolver queda disponible para
    pasar por 'Recuperar relaciones perdidas' o por revisar.py más tarde.

    Parámetros:
      umbral (float, default 0.80): qué tan similar debe ser un nombre para
        aceptarse como el mismo nodo (0 a 1; más alto = más estricto).
      dry_run (bool, default False): si es True, solo simula y muestra un
        reporte, sin escribir nada en la base de datos.
    """
    umbral = umbral if umbral is not None else UMBRAL_FUZZY
    if not CANDIDATOS_PATH.exists():
        print("✗ No hay candidatos_pendientes.json.")
        return

    candidatos = json.loads(CANDIDATOS_PATH.read_text(encoding="utf-8"))
    conn = _conectar_db()
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
                (n["tipo"], n["nombre"], n.get("descripcion", n.get("resumen", "")), json.dumps({"id_gemini": n["id"], "insertado_por": "conexion_automatica"})),
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
            "INSERT INTO relaciones (origen_id, destino_id, tipo, peso, fuente) VALUES (?, ?, ?, 1.0, ?)",
            (origen, destino, normalizar_tipo_relacion(r["tipo"]), r.get("fuente")),
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
# FASE 2 · REVISIÓN — 3. Recuperar relaciones perdidas
# ═══════════════════════════════════════════════════════════════════════════

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

    conn = _conectar_db()
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
                    "INSERT INTO relaciones (origen_id, destino_id, tipo, peso, fuente) VALUES (?, ?, ?, 1.0, ?)",
                    (origen, destino, normalizar_tipo_relacion(r["tipo"]), r.get("fuente")),
                )
                conn.commit()
                insertadas += 1

            estado.add(clave)
            RECUPERACION_ESTADO_PATH.write_text(json.dumps(sorted(estado), ensure_ascii=False, indent=2), encoding="utf-8")

    conn.close()
    print(f"Recuperadas: {insertadas} | Ya existían: {ya_existian} | No resolubles: {no_resolubles}")


# ═══════════════════════════════════════════════════════════════════════════
# FASE 3 · DIAGNÓSTICO — 4. Auditoría completa
# ═══════════════════════════════════════════════════════════════════════════

def herramienta_auditoria():
    """
    Diagnóstico completo, no cambia nada: progreso de revisión pendiente,
    estadísticas por tipo de nodo y de relación, integridad referencial
    (relaciones apuntando a nodos inexistentes), nodos aislados agrupados
    por tipo, cobertura de páginas por libro (según el campo 'fuente' de
    las relaciones), y duplicados sospechosos por similitud de nombre
    dentro de cada tipo.
    """
    conn = _conectar_db()

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
                if _es_exclusion_fusion(nombre_a, nombre_b):
                    continue
                s = similitud(nombre_a, nombre_b)
                if s >= UMBRAL_SIMILITUD:
                    print(f"  ⚠ [{tipo}] '{nombre_a}' ↔ '{nombre_b}' ({s:.2f})")
                    encontrados += 1
    if encontrados == 0:
        print("  ✓ Sin duplicados obvios")

    conn.close()


# ═══════════════════════════════════════════════════════════════════════════
# FASE 4 · LIMPIEZA — 5. Limpieza automática segura
# ═══════════════════════════════════════════════════════════════════════════

def herramienta_limpieza_automatica(aplicar=False):
    """
    Fusión segura de duplicados + eliminación de ruido biomédico, sin
    preguntar. Fusiona un par solo cuando el nombre corto está literalmente
    CONTENIDO en el nombre largo (mismo tipo) y el corto tiene 0 relaciones
    (caso típico: 'Rieger' vs 'Conrad Rieger'). Elimina nodos con 0
    relaciones que coinciden con vocabulario médico/biológico puntual
    (craneometría, antropometría, etc.). Respeta EXCLUSIONES_FUSION_NOMBRES. Todo
    lo que no encaja en estas dos reglas queda listado como 'ambiguo' para
    que lo resuelvas con las opciones 6/7/8.

    Parámetros:
      aplicar (bool, default False): si es False, solo simula y muestra el
        reporte sin tocar la base de datos.
    """
    conn = _conectar_db()
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
                if _es_exclusion_fusion(nombre_a, nombre_b):
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

    ruido = []
    for id_, tipo, nombre, desc in filas:
        desc = desc or ""
        if grados.get(id_, 0) == 0 and (PATRONES_RUIDO.search(nombre) or PATRONES_RUIDO.search(desc)):
            ruido.append((id_, tipo, nombre))

    ids_resueltos = {f["eliminar"][0] for f in fusiones} | {r[0] for r in ruido}
    ambiguos = [(id_, tipo, nombre) for id_, tipo, nombre, _ in filas if grados.get(id_, 0) == 0 and id_ not in ids_resueltos]

    print("═" * 60)
    print(f"LIMPIEZA AUTOMÁTICA SEGURA {'— APLICANDO' if aplicar else '— DRY RUN'}")
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

    por_tipo_ambiguo = defaultdict(list)
    for id_, tipo, nombre in ambiguos:
        por_tipo_ambiguo[tipo].append((id_, nombre))
    print(f"\n◈ AMBIGUOS (necesitan tu criterio, ver opciones 6/7/8): {len(ambiguos)}")
    for tipo, items in por_tipo_ambiguo.items():
        print(f"\n  [{tipo}]")
        for id_, nombre in items:
            print(f"    id={id_:4d}  {nombre}")

    conn.close()
    if not aplicar:
        print("\nPara aplicar de verdad: corré la opción 5 de nuevo y elegí 'aplicar'.")

def herramienta_limpieza_automatica_menu():
    """Wrapper interactivo: pregunta si simular (dry-run) o aplicar de verdad."""
    resp = pedir_opcion(
        "  ¿Simular (dry-run, no cambia nada) o aplicar de verdad? (simular/aplicar): ",
        validas={"simular", "aplicar"}, alias={"s": "simular", "a": "aplicar"},
    )
    herramienta_limpieza_automatica(aplicar=(resp == "aplicar"))


# ═══════════════════════════════════════════════════════════════════════════
# FASE 4 · LIMPIEZA — 6. Fusionar duplicados (manual)
# ═══════════════════════════════════════════════════════════════════════════

def herramienta_fusionar_duplicados():
    """
    Fusiona nodos duplicados UNO POR UNO: te muestra ambos candidatos y su
    número de relaciones para que decidas cuál mantener. Salta
    automáticamente los pares en EXCLUSIONES_FUSION_NOMBRES. Usá esta opción para
    los casos que 'Limpieza automática segura' dejó como 'ambiguos' (mismo
    tipo, alta similitud, pero ninguno de los dos está claramente aislado).
    """
    conn = _conectar_db()
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
                if _es_exclusion_fusion(nombre_a, nombre_b):
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
# FASE 4 · LIMPIEZA — 7. Fusionar duplicados automático
# ═══════════════════════════════════════════════════════════════════════════

def herramienta_fusionar_auto():
    """
    Fusión automática más simple que la 'segura': si de un par similar UNO
    de los dos tiene 0 relaciones y el otro tiene al menos 1, se fusionan
    sin preguntar (no exige containment de nombres como la opción 5, solo
    similitud + aislamiento de uno de los dos). Respeta EXCLUSIONES_FUSION_NOMBRES.
    """
    conn = _conectar_db()
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
                if _es_exclusion_fusion(nombre_a, nombre_b):
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
            print(f"[{i}] → Saltado: ambos con relaciones (o ambos en 0)")
            saltados += 1
    conn.close()
    print(f"\nRESUMEN: {fusionados} fusionados | {saltados} saltados")


# ═══════════════════════════════════════════════════════════════════════════
# FASE 4 · LIMPIEZA — 8. Limpieza asistida (manual)
# ═══════════════════════════════════════════════════════════════════════════

def _cargar_estado_limpieza():
    if LIMPIEZA_ESTADO_PATH.exists():
        return json.loads(LIMPIEZA_ESTADO_PATH.read_text(encoding="utf-8"))
    return {"revisados": {}}

def _guardar_estado_limpieza(estado):
    LIMPIEZA_ESTADO_PATH.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")

def herramienta_limpieza_asistida():
    """
    Detecta nodos sospechosos (vocabulario médico/biológico, o 1 sola
    relación con descripción muy corta) y te los presenta uno por uno con
    todas sus relaciones actuales, para decidir: Mantener / Reclasificar
    (incluye los 8 tipos válidos) / Eliminar (en cascada) / Saltar.
    Checkpoint retomable en limpieza_estado.json.
    """
    conn = _conectar_db()
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
# FASE 4 · LIMPIEZA — 9. Limpieza automática de ruido puro
# ═══════════════════════════════════════════════════════════════════════════

def herramienta_limpiar_auto():
    """
    Elimina, SIN PREGUNTAR NADA, todo nodo con patrón médico/biológico o
    con 1 sola relación y descripción corta. Más agresiva que 'Limpieza
    asistida' (que sí te deja decidir caso por caso) — usar solo si ya
    revisaste manualmente unas cuantas veces y confiás en el patrón, o en
    modo --dry-run mental (revisá el reporte de la opción 5 primero).
    """
    conn = _conectar_db()
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
    print(f"LIMPIEZA AUTOMÁTICA DE RUIDO — {len(candidatos)} candidatos")
    print("═" * 60)
    for c in candidatos:
        print(f"  [{c['tipo']}] {c['nombre']} (id={c['id']}, grado={c['grado']}): {c['razon']}")
        eliminar_nodo_cascada(conn, c["id"])
    conn.close()
    print(f"\n✓ {len(candidatos)} nodos eliminados")


# ═══════════════════════════════════════════════════════════════════════════
# FASE 6 · MANTENIMIENTO — 11. Exportar / 12. Reforzar esquema / 13. Limpiar
# ═══════════════════════════════════════════════════════════════════════════

def herramienta_exportar():
    """Exporta la DB a src/datos.json para que el navegador muestre el grafo actualizado."""
    subprocess.run([sys.executable, str(BASE_DIR.parent / "scripts" / "export_json.py")])

def herramienta_reforzar_esquema():
    """
    Blinda la DB con un índice único (origen_id, destino_id, tipo) que
    bloquea relaciones duplicadas A NIVEL DE ESQUEMA (ya no depende de que
    cada script se acuerde de chequear antes de insertar), más índices de
    rendimiento. Se corre UNA SOLA VEZ en la vida del proyecto — volver a
    correrla no hace daño (usa IF NOT EXISTS), pero no hace falta repetirla.
    Requisito: no debe haber duplicados exactos todavía en 'relaciones'
    (si los hay, corré primero la opción 5 o 6).
    """
    conn = _conectar_db()
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_relacion_unica ON relaciones (origen_id, destino_id, tipo)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_relaciones_origen ON relaciones (origen_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_relaciones_destino ON relaciones (destino_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_nodos_tipo ON nodos (tipo)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_nodos_nombre ON nodos (nombre)")
    conn.commit()
    conn.close()
    print("✓ Esquema reforzado: índice único anti-duplicados + índices de rendimiento.")

def herramienta_limpiar():
    """
    Borra archivos intermedios ya procesados (candidatos_procesados_*.json
    archivados, logs de extracción sin errores). NUNCA toca los PDFs de
    libros/ ni la base de datos. Si hay algo pendiente (revisión a medias),
    avisa y pide confirmación extra antes de forzar.
    """
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
# FASE 6 · MANTENIMIENTO — 14. Mantenimiento automático completo
# ═══════════════════════════════════════════════════════════════════════════

def herramienta_mantenimiento():
    """
    Atajo que encadena, sin preguntar: limpieza automática segura (aplicada
    de verdad) → recuperar relaciones → exportar → auditoría. Pensado para
    correr apenas termines de revisar un libro, cuando confiás en que no
    hay casos ambiguos que requieran tu ojo. Si la auditoría final muestra
    aislados/duplicados, seguí con las opciones 6, 7 u 8 manualmente.
    """
    print("\n◈ 1/4 — Fusionando duplicados obvios...")
    herramienta_limpieza_automatica(aplicar=True)

    print("\n◈ 2/4 — Recuperando relaciones...")
    herramienta_recuperar_relaciones()

    print("\n◈ 3/4 — Exportando...")
    herramienta_exportar()

    print("\n◈ 4/4 — Auditoría...")
    herramienta_auditoria()


# ═══════════════════════════════════════════════════════════════════════════
# EXTRACCIÓN (prefijo E) — se ejecutan ANTES de todo lo anterior
# ═══════════════════════════════════════════════════════════════════════════

def extraer():
    """
    Lanza extractor.py sobre un PDF: lo divide en fragmentos, llama a la
    API (con rotación automática entre las keys en .env) y acumula los
    candidatos en candidatos_pendientes.json. Tiene su propio checkpoint
    por chunk (checkpoint_<nombre>.json) — si se corta a la mitad, la
    próxima corrida retoma sola desde el fragmento siguiente.
    """
    ruta = input("Ruta del PDF (ej: ../libros/nombre.pdf): ").strip()
    if not ruta:
        print("Cancelado.")
        return
    subprocess.run([sys.executable, str(BASE_DIR / "extractor.py"), ruta])

def modo_manual_menu():
    """
    Alternativa a extraer() para cuando se agotan TODAS las API keys de
    .env: 'generar' crea un .txt con el prompt completo del siguiente
    fragmento pendiente, listo para pegar en un chat web (ChatGPT/Claude/
    Gemini); 'pegar' toma la respuesta JSON que copiaste de vuelta y la
    integra al mismo candidatos_pendientes.json y checkpoint que usa
    extractor.py — ambos modos son intercambiables sin duplicar ni perder
    progreso entre chunks.
    """
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
    """
    Cruza el log de extracción de un libro (extraccion_log_<stem>.json)
    contra las relaciones realmente guardadas en la DB, para confirmar si
    el libro fue cubierto por completo o si algún fragmento falló / quedó
    sin nada citable.
    """
    stem = input("Nombre del PDF SIN extensión (ej: boas-f-1911...): ").strip()
    if not stem:
        print("Cancelado.")
        return
    subprocess.run([sys.executable, str(BASE_DIR / "verificar_extraccion.py"), stem])


# ═══════════════════════════════════════════════════════════════════════════
# MENÚ PRINCIPAL — reordenado según el flujo real de uso
# ═══════════════════════════════════════════════════════════════════════════

EXTRAE = {
    "e1": ("Extraer un libro nuevo vía API (rota keys automáticamente)", extraer),
    "e2": ("Modo manual — generar prompt para chat web / integrar respuesta", modo_manual_menu),
    "e3": ("Verificar cobertura de extracción de un libro específico", verificar),
}

OPCIONES = {
    "1":  ("Revisar candidatos pendientes (manual, uno por uno)", herramienta_revisar),
    "2":  ("Conectar automático de relaciones (alternativa rápida a '1' para lotes grandes)", herramienta_conectar_automatico_menu),
    "3":  ("Recuperar relaciones perdidas (rescate histórico)", herramienta_recuperar_relaciones),
    "4":  ("Auditoría completa (diagnóstico)", herramienta_auditoria),
    "5":  ("Limpieza automática segura (fusión + eliminación de ruido)", herramienta_limpieza_automatica_menu),
    "6":  ("Fusionar duplicados (manual, casos ambiguos)", herramienta_fusionar_duplicados),
    "7":  ("Fusionar duplicados automático (solo si un lado tiene 0 relaciones)", herramienta_fusionar_auto),
    "8":  ("Limpieza asistida de nodos aislados/ruido (manual)", herramienta_limpieza_asistida),
    "9":  ("Limpieza automática de ruido puro (rápida, sin preguntar — cuidado)", herramienta_limpiar_auto),
    "10": ("Auditoría de nuevo (confirmar que quedó limpio)", herramienta_auditoria),
    "11": ("Exportar a datos.json", herramienta_exportar),
    "12": ("Reforzar esquema de la DB (una sola vez en la vida del proyecto)", herramienta_reforzar_esquema),
    "13": ("Limpiar archivos temporales", herramienta_limpiar),
    "14": ("Mantenimiento automático completo (atajo: 5+3+11+4)", herramienta_mantenimiento),
    "0":  ("Salir", None),
}

def mostrar_ayuda(clave):
    """Muestra la descripción y los parámetros de una herramienta sin ejecutarla."""
    if clave in OPCIONES:
        descripcion, funcion = OPCIONES[clave]
    elif clave in EXTRAE:
        descripcion, funcion = EXTRAE[clave]
    else:
        print(f"⚠ No existe la herramienta '{clave}'.")
        return
    if funcion is None:
        print("(Salir no tiene ayuda — simplemente termina el programa)")
        return
    print("\n" + "─" * 60)
    print(f"AYUDA — {clave}) {descripcion}")
    print("─" * 60)
    doc = inspect.getdoc(funcion)
    print(f"\n{doc if doc else '(sin descripción adicional)'}\n")
    firma = inspect.signature(funcion)
    if firma.parameters:
        print("Parámetros:")
        for nombre, param in firma.parameters.items():
            default = f" = {param.default}" if param.default is not inspect.Parameter.empty else " (requerido)"
            print(f"  - {nombre}{default}")
    else:
        print("No recibe parámetros por línea de comandos — todo lo pide de forma interactiva mientras corre.")
    print("─" * 60)

def mostrar_flujo():
    """Imprime el orden recomendado de uso, paso a paso, después de procesar un libro."""
    print("\n" + "═" * 60)
    print("FLUJO RECOMENDADO (después de procesar un libro nuevo)")
    print("═" * 60)
    pasos = [
        ("E1 o E2", "Extraer el libro (vía API, o modo manual si no hay tokens)"),
        ("1 o 2", "Revisar candidatos: '1' manual uno por uno, o '2' automático para lotes grandes"),
        ("3", "Recuperar relaciones perdidas (rescata lo que 1/2 no pudieron resolver)"),
        ("4", "Auditoría — mirá qué quedó: aislados, duplicados, cobertura de páginas"),
        ("5", "Limpieza automática segura — resuelve lo obvio sin preguntar"),
        ("6", "Fusionar duplicados restantes — casos ambiguos, con tu criterio"),
        ("7", "Fusionar aislados automático — solo si un lado tiene 0 relaciones"),
        ("8", "Limpieza asistida — lo que quede de ruido/aislados, uno por uno"),
        ("9", "(opcional) Limpieza automática de ruido puro — rápida, usar con cuidado"),
        ("10", "Auditoría de nuevo — confirmá que quedó limpio"),
        ("11", "Exportar a datos.json — para verlo en el navegador"),
        ("12", "Reforzar esquema — SOLO la primera vez que uses el proyecto"),
        ("13", "Limpiar archivos temporales — al final, cuando todo esté ok"),
    ]
    for numero, texto in pasos:
        print(f"  {numero:>7}) {texto}")
    print("\n  Atajo: la opción 14 encadena 5 + 3 + 11 + 4 automáticamente.")
    print("  Tip: '?N' (ej: '?6') muestra la ayuda de esa herramienta sin ejecutarla.")
    print("═" * 60)

def main():
    while True:
        print("\n" + "═" * 60)
        print("  CEREBRO ANTROPOLÓGICO — CENTRO DE COMANDOS UNIFICADO")
        print("═" * 60)
        print("  ── FASE 1 · Extracción ──")
        for clave, (descripcion, _) in EXTRAE.items():
            print(f"  {clave}) {descripcion}")
        print("  ── FASE 2 · Revisión ──")
        for clave in ("1", "2", "3"):
            print(f"  {clave:>2}) {OPCIONES[clave][0]}")
        print("  ── FASE 3 · Diagnóstico ──")
        print(f"   4) {OPCIONES['4'][0]}")
        print("  ── FASE 4 · Limpieza y deduplicación ──")
        for clave in ("5", "6", "7", "8", "9"):
            print(f"  {clave:>2}) {OPCIONES[clave][0]}")
        print("  ── FASE 5 · Confirmar ──")
        print(f"  10) {OPCIONES['10'][0]}")
        print("  ── FASE 6 · Mantenimiento y exportación ──")
        for clave in ("11", "12", "13", "14"):
            print(f"  {clave:>2}) {OPCIONES[clave][0]}")
        print("   0) Salir")
        print("\n  'flujo' = orden recomendado paso a paso  |  '?N' = ayuda de la herramienta N (ej: ?5)")

        eleccion = input("\n¿Qué querés hacer?: ").strip().lower()

        if eleccion == "flujo":
            mostrar_flujo()
        elif eleccion.startswith("?"):
            mostrar_ayuda(eleccion[1:])
        elif eleccion in EXTRAE:
            EXTRAE[eleccion][1]()
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