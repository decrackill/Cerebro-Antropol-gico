"""
Conexión automática de relaciones pendientes: resuelve ids por número directo,
fuzzy match contra nodos existentes, e inserta nodos huérfanos si no hay match.
Todo sin preguntar uno por uno — ideal para lotes grandes ya generados por
extractor.py. Al final te da un reporte completo, y guarda un log de las
decisiones "fuzzy" (menos seguras) para que las repases manualmente si quieres.

Uso: python conectar_automatico.py
Opcional: python conectar_automatico.py --umbral 0.85   (más estricto, default 0.80)
          python conectar_automatico.py --dry-run        (solo reporta, no inserta nada)
"""
import json
import sqlite3
import sys
from pathlib import Path
from difflib import get_close_matches

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR.parent / "data" / "grafo.db"
CANDIDATOS_PATH = BASE_DIR / "candidatos_pendientes.json"

UMBRAL_DEFAULT = 0.80


def cargar_catalogo(conn):
    filas = conn.execute("SELECT id, tipo, nombre FROM nodos").fetchall()
    return {nombre: (id_, tipo) for id_, tipo, nombre in filas}


def resolver_nodo(referencia_id, referencia_nombre, catalogo, umbral, log_fuzzy):
    """
    Intenta resolver una referencia de nodo (usada en origen/destino de una relación)
    a un id_real de la DB. Devuelve (id_real, metodo) donde metodo es
    'directo' | 'fuzzy' | 'nuevo'.
    """
    # 1. Si la referencia es numérica y existe tal cual, es directo
    if isinstance(referencia_id, int) or (isinstance(referencia_id, str) and referencia_id.strip().isdigit()):
        posible = int(referencia_id) if isinstance(referencia_id, int) else int(referencia_id.strip())
        for nombre, (id_real, tipo) in catalogo.items():
            if id_real == posible:
                return posible, "directo"
        return None, "no_encontrado"

    # 2. Fuzzy match del NOMBRE contra el catálogo
    if referencia_nombre:
        similares = get_close_matches(referencia_nombre, list(catalogo.keys()), n=1, cutoff=umbral)
        if similares:
            id_real, tipo = catalogo[similares[0]]
            log_fuzzy.append({
                "referencia_original": referencia_nombre,
                "matcheado_con": similares[0],
                "id_real": id_real,
            })
            return id_real, "fuzzy"

    return None, "no_encontrado"


def main():
    dry_run = "--dry-run" in sys.argv
    umbral = UMBRAL_DEFAULT
    if "--umbral" in sys.argv:
        umbral = float(sys.argv[sys.argv.index("--umbral") + 1])

    if not CANDIDATOS_PATH.exists():
        print("✗ No hay candidatos_pendientes.json.")
        return

    candidatos = json.loads(CANDIDATOS_PATH.read_text(encoding="utf-8"))
    conn = sqlite3.connect(DB_PATH)
    catalogo = cargar_catalogo(conn)

    print("═" * 60)
    print(f"CONEXIÓN AUTOMÁTICA (umbral fuzzy: {umbral}){' — DRY RUN, no se insertará nada' if dry_run else ''}")
    print("═" * 60)

    # PASO 1: Insertar nodos huérfanos (nodos_nuevos que aún no existen por nombre)
    log_nodos_nuevos = []
    mapa_id_gemini_a_real = {}

    for n in candidatos.get("nodos_nuevos", []):
        if n["nombre"] in catalogo:
            id_real, tipo = catalogo[n["nombre"]]
            mapa_id_gemini_a_real[n["id"]] = id_real
            continue

        if dry_run:
            mapa_id_gemini_a_real[n["id"]] = f"NUEVO:{n['nombre']}"
        else:
            cur = conn.execute(
                "INSERT INTO nodos (tipo, nombre, descripcion, metadatos) VALUES (?, ?, ?, ?)",
                (n["tipo"], n["nombre"], n.get("descripcion", n.get("resumen", "")), json.dumps({"id_gemini": n["id"], "insertado_por": "conectar_automatico"})),
            )
            id_real = cur.lastrowid
            conn.commit()
            mapa_id_gemini_a_real[n["id"]] = id_real
            catalogo[n["nombre"]] = (id_real, n["tipo"])

        log_nodos_nuevos.append(n["nombre"])

    print(f"\n◈ Nodos huérfanos insertados automáticamente: {len(log_nodos_nuevos)}")
    for nombre in log_nodos_nuevos:
        print(f"    + {nombre}")

    # PASO 2 y 4: Resolver y insertar relaciones
    insertadas = 0
    ya_existian = 0
    no_resolubles = 0
    log_fuzzy = []
    log_no_resolubles = []

    for r in candidatos.get("relaciones_nuevas", []):
        origen_ref = r["origen"]
        destino_ref = r["destino"]

        # Buscar nombre real si la referencia viene de nodos_nuevos de este lote
        nombre_origen = next((n["nombre"] for n in candidatos.get("nodos_nuevos", []) if n["id"] == origen_ref), None)
        nombre_destino = next((n["nombre"] for n in candidatos.get("nodos_nuevos", []) if n["id"] == destino_ref), None)

        origen_id = mapa_id_gemini_a_real.get(origen_ref)
        if origen_id is None:
            origen_id, metodo_o = resolver_nodo(origen_ref, nombre_origen or str(origen_ref), catalogo, umbral, log_fuzzy)
        destino_id = mapa_id_gemini_a_real.get(destino_ref)
        if destino_id is None:
            destino_id, metodo_d = resolver_nodo(destino_ref, nombre_destino or str(destino_ref), catalogo, umbral, log_fuzzy)

        if origen_id is None or destino_id is None or isinstance(origen_id, str) or isinstance(destino_id, str):
            no_resolubles += 1
            log_no_resolubles.append(r)
            continue

        if not dry_run:
            existe = conn.execute(
                "SELECT 1 FROM relaciones WHERE origen_id=? AND destino_id=? AND tipo=?",
                (origen_id, destino_id, r["tipo"]),
            ).fetchone()
            if existe:
                ya_existian += 1
                continue
            conn.execute(
                "INSERT INTO relaciones (origen_id, destino_id, tipo, peso, fuente) VALUES (?, ?, ?, 1.0, ?)",
                (origen_id, destino_id, r["tipo"], r.get("fuente")),
            )
            conn.commit()
        insertadas += 1

    conn.close()

    print("\n" + "═" * 60)
    print("REPORTE FINAL")
    print("═" * 60)
    print(f"  Relaciones insertadas: {insertadas}/{len(candidatos.get('relaciones_nuevas', []))}")
    print(f"  Ya existían (omitidas): {ya_existian}")
    print(f"  No resolubles: {no_resolubles}")
    print(f"  Resueltas por fuzzy match (verificar manualmente): {len(log_fuzzy)}")

    if log_fuzzy:
        print("\n  ⚠ Matches por similitud de texto, no exactos — repasa estos:")
        for f in log_fuzzy[:30]:
            print(f"    '{f['referencia_original']}' → '{f['matcheado_con']}' (id={f['id_real']})")

    if log_no_resolubles:
        log_path = BASE_DIR / "conexion_automatica_no_resueltas.json"
        log_path.write_text(json.dumps(log_no_resolubles, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n  Relaciones no resueltas guardadas en {log_path.name} para revisión manual con revisar.py")

    if not dry_run and insertadas > 0:
        print("\n◈ Corre: cd .. && python scripts/export_json.py")


if __name__ == "__main__":
    main()
