"""
Reprocesa relaciones que fueron omitidas por el bug de resolución de ids
(cuando una relación citaba un nodo existente por su id numérico y
revisar.py no sabía resolverlo). Lee todos los archivos
candidatos_procesados_*.json y candidatos_pendientes.json que encuentre,
y solo actúa sobre relaciones que:
  1. Ahora SÍ se pueden resolver con el fix.
  2. NO estén ya insertadas en la tabla relaciones (evita duplicados).

Uso: python recuperar_relaciones.py
"""
import json
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR.parent / "data" / "grafo.db"
ESTADO_PATH = BASE_DIR / "recuperacion_estado.json"


def resolver_id(referencia, ids_validos):
    if isinstance(referencia, int):
        return referencia if referencia in ids_validos else None
    if isinstance(referencia, str) and referencia.strip().isdigit():
        posible = int(referencia.strip())
        return posible if posible in ids_validos else None
    if isinstance(referencia, str):
        return None
    return None


def mapa_snake_case_a_id_real(conn):
    filas = conn.execute("SELECT id, metadatos FROM nodos WHERE metadatos IS NOT NULL").fetchall()
    mapa = {}
    for id_real, meta in filas:
        try:
            m = json.loads(meta)
            if "id_gemini" in m:
                mapa[m["id_gemini"]] = id_real
        except (json.JSONDecodeError, TypeError):
            pass
    return mapa


def cargar_estado():
    if ESTADO_PATH.exists():
        return set(json.loads(ESTADO_PATH.read_text(encoding="utf-8")))
    return set()


def guardar_estado(claves):
    ESTADO_PATH.write_text(json.dumps(sorted(claves), ensure_ascii=False, indent=2), encoding="utf-8")


def clave_relacion(r):
    return f"{r['origen']}->{r['destino']}::{r['tipo']}::{r['cita_textual'][:60]}"


def relacion_ya_existe(conn, origen, destino, tipo):
    fila = conn.execute(
        "SELECT 1 FROM relaciones WHERE origen_id = ? AND destino_id = ? AND tipo = ?",
        (origen, destino, tipo),
    ).fetchone()
    return fila is not None


def main():
    archivos = sorted(BASE_DIR.glob("candidatos_procesados_*.json"))
    pendiente = BASE_DIR / "candidatos_pendientes.json"
    if pendiente.exists():
        archivos.append(pendiente)

    if not archivos:
        print("✗ No se encontraron archivos candidatos_procesados_*.json ni candidatos_pendientes.json")
        return

    conn = sqlite3.connect(DB_PATH)
    ids_validos = {row[0] for row in conn.execute("SELECT id FROM nodos")}
    mapa_snake = mapa_snake_case_a_id_real(conn)
    ya_procesadas = cargar_estado()

    insertadas = 0
    todavia_no_resolubles = 0
    ya_existian = 0

    for archivo in archivos:
        print(f"\n◈ Revisando {archivo.name}...")
        datos = json.loads(archivo.read_text(encoding="utf-8"))
        relaciones = datos.get("relaciones_nuevas", [])

        for r in relaciones:
            clave = clave_relacion(r)
            if clave in ya_procesadas:
                continue

            origen = resolver_id(r["origen"], ids_validos) or mapa_snake.get(r["origen"])
            destino = resolver_id(r["destino"], ids_validos) or mapa_snake.get(r["destino"])

            if origen is None or destino is None:
                todavia_no_resolubles += 1
                ya_procesadas.add(clave)
                continue
            if origen not in ids_validos or destino not in ids_validos:
                todavia_no_resolubles += 1
                ya_procesadas.add(clave)
                continue

            if relacion_ya_existe(conn, origen, destino, r["tipo"]):
                ya_existian += 1
                ya_procesadas.add(clave)
                continue

            conn.execute(
                "INSERT INTO relaciones (origen_id, destino_id, tipo, peso, fuente) VALUES (?, ?, ?, 1.0, ?)",
                (origen, destino, r["tipo"], r.get("fuente")),
            )
            conn.commit()
            insertadas += 1
            ya_procesadas.add(clave)
            guardar_estado(ya_procesadas)
            print(f"  ✓ Recuperada: {origen} → {destino} ({r['tipo']})")

    conn.close()

    print("\n" + "═" * 60)
    print(f"RESUMEN: {insertadas} relaciones recuperadas | "
          f"{ya_existian} ya existían | {todavia_no_resolubles} siguen sin poder resolverse")
    print("═" * 60)
    if insertadas:
        print("◈ Corre: cd .. && python scripts/export_json.py")


if __name__ == "__main__":
    main()
