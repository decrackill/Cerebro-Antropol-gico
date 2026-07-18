"""
Limpieza automática del grafo: elimina nodos que probablemente sean "ruido"
usando heurísticas automáticas sin intervención del usuario.

Criterios de eliminación:
1. Términos médicos/biológicos/técnicos alejados del núcleo antropológico
2. Nodos con 1 relación y descripción muy corta (< 60 caracteres)

Uso: python limpiar_auto.py
"""
import sqlite3
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR.parent / "data" / "grafo.db"

PATRONES_RUIDO = re.compile(
    r"(cr[aá]neo|cef[aá]lic|torus|osteo|esquelet|patolog[ií]a|anatom[ií]a|"
    r"medici[oó]n corporal|antropometr[ií]a|índice cef[aá]lico|"
    r"malformaci[oó]n|enfermedad|hueso|dentici[oó]n|estatura promedio|"
    r"pigmentaci[oó]n|coeficiente craneal)",
    re.IGNORECASE,
)


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
            razon = "solo 1 relación y descripción muy corta"

        if razon:
            candidatos.append({
                "id": id_,
                "tipo": tipo,
                "nombre": nombre,
                "descripcion": desc,
                "razon": razon,
                "grado": grados.get(id_, 0)
            })

    return candidatos


def eliminar_nodo_cascada(conn, id_):
    conn.execute("DELETE FROM relaciones WHERE origen_id = ? OR destino_id = ?", (id_, id_))
    conn.execute("DELETE FROM nodos WHERE id = ?", (id_,))
    conn.commit()


def main():
    conn = sqlite3.connect(DB_PATH)
    candidatos = detectar_candidatos(conn)

    print("═" * 60)
    print(f"LIMPIEZA AUTOMÁTICA — {len(candidatos)} candidatos detectados")
    print("═" * 60)

    eliminados = 0
    for c in candidatos:
        print(f"  - [{c['tipo']}] {c['nombre']} (id={c['id']}, grado={c['grado']}): {c['razon']}")
        eliminar_nodo_cascada(conn, c["id"])
        eliminados += 1

    conn.close()

    print("\n" + "═" * 60)
    print(f"RESUMEN: {eliminados} nodos eliminados")
    print("═" * 60)
    print("\n◈ Corre: python3 verificar_extraccion.py boas-f-1911-cuestiones-fundamentales-de-antropologia-cultural")


if __name__ == "__main__":
    main()
