"""
Limpieza asistida del grafo: detecta nodos que probablemente sean "ruido"
(términos médicos/biológicos/técnicos alejados del núcleo antropológico-teórico)
usando heurísticas de palabras clave + nodos con muy pocas relaciones, y te los
presenta uno por uno para decidir: mantener, reclasificar, o eliminar (con
cascada de sus relaciones). Con checkpoint retomable, igual que revisar.py.

Uso: python limpieza_asistida.py
"""
import json
import re
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR.parent / "data" / "grafo.db"
ESTADO_PATH = BASE_DIR / "limpieza_estado.json"

TIPOS_VALIDOS = {"autor", "obra", "concepto", "escuela", "cultura", "debate", "poblacion", "corriente"}

PATRONES_RUIDO = re.compile(
    r"(cr[aá]neo|cef[aá]lic|torus|osteo|esquelet|patolog[ií]a|anatom[ií]a|"
    r"medici[oó]n corporal|antropometr[ií]a|índice cef[aá]lico|"
    r"malformaci[oó]n|enfermedad|hueso|dentici[oó]n|estatura promedio|"
    r"pigmentaci[oó]n|coeficiente craneal)",
    re.IGNORECASE,
)


def cargar_estado():
    if ESTADO_PATH.exists():
        return json.loads(ESTADO_PATH.read_text(encoding="utf-8"))
    return {"revisados": {}}


def guardar_estado(estado):
    ESTADO_PATH.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")


def detectar_candidatos(conn):
    filas = conn.execute("SELECT id, tipo, nombre, descripcion FROM nodos ORDER BY id").fetchall()
    grados = dict(conn.execute("""
        SELECT id_nodo, COUNT(*) FROM (
            SELECT origen_id AS id_nodo FROM relaciones
            UNION ALL
            SELECT destino_id AS id_nodo FROM relaciones
        ) GROUP BY id_nodo
    """).fetchall())

    candidatos = []
    for id_, tipo, nombre, desc in filas:
        desc = desc or ""
        razon = None
        if PATRONES_RUIDO.search(nombre) or PATRONES_RUIDO.search(desc):
            razon = "término médico/biológico detectado"
        elif grados.get(id_, 0) == 1 and len(desc) < 60:
            razon = "solo 1 relación y descripción muy corta (posible mención de paso)"

        if razon:
            candidatos.append({"id": id_, "tipo": tipo, "nombre": nombre, "descripcion": desc, "razon": razon, "grado": grados.get(id_, 0)})

    return candidatos


def mostrar_relaciones(conn, id_):
    filas = conn.execute("""
        SELECT r.tipo, n2.nombre, 'saliente' AS direccion
        FROM relaciones r JOIN nodos n2 ON r.destino_id = n2.id
        WHERE r.origen_id = ?
        UNION ALL
        SELECT r.tipo, n1.nombre, 'entrante' AS direccion
        FROM relaciones r JOIN nodos n1 ON r.origen_id = n1.id
        WHERE r.destino_id = ?
    """, (id_, id_)).fetchall()
    return filas


def eliminar_nodo_cascada(conn, id_):
    conn.execute("DELETE FROM relaciones WHERE origen_id = ? OR destino_id = ?", (id_, id_))
    conn.execute("DELETE FROM nodos WHERE id = ?", (id_,))
    conn.commit()


def pedir_opcion(mensaje, validas):
    while True:
        resp = input(mensaje).strip().lower()
        if resp in validas:
            return resp
        print(f"  ⚠ Opción no válida. Usa: {', '.join(sorted(validas))}")


def main():
    conn = sqlite3.connect(DB_PATH)
    estado = cargar_estado()

    candidatos = detectar_candidatos(conn)
    pendientes = [c for c in candidatos if str(c["id"]) not in estado["revisados"]]

    print("═" * 60)
    print(f"LIMPIEZA ASISTIDA — {len(candidatos)} candidatos detectados, {len(pendientes)} pendientes de revisar")
    print("═" * 60)

    if not pendientes:
        print("\n✓ No hay más candidatos pendientes de esta pasada.")
        print("  (si agregaste un libro nuevo, borra limpieza_estado.json para re-escanear todo)")
        conn.close()
        return

    for i, c in enumerate(pendientes, 1):
        print(f"\n[{i}/{len(pendientes)}] [{c['tipo']}] {c['nombre']} (id={c['id']}, grado={c['grado']})")
        print(f"  Descripción: {c['descripcion']}")
        print(f"  Razón de detección: {c['razon']}")

        relaciones = mostrar_relaciones(conn, c["id"])
        if relaciones:
            print("  Relaciones actuales:")
            for tipo, otro_nombre, direccion in relaciones:
                flecha = "→" if direccion == "saliente" else "←"
                print(f"    {flecha} {tipo} {flecha} {otro_nombre}")
        else:
            print("  (sin relaciones)")

        resp = pedir_opcion(
            "  ¿Mantener / Reclasificar / Eliminar / Saltar por ahora? (m/r/e/s): ",
            validas={"m", "r", "e", "s"},
        )

        if resp == "m":
            estado["revisados"][str(c["id"])] = {"decision": "mantenido"}
            print("  ✓ Mantenido tal cual")

        elif resp == "r":
            nuevo_tipo = pedir_opcion(
                f"  Nuevo tipo (actual: {c['tipo']}) [{'/'.join(sorted(TIPOS_VALIDOS))}]: ",
                validas=TIPOS_VALIDOS,
            )
            conn.execute("UPDATE nodos SET tipo = ? WHERE id = ?", (nuevo_tipo, c["id"]))
            conn.commit()
            estado["revisados"][str(c["id"])] = {"decision": "reclasificado", "nuevo_tipo": nuevo_tipo}
            print(f"  ✓ Reclasificado a '{nuevo_tipo}'")

        elif resp == "e":
            confirmar = pedir_opcion(
                f"  Esto borra el nodo Y sus {len(relaciones)} relación(es). ¿Confirmas? (s/n): ",
                validas={"s", "n"},
            )
            if confirmar == "s":
                eliminar_nodo_cascada(conn, c["id"])
                estado["revisados"][str(c["id"])] = {"decision": "eliminado"}
                print("  ✓ Eliminado (con sus relaciones)")
            else:
                print("  Cancelado, se deja pendiente para la próxima corrida.")
                guardar_estado(estado)
                continue

        else:
            print("  → Saltado, seguirá apareciendo en próximas corridas.")
            guardar_estado(estado)
            continue

        guardar_estado(estado)

    print("\n" + "═" * 60)
    mantenidos = sum(1 for v in estado["revisados"].values() if v["decision"] == "mantenido")
    reclasificados = sum(1 for v in estado["revisados"].values() if v["decision"] == "reclasificado")
    eliminados = sum(1 for v in estado["revisados"].values() if v["decision"] == "eliminado")
    print(f"RESUMEN: {mantenidos} mantenidos | {reclasificados} reclasificados | {eliminados} eliminados")
    print("═" * 60)
    conn.close()
    print("\n◈ Corre: cd .. && python scripts/export_json.py")


if __name__ == "__main__":
    main()
