"""
CENTRO DE COMANDOS del pipeline — un solo punto de entrada para todo.
No reemplaza los scripts individuales (siguen existiendo), simplemente
los organiza en un menú para que no tengas que acordarte de cada nombre.

Uso: python cerebro.py
"""
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent

OPCIONES = {
    "1": ("Extraer un libro nuevo (pide ruta del PDF)", "extraer"),
    "2": ("Revisar candidatos pendientes (manual, uno por uno)", "revisar.py"),
    "3": ("Mantenimiento automático COMPLETO (recomendado tras cada libro)", "mantenimiento"),
    "4": ("Fusionar duplicados (requiere tu criterio, uno por uno)", "fusionar_duplicados.py"),
    "5": ("Limpieza asistida de nodos aislados/ruido (requiere tu criterio)", "limpieza_asistida.py"),
    "6": ("Auditoría completa (solo diagnóstico, no cambia nada)", "auditoria.py"),
    "7": ("Verificar cobertura de un libro específico", "verificar"),
    "8": ("Exportar a datos.json para el navegador", "exportar"),
    "9": ("Limpiar archivos temporales ya procesados", "limpiar.py"),
    "0": ("Salir", None),
}


def correr(script, *args):
    subprocess.run([sys.executable, str(BASE_DIR / script), *args])


def mantenimiento_automatico():
    """
    El combo que corres SIEMPRE después de terminar de revisar un libro,
    antes de mirar el grafo. Solo hace lo que es seguro sin tu intervención;
    al final te dice si queda algo que sí necesita tu criterio.
    """
    print("\n◈ 1/4 — Fusionando duplicados obvios (nombre corto contenido en nombre largo)...")
    correr("limpieza_automatica.py", "--aplicar")

    print("\n◈ 2/4 — Intentando recuperar relaciones que quedaron sin resolver...")
    correr("recuperar_relaciones.py")

    print("\n◈ 3/4 — Exportando a datos.json...")
    subprocess.run([sys.executable, str(BASE_DIR.parent / "scripts" / "export_json.py")])

    print("\n◈ 4/4 — Auditoría final (revisa el reporte abajo)...")
    correr("auditoria.py")

    print("\n" + "═" * 60)
    print("Si la auditoría de arriba todavía muestra nodos aislados o")
    print("duplicados sospechosos, corre desde este menú las opciones")
    print("4 (fusionar) y 5 (limpieza asistida) — esas sí requieren tu criterio.")
    print("═" * 60)


def extraer():
    ruta = input("Ruta del PDF (ej: ../libros/nombre.pdf): ").strip()
    if not ruta:
        print("Cancelado.")
        return
    correr("extractor.py", ruta)


def verificar():
    stem = input("Nombre del PDF SIN extensión ni ruta (ej: boas-f-1911...): ").strip()
    if not stem:
        print("Cancelado.")
        return
    correr("verificar_extraccion.py", stem)


def exportar():
    subprocess.run([sys.executable, str(BASE_DIR.parent / "scripts" / "export_json.py")])


def main():
    while True:
        print("\n" + "═" * 60)
        print("CEREBRO ANTROPOLÓGICO — CENTRO DE COMANDOS")
        print("═" * 60)
        for clave, (descripcion, _) in OPCIONES.items():
            print(f"  {clave}) {descripcion}")

        eleccion = input("\n¿Qué querés hacer?: ").strip()
        if eleccion not in OPCIONES:
            print("⚠ Opción no válida.")
            continue

        descripcion, accion = OPCIONES[eleccion]
        if accion is None:
            print("Hasta luego.")
            break
        elif accion == "extraer":
            extraer()
        elif accion == "mantenimiento":
            mantenimiento_automatico()
        elif accion == "verificar":
            verificar()
        elif accion == "exportar":
            exportar()
        else:
            correr(accion)


if __name__ == "__main__":
    main()
