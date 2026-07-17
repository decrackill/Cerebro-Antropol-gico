"""
Limpieza post-revisión: verifica que no quede nada pendiente y, si todo está
en orden, borra los archivos intermedios que ya cumplieron su función
(candidatos_procesados_*.json, logs de extracción ya verificados,
revision_estado.json huérfano). Si algo sigue pendiente, AVISA y no borra nada.

Uso: python limpiar.py
Opcional: python limpiar.py --forzar   (borra aunque haya advertencias, con confirmación extra)
"""
import json
import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR.parent / "data" / "grafo.db"
CANDIDATOS_PATH = BASE_DIR / "candidatos_pendientes.json"
ESTADO_PATH = BASE_DIR / "revision_estado.json"


def verificar_bloqueos():
    bloqueos = []

    if CANDIDATOS_PATH.exists():
        candidatos = json.loads(CANDIDATOS_PATH.read_text(encoding="utf-8"))
        total_nodos = len(candidatos.get("nodos_nuevos", []))
        total_rels = len(candidatos.get("relaciones_nuevas", []))
        bloqueos.append(
            f"Existe candidatos_pendientes.json sin archivar "
            f"({total_nodos} nodos, {total_rels} relaciones) — corre revisar.py primero."
        )

    if ESTADO_PATH.exists():
        estado = json.loads(ESTADO_PATH.read_text(encoding="utf-8"))
        nodos_hechos = len(estado.get("nodos_revisados", {}))
        rels_hechas = len(estado.get("relaciones_revisadas", []))
        bloqueos.append(
            f"Existe revision_estado.json con progreso a medias "
            f"({nodos_hechos} nodos, {rels_hechas} relaciones revisadas) — "
            f"esto no debería pasar si candidatos_pendientes.json no existe; revisa manualmente."
        )

    for log_path in BASE_DIR.glob("extraccion_log_*.json"):
        log = json.loads(log_path.read_text(encoding="utf-8"))
        if log.get("chunks_con_error"):
            bloqueos.append(
                f"{log_path.name} tiene {len(log['chunks_con_error'])} chunk(s) con error "
                f"sin resolver — corre verificar_extraccion.py {log_path.stem.replace('extraccion_log_', '')} primero."
            )

    if DB_PATH.exists():
        conn = sqlite3.connect(DB_PATH)
        rotas = conn.execute("SELECT COUNT(*) FROM relaciones WHERE origen_id NOT IN (SELECT id FROM nodos) OR destino_id NOT IN (SELECT id FROM nodos)").fetchone()[0]
        conn.close()
        if rotas > 0:
            bloqueos.append(f"Hay {rotas} relación(es) apuntando a nodos inexistentes en la DB — corre auditoria.py.")

    return bloqueos


def archivos_a_limpiar():
    candidatos = list(BASE_DIR.glob("candidatos_procesados_*.json"))
    logs_ok = []
    for log_path in BASE_DIR.glob("extraccion_log_*.json"):
        log = json.loads(log_path.read_text(encoding="utf-8"))
        if not log.get("chunks_con_error"):
            logs_ok.append(log_path)
    return candidatos, logs_ok


def main():
    forzar = "--forzar" in sys.argv

    print("═" * 60)
    print("LIMPIEZA DEL PIPELINE")
    print("═" * 60)

    bloqueos = verificar_bloqueos()
    if bloqueos and not forzar:
        print("\n⚠ NO se limpiará nada — hay cosas pendientes:\n")
        for b in bloqueos:
            print(f"  - {b}")
        print("\nResuelve esto primero, o corre 'python limpiar.py --forzar' si sabes lo que haces.")
        return

    if bloqueos and forzar:
        print("\n⚠ Advertencias detectadas, pero --forzar está activo:\n")
        for b in bloqueos:
            print(f"  - {b}")
        resp = input("\n¿Seguro que quieres limpiar de todos modos? (escribe 'si' para confirmar): ").strip().lower()
        if resp != "si":
            print("Cancelado. No se borró nada.")
            return

    candidatos, logs_ok = archivos_a_limpiar()

    if not candidatos and not logs_ok:
        print("\n✓ No hay nada que limpiar — el pipeline ya está en estado limpio.")
        return

    print(f"\nSe van a borrar {len(candidatos)} archivo(s) de candidatos archivados")
    print(f"y {len(logs_ok)} log(s) de extracción ya verificados sin errores:\n")
    for f in candidatos + logs_ok:
        print(f"  - {f.name}")

    resp = input("\n¿Confirmas el borrado? (s/n): ").strip().lower()
    if resp != "s":
        print("Cancelado. No se borró nada.")
        return

    for f in candidatos + logs_ok:
        f.unlink()

    print(f"\n✓ Limpieza completa. {len(candidatos) + len(logs_ok)} archivo(s) eliminado(s).")
    print("  Los PDFs en libros/ y la base de datos NO se tocaron (nunca se borran automáticamente).")


if __name__ == "__main__":
    main()
