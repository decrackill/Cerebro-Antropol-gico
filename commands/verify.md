---
description: Run verification loop to validate implementation
agent: build-error-resolver
---

# Verify Command

Ejecutar verificación completa: $ARGUMENTS

## Tu Tarea

Ejecutar verificación integral:

1. **Lint**: `ruff check pipeline/ tests/`
2. **Tests**: `pytest -q`
3. **Frontend build**: `npm run build`
4. **Export**: `python3 scripts/export_json.py`

## Checklist

### Tests
- [ ] Todos los tests pasando
- [ ] Cobertura >= 80%

### Lint
- [ ] Sin errores de ruff
- [ ] Sin warnings

### Build
- [ ] `npm run build` exitoso

### DB
- [ ] Export a datos.json exitoso

## Reporte

### Resumen
- Tests: PASS/FAIL
- Lint: PASS/FAIL
- Build: PASS/FAIL
- Export: PASS/FAIL

### Acciones
[Si FAIL, listar qué arreglar]
