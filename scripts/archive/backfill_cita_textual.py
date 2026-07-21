"""
Migración retroactiva: pobla cita_textual en relaciones existentes
usando los datos de los archivos JSON fuente del pipeline.

Uso:
    python scripts/backfill_cita_textual.py
"""
import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "grafo.db"
PIPELINE_DIR = Path(__file__).parent.parent / "pipeline"


def cargar_mapeo_ids():
    """Carga el mapeo snake_case_id -> real_id desde revision_estado.json."""
    estado_path = PIPELINE_DIR / "revision_estado.json"
    if not estado_path.exists():
        print("No se encontró revision_estado.json")
        return {}
    estado = json.loads(estado_path.read_text(encoding="utf-8"))
    revisados = estado.get("nodos_revisados", {})
    mapping = {}
    for snake_id, info in revisados.items():
        if info.get("decision") in ("insertado", "reutilizado"):
            mapping[snake_id] = info["id_real"]
    return mapping


def cargar_candidatos():
    """Carga todas las relaciones de candidatos_procesados_*.json."""
    candidatos = []
    for f in sorted(PIPELINE_DIR.glob("candidatos_procesados_*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        rels = data.get("relaciones_nuevas", [])
        candidatos.extend(rels)
        print(f"  {f.name}: {len(rels)} relaciones")
    return candidatos


def cargar_no_resueltas():
    """Carga relaciones de conexion_automatica_no_resueltas.json."""
    path = PIPELINE_DIR / "conexion_automatica_no_resueltas.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    print(f"  conexion_automatica_no_resueltas.json: {len(data)} relaciones")
    return data


def resolver_id(id_str, mapping):
    """Resuelve un ID string a un ID numérico real."""
    if id_str in mapping:
        return mapping[id_str]
    if isinstance(id_str, str) and id_str.isdigit():
        return int(id_str)
    if isinstance(id_str, int):
        return id_str
    return None


def normalizar_tipo(tipo):
    """Normaliza un tipo de relación al formato canónico."""
    aliases = {
        "autor_de": "autor_de",
        "es_autor_de": "autor_de",
        "escribió": "escribió",
        "escribe": "escribió",
        "estudia_a": "estudia_a",
        "desarrolla_concepto": "desarrolla_concepto",
        "critica_a": "critica_a",
        "influenciado_por": "influenciado_por",
        "influido_por": "influenciado_por",
        "pertenece_a": "pertenece_a",
        "contemporaneo_de": "contemporaneo_de",
        "precursor_de": "precursor_de",
        "redefine_a": "redefine_a",
        "trata_de": "trata_de",
    }
    return aliases.get(tipo, tipo)


def backfill():
    print("=== Migración retroactiva de cita_textual ===\n")

    mapping = cargar_mapeo_ids()
    print(f"Mapeo de IDs: {len(mapping)} entradas\n")

    print("Cargando candidatos:")
    candidatos = cargar_candidatos()
    no_resueltas = cargar_no_resueltas()
    todos = candidatos + no_resueltas
    print(f"Total relaciones fuente: {len(todos)}\n")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    db_rels = conn.execute("""
        SELECT r.id, r.origen_id, r.destino_id, r.tipo, r.cita_textual
        FROM relaciones r
    """).fetchall()

    db_lookup = {}
    for r in db_rels:
        key = (r["origen_id"], r["destino_id"])
        if key not in db_lookup:
            db_lookup[key] = []
        db_lookup[key].append(dict(r))

    actualizadas = 0
    sin_resolver = 0
    sin_match = 0
    ya_tenian = 0

    for cand in todos:
        origen_str = str(cand.get("origen", ""))
        destino_str = str(cand.get("destino", ""))
        tipo_cand = cand.get("tipo", "")
        cita = cand.get("cita_textual", "")

        if not cita:
            continue

        origen_id = resolver_id(origen_str, mapping)
        destino_id = resolver_id(destino_str, mapping)

        if origen_id is None or destino_id is None:
            sin_resolver += 1
            continue

        candidatas = db_lookup.get((origen_id, destino_id), [])
        if not candidatas:
            sin_match += 1
            continue

        match = None
        tipo_norm = normalizar_tipo(tipo_cand)
        for db_r in candidatas:
            if db_r["tipo"] == tipo_cand or db_r["tipo"] == tipo_norm:
                match = db_r
                break

        if match is None and len(candidatas) == 1:
            match = candidatas[0]

        if match is None:
            sin_match += 1
            continue

        if match["cita_textual"]:
            ya_tenian += 1
            continue

        conn.execute(
            "UPDATE relaciones SET cita_textual = ? WHERE id = ?",
            (cita, match["id"]),
        )
        actualizadas += 1

    conn.commit()
    conn.close()

    print("=== Resultados ===")
    print(f"Relaciones actualizadas con cita_textual: {actualizadas}")
    print(f"Ya tenían cita_textual: {ya_tenian}")
    print(f"No se pudo resolver ID: {sin_resolver}")
    print(f"No se encontró match en DB: {sin_match}")

    conn = sqlite3.connect(DB_PATH)
    total = conn.execute("SELECT COUNT(*) FROM relaciones").fetchone()[0]
    con_cita = conn.execute("SELECT COUNT(*) FROM relaciones WHERE cita_textual IS NOT NULL").fetchone()[0]
    print(f"\nEstado final de la DB:")
    print(f"  Total relaciones: {total}")
    print(f"  Con cita_textual: {con_cita}")
    print(f"  Sin cita_textual: {total - con_cita}")
    conn.close()


if __name__ == "__main__":
    backfill()
