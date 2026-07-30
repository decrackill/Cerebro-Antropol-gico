---
description: Enforce TDD workflow with pytest
agent: tdd-guide
subtask: true
---

# TDD Command

Implementar usando TDD estricto: $ARGUMENTS

## Ciclo TDD (OBLIGATORIO)

```
RED → GREEN → REFACTOR → REPETIR
```

1. **RED**: Escribir test fallido PRIMERO — `pytest -q` debe fallar
2. **GREEN**: Código mínimo para que pase — `pytest -q` debe pasar
3. **REFACTOR**: Mejorar, mantener tests verdes
4. **REPETIR**: Hasta completar feature

## Tu Tarea

### Paso 1: Escribir Tests Fallidos (RED)
- Happy path, edge cases, errores
- Ejecutar `pytest -q` — verificar que fallan

### Paso 2: Implementar Mínimo (GREEN)
- Código justo para pasar tests
- Sin optimización prematura
- Ejecutar `pytest -q` — verificar que pasan

### Paso 3: Refactorizar (IMPROVE)
- Extraer constantes, mejorar nombres
- Tests deben seguir pasando

### Paso 4: Verificar Cobertura
- Mínimo 80%
- 100% para lógica ontológica y DB

**OBLIGATORIO**: Tests primero. Nunca saltar la fase RED.
