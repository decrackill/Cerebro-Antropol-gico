# Cerebro Antropológico — Instrucciones Globales

## Stack del Proyecto

| Capa | Tecnología | Comandos |
|------|-----------|----------|
| Pipeline | Python 3.11+ | `python3 -m pipeline.cli.menu` |
| Frontend | Vite + Cytoscape.js | `npm run dev` (puerto :5173) |
| DB | SQLite (`data/grafo.db`) | `PRAGMA foreign_keys = ON` |
| Tests | pytest (107 tests) | `pytest -q` |
| Export | `scripts/export_json.py` | `python3 scripts/export_json.py` |

## Convenciones de Código

- **Python**: `snake_case`, type hints, `pathlib.Path` (no os.path), docstrings en español
- **JavaScript**: `camelCase`, funciones en español, CSS `snake_case`
- **SQL**: `PRAGMA foreign_keys = ON` siempre, índices con opción 12 del menú
- **Frontend**: No usar Wrangler local, Vite sirve index.html, proxy `/api` a producción

## Reglas DB (Ontología v1.1)

- Antes de INSERT en `relaciones`, llamar `validar_relacion()`
- `poblacion` solo es destino de `estudia_a` y origen de `parte_del_debate` (firewall)
- 8 tipos de nodo: autor, obra, concepto, escuela, corriente, cultura, poblacion, debate
- 12 relaciones Nivel A + 3 Nivel B (~40 aliases en config.py)
- Fusión: preservar `ids_previos` en metadatos, no fusionar pares en EXCLUSIONES_FUSION

## Pipeline de Extracción

- Ejecutar siempre con: `python3 -m pipeline.cli.menu`
- Opciones: e1 (extraer), e2 (modo manual), e3 (verificar cobertura)
- Checkpoint reanudable en `runtime/state/checkpoint_<pdf>.json`
- API keys en `pipeline/.env`: GEMINI_API_KEY, GEMINI_API_KEY_2..._5, OPENROUTER_API_KEY

## Mantenimiento

- `python3 -m pipeline.cli.menu` → opción 14 = mantenimiento completo
- Export: opción 11 del menú (genera `frontend/public/datos.json`)
- Auditoría: opción 4 (diagnóstico completo del grafo)
- Limpieza: opciones 5-9 (fusión, ruido biomédico, aislados)

## Testing

```bash
pytest -q              # Rápido
pytest -v              # Verboso
pytest tests/ -k test_db  # Filtro por nombre
```

## Seguridad

- NO hardcodear API keys en código
- Validar todo input de usuario
- Usar parámetros en queries SQL (no f-strings)
- No exponer `.env` ni `data/grafo.db`

## Estructura de Carpetas Clave

```
pipeline/                  → Backend Python
frontend/                  → Aplicación web (Vite)
  src/                     → JS y CSS
  public/datos.json        → Datos curados para producción
libros/                    → PDFs fuente (gitignored)
data/grafo.db              → SQLite (gitignored)
runtime/                   → Caché, logs, checkpoints (gitignored)
scripts/                   → Utilidades standalone
archive/                   → Scripts one-off y docs históricas
tests/                     → Pytest
docs/                      → Documentación ontológica y guías
```
