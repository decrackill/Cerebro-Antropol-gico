# Guía de Contribución

## Configuración del Entorno

1. Clonar el repositorio
2. Instalar dependencias: `pip install -r requirements.txt && npm install`
3. Configurar `.env` con API keys
4. Ejecutar tests: `pytest`

## Convenciones de Código

### Python
- snake_case para funciones y variables
- UPPER_CASE para constantes
- Type hints en funciones públicas
- Docstrings en español

### JavaScript
- camelCase para variables y funciones
- snake_case para CSS classes

## Estructura de Carpetas

- `pipeline/core/` — Configuración, DB, utilidades
- `pipeline/extract/` — Extracción de PDFs
- `pipeline/review/` — Revisión y limpieza
- `pipeline/cli/` — Interfaz de línea de comandos
- `tests/` — Tests automatizados

## Ejecución de Tests

```bash
pytest -v
```

## Commits

- Mensajes descriptivos en inglés
- Formato: `tipo: descripción`
- Tipos: `feat`, `fix`, `refactor`, `test`, `docs`

## Pull Requests

1. Crear rama features
2. Hacer tests pasen
3. Documentar cambios
4. Solicitar revisión
