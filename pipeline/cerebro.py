"""
CEREBRO ANTROPOLÓGICO — Wrapper de compatibilidad
==================================================
Este archivo mantiene compatibilidad con usuarios antiguos.
Usa: python cerebro.py

El código real ahora está en pipeline/cli/menu.py
"""
import sys
from pathlib import Path

# Agregar el directorio padre al path para que funcione como script
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.cli.menu import main

if __name__ == "__main__":
    main()
