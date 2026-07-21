"""
Migración: normalizar tipos de relación en la DB.

Elimina aliases incorrectos y normaliza los que se mantienen.
Incluye backup automático y rollback si falla.

Uso: python scripts/migrate_relacion_types.py
"""
import sqlite3
import shutil
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "grafo.db"
BAK_PATH = DB_PATH.with_suffix(".db.bak")

# Aliases que SÍ se mantienen (sinónimos reales)
# Solo normalizamos los que aparecen en la DB y deben convertirse
ALIASES_A_NORMALIZAR = {
    "influyó_en": "influenciado_por",
    "influye_en": "influenciado_por",
    "influencio_a": "influenciado_por",
    "estudio": "estudia_a",
    "escribe_estudio_preliminar_para": "estudia_a",
    "describe_a": "estudia_a",
    "ejemplifica_con": "desarrolla_concepto",
    "ejemplo_de": "desarrolla_concepto",
    "ejemplo_en": "desarrolla_concepto",
    "ejemplificado_por": "desarrolla_concepto",
    "practica_concepto": "desarrolla_concepto",
    "promueve_concepto": "desarrolla_concepto",
    "incorpora_concepto": "desarrolla_concepto",
    "discute_concepto": "desarrolla_concepto",
    "estudia_concepto": "desarrolla_concepto",
    "sostiene_teoria": "desarrolla_concepto",
    "defiende": "desarrolla_concepto",
    "refuta": "critica_a",
    "lucha_contra": "critica_a",
    "opuesto_a": "critica_a",
    "contrasta_con": "critica_a",
    "malinterpreta_a": "critica_a",
    "subestima_concepto": "critica_a",
    "manipula_concepto": "critica_a",
    "es_fuente_sobre": "estudia_a",
    "cita_a": "estudia_a",
    "localizado_en": "pertenece_a",
    "ubica_en": "pertenece_a",
    "incluye_a": "pertenece_a",
    "realiza_trabajo_de_campo_en": "estudia_a",
    "migra_a": "pertenece_a",
    "prologa_obra": "pertenece_a",
    "traduce_obra": "pertenece_a",
    "publicado_como_traduccion": "pertenece_a",
    "publica": "pertenece_a",
    "origen_de": "precursor_de",
    "facilito_por": "influenciado_por",
    "expandida_en": "pertenece_a",
    "evalua_contribucion_de": "estudia_a",
    "dirige_publicacion": "pertenece_a",
    "difundido_en": "pertenece_a",
    "dedica_obra_a": "pertenece_a",
    "condiciona": "influenciado_por",
    "atribuye_origen_a": "precursor_de",
    "es_respuesta_a": "critica_a",
    "es_tipo_de": "pertenece_a",
    "trata_de": "desarrolla_concepto",
}

# Tipos que NO se tocan (quedan como están en la DB)
# autor_de, colabora_con, es_mentor_de, clasifica_como_activo, etc.


def migrate():
    if not DB_PATH.exists():
        print(f"ERROR: No se encontró {DB_PATH}")
        return

    # Backup
    shutil.copy2(DB_PATH, BAK_PATH)
    print(f"Backup creado: {BAK_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    # Contar ANTES
    total_antes = conn.execute("SELECT COUNT(*) FROM relaciones").fetchone()[0]
    tipos_antes = dict(conn.execute("SELECT tipo, COUNT(*) FROM relaciones GROUP BY tipo").fetchall())
    print(f"\nANTES: {total_antes} relaciones, {len(tipos_antes)} tipos distintos")

    try:
        # Normalizar cada alias
        normalizadas = 0
        for alias, canonical in ALIASES_A_NORMALIZAR.items():
            count = conn.execute(
                "SELECT COUNT(*) FROM relaciones WHERE tipo = ?", (alias,)
            ).fetchone()[0]
            if count > 0:
                conn.execute(
                    "UPDATE relaciones SET tipo = ? WHERE tipo = ?",
                    (canonical, alias)
                )
                normalizadas += count
                print(f"  {alias} -> {canonical}: {count} relaciones")

        conn.commit()

        # Contar DESPUÉS
        total_despues = conn.execute("SELECT COUNT(*) FROM relaciones").fetchone()[0]
        tipos_despues = dict(conn.execute("SELECT tipo, COUNT(*) FROM relaciones GROUP BY tipo").fetchall())

        print(f"\nDESPUÉS: {total_despues} relaciones, {len(tipos_despues)} tipos distintos")
        print(f"Normalizadas: {normalizadas} relaciones")

        # Verificar integridad
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        assert integrity == "ok", f"Integridad falló: {integrity}"
        assert total_despues == total_antes, f"Conteo cambió: {total_antes} -> {total_despues}"

        print(f"\nIntegridad: {integrity}")
        print("Migración exitosa!")

    except Exception as e:
        conn.rollback()
        print(f"\nERROR: {e}")
        print("Rollback ejecutado. La DB se restauró.")
        # Restaurar desde backup
        conn.close()
        shutil.copy2(BAK_PATH, DB_PATH)
        print("DB restaurada desde backup.")
        return

    conn.close()


if __name__ == "__main__":
    migrate()
