"""
Revisión manual de candidatos, con alerta de posibles duplicados.
Adaptado al schema real: nodos.id INTEGER autoincrement,
relaciones usa origen_id/destino_id INTEGER y fuente TEXT.

Uso: python revisar.py
"""
import json
import sqlite3
from pathlib import Path
from difflib import get_close_matches

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR.parent / "data" / "grafo.db"
CANDIDATOS_PATH = BASE_DIR / "candidatos_pendientes.json"

UMBRAL_SIMILITUD = 0.75


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
    conn = sqlite3.connect(DB_PATH)

    catalogo = cargar_nodos_existentes(conn)
    mapa_gemini_a_real = {}

    print("═" * 60)
    print(f"NODOS NUEVOS ({len(candidatos.get('nodos_nuevos', []))})")
    print("═" * 60)

    for n in candidatos.get("nodos_nuevos", []):
        id_gemini = n["id"]
        print(f"\n[{n['confianza'].upper()}] {n['tipo']} — {n['nombre']} (id propuesto: {id_gemini})")
        print(f"  {n.get('descripcion', n.get('resumen', ''))}")

        similares = buscar_similares(n["nombre"], list(catalogo.keys()))
        if similares:
            print(f"  ⚠ POSIBLE DUPLICADO de: {', '.join(similares)}")
            print(f"    (id existente: {catalogo[similares[0]]})")
            resp = input("  ¿Es el mismo nodo? (s = usar existente / n = es distinto / omitir): ").strip().lower()
            if resp == "s":
                mapa_gemini_a_real[id_gemini] = catalogo[similares[0]]
                print("  ✓ Se reutilizará el nodo existente")
                continue
            elif resp == "omitir":
                print("  ✗ Omitido")
                continue

        resp = input("  ¿Aprobar como nodo nuevo? (s/n/editar): ").strip().lower()
        if resp == "s":
            cur = conn.execute(
                "INSERT INTO nodos (tipo, nombre, descripcion, metadatos) VALUES (?, ?, ?, ?)",
                (n["tipo"], n["nombre"], n.get("descripcion", n.get("resumen", "")), json.dumps({"id_gemini": id_gemini})),
            )
            id_real = cur.lastrowid
            mapa_gemini_a_real[id_gemini] = id_real
            catalogo[n["nombre"]] = id_real
            print(f"  ✓ Insertado (id real: {id_real})")
            conn.commit()
        elif resp == "editar":
            nuevo_nombre = input(f"  Nombre [{n['nombre']}]: ") or n["nombre"]
            nueva_desc = input(f"  Descripción [{n.get('descripcion', n.get('resumen', ''))}]: ") or n.get("descripcion", n.get("resumen", ""))
            cur = conn.execute(
                "INSERT INTO nodos (tipo, nombre, descripcion, metadatos) VALUES (?, ?, ?, ?)",
                (n["tipo"], nuevo_nombre, nueva_desc, json.dumps({"id_gemini": id_gemini})),
            )
            id_real = cur.lastrowid
            mapa_gemini_a_real[id_gemini] = id_real
            catalogo[nuevo_nombre] = id_real
            print(f"  ✓ Insertado (editado, id real: {id_real})")
            conn.commit()
        else:
            print("  ✗ Descartado")

    print("\n" + "═" * 60)
    print(f"RELACIONES NUEVAS ({len(candidatos.get('relaciones_nuevas', []))})")
    print("═" * 60)

    ids_validos = {row[0] for row in conn.execute("SELECT id FROM nodos")}

    for r in candidatos.get("relaciones_nuevas", []):
        origen = mapa_gemini_a_real.get(r["origen"], None)
        destino = mapa_gemini_a_real.get(r["destino"], None)

        if origen is None or destino is None:
            print(f"\n⚠ Relación omitida — nodo no mapeado: {r['origen']} → {r['destino']}")
            continue
        if origen not in ids_validos or destino not in ids_validos:
            print(f"\n⚠ Relación omitida — nodo no existe en DB: {origen} → {destino}")
            continue

        print(f"\n[{r['confianza'].upper()}] {r['origen']} → {r['destino']} --{r['tipo']}-->")
        print(f'  Cita: "{r["cita_textual"]}"')
        if r.get("fuente"):
            print(f"  Fuente: {r['fuente']}")
        resp = input("  ¿Aprobar? (s/n): ").strip().lower()
        if resp == "s":
            conn.execute(
                "INSERT INTO relaciones (origen_id, destino_id, tipo, peso, fuente) VALUES (?, ?, ?, 1.0, ?)",
                (origen, destino, r["tipo"], r.get("fuente")),
            )
            print("  ✓ Insertada")
            conn.commit()
        else:
            print("  ✗ Descartada")

    conn.close()

    print("\n◈ Listo. Corre: cd .. && python scripts/export_json.py")


if __name__ == "__main__":
    main()
