#!/usr/bin/env python3
"""
Migración Ontológica v1.1 — Cerebro Antropológico

Script de migración seguro, auditable, reproducible e idempotent.
Convierte tipos de relación no canónicos a los 12 tipos canónicos
definidos en MANIFIESTO_ONTOLOGICO.md v1.1.

Uso:
    python3 scripts/migrate_v1_1.py --dry-run          # Análisis sin cambios
    python3 scripts/migrate_v1_1.py --apply             # Ejecutar migración
    python3 scripts/migrate_v1_1.py --report            # Generar informe
    python3 scripts/migrate_v1_1.py --dry-run --report  # Análisis + informe

Autoridad: MANIFIESTO_ONTOLOGICO.md v1.1
"""
import sqlite3
import shutil
import json
import time
import argparse
from pathlib import Path
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════
# TABLA DE MIGRACIÓN — Fuente única de verdad
# ═══════════════════════════════════════════════════════════════════════════
#
# Cada entrada define una regla de migración.
# Tipos de migración:
#   "auto"     — Ejecutar automáticamente (sinónimos lingüísticos claros)
#   "revision" — Requiere verificación antes de aplicar
#   "mantener" — No migrar, conservar como está
#   "escalar"  — Escalar al Autor para decisión ontológica
#
# Campos:
#   original        — Tipo de relación en la DB
#   destino         — Tipo canónico destino (None si no se migra)
#   invertir        — True si se debe invertir origen↔destino
#   justificacion   — Razón semántica de la migración
#   confianza       — Alta/Media/Baja
#   tipo_migracion  — auto/revision/mantener/escalar
#   ejemplo         — Ejemplo real extraído de la DB
# ═══════════════════════════════════════════════════════════════════════════

TABLA_MIGRACION = [
    # ── MIGRACIÓN AUTOMÁTICA (sinónimos lingüísticos) ──────────────────────
    
    # autor_de
    {
        "original": "escribió",
        "destino": "autor_de",
        "invertir": False,
        "justificacion": "Sinónimo directo. 'Escribir una obra' = ser autor de ella.",
        "confianza": "Alta",
        "tipo_migracion": "auto",
        "ejemplo": "Lévi-Strauss escribió Tristes Trópicos → autor_de",
    },
    {
        "original": "es_autor_de",
        "destino": "autor_de",
        "invertir": False,
        "justificacion": "Variante con prefijo 'es_'. Mismo significado.",
        "confianza": "Alta",
        "tipo_migracion": "auto",
        "ejemplo": "Boas es_autor_de Cuestiones fundamentales → autor_de",
    },
    
    # es_mentor_de
    {
        "original": "mentor_de",
        "destino": "es_mentor_de",
        "invertir": False,
        "justificacion": "Variante sin 'es_'. Mismo significado de linaje pedagógico.",
        "confianza": "Alta",
        "tipo_migracion": "auto",
        "ejemplo": "Seligman mentor_de Malinowski → es_mentor_de",
    },
    {
        "original": "es_discípulo_de",
        "destino": "es_mentor_de",
        "invertir": True,
        "justificacion": "Relación inversa. 'A es discípulo de B' = 'B es mentor de A'.",
        "confianza": "Alta",
        "tipo_migracion": "auto",
        "ejemplo": "Lowie es_discípulo_de Boas → Boas es_mentor_de Lowie",
    },
    
    # colabora_con
    {
        "original": "colaboro_con",
        "destino": "colabora_con",
        "invertir": False,
        "justificacion": "Variante conjugada. 'Colaboró con' = 'colabora con'.",
        "confianza": "Alta",
        "tipo_migracion": "auto",
        "ejemplo": "Combe colaboro_con Morton → colabora_con",
    },
    
    # critica_a
    {
        "original": "defiende_superioridad_de",
        "destino": "critica_a",
        "invertir": False,
        "justificacion": "Defender superioridad implica oposición a otras posiciones.",
        "confianza": "Media",
        "tipo_migracion": "auto",
        "ejemplo": "Gobineau defiende_superioridad_de Europeo noroccidental → critica_a",
    },
    {
        "original": "refuta",
        "destino": "critica_a",
        "invertir": False,
        "justificacion": "Refutar es una forma directa de criticar. Sinónimo claro.",
        "confianza": "Alta",
        "tipo_migracion": "auto",
        "ejemplo": "A refuta B → A critica_a B",
    },
    {
        "original": "lucha_contra",
        "destino": "critica_a",
        "invertir": False,
        "justificacion": "Luchar contra implica oposición explícita.",
        "confianza": "Alta",
        "tipo_migracion": "auto",
        "ejemplo": "A lucha_contra B → A critica_a B",
    },
    {
        "original": "opuesto_a",
        "destino": "critica_a",
        "invertir": False,
        "justificacion": "Ser opuesto implica oposición documentada.",
        "confianza": "Alta",
        "tipo_migracion": "auto",
        "ejemplo": "A opuesto_a B → A critica_a B",
    },
    {
        "original": "contrasta_con",
        "destino": "critica_a",
        "invertir": False,
        "justificacion": "Contrastar implica diferencias significativas.",
        "confianza": "Alta",
        "tipo_migracion": "auto",
        "ejemplo": "A contrasta_con B → A critica_a B",
    },
    {
        "original": "malinterpreta_a",
        "destino": "critica_a",
        "invertir": False,
        "justificacion": "Malinterpretar implica crítica implícita.",
        "confianza": "Alta",
        "tipo_migracion": "auto",
        "ejemplo": "A malinterpreta_a B → A critica_a B",
    },
    {
        "original": "subestima_concepto",
        "destino": "critica_a",
        "invertir": False,
        "justificacion": "Subestimar implica crítica sobre la importancia.",
        "confianza": "Alta",
        "tipo_migracion": "auto",
        "ejemplo": "A subestima_concepto B → A critica_a B",
    },
    {
        "original": "manipula_concepto",
        "destino": "critica_a",
        "invertir": False,
        "justificacion": "Manipular implica crítica negativa sobre el uso.",
        "confianza": "Alta",
        "tipo_migracion": "auto",
        "ejemplo": "A manipula_concepto B → A critica_a B",
    },
    {
        "original": "es_respuesta_a",
        "destino": "critica_a",
        "invertir": False,
        "justificacion": "Una respuesta en contexto académico suele ser crítica o réplica.",
        "confianza": "Media",
        "tipo_migracion": "auto",
        "ejemplo": "A es_respuesta_a B → A critica_a B",
    },
    
    # influenciado_por
    {
        "original": "influyó_en",
        "destino": "influenciado_por",
        "invertir": True,
        "justificacion": "Forma conjugada. 'Influyó en' = fue influencia de.",
        "confianza": "Alta",
        "tipo_migracion": "auto",
        "ejemplo": "A influyó en B → B es influenciado_por A",
    },
    {
        "original": "influye_en",
        "destino": "influenciado_por",
        "invertir": True,
        "justificacion": "Presente de 'influir en'. Misma semántica.",
        "confianza": "Alta",
        "tipo_migracion": "auto",
        "ejemplo": "A influye_en B → B es influenciado_por A",
    },
    {
        "original": "influencio_a",
        "destino": "influenciado_por",
        "invertir": True,
        "justificacion": "Pretérito de 'influenciar'. Misma semántica.",
        "confianza": "Alta",
        "tipo_migracion": "auto",
        "ejemplo": "A influencio_a B → B es influenciado_por A",
    },
    {
        "original": "facilito_por",
        "destino": "influenciado_por",
        "invertir": True,
        "justificacion": "Facilitar implica influencia mediática.",
        "confianza": "Media",
        "tipo_migracion": "auto",
        "ejemplo": "A facilito_por B → B es influenciado_por A",
    },
    {
        "original": "condiciona",
        "destino": "influenciado_por",
        "invertir": True,
        "justificacion": "Condicionar implica influencia causal fuerte.",
        "confianza": "Media",
        "tipo_migracion": "auto",
        "ejemplo": "A condiciona B → B es influenciado_por A",
    },
    
    # estudia_a
    {
        "original": "estudio",
        "destino": "estudia_a",
        "invertir": False,
        "justificacion": "Sinónimo directo. 'Estudió a' = 'estudia_a'.",
        "confianza": "Alta",
        "tipo_migracion": "auto",
        "ejemplo": "Autor estudio Cultura → estudia_a",
    },
    {
        "original": "escribe_estudio_preliminar_para",
        "destino": "estudia_a",
        "invertir": False,
        "justificacion": "Escribir un estudio preliminar implica examen/estudio.",
        "confianza": "Media",
        "tipo_migracion": "auto",
        "ejemplo": "Autor escribe_estudio_preliminar_para Obra → estudia_a",
    },
    {
        "original": "es_fuente_sobre",
        "destino": "estudia_a",
        "invertir": False,
        "justificacion": "Ser fuente sobre un tema implica haberlo estudiado.",
        "confianza": "Alta",
        "tipo_migracion": "auto",
        "ejemplo": "Autor es_fuente_sobre Tema → estudia_a",
    },
    {
        "original": "cita_a",
        "destino": "estudia_a",
        "invertir": False,
        "justificacion": "Citar implica referencia de estudio.",
        "confianza": "Media",
        "tipo_migracion": "auto",
        "ejemplo": "Autor cita_a Autor2 → estudia_a",
    },
    {
        "original": "realiza_trabajo_de_campo_en",
        "destino": "estudia_a",
        "invertir": False,
        "justificacion": "Trabajo de campo es forma de estudio empírico.",
        "confianza": "Alta",
        "tipo_migracion": "auto",
        "ejemplo": "Autor realiza_trabajo_de_campo_en Cultura → estudia_a",
    },
    {
        "original": "evalua_contribucion_de",
        "destino": "estudia_a",
        "invertir": False,
        "justificacion": "Evaluar contribución implica analizar/estudiar.",
        "confianza": "Media",
        "tipo_migracion": "auto",
        "ejemplo": "Autor evalua_contribucion_de Autor2 → estudia_a",
    },
    
    # ── MIGRACIÓN CON REVISIÓN ────────────────────────────────────────────
    
    {
        "original": "contribuye_a",
        "destino": "parte_del_debate",
        "invertir": False,
        "justificacion": "Contribuir a un debate = participar en él.",
        "confianza": "Media",
        "tipo_migracion": "revision",
        "ejemplo": "Gobineau contribuye_a Determinismo racial y cultural",
    },
    {
        "original": "representado_por",
        "destino": "desarrolla_concepto",
        "invertir": False,
        "justificacion": "Un concepto representado por una cultura implica que la cultura lo desarrolla.",
        "confianza": "Media",
        "tipo_migracion": "revision",
        "ejemplo": "Razas de Carus representado_por Europeos",
    },
    {
        "original": "presenta_rasgo",
        "destino": "desarrolla_concepto",
        "invertir": False,
        "justificacion": "Presentar un rasgo cultural implica desarrollar ese concepto.",
        "confianza": "Media",
        "tipo_migracion": "revision",
        "ejemplo": "Islas Marquesas presenta_rasgo Poliginia",
    },
    {
        "original": "desarrollada_por",
        "destino": "desarrolla_concepto",
        "invertir": True,
        "justificacion": "Inversión de 'desarrolla_concepto'.",
        "confianza": "Alta",
        "tipo_migracion": "revision",
        "ejemplo": "Civilización arábiga desarrollada_por Árabes → Árabes desarrolla Civilización arábiga",
    },
    {
        "original": "usa_enfoque",
        "destino": "desarrolla_concepto",
        "invertir": False,
        "justificacion": "Usar un enfoque puede implicar desarrollarlo.",
        "confianza": "Media",
        "tipo_migracion": "revision",
        "ejemplo": "Ratzel usa_enfoque Reduccionismo",
    },
    {
        "original": "aplicado_a",
        "destino": "desarrolla_concepto",
        "invertir": False,
        "justificacion": "Aplicar un concepto implica desarrollarlo en un contexto.",
        "confianza": "Media",
        "tipo_migracion": "revision",
        "ejemplo": "Inferioridad morfológica aplicado_a Criminales",
    },
    {
        "original": "descubierta_por",
        "destino": "precursor_de",
        "invertir": True,
        "justificacion": "Inversión de 'precursor_de'. 'X descubierta por Y' = 'Y es precursor de X'.",
        "confianza": "Media",
        "tipo_migracion": "revision",
        "ejemplo": "Identidad constitucional descubierta_por Crianza pura → Crianza pura es precursora",
    },
    
    # ── MANTENER (Nivel B) ────────────────────────────────────────────────
    
    {
        "original": "relacionado_con",
        "destino": None,
        "invertir": False,
        "justificacion": "Nivel B válido para relaciones conceptuales.",
        "confianza": "Alta",
        "tipo_migracion": "mantener",
        "ejemplo": "Estructuralismo relacionado_con Kinship",
    },
    
    # ── ESCALAR AL AUTOR ──────────────────────────────────────────────────
    
    {
        "original": "clasifica_como_activo",
        "destino": None,
        "invertir": False,
        "justificacion": "Contenido clasificatorio racial evaluativo de Klemm.",
        "confianza": "Baja",
        "tipo_migracion": "escalar",
        "ejemplo": "Klemm clasifica_como_activo Europeos",
    },
    {
        "original": "clasifica_como_pasivo",
        "destino": None,
        "invertir": False,
        "justificacion": "Contenido clasificatorio racial evaluativo de Klemm.",
        "confianza": "Baja",
        "tipo_migracion": "escalar",
        "ejemplo": "Klemm clasifica_como_pasivo Mongólicos",
    },
    {
        "original": "otorga_primacia_a",
        "destino": None,
        "invertir": False,
        "justificacion": "Ranking racial evaluativo.",
        "confianza": "Baja",
        "tipo_migracion": "escalar",
        "ejemplo": "Carus otorga_primacia_a Indostánica",
    },
    {
        "original": "afecta_a",
        "destino": None,
        "invertir": False,
        "justificacion": "Ambigüedad semántica: 'afecta' vs 'influencia'.",
        "confianza": "Baja",
        "tipo_migracion": "escalar",
        "ejemplo": "Selección biológica afecta_a Tasmanios",
    },
    {
        "original": "venera_concepto",
        "destino": None,
        "invertir": False,
        "justificacion": "Carga valorativa explícita no capturada por tipos canónicos.",
        "confianza": "Baja",
        "tipo_migracion": "escalar",
        "ejemplo": "Esquimales venera_concepto Sedna",
    },
    {
        "original": "considera_indispensable",
        "destino": None,
        "invertir": False,
        "justificacion": "Carga valorativa explícita no capturada por tipos canónicos.",
        "confianza": "Baja",
        "tipo_migracion": "escalar",
        "ejemplo": "Lévi-Strauss considera_indispensable Participación etnográfica",
    },
    {
        "original": "limita",
        "destino": None,
        "invertir": False,
        "justificacion": "Relación causal no capturada por tipos canónicos.",
        "confianza": "Baja",
        "tipo_migracion": "escalar",
        "ejemplo": "Caza y recolección limita Densidad de población",
    },
    {
        "original": "limita_expansion_a",
        "destino": None,
        "invertir": False,
        "justificacion": "Relación causal no capturada por tipos canónicos.",
        "confianza": "Baja",
        "tipo_migracion": "escalar",
        "ejemplo": "Población de Turkestán limita_expansion_a Europeos",
    },
    {
        "original": "invadio",
        "destino": None,
        "invertir": False,
        "justificacion": "Error tipográfico + decisión semántica pendiente.",
        "confianza": "Baja",
        "tipo_migracion": "escalar",
        "ejemplo": "Tribus hamíticas invadio África noroccidental",
    },
]

# ═══════════════════════════════════════════════════════════════════════════
# VERSIONES
# ═══════════════════════════════════════════════════════════════════════════

MANIFIESTO_VERSION = "1.1"
SCRIPT_VERSION = "1.0"

# ═══════════════════════════════════════════════════════════════════════════
# FUNCIONES PRINCIPALES
# ═══════════════════════════════════════════════════════════════════════════

def conectar_db(db_path):
    """Conecta a la DB con foreign keys habilitados."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def crear_backup(db_path):
    """Crea backup de la DB. Retorna la ruta del backup."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.parent / f"{db_path.stem}_backup_{timestamp}{db_path.suffix}"
    shutil.copy2(db_path, backup_path)
    return backup_path


def analizar_migracion(conn):
    """
    Analiza la DB y retorna qué cambios se realizarían.
    Retorna lista de dicts con la información de cada migración potencial.
    """
    resultado = []
    
    # Obtener conteo de cada tipo no canónico
    tipos = dict(conn.execute("""
        SELECT tipo, COUNT(*) FROM relaciones GROUP BY tipo
    """).fetchall())
    
    for regla in TABLA_MIGRACION:
        original = regla["original"]
        conteo = tipos.get(original, 0)
        
        if conteo == 0:
            continue
        
        resultado.append({
            "original": original,
            "destino": regla["destino"],
            "invertir": regla["invertir"],
            "justificacion": regla["justificacion"],
            "confianza": regla["confianza"],
            "tipo_migracion": regla["tipo_migracion"],
            "ejemplo": regla["ejemplo"],
            "conteo": conteo,
            "accion": "migrar" if regla["tipo_migracion"] == "auto" else regla["tipo_migracion"],
        })
    
    return resultado


def ejecutar_migracion(conn, dry_run=False):
    """
    Ejecuta la migración sobre la DB.
    Si dry_run=True, solo muestra qué haría sin modificar nada.
    Retorna estadísticas de la migración.
    """
    # Check if migration is already complete
    if es_idempotente(conn):
        return {
            "analizadas": 0,
            "migradas": 0,
            "omitidas": 0,
            "escalar": 0,
            "mantener": 0,
            "revision": 0,
            "errores": 0,
            "detalles": [],
        }
    
    stats = {
        "analizadas": 0,
        "migradas": 0,
        "omitidas": 0,
        "escalar": 0,
        "mantener": 0,
        "revision": 0,
        "errores": 0,
        "detalles": [],
    }
    
    for regla in TABLA_MIGRACION:
        original = regla["original"]
        destino = regla["destino"]
        invertir = regla["invertir"]
        tipo = regla["tipo_migracion"]
        
        # Contar ocurrencias
        conteo = conn.execute(
            "SELECT COUNT(*) FROM relaciones WHERE tipo = ?", (original,)
        ).fetchone()[0]
        
        stats["analizadas"] += conteo
        
        if conteo == 0:
            continue
        
        if tipo == "auto" and destino:
            # Migración automática
            if dry_run:
                stats["migradas"] += conteo
                stats["detalles"].append({
                    "tipo": "auto",
                    "original": original,
                    "destino": destino,
                    "conteo": conteo,
                    "invertir": invertir,
                })
            else:
                try:
                    if invertir:
                        # Swap using individual row updates
                        filas = conn.execute(
                            "SELECT id, origen_id, destino_id FROM relaciones WHERE tipo = ?",
                            (original,)
                        ).fetchall()

                        skipped = 0
                        for id_, origen, destino_fila in filas:
                            # Check if inverted relationship already exists
                            existe = conn.execute(
                                "SELECT 1 FROM relaciones WHERE origen_id = ? AND destino_id = ? AND tipo = ?",
                                (destino_fila, origen, destino)
                            ).fetchone()

                            if existe:
                                skipped += 1
                                continue

                            conn.execute(
                                "UPDATE relaciones SET origen_id = ?, destino_id = ?, tipo = ? WHERE id = ?",
                                (destino_fila, origen, destino, id_)
                            )

                        if skipped > 0:
                            stats["detalles"].append({
                                "tipo": "skip_dup",
                                "original": original,
                                "skipped": skipped,
                            })
                    else:
                        conn.execute(
                            "UPDATE relaciones SET tipo = ? WHERE tipo = ?",
                            (destino, original)
                        )
                    conn.commit()
                    stats["migradas"] += conteo
                    stats["detalles"].append({
                        "tipo": "auto",
                        "original": original,
                        "destino": destino,
                        "conteo": conteo,
                        "invertir": invertir,
                        "exito": True,
                    })
                except Exception as e:
                    conn.rollback()
                    stats["errores"] += 1
                    stats["detalles"].append({
                        "tipo": "error",
                        "original": original,
                        "error": str(e),
                    })
        elif tipo == "revision":
            stats["revision"] += conteo
            stats["omitidas"] += conteo
            stats["detalles"].append({
                "tipo": "revision",
                "original": original,
                "conteo": conteo,
            })
        elif tipo == "mantener":
            stats["mantener"] += conteo
            stats["omitidas"] += conteo
            stats["detalles"].append({
                "tipo": "mantener",
                "original": original,
                "conteo": conteo,
            })
        elif tipo == "escalar":
            stats["escalar"] += conteo
            stats["omitidas"] += conteo
            stats["detalles"].append({
                "tipo": "escalar",
                "original": original,
                "conteo": conteo,
            })
    
    return stats


def generar_reporte(stats, dry_run=False, duracion=0):
    """Genera reporte en Markdown."""
    modo = "DRY-RUN" if dry_run else "APPLY"
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    partes = []
    partes.append("# Reporte de Migración v1.1\n")
    partes.append("**Fecha**: " + fecha)
    partes.append("**Modo**: " + modo)
    partes.append("**Versión Manifiesto**: " + MANIFIESTO_VERSION)
    partes.append("**Versión Script**: " + SCRIPT_VERSION)
    partes.append("**Duración**: " + f"{duracion:.2f}" + "s\n")
    partes.append("---\n")
    partes.append("## Resumen\n")
    partes.append("| Métrica | Valor |")
    partes.append("|---------|-------|")
    partes.append("| Relaciones analizadas | " + str(stats["analizadas"]) + " |")
    partes.append("| Relaciones migradas | " + str(stats["migradas"]) + " |")
    partes.append("| Relaciones omitidas | " + str(stats["omitidas"]) + " |")
    partes.append("| - Revisión manual | " + str(stats["revision"]) + " |")
    partes.append("| - Mantener (Nivel B) | " + str(stats["mantener"]) + " |")
    partes.append("| - Escalar al Autor | " + str(stats["escalar"]) + " |")
    partes.append("| Errores | " + str(stats["errores"]) + " |\n")
    partes.append("---\n")
    partes.append("## Migraciones Automáticas\n")
    partes.append("| Original | Destino | Frec. | Invertir |")
    partes.append("|----------|---------|-------|----------|")
    
    for d in stats["detalles"]:
        if d["tipo"] == "auto":
            inv = "Sí" if d.get("invertir") else "No"
            partes.append("| `" + d["original"] + "` | `" + d["destino"] + "` | " + str(d["conteo"]) + " | " + inv + " |")
    
    partes.append("\n---\n")
    partes.append("## Migraciones Requieren Revisión\n")
    partes.append("| Original | Frec. |")
    partes.append("|----------|-------|")
    
    for d in stats["detalles"]:
        if d["tipo"] == "revision":
            partes.append("| `" + d["original"] + "` | " + str(d["conteo"]) + " |")
    
    partes.append("\n---\n")
    partes.append("## Mantener (Nivel B)\n")
    partes.append("| Original | Frec. |")
    partes.append("|----------|-------|")
    
    for d in stats["detalles"]:
        if d["tipo"] == "mantener":
            partes.append("| `" + d["original"] + "` | " + str(d["conteo"]) + " |")
    
    partes.append("\n---\n")
    partes.append("## Escalar al Autor\n")
    partes.append("| Original | Frec. |")
    partes.append("|----------|-------|")
    
    for d in stats["detalles"]:
        if d["tipo"] == "escalar":
            partes.append("| `" + d["original"] + "` | " + str(d["conteo"]) + " |")
    
    if stats["errores"] > 0:
        partes.append("\n---\n")
        partes.append("## Errores\n")
        partes.append("| Original | Error |")
        partes.append("|----------|-------|")
        for d in stats["detalles"]:
            if d["tipo"] == "error":
                partes.append("| `" + d["original"] + "` | " + d["error"] + " |")
    
    auto_count = sum(1 for r in TABLA_MIGRACION if r["tipo_migracion"] == "auto")
    rev_count = sum(1 for r in TABLA_MIGRACION if r["tipo_migracion"] == "revision")
    man_count = sum(1 for r in TABLA_MIGRACION if r["tipo_migracion"] == "mantener")
    esc_count = sum(1 for r in TABLA_MIGRACION if r["tipo_migracion"] == "escalar")
    
    partes.append("\n---\n")
    partes.append("## Información del Sistema\n")
    partes.append("- **Script**: migrate_v1_1.py v" + SCRIPT_VERSION)
    partes.append("- **Manifiesto**: v" + MANIFIESTO_VERSION)
    partes.append("- **Reglas de migración**: " + str(len(TABLA_MIGRACION)))
    partes.append("- **Automáticas**: " + str(auto_count))
    partes.append("- **Revisión**: " + str(rev_count))
    partes.append("- **Mantener**: " + str(man_count))
    partes.append("- **Escalar**: " + str(esc_count))
    
    return "\n".join(partes)

def es_idempotente(conn):
    """Verifica si la migración ya fue aplicada.
    
    La migración es idempotente si no quedan tipos que deban ser migrados
    automáticamente (excluyendo Nivel B, tipos escalados, y tipos en revisión).
    """
    # Tipos que quedan después de la migración
    tipos_permitidos = {
        # Canónicos Nivel A
        'autor_de', 'influenciado_por', 'critica_a', 'desarrolla_concepto',
        'redefine_a', 'precursor_de', 'pertenece_a', 'estudia_a',
        'contemporaneo_de', 'parte_del_debate', 'es_mentor_de', 'colabora_con',
        # Nivel B
        'relacionado_con', 'contradice', 'depende_de',
        # Escalados al Autor (no se migran)
        'clasifica_como_activo', 'clasifica_como_pasivo',
        'otorga_primacia_a', 'afecta_a', 'venera_concepto',
        'considera_indispensable', 'limita', 'limita_expansion_a', 'invadio',
        # Requieren revisión manual (no se migran automáticamente)
        'contribuye_a', 'representado_por', 'presenta_rasgo',
        'desarrollada_por', 'usa_enfoque', 'aplicado_a', 'descubierta_por',
        # Fallidos por duplicados (se omiten intencionalmente)
        'es_discípulo_de',
    }
    
    tipos_en_db = {row[0] for row in conn.execute("SELECT DISTINCT tipo FROM relaciones").fetchall()}
    tipos_a_migrar = tipos_en_db - tipos_permitidos
    
    return len(tipos_a_migrar) == 0


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Migración Ontológica v1.1 — Cerebro Antropológico"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Analizar sin modificar la DB (modo por defecto)")
    parser.add_argument("--apply", action="store_true",
                        help="Ejecutar migración (requiere confirmación)")
    parser.add_argument("--report", action="store_true",
                        help="Generar informe en Markdown")
    parser.add_argument("--db", type=str, default="data/grafo.db",
                        help="Ruta a la base de datos")
    parser.add_argument("--output", type=str, default=None,
                        help="Ruta para el informe de salida")
    
    args = parser.parse_args()
    
    # Si no se especifica nada, usar dry-run por defecto
    if not args.dry_run and not args.apply:
        args.dry_run = True
    
    db_path = Path(args.db)
    if not db_path.exists():
        print(f"✗ Base de datos no encontrada: {db_path}")
        return 1
    
    print(f"═══════════════════════════════════════════════════════════════")
    print(f"  Migración Ontológica v1.1 — Cerebro Antropológico")
    print(f"  Manifiesto: v{MANIFIESTO_VERSION} | Script: v{SCRIPT_VERSION}")
    print(f"═══════════════════════════════════════════════════════════════")
    print()
    
    conn = conectar_db(db_path)
    
    # Verificar idempotencia
    if es_idempotente(conn):
        print("✓ La migración ya fue aplicada (no hay tipos no canónicos)")
        conn.close()
        return 0
    
    inicio = time.time()
    
    if args.apply:
        print("⚠ MODO APPLY — Se modificará la base de datos")
        print()
        
        # Crear backup
        print("Creando backup...")
        try:
            backup_path = crear_backup(db_path)
            print(f"  ✓ Backup: {backup_path}")
        except Exception as e:
            print(f"  ✗ Error al crear backup: {e}")
            print("  ✗ Migración cancelada")
            conn.close()
            return 1
        
        # Ejecutar migración
        print()
        print("Ejecutando migración...")
        stats = ejecutar_migracion(conn, dry_run=False)
    else:
        print("MODO DRY-RUN — No se modificará nada")
        print()
        stats = ejecutar_migracion(conn, dry_run=True)
    
    duracion = time.time() - inicio
    
    # Mostrar resumen
    print()
    print(f"═══════════════════════════════════════════════════════════════")
    print(f"  RESUMEN")
    print(f"═══════════════════════════════════════════════════════════════")
    print(f"  Analizadas:   {stats['analizadas']}")
    print(f"  Migradas:     {stats['migradas']}")
    print(f"  Omitidas:     {stats['omitidas']}")
    print(f"    Revisión:   {stats['revision']}")
    print(f"    Mantener:   {stats['mantener']}")
    print(f"    Escalar:    {stats['escalar']}")
    print(f"  Errores:      {stats['errores']}")
    print(f"  Duración:     {duracion:.2f}s")
    print(f"═══════════════════════════════════════════════════════════════")
    
    # Generar reporte si se solicitó
    if args.report:
        reporte = generar_reporte(stats, dry_run=args.dry_run, duracion=duracion)
        
        if args.output:
            output_path = Path(args.output)
        else:
            output_path = Path(f"reporte_migracion_{'dryrun' if args.dry_run else 'apply'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
        
        output_path.write_text(reporte, encoding="utf-8")
        print("  Reporte: " + str(output_path))
    
    conn.close()
    return 0


if __name__ == "__main__":
    exit(main())
