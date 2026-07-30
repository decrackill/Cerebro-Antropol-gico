---
description: Fix build and import errors
agent: build-error-resolver
subtask: true
---

# Build Fix Command

Corregir error de build: $ARGUMENTS

## Tu Tarea

1. Leer el mensaje de error completo
2. Identificar tipo de error y archivo
3. Aplicar fix mínimo
4. Verificar que el error desaparezca

## Errores Comunes

### ImportError
- Usar `python3 -m pipeline.cli.menu` en vez de ruta directa
- Verificar `__init__.py` en cada carpeta

### pytest failures
- `pytest -q` para ejecutar
- Verificar que `data/grafo.db` existe

### Linting
```bash
ruff check pipeline/ tests/
```

### Frontend
```bash
npm run dev
npm run build
```

## Proceso
1. Analizar error
2. Fix mínimo
3. Verificar
4. Si persiste, repetir
