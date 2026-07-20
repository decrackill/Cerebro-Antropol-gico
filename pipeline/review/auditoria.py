"""Herramientas de diagnóstico (Fase 3).

Función de auditoría completa de la base de datos.
"""
import json
import logging
import re
from collections import defaultdict

from ..core.config import (
    CANDIDATOS_PATH, REVISION_ESTADO_PATH,
    UMBRAL_SIMILITUD, TIPOS_VALIDOS_NODO,
)
from ..core.db import conectar_db
from ..core.utils import similitud, es_exclusion_fusion

logger = logging.getLogger("cerebro.auditoria")


def herramienta_auditoria():
    """
    Diagnóstico completo, no cambia nada: progreso de revisión pendiente,
    estadísticas por tipo de nodo y de relación, integridad referencial
    (relaciones apuntando a nodos inexistentes), nodos aislados agrupados
    por tipo, cobertura de páginas por libro (según el campo 'fuente' de
    las relaciones), y duplicados sospechosos por similitud de nombre
    dentro de cada tipo.
    """
    conn = conectar_db()

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
                if es_exclusion_fusion(nombre_a, nombre_b):
                    continue
                s = similitud(nombre_a, nombre_b)
                if s >= UMBRAL_SIMILITUD:
                    print(f"  ⚠ [{tipo}] '{nombre_a}' ↔ '{nombre_b}' ({s:.2f})")
                    encontrados += 1
    if encontrados == 0:
        print("  ✓ Sin duplicados obvios")

    conn.close()
