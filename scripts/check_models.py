"""
Ejecuta este script en pipeline/ para ver qué modelos tienes disponibles
y cuál es el estado de tu cuota.

Uso: python check_models.py
"""

import os
from pathlib import Path
from google import genai
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("✗ No se encontró GEMINI_API_KEY en .env")
    exit(1)

client = genai.Client(api_key=api_key)

print("\n◈ Modelos Gemini disponibles para tu API key")
print("─" * 52)

modelos_interes = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    "gemini-1.5-flash-8b-001",
    "gemini-1.5-pro",
]

try:
    modelos = client.models.list()
    nombres = [m.name for m in modelos]

    print(f"\n  Total de modelos en tu cuenta: {len(nombres)}\n")
    print("  Modelos de interés (generateContent):")

    for nombre in nombres:
        nombre_corto = nombre.replace("models/", "")
        if any(m in nombre_corto for m in ["flash", "pro", "gemini"]):
            print(f"    ✓ {nombre_corto}")

except Exception as e:
    print(f"  ✗ Error al listar modelos: {e}")

print("\n─" * 52)
print("  Probando llamada mínima (1 token)…")

for modelo in modelos_interes:
    try:
        r = client.models.generate_content(
            model=modelo,
            contents="Di solo: ok",
        )
        print(f"  ✓ {modelo} → FUNCIONA ({r.text.strip()[:30]})")
        break
    except Exception as e:
        codigo = str(e)[:80]
        print(f"  ✗ {modelo} → {codigo}")

print("─" * 52)
print("  Copia el nombre del primer modelo con ✓ y úsalo en extractor.py\n")
