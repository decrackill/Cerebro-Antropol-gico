---
description: Remove dead code and consolidate duplicates
agent: refactor-cleaner
subtask: true
---

# Refactor Clean Command

Limpiar código muerto y duplicados: $ARGUMENTS

## Tu Tarea

1. Identificar código no utilizado
2. Eliminar archivos temporales
3. Fusionar duplicados
4. Verificar integridad

## Áreas

### Ruido Biomédico
- Términos médicos/craneales/óseos en la DB
- Opción 9 del menú

### Duplicados
- Nodos con nombres similares
- Opciones 6 (manual) o 7 (automática) del menú

### Código Muerto
- Variables/funciones sin usar
- Imports no utilizados

### Archivos Temporales
- `runtime/cache/*.json`
- `runtime/logs/*.json`

## Verificación
```bash
python3 -m pipeline.cli.menu  # opción 4 (auditoría)
python3 -m pipeline.cli.menu  # opción 11 (exportar)
```
