---
description: Review code for quality, security, and maintainability
agent: code-reviewer
subtask: true
---

# Code Review Command

Revisar cambios de código: $ARGUMENTS

## Tu Tarea

1. Ejecutar `git diff --name-only HEAD` para cambios recientes
2. Analizar cada archivo modificado
3. Generar reporte estructurado

## Categorías

### Seguridad (CRITICAL)
- Secrets hardcodeados, inyección SQL, XSS, path traversal

### Calidad (HIGH)
- Funciones > 50 líneas, archivos > 800, anidamiento > 4, errores sin manejar

### Estilo (MEDIUM)
- snake_case/camelCase, type hints, pathlib, nombres descriptivos

### Tests (MEDIUM)
- Tests faltantes, cobertura < 80%

## Formato
```
[SEVERIDAD] Título
Archivo: ruta:línea
Problema: [descripción]
Fix: [solución]
```

## Decisión
- **CRITICAL o HIGH**: Bloquear, requerir fixes
- **MEDIUM**: Recomendar fixes
- **LOW**: Mejoras opcionales
