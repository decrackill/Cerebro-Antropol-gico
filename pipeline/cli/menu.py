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
from ..core.config import BASE_DIR


def _extraer():
    """Lanza extractor.py sobre un PDF."""
    script = BASE_DIR / "extract" / "extractor.py"
    pdf_path = input("  Ruta del PDF: ").strip()
    if not pdf_path:
        print("  Cancelado.")
        return
    subprocess.run([sys.executable, str(script), pdf_path])


def _modo_manual_menu():
    """Lanza modo_manual.py (generar prompt / pegar respuesta)."""
    script = BASE_DIR / "extract" / "modo_manual.py"
    pdf_path = input("  Ruta del PDF: ").strip()
    if not pdf_path:
        print("  Cancelado.")
        return
    resp = input("  Acción (generar/pegar): ").strip().lower()
    if resp in ("generar", "g"):
        subprocess.run([sys.executable, str(script), pdf_path, "generar"])
    elif resp in ("pegar", "p"):
        subprocess.run([sys.executable, str(script), pdf_path, "pegar"])
    else:
        print("  Opción no válida.")


def _verificar():
    """Lanza verificar_extraccion.py."""
    script = BASE_DIR / "verificar_extraccion.py"
    stem = input("  Nombre stem del PDF (sin extensión): ").strip()
    if not stem:
        print("  Cancelado.")
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
    print("✓ Índices creados/verificados")


def _herramienta_limpiar_archivos():
    """Elimina archivos intermedios procesados."""
    archivos = list(BASE_DIR.glob("candidatos_procesados_*.json"))
    logs = list(BASE_DIR.glob("extraccion_log_*.json"))
    if not archivos and not logs:
        print("✓ No hay archivos temporales para limpiar.")
        return
    print(f"Archivos a eliminar: {len(archivos)} procesados, {len(logs)} logs")
    resp = input("  ¿Eliminar? (s/n): ").strip().lower()
    if resp in ("s", "si", "sí"):
        for f in archivos + logs:
            f.unlink()
        print(f"✓ Eliminados {len(archivos) + len(logs)} archivos")
    else:
        print("  Cancelado")


def _herramienta_mantenimiento():
    """Mantenimiento completo: limpieza + recuperación + export + auditoría."""
    print("═" * 60)
    print("MANTENIMIENTO AUTOMÁTICO COMPLETO")
    print("═" * 60)
    print("\n1/4 Limpieza automática...")
    herramienta_limpieza_automatica(aplicar=True)
    print("\n2/4 Recuperación de relaciones...")
    herramienta_recuperar_relaciones()
    print("\n3/4 Exportación...")
    _herramienta_exportar()
    print("\n4/4 Auditoría final...")
    herramienta_auditoria()
    print("\n✓ Mantenimiento completo")


EXTRAE = {
    "e1": ("Extraer", _extraer, "Lanza extractor.py sobre un PDF"),
    "e2": ("Modo manual", _modo_manual_menu, "Genera prompt para chat o pega respuesta"),
    "e3": ("Verificar", _verificar, "Verifica cobertura de extracción"),
}

OPCIONES = {
    "0": ("Flujo", None, "Muestra el orden paso a paso recomendado"),
    "1": ("Revisar candidatos", herramienta_revisar, "Revisión manual uno por uno"),
    "2": ("Conectar automático", herramienta_conectar_automatico_menu, "Bulk connection"),
    "3": ("Recuperar relaciones", herramienta_recuperar_relaciones, "Rescata relaciones perdidas"),
    "4": ("Auditoría", herramienta_auditoria, "Diagnóstico completo"),
    "5": ("Limpieza segura", herramienta_limpieza_automatica_menu, "Fusión + ruido automático"),
    "6": ("Fusionar duplicados", herramienta_fusionar_duplicados, "Fusión manual uno por uno"),
    "7": ("Fusión automática", herramienta_fusionar_auto, "Fusión sin preguntar"),
    "8": ("Limpieza asistida", herramienta_limpieza_asistida, "Revisión de nodos aislados"),
    "9": ("Limpiar ruido", herramienta_limpiar_auto, "Eliminación agresiva"),
    "10": ("Auditoría (repetir)", herramienta_auditoria, "Re-ejecutar diagnóstico"),
    "11": ("Exportar", _herramienta_exportar, "DB → src/datos.json"),
    "12": ("Reforzar esquema", _herramienta_reforzar_esquema, "Crear índices (run-once)"),
    "13": ("Limpiar archivos", _herramienta_limpiar_archivos, "Eliminar temporales"),
    "14": ("Mantenimiento", _herramienta_mantenimiento, "Cadena automática completa"),
    "15": ("Revisión total", herramienta_revision_total_menu, "Revisar TODOS los nodos"),
}


def mostrar_flujo():
    print("""
╔══════════════════════════════════════════════════════════╗
║  FLUJO RECOMENDADO DE USO                               ║
╠══════════════════════════════════════════════════════════╣
║  1. Colocar PDFs en libros/                             ║
║  2. e1) Extraer entidades                               ║
║  3. 1) Revisar candidatos                               ║
║  4. 2) Conectar automático (si hay muchos)              ║
║  5. 3) Recuperar relaciones perdidas                     ║
║  6. 4) Auditoría                                        ║
║  7. 5-9) Limpiar y deduplicar                           ║
║  8. 11) Exportar                                        ║
║  9. npm run dev (visualizar)                             ║
╚══════════════════════════════════════════════════════════╝
""")


def mostrar_ayuda(clave):
    if clave in EXTRAE:
        nombre, func, desc = EXTRAE[clave]
        print(f"\n  {clave}) {nombre}: {desc}")
        if func and func.__doc__:
            print(f"  {func.__doc__.strip()}")
        return
    if clave in OPCIONES:
        nombre, func, desc = OPCIONES[clave]
        print(f"\n  {clave}) {nombre}: {desc}")
        if func and func.__doc__:
            print(f"  {func.__doc__.strip()}")
        return
    print(f"  No hay ayuda para '{clave}'")


def main():
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  CEREBRO ANTROPOLÓGICO — Centro de Comandos             ║")
    print("║  Escribí 'flujo' para ver el orden paso a paso          ║")
    print("║  Escribí '?N' (ej: '?5') para ver ayuda de una opción  ║")
    print("╚══════════════════════════════════════════════════════════╝")

    while True:
        print("\n── EXTRACCIÓN ──")
        for clave, (nombre, _, desc) in EXTRAE.items():
            print(f"  {clave}) {nombre} — {desc}")

        print("\n── HERRAMIENTAS ──")
        for clave, (nombre, _, desc) in OPCIONES.items():
            print(f"  {clave:>3}) {nombre} — {desc}")

        print("\n  0) Flujo  |  ?N) Ayuda  |  q) Salir")
        resp = input("\n  Opción: ").strip().lower()

        if resp == "q":
            print("  ¡Hasta luego!")
            break
        if resp == "flujo":
            mostrar_flujo()
            continue
        if resp.startswith("?"):
            mostrar_ayuda(resp[1:])
            continue

        if resp in EXTRAE:
            try:
                EXTRAE[resp][1]()
            except KeyboardInterrupt:
                print("\n  (cancelado)")
            except Exception as e:
                print(f"\n  ✗ Error: {e}")
            continue

        if resp in OPCIONES:
            if resp == "0":
                mostrar_flujo()
            elif OPCIONES[resp][1]:
                try:
                    OPCIONES[resp][1]()
                except KeyboardInterrupt:
                    print("\n  (cancelado)")
                except Exception as e:
                    print(f"\n  ✗ Error: {e}")
            continue

        print(f"  ⚠ Opción '{resp}' no reconocida")


if __name__ == "__main__":
    main()
