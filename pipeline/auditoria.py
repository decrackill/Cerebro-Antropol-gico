"""
Auditoría del grafo: cobertura de páginas procesadas por libro,
estadísticas por tipo de nodo, y escaneo de posibles duplicados
en TODA la base de datos (no solo en la revisión en curso).

Uso: python auditoria.py
"""
import json
import re
import sqlite3
from pathlib import Path
from difflib import get_close_matches
from collections import defaultdict

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR.parent / "data" / "grafo.db"
CANDIDATOS_PATH = BASE_DIR / "candidatos_pendientes.json"
ESTADO_PATH = BASE_DIR / "revision_estado.json"

UMBRAL_SIMILITUD = 0.75


def auditar_cobertura_libros(conn):
    print("═" * 60)
    print("COBERTURA DE PÁGINAS POR LIBRO (según relaciones con 'fuente')")
    print("═" * 60)
    filas = conn.execute("SELECT fuente FROM relaciones WHERE fuente IS NOT NULL").fetchall()
    por_libro = defaultdict(set)
    patron = re.compile(r"^(.*), p\.(\d+)-(\d+)$")

    for (fuente,) in filas:
        m = patron.match(fuente or "")
        if not m:
            continue
        libro, pi, pf = m.group(1), int(m.group(2)), int(m.group(3))
        por_libro[libro].update(range(pi, pf + 1))

    if not por_libro:
        print("  (sin relaciones con fuente registrada todavía)")
        return

    for libro, paginas in por_libro.items():
        pi, pf = min(paginas), max(paginas)
        rango_total = set(range(pi, pf + 1))
        faltantes = sorted(rango_total - paginas)
        print(f"\n  {libro}")
        print(f"    Páginas con al menos una relación citada: {len(paginas)} (rango {pi}-{pf})")
        if faltantes:
            print(f"    ⚠ Páginas dentro del rango SIN ninguna relación citada: {faltantes[:30]}"
                  + (" ..." if len(faltantes) > 30 else ""))
        else:
            print("    ✓ Todo el rango tiene al menos una relación citada")


def auditar_estadisticas(conn):
    print("\n" + "═" * 60)
    print("ESTADÍSTICAS GENERALES DE LA DB")
    print("═" * 60)
    filas = conn.execute("SELECT tipo, COUNT(*) FROM nodos GROUP BY tipo").fetchall()
    total = sum(c for _, c in filas)
    for tipo, c in filas:
        print(f"  {tipo:12s} {c:4d}")
    print(f"  {'TOTAL':12s} {total:4d}")
    total_rel = conn.execute("SELECT COUNT(*) FROM relaciones").fetchone()[0]
    print(f"\n  Relaciones totales: {total_rel}")


def auditar_duplicados_globales(conn):
    print("\n" + "═" * 60)
    print("ESCANEO DE POSIBLES DUPLICADOS EN TODA LA DB")
    print("═" * 60)
    filas = conn.execute("SELECT id, nombre FROM nodos ORDER BY id").fetchall()
    nombres = [nombre for _, nombre in filas]
    ya_reportado = set()
    encontrados = 0

    for id_, nombre in filas:
        if nombre in ya_reportado:
            continue
        similares = get_close_matches(nombre, [n for n in nombres if n != nombre], n=3, cutoff=UMBRAL_SIMILITUD)
        if similares:
            encontrados += 1
            print(f"\n  ⚠ '{nombre}' (id={id_}) se parece a: {', '.join(similares)}")
            ya_reportado.add(nombre)
            ya_reportado.update(similares)

    if encontrados == 0:
        print("  ✓ No se detectaron duplicados obvios por similitud de nombre")
    else:
        print(f"\n  Total de grupos sospechosos: {encontrados}")
        print("  (revisa manualmente — la similitud de texto no siempre implica duplicado real)")


def auditar_progreso_pendiente():
    print("\n" + "═" * 60)
    print("PROGRESO DE REVISIÓN PENDIENTE")
    print("═" * 60)
    if not CANDIDATOS_PATH.exists():
        print("  No hay candidatos_pendientes.json — nada pendiente de revisar.")
        return

    candidatos = json.loads(CANDIDATOS_PATH.read_text(encoding="utf-8"))
    total_nodos = len(candidatos.get("nodos_nuevos", []))
    total_rels = len(candidatos.get("relaciones_nuevas", []))

    estado = {"nodos_revisados": {}, "relaciones_revisadas": []}
    if ESTADO_PATH.exists():
        estado = json.loads(ESTADO_PATH.read_text(encoding="utf-8"))

    nodos_hechos = len(estado["nodos_revisados"])
    rels_hechas = len(estado["relaciones_revisadas"])

    print(f"  Nodos:      {nodos_hechos}/{total_nodos} revisados")
    print(f"  Relaciones: {rels_hechas}/{total_rels} revisadas")
    if nodos_hechos < total_nodos or rels_hechas < total_rels:
        print("  ◈ Corre 'python revisar.py' para continuar donde quedaste.")
    else:
        print("  ✓ Revisión completa — corre export_json.py si aún no lo hiciste.")


def main():
    conn = sqlite3.connect(DB_PATH)
    auditar_progreso_pendiente()
    auditar_estadisticas(conn)
    auditar_cobertura_libros(conn)
    auditar_duplicados_globales(conn)
    conn.close()


if __name__ == "__main__":
    main()
