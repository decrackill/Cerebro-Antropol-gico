"""
Auditoría del grafo: integridad referencial, cobertura de páginas por libro,
estadísticas, duplicados (ahora comparados solo dentro del mismo tipo de nodo),
nodos aislados nombrados, distribución de tipos de relación, y tasa de pérdida
de relaciones a través de todos los archivos de candidatos procesados.

Uso: python auditoria.py
"""
import json
import re
import sqlite3
from pathlib import Path
from difflib import SequenceMatcher
from collections import defaultdict, Counter

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR.parent / "data" / "grafo.db"
CANDIDATOS_PATH = BASE_DIR / "candidatos_pendientes.json"
ESTADO_PATH = BASE_DIR / "revision_estado.json"

UMBRAL_SIMILITUD = 0.80


def similitud(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def auditar_progreso_pendiente():
    print("═" * 60)
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
        print("  ✓ Revisión completa.")


def auditar_estadisticas(conn):
    print("\n" + "═" * 60)
    print("ESTADÍSTICAS GENERALES DE LA DB")
    print("═" * 60)
    filas = conn.execute("SELECT tipo, COUNT(*) FROM nodos GROUP BY tipo").fetchall()
    total = sum(c for _, c in filas)
    for tipo, c in sorted(filas):
        print(f"  {tipo:12s} {c:4d}")
    print(f"  {'TOTAL':12s} {total:4d}")

    total_rel = conn.execute("SELECT COUNT(*) FROM relaciones").fetchone()[0]
    print(f"\n  Relaciones totales: {total_rel}")

    print("\n  Distribución por tipo de relación:")
    tipos_rel = conn.execute(
        "SELECT tipo, COUNT(*) FROM relaciones GROUP BY tipo ORDER BY COUNT(*) DESC"
    ).fetchall()
    for tipo, c in tipos_rel:
        print(f"    {tipo:25s} {c:4d}")

    if total > 0:
        promedio_grado = (total_rel * 2) / total
        print(f"\n  Grado promedio por nodo (conexiones): {promedio_grado:.2f}")


def auditar_integridad_referencial(conn):
    print("\n" + "═" * 60)
    print("INTEGRIDAD REFERENCIAL (relaciones apuntando a nodos inexistentes)")
    print("═" * 60)
    ids_validos = {row[0] for row in conn.execute("SELECT id FROM nodos")}
    rotas = conn.execute("SELECT id, origen_id, destino_id, tipo FROM relaciones").fetchall()
    encontradas = 0
    for rel_id, origen, destino, tipo in rotas:
        if origen not in ids_validos or destino not in ids_validos:
            encontradas += 1
            print(f"  ⚠ Relación id={rel_id} ({tipo}) rota: origen={origen}, destino={destino}")
    if encontradas == 0:
        print("  ✓ Todas las relaciones apuntan a nodos existentes")
    else:
        print(f"\n  Total de relaciones rotas: {encontradas} — bórralas o corrige manualmente.")


def auditar_nodos_aislados(conn):
    print("\n" + "═" * 60)
    print("NODOS SIN NINGUNA RELACIÓN (aislados)")
    print("═" * 60)
    filas = conn.execute("""
        SELECT id, tipo, nombre FROM nodos
        WHERE id NOT IN (SELECT origen_id FROM relaciones)
          AND id NOT IN (SELECT destino_id FROM relaciones)
        ORDER BY tipo, nombre
    """).fetchall()

    if not filas:
        print("  ✓ No hay nodos aislados — todo el grafo está conectado")
        return

    print(f"  {len(filas)} nodo(s) aislado(s):\n")
    por_tipo = defaultdict(list)
    for id_, tipo, nombre in filas:
        por_tipo[tipo].append((id_, nombre))
    for tipo, items in por_tipo.items():
        print(f"  [{tipo}]")
        for id_, nombre in items:
            print(f"    id={id_:4d}  {nombre}")


def auditar_cobertura_libros(conn):
    print("\n" + "═" * 60)
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


def auditar_duplicados_por_tipo(conn):
    print("\n" + "═" * 60)
    print(f"ESCANEO DE DUPLICADOS (comparando SOLO dentro del mismo tipo, umbral {UMBRAL_SIMILITUD})")
    print("═" * 60)
    filas = conn.execute("SELECT id, tipo, nombre FROM nodos ORDER BY tipo, id").fetchall()
    por_tipo = defaultdict(list)
    for id_, tipo, nombre in filas:
        por_tipo[tipo].append((id_, nombre))

    encontrados = 0
    for tipo, items in por_tipo.items():
        ya_reportado = set()
        for i, (id_a, nombre_a) in enumerate(items):
            if nombre_a in ya_reportado:
                continue
            sospechosos = []
            for id_b, nombre_b in items[i + 1:]:
                s = similitud(nombre_a, nombre_b)
                if s >= UMBRAL_SIMILITUD:
                    sospechosos.append((nombre_b, id_b, s))
            if sospechosos:
                encontrados += 1
                print(f"\n  ⚠ [{tipo}] '{nombre_a}' (id={id_a}) se parece a:")
                for nombre_b, id_b, s in sospechosos:
                    print(f"      - '{nombre_b}' (id={id_b}), similitud={s:.2f}")
                ya_reportado.add(nombre_a)
                ya_reportado.update(n for n, _, _ in sospechosos)

    if encontrados == 0:
        print("  ✓ No se detectaron duplicados obvios dentro de cada tipo")
    else:
        print(f"\n  Total de grupos sospechosos: {encontrados}")
        print("  (misma tipo + alta similitud de texto — aun así revisa manualmente,")
        print("   términos antónimos como 'Endocanibalismo'/'Exocanibalismo' pueden salir")
        print("   aquí por parecido textual sin ser duplicados reales)")


def auditar_tasa_perdida_relaciones():
    print("\n" + "═" * 60)
    print("TASA DE PÉRDIDA DE RELACIONES (across archivos candidatos_procesados_*.json)")
    print("═" * 60)
    archivos = sorted(BASE_DIR.glob("candidatos_procesados_*.json"))
    if not archivos:
        print("  (no hay archivos candidatos_procesados_*.json todavía)")
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
    conn.close()

    total_rels = 0
    no_resolubles = 0
    for archivo in archivos:
        datos = json.loads(archivo.read_text(encoding="utf-8"))
        rels = datos.get("relaciones_nuevas", [])
        total_rels += len(rels)
        for r in rels:
            origen = r["origen"]
            destino = r["destino"]

            def resuelto(ref):
                if isinstance(ref, int):
                    return ref in ids_validos
                if isinstance(ref, str) and ref.strip().isdigit():
                    return int(ref.strip()) in ids_validos
                return ref in mapa_snake

            if not resuelto(origen) or not resuelto(destino):
                no_resolubles += 1

    if total_rels == 0:
        print("  (sin relaciones candidatas en el histórico)")
        return

    tasa = (no_resolubles / total_rels) * 100
    print(f"  Relaciones candidatas históricas: {total_rels}")
    print(f"  Actualmente NO resolubles (nodo destino/origen inexistente): {no_resolubles} ({tasa:.1f}%)")
    if no_resolubles > 0:
        print("  ◈ Corre 'python recuperar_relaciones.py' para intentar rescatar las resolubles.")


def main():
    conn = sqlite3.connect(DB_PATH)
    auditar_progreso_pendiente()
    auditar_estadisticas(conn)
    auditar_integridad_referencial(conn)
    auditar_nodos_aislados(conn)
    auditar_cobertura_libros(conn)
    auditar_duplicados_por_tipo(conn)
    conn.close()
    auditar_tasa_perdida_relaciones()


if __name__ == "__main__":
    main()
