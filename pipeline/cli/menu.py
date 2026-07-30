"""Menú principal del Cerebro Antropológico.

Punto de entrada CLI que reemplaza cerebro.py monolito.
Uso: python -m pipeline.cli.menu
"""
import subprocess
import sys

from ..review.revision import (
    herramienta_revisar, herramienta_conectar_automatico_menu,
    herramienta_revision_total_menu,
)
from ..review.limpieza import (
    herramienta_limpieza_automatica, herramienta_limpieza_automatica_menu,
    herramienta_fusionar_duplicados, herramienta_fusionar_auto,
    herramienta_limpieza_asistida, herramienta_limpiar_auto,
    herramienta_recuperar_relaciones,
)
from ..review.auditoria import herramienta_auditoria
from ..core.config import BASE_DIR, LIBROS_DIR, PROJECT_ROOT

# ── ANSI colors (sin dependencias externas) ─────────────────────────
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
BOLD = "\033[1m"
RESET = "\033[0m"
DIM = "\033[2m"


def _print_header():
    """Muestra el encabezado con estadísticas de la DB."""
    try:
        from ..core.db import conectar_db
        conn = conectar_db()
        nodos = conn.execute("SELECT COUNT(*) FROM nodos").fetchone()[0]
        rels = conn.execute("SELECT COUNT(*) FROM relaciones").fetchone()[0]
        pendientes = conn.execute(
            "SELECT COUNT(*) FROM nodos WHERE revision_estado != 'ok' OR revision_estado IS NULL"
        ).fetchone()[0]
        conn.close()
        stats = f" {CYAN}{nodos}{RESET} nodos · {CYAN}{rels}{RESET} relaciones"
        if pendientes:
            stats += f" · {YELLOW}{pendientes} pendientes{RESET}"
    except Exception:
        stats = f"{DIM}DB no disponible{RESET}"

    print(f"\n{BOLD}╔{'═' * 57}╗{RESET}")
    print(f"{BOLD}║{RESET}  CEREBRO ANTROPOLÓGICO — Centro de Comandos{' ' * 18}{BOLD}║{RESET}")
    print(f"{BOLD}║{RESET}  {stats}{' ' * max(0, 48 - len(stats) + 20)}{BOLD}║{RESET}")
    print(f"{BOLD}║{RESET}  {DIM}flujo{RESET} sugerido  ·  {DIM}?N{RESET} ayuda  ·  {DIM}help{RESET} guía{' ' * 2}{BOLD}║{RESET}")
    print(f"{BOLD}╚{'═' * 57}╝{RESET}")


# ── Funciones helper del menú ───────────────────────────────────────

def _pdf_stem_a_ruta(stem):
    """Busca un PDF por su stem (sin extensión) en libros/."""
    pdf = LIBROS_DIR / f"{stem}.pdf"
    if not pdf.exists():
        print(f"  {RED}✗{RESET} No existe {pdf}")
        return None
    return pdf


def _extraer():
    """Lanza extractor.py sobre un PDF."""
    stem = input("  Nombre del PDF (sin extensión, ej: boas-f-1911-...): ").strip()
    if not stem:
        print(f"  {YELLOW}⊙{RESET} Cancelado.")
        return
    pdf = _pdf_stem_a_ruta(stem)
    if not pdf:
        return
    subprocess.run([sys.executable, "-m", "pipeline.extract.extractor", str(pdf)])


def _modo_manual_menu():
    """Lanza modo_manual.py (generar prompt / pegar respuesta)."""
    stem = input("  Nombre del PDF (sin extensión): ").strip()
    if not stem:
        print(f"  {YELLOW}⊙{RESET} Cancelado.")
        return
    pdf = _pdf_stem_a_ruta(stem)
    if not pdf:
        return
    resp = input("  Acción (generar/pegar): ").strip().lower()
    if resp in ("generar", "g"):
        subprocess.run([sys.executable, "-m", "pipeline.extract.modo_manual", str(pdf), "generar"])
    elif resp in ("pegar", "p"):
        subprocess.run([sys.executable, "-m", "pipeline.extract.modo_manual", str(pdf), "pegar"])
    else:
        print(f"  {RED}✗{RESET} Opción no válida.")


def _verificar():
    """Lanza verificar_extraccion.py."""
    script = BASE_DIR.parent / "scripts" / "verificar_extraccion.py"
    stem = input("  Nombre stem del PDF (sin extensión): ").strip()
    if not stem:
        print(f"  {YELLOW}⊙{RESET} Cancelado.")
        return
    subprocess.run([sys.executable, str(script), stem])


def _herramienta_exportar():
    """Exporta la DB a src/datos.json."""
    script = BASE_DIR.parent / "scripts" / "export_json.py"
    subprocess.run([sys.executable, str(script)], check=True)


def _herramienta_reforzar_esquema():
    """Crea índices únicos y de rendimiento (run-once)."""
    from ..core.db import conectar_db
    conn = conectar_db()
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_relacion_unica ON relaciones (origen_id, destino_id, tipo)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_rel_tipo ON relaciones(tipo)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_nodo_tipo ON nodos(tipo)")
    conn.commit()
    conn.close()
    print(f"  {GREEN}✓{RESET} Índices creados/verificados")


def _herramienta_limpiar_archivos():
    """Elimina archivos intermedios procesados."""
    archivos = list(BASE_DIR.glob("candidatos_procesados_*.json"))
    logs = list(BASE_DIR.glob("extraccion_log_*.json"))
    if not archivos and not logs:
        print(f"  {GREEN}✓{RESET} No hay archivos temporales para limpiar.")
        return
    print(f"  Archivos a eliminar: {len(archivos)} procesados, {len(logs)} logs")
    resp = input("  ¿Eliminar? (s/n): ").strip().lower()
    if resp in ("s", "si", "sí"):
        for f in archivos + logs:
            f.unlink()
        print(f"  {GREEN}✓{RESET} Eliminados {len(archivos) + len(logs)} archivos")
    else:
        print(f"  {YELLOW}⊙{RESET} Cancelado")


def _herramienta_marcar_revisados():
    """Marca nodos como ontológicamente revisados (revision_estado='ok')."""
    from ..core.db import conectar_db, migrar_revision_estado, marcar_nodos_revisados
    conn = conectar_db()
    migrar_revision_estado(conn)
    print(f"\n  {BOLD}¿Qué nodos marcar como revisados?{RESET}")
    print(f"    {CYAN}t{RESET}) Por tipo (ej. 'concepto', 'poblacion')")
    print(f"    {CYAN}a{RESET}) Todos los nodos")
    print(f"    {CYAN}n{RESET}) Solo nodos pendientes (revision_estado != 'ok')")
    resp = input("  Opción (t/a/n): ").strip().lower()
    if resp == 't':
        tipo = input("  Tipo de nodo (autor/obra/concepto/escuela/corriente/cultura/poblacion/debate): ").strip()
        cnt = marcar_nodos_revisados(conn, tipo=tipo)
        print(f"  {GREEN}✓{RESET} {cnt} nodos de tipo '{tipo}' marcados como revisados")
    elif resp == 'a':
        cnt = marcar_nodos_revisados(conn)
        print(f"  {GREEN}✓{RESET} {cnt} nodos marcados como revisados")
    elif resp == 'n':
        pendientes = conn.execute("SELECT id FROM nodos WHERE revision_estado != 'ok' OR revision_estado IS NULL").fetchall()
        if pendientes:
            ids = [r[0] for r in pendientes]
            cnt = marcar_nodos_revisados(conn, ids=ids)
            print(f"  {GREEN}✓{RESET} {cnt} nodos pendientes marcados como revisados")
        else:
            print(f"  {GREEN}✓{RESET} No hay nodos pendientes.")
    else:
        print(f"  {YELLOW}⊙{RESET} Cancelado.")
    conn.close()


def _herramienta_mantenimiento():
    """Mantenimiento completo: limpieza + recuperación + export + auditoría."""
    print(f"\n{BOLD}═" * 60)
    print("MANTENIMIENTO AUTOMÁTICO COMPLETO")
    print(f"═" * 60 + f"{RESET}")
    print(f"\n{BOLD}1/4{RESET} Limpieza automática...")
    herramienta_limpieza_automatica(aplicar=True)
    print(f"\n{BOLD}2/4{RESET} Recuperación de relaciones...")
    herramienta_recuperar_relaciones()
    print(f"\n{BOLD}3/4{RESET} Exportación...")
    _herramienta_exportar()
    print(f"\n{BOLD}4/4{RESET} Auditoría final...")
    herramienta_auditoria()
    print(f"\n{GREEN}✓{RESET} Mantenimiento completo")


# ── Opciones del menú ───────────────────────────────────────────────
# EXTRAE se mantiene para compatibilidad con tests
EXTRAE = {
    "e1": ("Extraer", _extraer, "Lanza extractor.py sobre un PDF"),
    "e2": ("Modo manual", _modo_manual_menu, "Genera prompt para chat o pega respuesta"),
    "e3": ("Verificar", _verificar, "Verifica cobertura de extracción"),
}

SECCIONES = [
    ("EXTRACCIÓN", [
        ("e1", "Extraer", _extraer, "Lanza extractor.py sobre un PDF"),
        ("e2", "Modo manual", _modo_manual_menu, "Genera prompt para chat o pega respuesta"),
        ("e3", "Verificar", _verificar, "Verifica cobertura de extracción"),
    ]),
    ("REVISIÓN", [
        ("1", "Revisar candidatos", herramienta_revisar, "Revisión manual uno por uno"),
        ("15", "Revisión total", herramienta_revision_total_menu, "Revisar TODOS los nodos de la DB"),
        ("16", "Marcar revisados", _herramienta_marcar_revisados, "Marcar nodos como ontológicamente revisados"),
    ]),
    ("CONEXIONES", [
        ("2", "Conectar automático", herramienta_conectar_automatico_menu, "Resuelve relaciones candidate → DB"),
        ("3", "Recuperar relaciones", herramienta_recuperar_relaciones, "Rescata relaciones de caché histórica"),
    ]),
    ("LIMPIEZA", [
        ("5", "Limpieza segura", herramienta_limpieza_automatica_menu, "Fusión automática + eliminación de ruido"),
        ("6", "Fusionar duplicados", herramienta_fusionar_duplicados, "Fusión manual uno por uno"),
        ("7", "Fusión automática", herramienta_fusionar_auto, "Fusión sin preguntar (usa umbrales)"),
        ("8", "Limpieza asistida", herramienta_limpieza_asistida, "Revisión de nodos aislados"),
        ("9", "Limpiar ruido", herramienta_limpiar_auto, "Eliminación agresiva de ruido biomédico"),
    ]),
    ("DIAGNÓSTICO", [
        ("4", "Auditoría", herramienta_auditoria, "Diagnóstico completo del grafo"),
        ("10", "Auditoría (repetir)", herramienta_auditoria, "Re-ejecutar diagnóstico"),
    ]),
    ("MANTENIMIENTO", [
        ("11", "Exportar", _herramienta_exportar, "DB → public/datos.json"),
        ("12", "Reforzar esquema", _herramienta_reforzar_esquema, "Crear índices (run-once, seguro)"),
        ("13", "Limpiar archivos", _herramienta_limpiar_archivos, "Eliminar temporales y logs"),
        ("14", "Mantenimiento", _herramienta_mantenimiento, "Cadena automática completa"),
    ]),
]

# Para búsqueda rápida por clave
OPCIONES_DICT = {}
for _seccion, items in SECCIONES:
    for clave, nombre, func, desc in items:
        OPCIONES_DICT[clave] = (nombre, func, desc)


def mostrar_flujo():
    """Muestra el orden paso a paso recomendado con indicaciones contextuales."""
    print(f"""
{BOLD}╔{'═' * 57}╗{RESET}
{BOLD}║{RESET}  FLUJO RECOMENDADO DE USO{' ' * 30}{BOLD}║{RESET}
{BOLD}╠{'═' * 57}╣{RESET}
{BOLD}║{RESET}  {CYAN}1.{RESET} Colocar PDFs en {DIM}libros/{RESET}{' ' * 34}{BOLD}║{RESET}
{BOLD}║{RESET}  {CYAN}2.{RESET} {GREEN}e1{RESET} Extraer entidades{' ' * 34}{BOLD}║{RESET}
{BOLD}║{RESET}  {CYAN}3.{RESET} {GREEN}1{RESET}  Revisar candidatos{' ' * 35}{BOLD}║{RESET}
{BOLD}║{RESET}  {CYAN}4.{RESET} {GREEN}2{RESET}  Conectar automático{' ' * 31}{BOLD}║{RESET}
{BOLD}║{RESET}  {CYAN}5.{RESET} {GREEN}3{RESET}  Recuperar relaciones{' ' * 30}{BOLD}║{RESET}
{BOLD}║{RESET}  {CYAN}6.{RESET} {GREEN}4{RESET}  Auditoría{' ' * 42}{BOLD}║{RESET}
{BOLD}║{RESET}  {CYAN}7.{RESET} {GREEN}5-9{RESET} Limpiar y deduplicar{' ' * 30}{BOLD}║{RESET}
{BOLD}║{RESET}  {CYAN}8.{RESET} {GREEN}11{RESET} Exportar (DB → datos.json){' ' * 24}{BOLD}║{RESET}
{BOLD}║{RESET}  {CYAN}9.{RESET} {GREEN}npm run dev{RESET} Visualizar en navegador{' ' * 18}{BOLD}║{RESET}
{BOLD}╚{'═' * 57}╝{RESET}
""")


def mostrar_ayuda(clave):
    """Muestra descripción detallada de una opción."""
    if clave in OPCIONES_DICT:
        nombre, func, desc = OPCIONES_DICT[clave]
        print(f"\n  {CYAN}{clave}{RESET}) {BOLD}{nombre}{RESET}")
        print(f"    {desc}")
        if func and func.__doc__:
            print(f"    {DIM}{func.__doc__.strip()}{RESET}")
        return
    print(f"  {RED}✗{RESET} No hay ayuda para '{clave}'")


# ── Punto de entrada ────────────────────────────────────────────────

def main():
    _print_header()

    while True:
        # Mostrar secciones
        for seccion, items in SECCIONES:
            print(f"\n{BOLD}── {seccion}{RESET}")
            for clave, nombre, _, desc in items:
                print(f"  {CYAN}{clave:>3}{RESET}) {nombre} — {DIM}{desc}{RESET}")

        print(f"\n  {DIM}flujo{RESET} sugerido  ·  {DIM}?N{RESET} ayuda  ·  {DIM}q{RESET} salir")
        resp = input(f"\n  {BOLD}Opción:{RESET} ").strip().lower()

        if resp == "q":
            print(f"\n  {GREEN}¡Hasta luego!{RESET}")
            break
        if resp == "flujo":
            mostrar_flujo()
            continue
        if resp == "help":
            print(f"\n  {DIM}HELP.md disponible en:{RESET} {PROJECT_ROOT / 'HELP.md'}")
            print(f"  {DIM}Comandos rápidos:{RESET} flujo, ?N (ej: ?5), q")
            continue
        if resp.startswith("?"):
            mostrar_ayuda(resp[1:])
            continue

        if resp in OPCIONES_DICT:
            nombre, func, _ = OPCIONES_DICT[resp]
            if func:
                try:
                    func()
                except KeyboardInterrupt:
                    print(f"\n  {YELLOW}⊙{RESET} Cancelado por el usuario")
                except Exception as e:
                    print(f"\n  {RED}✗ Error:{RESET} {e}")
            continue

        print(f"  {YELLOW}⚠{RESET} Opción '{resp}' no reconocida")


if __name__ == "__main__":
    main()
