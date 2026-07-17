"""
Revisión manual de candidatos, con alerta de posibles duplicados y checkpoint
de progreso — si cancelas a mitad de camino, la próxima corrida retoma
exactamente donde quedaste, sin duplicar ni perder nada.

Uso: python revisar.py
"""
import json
import sqlite3
from pathlib import Path
from difflib import get_close_matches

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR.parent / "data" / "grafo.db"
CANDIDATOS_PATH = BASE_DIR / "candidatos_pendientes.json"
ESTADO_PATH = BASE_DIR / "revision_estado.json"

UMBRAL_SIMILITUD = 0.75


def pedir_opcion(mensaje, validas, alias=None):
    alias = alias or {}
    while True:
        resp = input(mensaje).strip().lower()
        if resp in alias:
            resp = alias[resp]
        if resp in validas:
            return resp
        print(f"  ⚠ No entendí '{resp}'. Opciones válidas: {', '.join(sorted(validas))}. Intenta de nuevo.")


def cargar_estado():
    if ESTADO_PATH.exists():
        return json.loads(ESTADO_PATH.read_text(encoding="utf-8"))
    return {"nodos_revisados": {}, "relaciones_revisadas": []}


def guardar_estado(estado):
    ESTADO_PATH.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")


def clave_relacion(r):
    return f"{r['origen']}->{r['destino']}::{r['tipo']}::{r['cita_textual'][:60]}"


def cargar_nodos_existentes(conn):
    filas = conn.execute("SELECT id, nombre FROM nodos").fetchall()
    return {nombre: id_ for id_, nombre in filas}


def buscar_similares(nombre, catalogo_nombres):
    return get_close_matches(nombre, catalogo_nombres, n=3, cutoff=UMBRAL_SIMILITUD)


def main():
    if not CANDIDATOS_PATH.exists():
        print("✗ No hay candidatos_pendientes.json. Corre extractor.py primero.")
        return

    candidatos = json.loads(CANDIDATOS_PATH.read_text(encoding="utf-8"))
    estado = cargar_estado()
    conn = sqlite3.connect(DB_PATH)

    catalogo = cargar_nodos_existentes(conn)
    mapa_gemini_a_real = {
        id_gemini: info["id_real"]
        for id_gemini, info in estado["nodos_revisados"].items()
        if info["decision"] in ("insertado", "reutilizado")
    }

    nodos_nuevos = candidatos.get("nodos_nuevos", [])
    pendientes_nodos = [n for n in nodos_nuevos if n["id"] not in estado["nodos_revisados"]]

    print("═" * 60)
    print(f"NODOS NUEVOS — {len(pendientes_nodos)} pendientes de {len(nodos_nuevos)} totales")
    if len(pendientes_nodos) < len(nodos_nuevos):
        print(f"  (retomando; {len(nodos_nuevos) - len(pendientes_nodos)} ya revisados en sesión anterior)")
    print("═" * 60)

    for n in pendientes_nodos:
        id_gemini = n["id"]
        print(f"\n[{n['confianza'].upper()}] {n['tipo']} — {n['nombre']} (id propuesto: {id_gemini})")
        print(f"  {n.get('descripcion', n.get('resumen', ''))}")
        if n.get("justificacion_concepto") and n["tipo"] == "concepto":
            print(f"  Justificación: {n['justificacion_concepto']}")

        similares = buscar_similares(n["nombre"], list(catalogo.keys()))
        decision_tomada = False

        if similares:
            print(f"  ⚠ POSIBLE DUPLICADO de: {', '.join(similares)}")
            print(f"    (id existente: {catalogo[similares[0]]})")
            resp = pedir_opcion(
                "  ¿Es el mismo nodo? (s = usar existente / n = es distinto / omitir): ",
                validas={"s", "n", "omitir"},
                alias={"si": "s", "sí": "s", "o": "omitir"},
            )
            if resp == "s":
                id_real = catalogo[similares[0]]
                mapa_gemini_a_real[id_gemini] = id_real
                estado["nodos_revisados"][id_gemini] = {"decision": "reutilizado", "id_real": id_real}
                guardar_estado(estado)
                print("  ✓ Se reutilizará el nodo existente")
                decision_tomada = True
            elif resp == "omitir":
                estado["nodos_revisados"][id_gemini] = {"decision": "omitido", "id_real": None}
                guardar_estado(estado)
                print("  ✗ Omitido")
                decision_tomada = True

        if not decision_tomada:
            resp = pedir_opcion(
                "  ¿Aprobar como nodo nuevo? (s/n/editar): ",
                validas={"s", "n", "editar"},
                alias={"si": "s", "sí": "s", "e": "editar"},
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
                guardar_estado(estado)
                print(f"  ✓ Insertado (id real: {id_real})")
            elif resp == "editar":
                nuevo_nombre = input(f"  Nombre [{n['nombre']}]: ") or n["nombre"]
                nueva_desc = input(f"  Descripción [{n.get('descripcion', n.get('resumen', ''))}]: ") or n.get("descripcion", n.get("resumen", ""))
                cur = conn.execute(
                    "INSERT INTO nodos (tipo, nombre, descripcion, metadatos) VALUES (?, ?, ?, ?)",
                    (n["tipo"], nuevo_nombre, nueva_desc, json.dumps({"id_gemini": id_gemini})),
                )
                id_real = cur.lastrowid
                conn.commit()
                mapa_gemini_a_real[id_gemini] = id_real
                catalogo[nuevo_nombre] = id_real
                estado["nodos_revisados"][id_gemini] = {"decision": "insertado", "id_real": id_real}
                guardar_estado(estado)
                print(f"  ✓ Insertado (editado, id real: {id_real})")
            else:
                estado["nodos_revisados"][id_gemini] = {"decision": "descartado", "id_real": None}
                guardar_estado(estado)
                print("  ✗ Descartado")

    print("\n" + "═" * 60)
    relaciones_nuevas = candidatos.get("relaciones_nuevas", [])
    ids_validos = {row[0] for row in conn.execute("SELECT id FROM nodos")}
    pendientes_rels = [r for r in relaciones_nuevas if clave_relacion(r) not in estado["relaciones_revisadas"]]
    print(f"RELACIONES NUEVAS — {len(pendientes_rels)} pendientes de {len(relaciones_nuevas)} totales")
    print("═" * 60)

    for r in pendientes_rels:
        clave = clave_relacion(r)
        origen = mapa_gemini_a_real.get(r["origen"], None)
        destino = mapa_gemini_a_real.get(r["destino"], None)

        if origen is None or destino is None:
            print(f"\n⚠ Relación omitida — nodo no mapeado: {r['origen']} → {r['destino']}")
            estado["relaciones_revisadas"].append(clave)
            guardar_estado(estado)
            continue
        if origen not in ids_validos or destino not in ids_validos:
            print(f"\n⚠ Relación omitida — nodo no existe en DB: {origen} → {destino}")
            estado["relaciones_revisadas"].append(clave)
            guardar_estado(estado)
            continue

        print(f"\n[{r['confianza'].upper()}] {r['origen']} → {r['destino']} --{r['tipo']}-->")
        print(f'  Cita: "{r["cita_textual"]}"')
        if r.get("fuente"):
            print(f"  Fuente: {r['fuente']}")
        resp = pedir_opcion(
            "  ¿Aprobar? (s/n): ",
            validas={"s", "n"},
            alias={"si": "s", "sí": "s"},
        )
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
        guardar_estado(estado)

    conn.close()

    total_nodos = len(candidatos.get("nodos_nuevos", []))
    total_rels = len(candidatos.get("relaciones_nuevas", []))
    if len(estado["nodos_revisados"]) >= total_nodos and len(estado["relaciones_revisadas"]) >= total_rels:
        print("\n◈ Revisión completa. Archivando candidatos procesados...")
        archivo = BASE_DIR / f"candidatos_procesados_{__import__('datetime').datetime.now():%Y%m%d_%H%M%S}.json"
        CANDIDATOS_PATH.rename(archivo)
        ESTADO_PATH.unlink()
        print(f"  Movido a {archivo.name}")

    print("\n◈ Corre: cd .. && python scripts/export_json.py")


if __name__ == "__main__":
    main()
