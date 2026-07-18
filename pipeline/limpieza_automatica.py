"""
Limpieza automática con reglas seguras (sin preguntar), y reporte de lo
ambiguo para revisar manualmente después. Reglas aplicadas SIN preguntar:

1. FUSIÓN AUTOMÁTICA: dos nodos del mismo tipo, similares, donde uno de los
   dos nombres está CONTENIDO dentro del otro (ej. "Nyström" dentro de
   "Anton Nyström") Y el nodo del nombre corto tiene 0 relaciones. Se fusiona
   sin preguntar porque es un caso técnicamente inequívoco: alguien resolvió
   mal el nombre completo antes.

2. ELIMINACIÓN AUTOMÁTICA DE RUIDO: nodo con 0 relaciones Y coincide con el
   patrón de vocabulario médico/biológico/antropología física puntual.

Todo lo demás (aislados sin patrón claro, duplicados sin containment) se
deja en un reporte aparte para limpieza_asistida.py.

Uso: python limpieza_automatica.py            (dry-run por defecto, no toca nada)
     python limpieza_automatica.py --aplicar   (ejecuta los cambios de verdad)
"""
import re
import sqlite3
import sys
from pathlib import Path
from difflib import SequenceMatcher

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR.parent / "data" / "grafo.db"
UMBRAL = 0.80

# Pares que contienen subcadena pero son conceptos distintos — nunca fusionar
EXCLUSIONES_FUSION = {
    frozenset({236, 67}),    # América ≠ Norteamérica
    frozenset({236, 233}),   # América ≠ América Central
    frozenset({243, 69}),    # Australianos ≠ Aborígenes australianos
    frozenset({230, 317}),   # Japoneses ≠ Japoneses de Hawái
}

PATRONES_RUIDO = re.compile(
    r"(cr[aá]neo|cef[aá]lic|torus|osteo|esquelet|patolog[ií]a|anatom[ií]a|"
    r"medici[oó]n corporal|antropometr[ií]a|índice cef[aá]lico|"
    r"malformaci[oó]n|enfermedad|hueso|dentici[oó]n|estatura promedio|"
    r"pigmentaci[oó]n|coeficiente craneal|prognatismo|distribuci[oó]n de variables)",
    re.IGNORECASE,
)


def similitud(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def normalizar(nombre):
    return re.sub(r"[^\wáéíóúñ ]", "", nombre.lower()).strip()


def cargar_datos(conn):
    filas = conn.execute("SELECT id, tipo, nombre, descripcion FROM nodos ORDER BY tipo, id").fetchall()
    grados = dict(conn.execute("""
        SELECT id_nodo, COUNT(*) FROM (
            SELECT origen_id AS id_nodo FROM relaciones
            UNION ALL SELECT destino_id AS id_nodo FROM relaciones
        ) GROUP BY id_nodo
    """).fetchall())
    return filas, grados


def detectar_fusiones_seguras(filas, grados):
    """Nombre corto CONTENIDO en nombre largo, mismo tipo, el corto con 0 relaciones."""
    por_tipo = {}
    for id_, tipo, nombre, desc in filas:
        por_tipo.setdefault(tipo, []).append((id_, nombre, desc))

    fusiones = []
    ya_usados = set()

    for tipo, items in por_tipo.items():
        for id_a, nombre_a, _ in items:
            if id_a in ya_usados:
                continue
            norm_a = normalizar(nombre_a)
            for id_b, nombre_b, _ in items:
                if id_b == id_a or id_b in ya_usados:
                    continue
                norm_b = normalizar(nombre_b)
                if norm_a == norm_b:
                    continue

                if frozenset({id_a, id_b}) in EXCLUSIONES_FUSION:
                    continue

                corto_contenido_en_largo = norm_a in norm_b or norm_b in norm_a
                if not corto_contenido_en_largo:
                    continue
                if similitud(nombre_a, nombre_b) < 0.5:
                    continue

                grado_a, grado_b = grados.get(id_a, 0), grados.get(id_b, 0)
                if len(norm_a) < len(norm_b) and grado_a == 0:
                    fusiones.append({"mantener": (id_b, nombre_b), "eliminar": (id_a, nombre_a)})
                    ya_usados.add(id_a)
                elif len(norm_b) < len(norm_a) and grado_b == 0:
                    fusiones.append({"mantener": (id_a, nombre_a), "eliminar": (id_b, nombre_b)})
                    ya_usados.add(id_b)

    return fusiones


def detectar_ruido_eliminable(filas, grados):
    eliminables = []
    for id_, tipo, nombre, desc in filas:
        desc = desc or ""
        if grados.get(id_, 0) == 0 and (PATRONES_RUIDO.search(nombre) or PATRONES_RUIDO.search(desc)):
            eliminables.append((id_, tipo, nombre, desc))
    return eliminables


def detectar_ambiguos(filas, grados, ids_ya_resueltos):
    """Todo lo demás que sigue aislado o duplicado sin regla clara -> para revisar a mano."""
    aislados_restantes = [
        (id_, tipo, nombre) for id_, tipo, nombre, _ in filas
        if grados.get(id_, 0) == 0 and id_ not in ids_ya_resueltos
    ]
    return aislados_restantes


def fusionar(conn, id_mantener, id_borrar):
    conn.execute("UPDATE relaciones SET origen_id = ? WHERE origen_id = ?", (id_mantener, id_borrar))
    conn.execute("UPDATE relaciones SET destino_id = ? WHERE destino_id = ?", (id_mantener, id_borrar))
    conn.execute("""
        DELETE FROM relaciones WHERE id NOT IN (
            SELECT MIN(id) FROM relaciones GROUP BY origen_id, destino_id, tipo
        )
    """)
    conn.execute("DELETE FROM nodos WHERE id = ?", (id_borrar,))


def eliminar(conn, id_):
    conn.execute("DELETE FROM relaciones WHERE origen_id = ? OR destino_id = ?", (id_, id_))
    conn.execute("DELETE FROM nodos WHERE id = ?", (id_,))


def main():
    aplicar = "--aplicar" in sys.argv
    conn = sqlite3.connect(DB_PATH)
    filas, grados = cargar_datos(conn)

    fusiones = detectar_fusiones_seguras(filas, grados)
    ruido = detectar_ruido_eliminable(filas, grados)

    ids_resueltos = {f["eliminar"][0] for f in fusiones} | {r[0] for r in ruido}
    ambiguos = detectar_ambiguos(filas, grados, ids_resueltos)

    print("═" * 60)
    print(f"LIMPIEZA AUTOMÁTICA {'— APLICANDO CAMBIOS' if aplicar else '— DRY RUN (nada se modifica)'}")
    print("═" * 60)

    print(f"\n◈ FUSIONES AUTOMÁTICAS SEGURAS: {len(fusiones)}")
    for f in fusiones:
        print(f"    '{f['eliminar'][1]}' (id={f['eliminar'][0]}) → fusionado en → '{f['mantener'][1]}' (id={f['mantener'][0]})")
        if aplicar:
            fusionar(conn, f["mantener"][0], f["eliminar"][0])

    print(f"\n◈ ELIMINACIONES AUTOMÁTICAS (ruido, 0 relaciones): {len(ruido)}")
    for id_, tipo, nombre, desc in ruido:
        print(f"    [{tipo}] '{nombre}' (id={id_}) — {desc[:70]}")
        if aplicar:
            eliminar(conn, id_)

    if aplicar:
        conn.commit()

    print(f"\n◈ AISLADOS SIN REGLA CLARA (necesitan tu criterio, quedan para limpieza_asistida.py): {len(ambiguos)}")
    por_tipo_ambiguo = {}
    for id_, tipo, nombre in ambiguos:
        por_tipo_ambiguo.setdefault(tipo, []).append((id_, nombre))
    for tipo, items in por_tipo_ambiguo.items():
        print(f"\n  [{tipo}]")
        for id_, nombre in items:
            print(f"    id={id_:4d}  {nombre}")

    conn.close()

    print("\n" + "═" * 60)
    if not aplicar:
        print("Esto fue una SIMULACIÓN. Para aplicar de verdad:")
        print("  python3 limpieza_automatica.py --aplicar")
    else:
        print(f"✓ Aplicado: {len(fusiones)} fusiones + {len(ruido)} eliminaciones")
        print("◈ Corre: cd .. && python scripts/export_json.py")
        print(f"◈ Quedan {len(ambiguos)} nodos aislados que sí necesitan tu decisión — corre limpieza_asistida.py")


if __name__ == "__main__":
    main()
